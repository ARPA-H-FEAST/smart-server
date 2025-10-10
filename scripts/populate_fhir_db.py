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
DB_HOME = PROJECT_ROOT.parent / "data-offline"
sys.path.append(str(PROJECT_ROOT))

from data_api.db_interfaces import DBInterface, FHIR_CONVERTER

# BASE_URL = "http://localhost:8000/fhir-api/"
BASE_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir-api/"
DATA_BASE_URL = BASE_URL + "data-api/"
AUTH_BASE_URL = BASE_URL + "oauth/token/"

db_config_path = os.path.join(PROJECT_ROOT, "data_api/db_interfaces/db_config.json")
with open(db_config_path, "r") as fp:
    config = json.load(fp)
DB_CONNECTIONS = {}
for bco_id, dataset_config in config.items():
    db_path = os.path.join(DB_HOME, dataset_config["db_location"])
    DB_CONNECTIONS[bco_id] = DBInterface(db_path, dataset_config, logger)


def get_access_token():

    fp = None
    client_info = None

    if os.path.isfile("secrets.json"):
        with open("secrets.json", "r") as fp:
            client_info = json.load(fp)
    else:
        path = Path(__file__).parent.parent / "server/secrets.json"
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
        AUTH_BASE_URL,
        json={"grant_type": "client_credentials"},
        headers=headers,
    )

    auth_response = response.json()

    print(f"AUTH: Got response {auth_response}")

    return auth_response

def get_data_sets(access_token):

    query_api = DATA_BASE_URL + "datasets/"

    print("*" * 80)
    print(f"Query API: {query_api}")
    print(f'Auth string: "Authorization: Bearer {access_token}"')
    print("*" * 80)

    response = requests.get(
        query_api, headers={"Authorization": f"Bearer {access_token}"}
    )

    print("*" * 80)
    print(f"Got response: {response}")
    print("*" * 80)

    data = response.json()

    return data


    query_api = DATA_BASE_URL + "dataset-detail/"
    response = requests.post(
        query_api,
        json={
            "bcoid": dataset_bco,
            "sample_limit": limit,
            "sample_offset": sample_offset,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )

    data = response.json()

    return data

def post_fhir_data(access_token, fhir_sample, fhir_endpoint):
    # POST request to the FHIR server via django wrapper
    db_uri = BASE_URL + f"api/fhir-query/{fhir_endpoint}"
    # print(f"Submitting sample:\n{fhir_sample}\n")
    response = requests.post(
        db_uri,
        json=json.dumps(fhir_sample, default=str),
        headers={"Authorization": f"Bearer {access_token}"}
    )
    data = response.json()
    return data

if __name__ == "__main__":

    # Test the connection
    access_info = get_access_token()
    access_token = access_info["access_token"]

    datasets = get_data_sets(access_token)

    data_mapping = {k: v for k, v in datasets["results"].items()}
    print(f"Data mapping: {data_mapping}")

    for db_bco, dbi in DB_CONNECTIONS.items():
        print(f"---> Checking in on BCO {db_bco}")
        metadata = dbi.get_db_metadata()
        print(f"{db_bco} - DB size: {metadata['size']}")
        sample_count = metadata['size']
        chunk_size = 100
        offset = 0
        chunk_count = 0
        while sample_count > 0:
            chunk_limit = chunk_size if chunk_size <= sample_count else sample_count
            # Get the first chunk
            patient_data = dbi.get_sample(
                output_format="fhir", data_type="patient", offset=offset, limit=chunk_limit
            )
            # print(f"{data_mapping[db_bco]}:\n{patient_data['data'][0]}")
            for idx in range(len(patient_data['data'])):
                post_success = post_fhir_data(access_token, patient_data['data'][idx], "Patient")
            # print(f"===> Success?\n{post_success}")
            samples_uploaded = len(patient_data['data'])
            sample_count -= samples_uploaded
            offset += samples_uploaded
            print(f"Uploaded {offset}: {sample_count} samples remaining")
