import datetime
import math
import random


try:
    ## Import in Django
    from .fhir_objs.R5 import (
        Patient,
        DiagnosticReport,
        GenomicStudy,
    )
    from django.conf import settings
    FHIR_VERSION = settings.FHIR_VERSION
except:
    
    import sys
    from pathlib import Path

    this_path = Path(__file__).parent.parent.parent
    print(f"===> Adding path {this_path}")
    sys.path.append(str(this_path))
    ## Import for command line
    from data_api.db_interfaces.fhir_objs.R5 import (
        Patient, DiagnosticReport, Procedure,
        Encounter, Observation, Medication,
        GenomicStudy, Location
    )
    FHIR_VERSION = "R5"
    ############
    # SHIM TOOLS
    import json
    ############

import datetime

gwdc_converter = {
    "pronoun_map": {"Male": "male", "Female": "female", "*Unspecified": "unknown", "": "unknown"}
}

nbcc_converter = {
    "pronoun_map": {
    'Male': "M", 'Female': "F", 'N': "N/A", 'Intersex': "Intersex", 'Masculino': "M",
    'Weiblich': "F", 'Maschio': "M", 'Femelle': "F",
    'Erkek': "M", 'Vrouw': "F", 'Hembra':"F", 'Femmina': "F", 'mann': "M",
    'Manlig': "M", 'Kvinna': "F", 'Malen': "M",
    'Maleb': "M", 'Malee': "M", 'Malep': "M", 'Male\x14': "M", 'Malel': "M",
    'Male\x10': "M", 'Maleg': "M", 'Malez': "M",
    'MaleS': "M", 'Malea': "M", 'Maler': "M", 'Males': "M", 'Maley': "M",
    'Malet': "M", 'Femeie': "F", 'Feminino': "F",
    'Mannetje': "M",
    },
    "alive_map": {'t': 'Y', 'N': 'N', 'alive': 'Y'},
    "cancer_map": {
        "N": "No", "No": "No", "I don't know": "I don't know", "Yes": "Yes", "Nein": "No",
        "Non": "No", "Nee": "No", "Je ne sais pas": "I don't know", "Non lo so": "I don't know",
        "Nei": "No", "Ja": "Yes", "Nie": "No", "tak": "Yes", "Nem": "No",
        "Nej": "No", "Nom": "No", "Nor": "No", "No": "No", "Nol": "No", "-e": "Unknown",
        "No": "No", "Nof": "No", "Noe": "No", "No": "No", "Nog": "No",
        "Noa": "No", "Nod": "No", "NoL": "No", "Nos": "No",
        "Noc": "No", "NoA": "No", "-I": "Unknown", "-a": "Unknown",
        "Nob": "No", "Nok": "No", "Nu": "No", "Noi": "No",
        "Ne": "No", "Oui": "Yes", "sim": "Yes", "Jag vet inte": "I don't know",
        "Nie wiem": "I don't know", 
        'No\x01': "No", 'No\x03': "No", 'No\x02': "No",
    },
    "secondary_map": {"M": "male", "F": "female", "Intersex": "other", "N/A": "unknown"}
}

def generate_random_datetime(start_dt, end_dt):
    """
    Generates a random datetime object between two specified datetime objects.

    Args:
        start_dt (datetime.datetime): The starting datetime.
        end_dt (datetime.datetime): The ending datetime.

    Returns:
        datetime.datetime: A random datetime object within the specified range.
    """
    time_delta = end_dt - start_dt
    random_seconds = random.uniform(0, time_delta.total_seconds())
    return start_dt + datetime.timedelta(seconds=random_seconds)

# Example Usage:
start_date = datetime.datetime(2023, 1, 1, 0, 0, 0)
end_date = datetime.datetime(2024, 12, 31, 23, 59, 59)

OLD_DATE = datetime.date(1900, 1, 1)
FUTURE_DATE = datetime.date(2199, 1, 1)

def record_to_datetime(record):
    try:
        return datetime.datetime(record).isoformat()
    except:
        return generate_random_datetime(start_date, end_date).strftime('%Y-%m-%d')

def nbcc_gender_converter(record):
    if record in nbcc_converter["secondary_map"]:
        return nbcc_converter["secondary_map"][record]
    primary_key = nbcc_converter["pronoun_map"][record]
    return nbcc_converter["secondary_map"][primary_key]

def gwdc_patient(record):
    return Patient(
        {
            "gender": gwdc_converter["pronoun_map"][record[0]],
            "communication": [{"language": {"text": record[1]}}],
            "birthDate": record[2].strftime("%Y-%m-%d"),
            "deceasedDateTime": None 
                if record[3] is None 
                else record[3].strftime("%Y-%m-%d"),
            "identifier": [{"value": record[4]}],
        }
    )

def brprlu_date(dateValue):
    try:
        return None if math.isnan(dateValue) else datetime.datetime(int(dateValue), 1, 1).date().strftime("%Y-%m-%d")
    except Exception as e:
        print(f"Exception in deceased time conversion: {e}")
        print(f"Record was {dateValue}")

def brprlu_duration(length):
    try:
        return 0 if math.isnan(length) else int(length)
    except Exception as e:
        print(f"Exception in deceased time conversion: {e}")
        print(f"Record was {length}")


def brprlu_patient(record, p_ref=None):
    return Patient(
        {
            "gender": gwdc_converter["pronoun_map"][record[0]],
            "communication": [{"language": {"text": record[1]}}],
            "birthDate": datetime.datetime(int(record[2]), 1, 1).date().strftime("%Y-%m-%d"),
            "deceasedDateTime": brprlu_date(record[3]),
            "identifier": [{"value": record[4]}],
            "address": [{
                "state": record[5],
                "country": record[6],
            }],
            # "generalPrectitioner": [{"reference": record[7]}]
        }
    )

def nbcc_patient(record, p_ref=None):
    return Patient(
        {
            "gender": nbcc_gender_converter(record[0]),
            "birthDate": record_to_datetime(record[1]),
            "deceasedDateTime": None if record[2] == "N" else record_to_datetime(record[2]),
            "identifier": [{"value": record[3]}],
        }
    )


def gwdc_diagnosis(record, p_ref=None):
    return DiagnosticReport(
        {
            "status": "final",
            "category": record[2],
            "code": record[3],
            "subject": record[0],
            "effective": None if record[4] is None else datetime.datetime(int(record[4]), 1, 1).date().strftime("%Y-%m-%d"),
            "performer": record[1],
            "encounter": record[4],
            "identifier": record[6],
            "interpreter": record[7],
        }
    )

def brprlu_diagnosis(record, p_ref=None):
    ref = "Patient/1" if p_ref is None else p_ref
    return DiagnosticReport(
        {
            "identifier": [{"value": str(record[6])}],
            "status": "final", # str(record[9]),
            "code": {"text": record[15]},
            "subject": {"reference": ref, "type": "Patient"}, # {"reference": record[0], "type": "Patient"},
            # "encounter": {"reference": str(record[4]), "type": "Encounter"},
            "effectiveDateTime": "2299-01-01" if record[5] < 1900 else datetime.datetime(int(record[5]), 1, 1).date().strftime("%Y-%m-%d"),
            # "performer": [{"reference": "Practitioner/1", "type": "Performer"}],  # [{"reference": str(record[8]), "type": "Performer"}],
            # "result": [{"reference": "Observation/1", "type": "Observation"}],  # [{"reference": record[10], "type": "Observation"}],
            "note": [{"text": "\n".join(record[11:15]), "author": str(record[8])}],
            "supportingInfo": [{"type": {"text": record[15]}, "reference": {"type": "FalseSupportingInfo", "reference": "NestedReference"}}],
            "conclusion": record[17],
            "conclusionCode": [
                {
                    "text": f"{record[18]}:{record[19]}", 
                    # "coding": [{"code": "bah!", "system": "bah!", "version": "humbug!"}]
                }
            ],
        }
    )


def nbcc_diagnosis(record, p_ref=None):
    return DiagnosticReport(
        {
            "identifier": "nbcc",
            "status": "final",
            "category": record[0],
            "code": record[4],
            "subject": record[9],
            "performer": "nbcc",
            "result": record[3],
            "annotation": (record[7], record[8]),
            "supporting_info": (record[5], record[6]),
            "effective": datetime.datetime(record[1]),
        }
    )

def brprlu_procedure(record, p_ref=None):
    # for idx, val in enumerate(record):
    #     print(f"{idx}: {val} (type {type(val)})")
    # print(f"Datetime: {datetime.datetime(int(record[5]), 1, 1, 1).isoformat()}")
    # print(f"Record:\n{record}\n")
    start_time = "1900-01-01" if record[14] <  OLD_DATE else record[14].strftime("%Y-%m-%d")
    end_time = "2099-12-31" if record[15] >  FUTURE_DATE else record[15].strftime("%Y-%m-%d")
    # f_url = "https://feast.mgpc.biochemistry.gwu.edu/"
    f_url = "/data"
    fhir_url = f_url + "fhir/"
    note_text = "\n".join(record[7:12]) + "\n".join(record[17:])
    ref = "Patient/1" if p_ref is None else p_ref
    return Procedure(
        {
            "identifier": [{"value": str(record[0])}],
            # "partOf": [{"reference": str(record[1]), "type": "Encounter"}],
            "status": "completed",   # str(record[12]), T/F in DB; enum in HL7
            "code": {"text": f"{record[4]}+{record[3]}"},
            "subject": {"reference": ref, "type": "Patient"},#  {"reference": record[5], "type": "Patient"},
            # "encounter": {"reference": "0", "type": "Encounter"}, ## {"reference": str(record[1]), "type": "Encounter"},
            "occurrenceDateTime": start_time,
            "occurrencePeriod": {"start": start_time, "end": end_time},
            # "performer": [{"actor": {"reference": str(record[6]), "type": "Performer"}}],
            # "reason": [{"reference": {"reference": f_url}}],  #  {"reference": record[16]}}],
            # "report": [{"reference": "Patient/1", "type": "DocumentReference"}],  # [{"reference": "\n".join(record[7:12]), "type": "DocumentReference"}],
            "note": [{"text": "\n".join(record[17:]), "author": str(record[6])}],
        }
    )

def brprlu_encounter(record, p_ref=None):
    # for idx, val in enumerate(record):
    #     print(f"{idx}: {val} (type {type(val)})")
    return Encounter(
        {
            "identifier": [{"value": str(record[0])}],
            "type": [{"text": str(record[1])}],
            "status": "completed",
            # "basedOn": {"text": f"{record[4]}+{record[3]}"},
            # "careTeam": record[3],
            # "partOf": f"{record[4]}:{record[5]}",
            # "serviceProvider": record[6],
            # "participant": [{"type": {"reference": "Patient/1", "type": "Patient"}}], #  record[7],
            "plannedStartDate": brprlu_date(record[9]), 
            # "length": {"duration": brprlu_duration(record[10])}, 
            # "reason": {"use": "keys", "value": record[11]},
            # "diagnosis": {"condition": record[12]},
            # "specialCourtesy": {record[13]},
            # XXX Hardcoded ...
            "location": [{"location": {"reference": "Location/160086", "type": "Location"}}],# str(record[14])}},
        }
    )



def gwdc_genomicStudy(record):
    return GenomicStudy({})


def nbcc_genomicStudy(record):
    return GenomicStudy({})


FHIR_CONVERTER = {
    "gwdc_prostate": {
        "Patient": gwdc_patient,
        "DiagnosticReport": gwdc_diagnosis,
        # "genomicStudy": gwdc_genomicStudy,  TODO?
    },
    "nbcc": {
        "Patient": nbcc_patient,
        "DiagnosticReport": nbcc_diagnosis,
        "genomicStudy": nbcc_genomicStudy,
    },
    "gwdc_brprlu": {
        "Patient": brprlu_patient,
        "DiagnosticReport": brprlu_diagnosis,
        "Procedure": brprlu_procedure,
        "Encounter": brprlu_encounter,
    }
}


#######################################################
AUTH_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir-api/"
AUTH_TOKEN_URL = AUTH_URL + "oauth/token/"
FHIR_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir/"

def _get_access_token():

    fp = None
    client_info = None

    path = Path(__file__).parent.parent.parent / "server/populate_fhir_secrets.json"

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

def _post_location_info(access_token, location):

    headers = {"Authorization": f"Bearer {access_token}"}
    
    URL = FHIR_URL + "Location"
    response = requests.post(
        URL,
        json=location,
        headers=headers
    )

    fhir_response = response.json()

    return fhir_response

if __name__ == "__main__":

    import base64
    import requests

    access_info = _get_access_token()
    print(f"Access info: {access_info}")
    access_token = access_info['access_token']
    
    print(f"Got access token:\n{access_token}")

    location = Location({
        "identifier": [{"value": "123abc"}],
        "status": "active",
        "name": "George Washington University Hospital"
    }).as_json()

    fhir_response = _post_location_info(access_token, location)

    print(f"Got FHIR response\n{fhir_response}\n")
