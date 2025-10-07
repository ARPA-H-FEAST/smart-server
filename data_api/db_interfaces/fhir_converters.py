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

def gwdc_diagnosis(record):
    return DiagnosticReport({
        "identifier": "gwdc", "status": "final", "category": record[2], "code": record[3],
        "subject": record[0], "effective": datetime.datetime(record[5]), "performer": record[1], 
        "encounter": record[4], "result": record[6], "interpreter": record[7],
    })

def nbcc_diagnosis(record):
    return DiagnosticReport({
        "identifier": "nbcc", "status": "final", "category": record[0], "code": record[4],
        "subject": record[9], "performer": "nbcc", "result": record[3], "annotation": (record[7], record[8]),
        "supporting_info": (record[5], record[6]), "effective": datetime.datetime(record[1])
    })

def gwdc_genomicStudy(record):
    return GenomicStudy({

    })

def nbcc_genomicStudy(record):
    return GenomicStudy({

    })

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
    }
}