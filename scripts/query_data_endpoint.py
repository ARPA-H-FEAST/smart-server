import base64
import json
import os
import requests
import time

from pathlib import Path

# FHIR_URL = "http://localhost:8080/fhir/"
FHIR_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir/"
# AUTH_URL = "http://localhost:8000/fhir-api/"
AUTH_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir-api/"

AUTH_TOKEN_URL = AUTH_URL + "oauth/token/"


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

    # print(f"Credential: {credential_string}")

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

    print(f"AUTH: Got response {auth_response}")

    return auth_response

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

def query_fhir_server(access_token, URL=None):

    headers = {"Authorization": f"Bearer {access_token}"}
    
    URL = (FHIR_URL + "Patient") if URL is None else URL
    response = requests.get(
        URL,
        headers=headers
    )

    fhir_response = response.json()

    print(f"Got FHIR response {fhir_response}")

    return fhir_response

if __name__ == "__main__":

    auth_response = get_auth_token()

    access_token = auth_response["access_token"]

    fhir_sample = query_fhir_server(access_token)

    next_url = None
    for k in fhir_sample.keys():
        if k != "link":
            continue
        for link_obj in fhir_sample[k]:
            # print(f"Link relation: {link_obj['relation']}")
            # print(f"Link url: {link_obj['url']}")
            if link_obj['relation'] == "next":
                next_url = link_obj['url']
    assert next_url is not None
    next_url = next_url.replace("http://127.0.0.1:4243","https://feast.mgpc.biochemistry.gwu.edu")
    print(f"Collecting new information from URL {next_url}")
    next_sample = query_fhir_server(access_token, URL=next_url)
