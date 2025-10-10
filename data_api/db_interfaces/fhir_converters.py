import datetime
import random

try:
    ## Import in Django
    from .fhir_adapters import (
        Patient,
        DiagnosticReport,
        GenomicStudy,
    )
except:
    ## Import for command line
    from fhir_adapters import (
        Patient,
        DiagnosticReport,
        GenomicStudy,
    )

import datetime

gwdc_converter = {
    "pronoun_map": {"Male": "male", "Female": "female", "*Unspecified": "unknown"}
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

def record_to_datetime(record):
    try:
        return datetime.datetime(record)
    except:
        return generate_random_datetime(start_date, end_date).isoformat()

def nbcc_gender_converter(record):
    if record in nbcc_converter["secondary_map"]:
        return nbcc_converter["secondary_map"][record]
    primary_key = nbcc_converter["pronoun_map"][record]
    return nbcc_converter["secondary_map"][primary_key]

def gwdc_patient(record):
    return Patient(
        {
            "gender": gwdc_converter["pronoun_map"][record[0]],
            "communication_preference": {"language": record[1]},
            "birthdate": record[2],
            "deceasedtime": record[3],
            "identifier": record[4],
        }
    ).to_json()


def nbcc_patient(record):
    return Patient(
        {
            "gender": nbcc_gender_converter(record[0]),
            "birthdate": record_to_datetime(record[1]),
            "deceasedtime": record[2],
            "identifier": record[3],
        }
    ).to_json()


def gwdc_diagnosis(record):
    return DiagnosticReport(
        {
            "identifier": "gwdc",
            "status": "final",
            "category": record[2],
            "code": record[3],
            "subject": record[0],
            "effective": datetime.datetime(record[5]),
            "performer": record[1],
            "encounter": record[4],
            "result": record[6],
            "interpreter": record[7],
        }
    )


def nbcc_diagnosis(record):
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

def gwdc_genomicStudy(record):
    return GenomicStudy({})


def nbcc_genomicStudy(record):
    return GenomicStudy({})


FHIR_CONVERTER = {
    "gwdc_prostate": {
        "patient": gwdc_patient,
        "diagnosis": gwdc_diagnosis,
        # "genomicStudy": gwdc_genomicStudy,  TODO?
    },
    "nbcc": {
        "patient": nbcc_patient,
        "diagnosis": nbcc_diagnosis,
        "genomicStudy": nbcc_genomicStudy,
    },
}
