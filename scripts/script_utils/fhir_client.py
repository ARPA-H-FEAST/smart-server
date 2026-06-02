import base64
import json
import requests

from pathlib import Path

FHIR_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir/"
AUTH_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir-api/"
AUTH_TOKEN_URL = AUTH_URL + "oauth/token/"

_SECRETS_PATH = Path(__file__).parent.parent.parent / "server/populate_fhir_secrets.json"


def get_access_token():
    with open(_SECRETS_PATH, "r") as fp:
        client_info = json.load(fp)
    credential = f"{client_info['clientID']}:{client_info['clientSecret']}"
    encoded_credential = base64.b64encode(credential.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {encoded_credential}",
        "Cache-Control": "no-cache",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        AUTH_TOKEN_URL,
        json={"grant_type": "client_credentials"},
        headers=headers,
    )
    return response.json()


def query_fhir_server(access_token):
    response = requests.get(
        FHIR_URL + "Patient",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()


def query_single_patient(access_token, patient_id):
    response = requests.get(
        FHIR_URL + f"Patient?identifier={patient_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()


def build_if_none_exist(fhir_sample):
    identifiers = fhir_sample.get("identifier")
    if not isinstance(identifiers, list) or not identifiers:
        return None
    id0 = identifiers[0]
    if not isinstance(id0, dict):
        return None
    value = id0.get("value")
    if not value:
        return None
    system = id0.get("system")
    return f"identifier={system}|{value}" if system else f"identifier={value}"


def post_fhir_data(access_token, fhir_sample, fhir_endpoint):
    headers = {"Authorization": f"Bearer {access_token}"}
    if_none_exist = build_if_none_exist(fhir_sample)
    if if_none_exist:
        headers["If-None-Exist"] = if_none_exist
    response = requests.post(
        FHIR_URL + fhir_endpoint,
        json=fhir_sample,
        headers=headers,
    )
    return response.json()


def remove_fhir_data(access_token, sample_url):
    response = requests.delete(
        sample_url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return response.json()
