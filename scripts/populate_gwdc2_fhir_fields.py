import base64
import datetime
import html
import json
import logging
import os
import pandas as pd
import requests
import sys
import time

from argparse import ArgumentParser
from collections import Counter
from pathlib import Path

from script_utils.populate_utilities import (
    objects_from_single_df,
    objects_from_joint_df,
    patients_from_df,
    describe_object_fields,
)

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

PROJECT_ROOT = Path(__file__).parent.parent
# DB_HOME = PROJECT_ROOT / "datadir/processed"
DB_HOME = Path("/data/arpah/processed")
sys.path.append(str(PROJECT_ROOT))

from data_api.db_interfaces import DBInterface, FHIR_CONVERTER

# FHIR_URL = "http://localhost:8080/fhir/"
FHIR_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir/"
# AUTH_URL = "http://localhost:8000/fhir-api/"
AUTH_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir-api/"
AUTH_TOKEN_URL = AUTH_URL + "oauth/token/"

BCO_ID = "FEAST_000013"

db_config_path = os.path.join(PROJECT_ROOT, "data_api/db_interfaces/db_config.json")
with open(db_config_path, "r") as fp:
    config = json.load(fp)
DB_CONNECTIONS = {}
for bco_id, dataset_config in config.items():
    if bco_id != BCO_ID:
        continue
    # Carve-out for parquets
    db_location = dataset_config["db_location"]
    if type(db_location) is not list:
        db_path = os.path.join(DB_HOME, db_location)
    else:
        db_path = str(Path(DB_HOME).parent / db_location[1])
    try:
        dbi = DBInterface(db_path, dataset_config, logger)
        DB_CONNECTIONS[bco_id] = dbi
    except Exception as e:
        if bco_id == "FEAST_000012":
            print(f"**** {bco_id} ****")
            print(f"DB Config: {dataset_config}")
            try:
                dataset_config["db_location"] = "nbcc.db"
                db_path = str(Path(__file__).parent / "nbcc.db")
                dbi = DBInterface(db_path, dataset_config, logger)
                DB_CONNECTIONS[bco_id] = dbi
            except Exception as e:
                raise
            raise
        if bco_id == "FEAST_000004" and os.path.exists("GDWC.duckdb"):
            print(f"Attempting alternate DB load on duckdb")
            try:
                dataset_config["db_location"] = "GDWC.duckdb"
                db_path = str(Path(__file__).parent / "GDWC.duckdb")
                dbi = DBInterface(db_path, dataset_config, logger)
                DB_CONNECTIONS[bco_id] = dbi
            except:
                raise
        print(f"---> EXCEPTION ON DB: {e}")
        print(f"...moving on...")
        continue
if not DB_CONNECTIONS.keys():
    print("No DB connections available, aborting")
    sys.exit(0)

def get_access_token():

    fp = None
    client_info = None

    path = Path(__file__).parent.parent / "server/populate_fhir_secrets.json"

    with open(path, "r") as fp:
        client_info = json.load(fp)
    credential = f"{client_info['clientID']}:{client_info['clientSecret']}"
    encoded_credential = base64.b64encode(credential.encode("utf-8"))

    credential_string = encoded_credential.decode("utf-8")

    headers = {
        "Authorization": f"Basic {credential_string}",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        AUTH_TOKEN_URL,
        json={"grant_type": "client_credentials"},
        headers=headers,
    )

    auth_response = response.json()

    return auth_response

def query_fhir_server(access_token):

    headers = {"Authorization": f"Bearer {access_token}"}
    
    URL = FHIR_URL + "Patient"
    response = requests.get(
        URL,
        headers=headers
    )

    fhir_response = response.json()

    # print(f"Got FHIR response\n{fhir_response}\n")

    return fhir_response

def query_single_patient(access_token, patient_id):

    headers = {"Authorization": f"Bearer {access_token}"}
    
    URL = FHIR_URL + f"Patient?identifier={patient_id}"
    response = requests.get(
        URL,
        headers=headers
    )

    fhir_response = response.json()

    return fhir_response



def post_fhir_data(access_token, fhir_sample, fhir_endpoint):
    # POST request to the FHIR server
    db_uri = FHIR_URL + f"{fhir_endpoint}"
    # print(f"Submitting sample:\n{fhir_sample}\n")
    response = requests.post(
        db_uri,
        json=fhir_sample,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()
    return data

def remove_fhir_data(access_token, sample_url):
    # DELETE request to the FHIR server
    response = requests.delete(
        sample_url,
        headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()
    print(f"===> Got response {data}")
    return data

big_start = time.time()

if __name__ == "__main__":

    access_info = get_access_token()
    access_token = access_info['access_token']

    db_bco = BCO_ID
    dbi = DB_CONNECTIONS[db_bco]
    metadata = dbi.get_db_metadata()
    print(f"{db_bco} - DB size: {metadata['size']}")
    sample_count = metadata['size']

    tables = dbi._get_tables()

    fhir_objects = dbi.config["fhir_columns"]
    fhir_entry_item = "Patient"
    fhir_items = ["Procedure", "DiagnosticReport", "Encounter"]
    # fhir_items = ["Procedure"]
    # fhir_items = ["DiagnosticReport"]
    # fhir_items = ["Encounter"]

    offset = 0
    chunk_size = 10
    print("Handling parquets...")

    parser = ArgumentParser()
    parser.add_argument(
        "--index", "-i", default=-1, type=int,
        help="Index 1-12; or default -1 for testing only"
    )
    parser.add_argument("--dryrun", "-d", action='store_true')
    parser.add_argument("--truncated_run", "-t", action='store_true')
    args = parser.parse_args()

    allowed_index = {-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    if args.index not in allowed_index:
        sys.exit(f"Index arg {type(args.index)} not valid (valid items are {type(allowed_index)})")

    patient_data = dbi.get_sample_for_fhir_upload(
        data_type=fhir_entry_item, offset=offset, limit=chunk_size
    )
    converter = patient_data['converter']

    patient_ids = patient_data['data']['DurableKey_e'].unique()
    print(f"---> Found a total of {len(patient_ids)} patient IDs.")
    patient_count = len(patient_ids)

    # *** Index logic here ***
    if args.index == -1:
        LOOP_LIMIT = 1
        SAMPLE_SIZE = 10
        START_PATIENT = 0
        patient_count = 10
    else:
        patient_indecies = [
            0, 7500, 15000, 22500, 30000, 37500, 45000, 
            52500, 60000, 67500, 75000, 82500, patient_count
            ]
        # patient_indecies = [
        #     0, 75, 150, 225, 300, 375, 450, 
        #     525, 600, 675, 750, 825, int(patient_count/100)
        #     ]

        LOOP_LIMIT = None
        SAMPLE_SIZE = 10
        START_PATIENT = patient_indecies[args.index-1]
        patient_count = patient_indecies[args.index] - START_PATIENT

    record_counter = Counter()

    for fhir_item in fhir_items:
        PATIENTS_REMAINING = patient_count
        PATIENT_INDEX = START_PATIENT
        PATIENTS_COUNTED = 0
        item_limit = LOOP_LIMIT
        iterations = 0

        base_name = f"{fhir_item}-{args.index}"
        log_name = f"upload_records/{base_name}.log"
        log = logging.getLogger(base_name)
        log.setLevel(logging.DEBUG)

        fh = logging.FileHandler(log_name)
        fh.setLevel(logging.DEBUG)
        log.addHandler(fh)        
        
        data_time = time.time()
        # data = {'data': {}}
        data = dbi.get_sample_for_fhir_upload(
            data_type=fhir_item, offset=offset, limit=chunk_size
        )
        log.debug(f" {base_name} : Beginning processing at {datetime.datetime.now()}")
        log.debug(f"---> Looping: Starting at index {START_PATIENT} for {patient_count} patients")
        log.debug(f"Loading data required {time.time() - data_time:.2f}s")

        start = time.time()
        while PATIENTS_REMAINING > 0:
            if item_limit is not None and item_limit > -1:
                item_limit -= 1
                # if item_limit > 0:
                #     print(f"\t\tLOOPS REMAINING: {item_limit}")

            if item_limit is not None and item_limit < 0:
                # print(f"\t\tNO LOOPS REMAINING!!")
                PATIENTS_REMAINING = 0
                break

            # iterations += 1
            # print(f">>>> Iteration {iterations} <<<<")

            if PATIENTS_REMAINING < SAMPLE_SIZE:
                # print("---> SMALL SAMPLE BRANCH <---")
                pids = patient_ids[PATIENT_INDEX:]
            else:
                # print(f"---> TYPICAL SAMPLE BRANCH {PATIENT_INDEX} // SIZE {SAMPLE_SIZE}<---")
                pids = patient_ids[PATIENT_INDEX:PATIENT_INDEX+SAMPLE_SIZE]
            resource_url_strings = {}
            types = set()
            for idx, pid in enumerate(pids):
                response = query_single_patient(access_token, pid)
                # print(f"\n{pid} ---> Server response type: {response}\n")
                types.add(response['resourceType'])
                if response['resourceType'] != "Bundle":
                    raise Exception(f"Unknown respones {response['resourceType']}")
                entry = response.get("entry", None)
                if entry is None:
                    log.debug(f"MISSING ID - PID {pid}: No entry found. Response was {response}")
                    failed_url = FHIR_URL + f"Patient?identifier={pid}"
                    log.debug(f"FAILED URL: {failed_url}")
                    continue
                elif type(entry) is not list:
                    raise Exception(f"Unknown entry shape {entry}")
                elif len(entry) > 0:
                    resource_url_strings[pid] = []
                    for e in entry:
                        resource_url_strings[pid].append("/".join(e['fullUrl'].split('/')[-2:]))
                else:
                    log.debug(f"Missing resource? {response}")
            if type(data['data']) is dict:
                if not args.dryrun:
                    # TODO: CREATE LOG FILE, PASS TO FUNCTION
                    objects = objects_from_joint_df(data, fhir_item, pids, converter, resource_url_strings)
                    log.debug(f"---> Found {len(objects)} total objects for upload...")
                    log.debug(f"\t(Estimate {len(objects) / 3000:.1f} minutes to complete)")
                    post_start = time.time()
                    for idx, o in enumerate(objects):
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        if "resourceType" not in post_success.keys():
                            log.error(f"BAD RESPONSE: {post_success}")
                        elif post_success["resourceType"] != fhir_item:
                            log.error(f"MISMATCHED ITEM for {fhir_item}: {post_success}")
                        # # Only print every 50...
                        # if idx % 50 == 0:
                        #     print(post_success)
                        # if args.index == -1:
                        #     print(post_success)
                        if args.truncated_run and idx > 10:
                            break
                    log.debug(f"{fhir_item}: POSTed {len(pids)} patient IDs {idx} samples uploaded (of {len(objects)}) in {time.time() - post_start:.2f} s")
                    log.debug(f"====> PIDs were {', '.join(pids)}")
                else:
                    describe_object_fields(data['data'], fhir_item, pids, converter)
            elif type(data['data']) is pd.DataFrame:
                if not args.dryrun:
                    # TODO: CREATE LOG FILE, PASS TO FUNCTION
                    objects = objects_from_single_df(data, fhir_item, pids, converter, resource_url_strings)
                    log.debug(f"---> Found {len(objects)} total objects for upload...")
                    log.debug(f"\t(Estimate {len(objects) / 3000:.1f} minutes to complete)")
                    post_start = time.time()
                    for idx, o in enumerate(objects):
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        # if args.index == -1:
                        #     print(post_success)
                        if "resourceType" not in post_success.keys():
                            log.error(f"BAD RESPONSE: {post_success}")
                        elif post_success["resourceType"] != fhir_item:
                            log.error(f"MISMATCHED ITEM for {fhir_item}: {post_success}")
                        # if idx % 50 == 0:
                        #     print(post_success)
                        if args.truncated_run and idx > 10:
                            break
                    log.debug(f"{fhir_item}: POSTed {len(pids)} patient IDs with {idx} samples in {time.time() - post_start:.2f} s")
                    log.debug(f"====> PIDs were {', '.join(pids)}")
                else:
                    describe_object_fields(data['data'], fhir_item, pids, converter)
                # print(f"IDs: ({len(identifiers)} total): {len(set(identifiers))} unique")

            PATIENTS_REMAINING -= len(pids)
            PATIENT_INDEX += len(pids)
            record_counter[fhir_item] += len(pids)
            log.debug(f"---> {fhir_item}: Now setting index to {PATIENT_INDEX}")

        log.debug(f"---> FHIR Item {fhir_item}: {PATIENT_INDEX} samples required {time.time() - start:.2f}s")

for k, v in record_counter.items():
    log.debug(f"{k}: {v} records recorded.")
log.debug("*"*80)
log.debug(f"{base_name} : Halting processing at {datetime.datetime.now()}")
log.debug(f"\tTotal processing time was {(time.time() - big_start) / 60:.1f} minutes")
log.debug("*"*80)
# with open(f"upload_records/gwdc2-fhir-fields-THREAD_{args.index}.txt", "w") as log:
#     for k, v in record_counter.items():
#         log.write(f"{k}: {v} records recorded.\n")
#     log.write(f"Total time required was {time.time()-big_start:.2f}\n")

