import base64
import json
import logging
import os
import pandas as pd
import requests
import sys
import time

from pathlib import Path

from script_utils.populate_utilities import (
    objects_from_single_df,
    objects_from_joint_df,
    patients_from_df,
)

logger = logging.getLogger("mine")
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

db_config_path = os.path.join(PROJECT_ROOT, "data_api/db_interfaces/db_config.json")
with open(db_config_path, "r") as fp:
    config = json.load(fp)
DB_CONNECTIONS = {}
for bco_id, dataset_config in config.items():
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

if __name__ == "__main__":

    # Test the connection
    access_info = get_access_token()
    access_token = access_info["access_token"]
    if not access_token:
        print(f"Access token error! Aborting")
        sys.exit(1)
    print(f"\tAccess token: {access_token}")

    db_bco = "FEAST_000013" # "FEAST_000013"|"FEAST_000004"|"FEAST_000012" 
    for db_bco, dbi in DB_CONNECTIONS.items():
    dbi = DB_CONNECTIONS[db_bco]
    print(f"---> Checking in on BCO {db_bco}")
    metadata = dbi.get_db_metadata()
    print(f"{db_bco} - DB size: {metadata['size']}")
    sample_count = metadata['size']

    tables = dbi._get_tables()
    # print(f"Got tables\n{tables}\n")

    # for fhir_objects, fhir_columns in dbi.config["fhir_columns"].items():
    #     print(f"Found FHIR conversions: {fhir_objects}\n{fhir_columns}")

    fhir_objects = dbi.config["fhir_columns"]
    fhir_entry_item = "Patient"
    # fhir_items = ["Procedure"]
    fhir_items = ["Procedure", "DiagnosticReport", "Encounter"]
    # if fhir_item not in fhir_objects.keys():
    #     continue

    if db_bco == "FEAST_000013":

        offset = 0
        chunk_size = 10
        print("Handling parquets...")

        patient_data = dbi.get_sample_for_fhir_upload(
            data_type=fhir_entry_item, offset=offset, limit=chunk_size
        )
        converter = patient_data['converter']

        # Get the patient objects, upload, etc.
        patient_objects = patients_from_df(patient_data['data'], converter)
        for idx, o in enumerate(patient_objects):
            post_results = post_fhir_data(access_token, o.as_json(), "Patient")
            print(f"Patient POST: {post_results}")
            if idx > 9:
                break

        patient_ids = patient_data['data']['DurableKey_e'].unique()
        print(f"---> Found a total of {len(patient_ids)} patient IDs.")
        patient_count = len(patient_ids)

        LOOP_LIMIT = 1
        SAMPLE_SIZE = 1

        for fhir_item in fhir_items:
            PATIENTS_REMAINING = patient_count
            PATIENT_INDEX = 0
            PATIENTS_COUNTED = 0
            item_limit = LOOP_LIMIT
            iterations = 0
            
            data_time = time.time()
            # data = {'data': {}}
            data = dbi.get_sample_for_fhir_upload(
                data_type=fhir_item, offset=offset, limit=chunk_size
            )
            print(f"Loading data required {time.time() - data_time:.2f}s")

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
                # print(f"---> Checking for results on FHIR item {fhir_item} with {len(pids)} patient IDs")
                # print(f"---> Patient IDs are {pids}")
                # Try small joins
                if type(data['data']) is dict:
                    # TODO: CREATE LOG FILE, PASS TO FUNCTION
                    objects = objects_from_joint_df(data, fhir_item, pids, converter)
                    post_start = time.time()
                    for o in objects:
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        print(post_success)
                    print(f"{fhir_item}: POSTed {len(objects)} samples in {time.time() - post_start:.2f} s")
                elif type(data['data']) is pd.DataFrame:
                    # TODO: CREATE LOG FILE, PASS TO FUNCTION
                    objects = objects_from_single_df(data, fhir_item, pids, converter)
                    post_start = time.time()
                    for o in objects:
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        print(post_success)
                    print(f"{fhir_item}: POSTed {len(objects)} samples in {time.time() - post_start:.2f} s")
                    # print(f"IDs: ({len(identifiers)} total): {len(set(identifiers))} unique")

                PATIENTS_REMAINING -= len(pids)
                PATIENT_INDEX += len(pids)

            print(f"---> FHIR Item {fhir_item}: {PATIENT_INDEX} samples required {time.time() - start:.2f}s")

        print(f"Processing BCO ID {db_bco} -- {sample_count} samples")
        print(f"...skipping")
        continue
        chunk_size = 100
        offset = 0
        chunk_count = 0
        while sample_count > 0:
            chunk_limit = chunk_size if chunk_size <= sample_count else sample_count
            try:
                # Get the first chunk
                data = dbi.get_sample_for_fhir_upload(
                    data_type=fhir_item,
                    offset=offset, limit=chunk_limit
                )
            except Exception as e:
                raise
            print(f"Now on sample {offset}")
            if DRYRUN:
                print(f"{db_bco}:\n{data['data'][0]}")
                samples_uploaded = len(data['data'])
                sample_count -= samples_uploaded
                offset += samples_uploaded
                break

            for idx in range(len(data['data'])):
                post_success = post_fhir_data(access_token, data['data'][idx], "Patient")
            samples_uploaded = len(data['data'])
            sample_count -= samples_uploaded
            offset += samples_uploaded
            # print(f"===> Success?\n{post_success}")
            # print(f"Uploaded {offset}: {sample_count} samples remaining")

