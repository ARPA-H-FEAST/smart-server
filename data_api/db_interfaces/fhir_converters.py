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
    
    try:
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
    except Exception as e:
        raise

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

BCP_47_LANG = {
    # See also
    # https://en.wikipedia.org/wiki/IETF_language_tag
    # Country codes: https://gist.github.com/typpo/b2b828a35e683b9bf8db91b5404f1bd1
    # Country codes not in the original data set, use "-UNK" if possible
    'English': "en-UNK", 
    'Spanish': "es-UNK",  #  
    '*Unspecified': "KEY204", 
    'Chinese': "zh-UNK",
    'Decline to Answer': "KEY204", 
    'Unknown': "KEY204", 
    'Amharic': "am-UNK", 
    'Arabic': "ar-UNK", 
    '*Masked:<10': "KEY204",
    # Assume ASL. There are *many* sign languages
    # see https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry
    'Sign Language': "ase-UNK", 
    '*Not Applicable': "KEY204", 
    'Tagalog': "tl-UNK", 
    'Korean': "ko-UNK", 
    'French': "fr-UNK",
    'Other': "KEY204", 
    'Vietnamese': "vi-UNK", 
    'Bengali': "bn-UNK", 
    'Russian': "ru-UNK", 
    'Tigrinya': "ti-UNK",
    'Portuguese': "pt-UNK", 
    'Persian': "fa-UNK",
    'Greek': "el-UNK",
    'Ukrainian': "uk-UNK",
}

def lang_to_bcp(record):
    return [{
        "language": {
            "coding": [{
                "system": "urn:ietf:bcp:47",
                "code": BCP_47_LANG[record],
                "display": record,
            }]
        }
    }]

OMB_RACE = {
    "American Indian or Alaska Native": "1002-5",
    "North American Native": "1002-5",
    "Asian": "2028-9",
    "Asian Indian": "2028-9",
    "Other Asian": "2028-9",
    "Vietnamese": "2028-9",
    "Chinese": "2028-9",
    "Korean": "2028-9",
    "Japanese": "2028-9",
    "Black or African American": "2054-5",
    "Black": "2054-5",
    "Native Hawaiian or Other Pacific Islander": "2076-8",
    "Other Pacific Islander": "2076-8",
    "Native Hawaiian": "2076-8",
    "Filipino": "2076-8",
    "Guamanian or Chamorro": "2076-8",
    "Samoan": "2076-8",
    "White": "2106-3",
    "Unknown": "UNK",
    "*Not Applicable": "UNK",
    "Other": "UNK",
    "": "UNK",
    "Asked but no answer": "ASKU",
    "Decline to Answer": "ASKU",
    "*Unspecified": "ASKU",
    ### This is in the DB dump, so it's moving into FHIR here
    "Hispanic": "2135-2",

}

OMB_ETHNICITY = {
    "Hispanic or Latino": "2135-2",
    "Mexican, Mexican American, or Chicano/a": "2135-2",
    "Cuban": "2135-2",
    "Puerto Rican": "2135-2",
    "Non Hispanic or Latino": "2186-5",
    "Not Hispanic, Latino/a, or Spanish origin": "2186-5",
    "Other Hispanic, Latino/a, or Spanish origin": "2186-5",
    "Unknown": "UNK",
    "*Not Applicable": "UNK",
    "Asked but no answer": "ASKU",
    "Decline to Answer": "ASKU",
    "*Unspecified": "ASKU",
    }

PATIENT_CLASS_FHIR_CODES = {
    # https://terminology.hl7.org/7.0.1/CodeSystem-v3-ActCode.html
    '*Unspecified': "KEY204",
    'Outpatient': "AMB",
    'Emergency': "EMER",
    'Inpatient': "IMP",
    'Radiation/Oncology Series': "CROC",
    'Observation': "OBSENC",
    'Extended Recovery': "KEY204",
    'Pre-Admission': "PRENC", 
    'Outpatient Surgery': "AMB", 
    'Case Management': "KEY204",
    'Procedural Series': "KEY204"
}

SYSTEM_TO_URI_CONVERTER = {
    '*Deleted': "UNK",
    'SNOMED CT': "http://snomed.info/sct",
    'ICD-9-CM': "www.icd9data.com/",
    'ICD-10-CM': "www.icd10data.com/",
    'Custom': "Custom",
}

def gwdc_system_code_to_url(code):
    return SYSTEM_TO_URI_CONVERTER[code]

def _extension_obj_from_record(rec):
    return [{
            "url": "ombCategory",
            "valueCoding": {
                "system": "urn:oid:2.16.840.1.113883.6.238",
                "code": OMB_RACE[rec],
                "display": rec
            }
        },
        {
            "url": "text",
            "valueString": rec,
        }]

def gwdc_race_to_fhir(records):
    # Return the python-object of the OMB race extension
    # c.f. http://hl7.org/fhir/us/core/STU8.0.1/StructureDefinition-us-core-race.html
    if records[0] == "":
        return None
    extension = []
    for r in records:
        if r != "":
            extension.extend(_extension_obj_from_record(r))
    return {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
        "extension": extension,
    }

def gwdc_ethnicity_to_fhir(record):
    # Return the python-object of the OMB race extension
    # c.f. http://hl7.org/fhir/us/core/STU8.0.1/StructureDefinition-us-core-ethnicity.html
    return {
        "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
        "extension": [
            {
                "url": "ombCategory",
                "valueCoding": {
                    "system": "urn:oid:2.16.840.1.113883.6.238",
                    "code": OMB_ETHNICITY[record],
                    "display": record,
                }
            },
            {
                "url": "text",
                "valueString": record,
            }
        ]
    }

def gwdc_patient_class_to_fhir(record):
    return [{
        "coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": PATIENT_CLASS_FHIR_CODES[record],
            "display": record,
        }
    ]
    }]

def gwdc_encounter_type_to_fhir(record0, record1):
    return [{
        "coding": [{
            "system": "GWU EPIC Caboodle",
            "code": str(record1),
            "display": record0,
        }]
    }]

# Example Usage:
start_date = datetime.datetime(2023, 1, 1, 0, 0, 0)
end_date = datetime.datetime(2024, 12, 31, 23, 59, 59)

OLD_DATE = datetime.date(1900, 1, 1)
FUTURE_DATE = datetime.date(2199, 1, 1)

def record_to_datetime(record):
    try:
        return datetime.datetime(record).isoformat()
    except:
        try:
            return datetime.datetime(int(record, 1, 1)).isoformat()
        except:
            return generate_random_datetime(start_date, end_date).strftime('%Y-%m-%d')

def nbcc_gender_converter(record):
    if record in nbcc_converter["secondary_map"]:
        return nbcc_converter["secondary_map"][record]
    primary_key = nbcc_converter["pronoun_map"][record]
    return nbcc_converter["secondary_map"][primary_key]

def gwdc_patient(record):
    p_extension = []
    p_race = gwdc_race_to_fhir(record[6:10])
    p_ethnicity = gwdc_ethnicity_to_fhir(record[5])
    if p_race is not None:
        p_extension.append(p_race)
    if p_ethnicity is not None:
        p_extension.append(p_ethnicity)
    if len(p_extension) > 0:
        return Patient({
            "gender": gwdc_converter["pronoun_map"][record[0]],
            "communication": lang_to_bcp(record[1]),
            "birthDate": record[2].strftime("%Y-%m-%d"),
            "deceasedDateTime": None 
                if record[3] is None 
                else record[3].strftime("%Y-%m-%d"),
            "identifier": [{"value": record[4]}],
            "extension": p_extension,
        })
    else:
        return Patient({
                "gender": gwdc_converter["pronoun_map"][record[0]],
                "communication": lang_to_bcp(record[1]),
                "birthDate": record[2].strftime("%Y-%m-%d"),
                "deceasedDateTime": None 
                    if record[3] is None 
                    else record[3].strftime("%Y-%m-%d"),
                "identifier": [{"value": record[4]}],
            })

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
    p_extension = []
    p_race = gwdc_race_to_fhir(record[9:13])
    p_ethnicity = gwdc_ethnicity_to_fhir(record[8])
    if p_race is not None:
        p_extension.append(p_race)
    if p_ethnicity is not None:
        p_extension.append(p_ethnicity)
    if len(p_extension) > 0:
        return Patient(
        {
            "gender": gwdc_converter["pronoun_map"][record[0]],
            "communication": lang_to_bcp(record[1]),
            "birthDate": datetime.datetime(int(record[2]), 1, 1).date().strftime("%Y-%m-%d"),
            "deceasedDateTime": brprlu_date(record[3]),
            "identifier": [{"value": record[4]}],
            "address": [{
                "state": record[5],
                "country": record[6],
            }],
            "extension": p_extension,
            # "generalPrectitioner": [{"reference": record[7]}]
        }
    )

    else:
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
    ref = "Patient/2" if p_ref is None else p_ref
    # for idx, r in enumerate(record):
    #     print(f"{idx}: {r}")
    return DiagnosticReport(
        {
            "status": "final",
            # "category": record[2],
            "code": {"coding": [{
                "system": gwdc_system_code_to_url(record[15]),
                "code": record[16], #  14 = "DisplayString"
                "display": record[13],
            }], "text": record[12]},
            "subject": {"reference": ref, "type": "Patient"},
            "effective": None if record[4] is None else datetime.datetime(int(record[4]), 1, 1).date().strftime("%Y-%m-%d"),
            "supportingInfo": [{"type": {"text": record[15]}, "reference": {"type": "", "reference": ""}}],
            "supportingInfo": [{"type": {"text": record[15]}, "reference": {"type": "", "reference": ""}}],
            "conclusion": record[12],
            "conclusionCode": [{
                "coding": [{
                    "code": record[14], 
                    "system": gwdc_system_code_to_url(record[15]),
                    "display": record[12], 
                }]}],
            # "performer": record[1],
            # "encounter": record[4],
            # "identifier": record[6],
            # "interpreter": record[7],
        }
    )

def brprlu_diagnosis(record, p_ref=None):
    ref = "Patient/2" if p_ref is None else p_ref
    return DiagnosticReport(
        {
            "identifier": [{"value": str(record[6])}],
            "status": "final", # str(record[9]),
            # 18: 
            "code": {"coding": [{
                "system": gwdc_system_code_to_url(record[18]),
                "code": record[19], # "DisplayString"
                "display": record[18],
                }], "text": record[15]},  # PREFERRED, Per DNAHIVE
            "subject": {"reference": ref, "type": "Patient"}, # {"reference": record[0], "type": "Patient"},
            # "encounter": {"reference": str(record[4]), "type": "Encounter"},
            "effectiveDateTime": "2299-01-01" if record[5] < 1900 else datetime.datetime(int(record[5]), 1, 1).date().strftime("%Y-%m-%d"),
            # "performer": [{"reference": "Practitioner/1", "type": "Performer"}],  # [{"reference": str(record[8]), "type": "Performer"}],
            # "result": [{"reference": "Observation/1", "type": "Observation"}],  # [{"reference": record[10], "type": "Observation"}],
            "note": [{"text": "\n".join(record[11:15]), "author": str(record[8])}],
            "supportingInfo": [{"type": {"text": record[15]}, "reference": {"type": "", "reference": ""}}],
            "conclusion": record[17],
            "conclusionCode": [{
                "coding": [{
                    "code": record[19], 
                    "system": gwdc_system_code_to_url(record[18]),
                    "display": record[17], 
                }]}],
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
    ref = "Patient/2" if p_ref is None else p_ref
    return Procedure(
        {
            "identifier": [{"value": str(record[0])}],
            # "partOf": [{"reference": str(record[1]), "type": "Encounter"}],
            "status": "completed",   # str(record[12]), T/F in DB; enum in HL7
            # "code": {"text": f"{record[4]}+{record[3]}"},  # DEPRECATED
            "code": {"coding": [{
                "system": record[3],
                "code": record[4],
                "display": record[16],
            }], 
                "text": f"{record[4]}+{record[3]}"
            },  # PREFERRED, Per DNAHIVE
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
    # print(record)
    patient = p_ref if p_ref is not None else "Patient/2"
    return Encounter(
        {
            "identifier": [{"value": str(record[0])}],
            "status": "completed",
            # "basedOn": {"text": f"{record[4]}+{record[3]}"},
            # "careTeam": record[3],
            # "partOf": f"{record[4]}:{record[5]}",
            # "serviceProvider": record[6],
            "class": gwdc_patient_class_to_fhir(record[16]),
            "type": gwdc_encounter_type_to_fhir(record[1], record[17]),
            "actualPeriod": {
                "start": record_to_datetime(record[9]), 
                "end": record_to_datetime(record[10])},
            "subject": {"reference": patient, "type": "Patient"}, #  record[7],
            "plannedStartDate": brprlu_date(record[9]), 
            # "length": {"duration": brprlu_duration(record[10])}, 
            # "reason": {"use": "keys", "value": record[11]},
            # "diagnosis": {"condition": record[12]},
            # "specialCourtesy": {record[13]},
            # XXX Hardcoded ...
            "location": [{"location": {"reference": "Location/1", "type": "Location"}}],# str(record[14])}},
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
# FHIR_URL = "http://localhost:8080/fhir/"

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

def _post_basic_info(access_token, fhir_object, fhir_item):

    headers = {"Authorization": f"Bearer {access_token}"}
    
    URL = FHIR_URL + fhir_item
    response = requests.post(
        URL,
        json=fhir_object,
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
    
    # access_token = "ABCDE"

    print(f"Got access token:\n{access_token}")

    location = Location({
        "identifier": [{"value": "123abc"}],
        "status": "active",
        "name": "George Washington University Hospital"
    }).as_json()

    fhir_response = _post_basic_info(access_token, location, "Location")

    print(f"LOCATION: Got FHIR response\n{fhir_response}\n")

    patient = Patient({
        "identifier": [{"value": "DUMMY - FOR HANDLING MISSING INDEX DATA"}]
    }).as_json()

    fhir_response = _post_basic_info(access_token, patient, "Patient")

    print(f"PATIENT: Got FHIR response\n{fhir_response}\n")
