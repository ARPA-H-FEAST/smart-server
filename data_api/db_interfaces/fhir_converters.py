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

    })

def nbcc_diagnosis(record):
    return DiagnosticReport({

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