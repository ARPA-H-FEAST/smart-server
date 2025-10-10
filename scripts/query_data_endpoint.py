import base64
import json
import os
import requests
import time

from pathlib import Path

# BASE_URL = "http://localhost:8000/fhir-api/"
BASE_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir-api/"
DATA_BASE_URL = BASE_URL + "data-api/"
AUTH_BASE_URL = BASE_URL + "oauth/token/"


def get_auth_token():

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

    print(f"Credential: {credential_string}")

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


def query_data_set_details(access_token, dataset_bco):

    query_api = DATA_BASE_URL + "dataset-metadata/"
    response = requests.post(
        query_api,
        json={"bcoid": dataset_bco},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = response.json()

    return data


def query_data_point(access_token, dataset_bco, sample_offset=0, limit=1):

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


if __name__ == "__main__":

    auth_response = get_auth_token()

    access_token = auth_response["access_token"]
    # access_token = None

    data = get_data_sets(access_token)

    print("*" * 80)
    print(f"---> Found data sets {data}")
    print("*" * 80)

    sample_patient = {}

    datasets = data["results"]

    single_dataset_key = list(datasets.keys())[0]

    start = time.time()

    dataset_bco = single_dataset_key
    dataset = datasets[dataset_bco]

    print(f"{dataset_bco}: {dataset}")
    response = query_data_set_details(access_token, dataset_bco)

    print("*" * 80)
    print(f"Dataset metadata response:")
    for k, v in response.items():
        print(f"{k}:\n{v}\n")
    print("*" * 80)

    sample_offset = 0
    sample_limit = 50

    # Collect a solitary data point
    data = query_data_point(access_token, dataset_bco)
    # Uncomment below line to get many data points
    # data = query_data_point(dataset_bco, shape=list, sample_offset=sample_offset, limit=sample_limit)

    sample_data = data["db_entries"]
    # metadata = data["db_metadata"]
    print("*" * 80)
    print(f"Dataset sample response:")
    for k, v in data.items():
        print(f"{k}:\n{v}\n")
    print("*" * 80)

    # sample_patient[dataset] = sample_data[0]

    print(f"Query roundtrip required {time.time() - start:.3f} s")

    # print(sample_patient)

    # # Focus on NBCC data
    # dataset = datasets["FEAST_000012"]

    # # Focus on GWDC data
    # dataset = datasets["FEAST_000004"]
