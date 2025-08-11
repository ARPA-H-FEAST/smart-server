from ..adapters import (
    Patient,
)

def gwdc_patient(record):
    return Patient({
        "gender": record[0], "communication_preference": {"language": record[1]},
        "birthdate": record[2], "deceasedtime": record[3], "identifier": record[4],
    }).to_json()

def nbcc_patient(record):
    return Patient({
        "gender": record[0], "birthdate": record[1], 
        "deceasedtime": record[2], "identifier": record[3],
    }).to_json()

FHIR_CONVERTER = {
    "gwdc_prostate": {"patient": gwdc_patient},
    "nbcc": {"patient": nbcc_patient}
}