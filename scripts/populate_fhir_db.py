import base64
import json
import logging
import os
import requests
import sys

from pathlib import Path

logger = logging.getLogger("mine")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

PROJECT_ROOT = Path(__file__).parent.parent
DB_HOME = PROJECT_ROOT / "datadir/processed"
sys.path.append(str(PROJECT_ROOT))

from data_api.db_interfaces import DBInterface, FHIR_CONVERTER

FHIR_URL = "http://localhost:8080/fhir/"
# FHIR_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir/"
AUTH_URL = "http://localhost:8000/fhir-api/"
AUTH_TOKEN_URL = AUTH_URL + "oauth/token/"

MODE = "notdev"
UPLOAD = True
DRYRUN = True
# The DB can take up to a minute to populate 
# & flush indicies, so just make the script run separate times
DELETE_ALL = not UPLOAD

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
        if bco_id != "FEAST_000004":
            raise
        if os.path.exists("GDWC.duckdb"):
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

    # print(f"AUTH: Got response {auth_response}")

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

    if not DRYRUN:
        # Test the connection
        access_info = get_access_token()
        access_token = access_info["access_token"]
        if not access_token:
            print(f"Access token error! Aborting")
            sys.exit(1)
        # print(f"\tAccess token: {access_token}")

        import time
        # Ping the FHIR server
        samples = query_fhir_server(access_token)


    if MODE == "dev":

        fp = None
        client_info = None

        path = Path(__file__).parent.parent / "data_api/dummy/patient0.json"
        with open(path, "r") as fp:
            patient0 = json.load(fp)
        if UPLOAD:
            print(f"Shipping patient0:\n{patient0}")
            for i in range(1):
                response = post_fhir_data(access_token, patient0, "Patient")
            print(f"Patient0 response: {response}\n\t(infected...)")

        if DELETE_ALL:
            while True:
                print(f"Got more samples! ....\n{samples}")
                time.sleep(1)
                if "total" in samples.keys() and samples["total"] == 0:
                    break
                # remove samples
                if "entry" in samples.keys():
                    sample_count = len(samples["entry"])
                    print(f"Removing {sample_count} samples...")
                    for entry in samples["entry"]:
                        remove_fhir_data(access_token, entry["fullUrl"])
                elif "link" in samples.keys():
                    for l in samples["link"]:
                        if l["relation"] != "next":
                            continue
                        samples = requests.get(
                            l["url"], 
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                    # Get the next batch
                    print(f"---> Found {samples['total']} more samples...")
                    links = samples["link"]
                    for entry in samples["entry"]:
                        remove_fhir_data(access_token, entry["fullUrl"])
                elif "total" in samples.keys():
                    if "link" not in samples.keys():
                        break
                    else:
                        for link in samples["link"]:
                            if "self" not in link["relation"]:
                                continue
                        samples = requests.get(
                            link, 
                            headers={"Authorization": f"Bearer {access_token}"}
                        )
                        for entry in samples['entry']:
                            remove_fhir_data(entry["fullUrl"])
                samples = query_fhir_server(access_token)
        print("Dev job complete, exiting")
        import sys
        sys.exit(0)

    for db_bco, dbi in DB_CONNECTIONS.items():
        # print(f"---> Checking in on BCO {db_bco}")
        metadata = dbi.get_db_metadata()
        print(f"{db_bco} - DB size: {metadata['size']}")
        sample_count = metadata['size']

        tables = dbi._get_tables()
        # print(f"Got tables\n{tables}\n")

        # for fhir_objects, fhir_columns in dbi.config["fhir_columns"].items():
        #     print(f"Found FHIR conversions: {fhir_objects}\n{fhir_columns}")

        fhir_objects = dbi.config["fhir_columns"]
        current_item = "Patient"
        if current_item not in fhir_objects.keys():
            continue

        if db_bco == "FEAST_000013":
            # Special handling of parquet/pandas frames in memory
            patient_data = dbi.get_sample(
                output_format="fhir", data_type=current_item, offset=offset, limit=chunk_limit
            )
            if DRYRUN:
                samples_uploaded = len(patient_data['data'])
                sample_count -= samples_uploaded
                offset += samples_uploaded
                continue

            print("Parquet --- success?")
            for idx in range(len(patient_data['data'])):
                post_success = post_fhir_data(access_token, patient_data['data'][idx], "Patient")
            print(f"===> Success?\n{post_success}")
            samples_uploaded = len(patient_data['data'])
            sample_count -= samples_uploaded
            offset += samples_uploaded

            continue

        chunk_size = 100
        offset = 0
        chunk_count = 0
        while sample_count > 0:
            chunk_limit = chunk_size if chunk_size <= sample_count else sample_count
            # Get the first chunk
            patient_data = dbi.get_sample(
                output_format="fhir", data_type=current_item, offset=offset, limit=chunk_limit
            )
            # print(f"{db_bco}:\n{patient_data['data'][0]}")
            if DRYRUN:
                samples_uploaded = len(patient_data['data'])
                sample_count -= samples_uploaded
                offset += samples_uploaded
                continue

            for idx in range(len(patient_data['data'])):
                post_success = post_fhir_data(access_token, patient_data['data'][idx], "Patient")
            samples_uploaded = len(patient_data['data'])
            sample_count -= samples_uploaded
            offset += samples_uploaded
            # print(f"===> Success?\n{post_success}")
            # print(f"Uploaded {offset}: {sample_count} samples remaining")
