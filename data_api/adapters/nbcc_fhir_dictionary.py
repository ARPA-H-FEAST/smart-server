NBCC_PATIENT_DICT = {
    "nbcc_userinfo_id": "identifier",
    "year_of_birth": "birthdate",
    "year_of_death": "deceasedtime",
    # "relationship": "" - In an extension domain?
    "alive": "",
    "sex": "",
    "siblingtype": "",
    "breast_cancer": "",
    "diagnosis_year": "",
    "diagnosis_age": "",
    "diagnosis_idk": "",
    "stage": "",
    "er": "",
    "pr": "",
    "other_diagnosis_descriptors": "",
    "receptors_idk": "",
    "recurrence": "",
    "recurrence_year": "",
    "recurrence_age": "",
    "recurrence_idk": "",
    "recurrence_kind": "",
    "last_screening_year": "",
    "last_screening_age": "",
    "last_screening_idk": "",
    "last_screening_none": "",
    "cause_of_death": "",
    "age_at_death": "",
}

GWDC_PROSTATE_DIAGNOSTIC_DICT = {
    # TODO?
}


def convert_nbcc_to_fhir(record):
    
    # patient_record = {}
    # for k, v in NBCC_PATIENT_DICT.items():
    #     if type(v) is str:
    #         patient_record[k] = record[k]
    #     elif type(v) is list:
    #         patient_record[k] = {}
    #         tracker_pointer = patient_record[k]
    #         for index, key in enumerate(v):
    #             if index < len(v) - 1:
    #                 # Why must FHIR be so over-specified ...
    #                 patient_record[key] = {}
    #                 ### TODO: Pick back up here
    # patient_record["managing_organization"] = "NBCC-BREAST"
    print(f"\n**** NBCC: Processing {record}\n")
    return {"identifier": 42}