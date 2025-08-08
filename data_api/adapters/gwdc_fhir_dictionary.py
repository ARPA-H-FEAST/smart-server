GWDC_PROSTATE_PATIENT_DICT = {
    "Sex": "gender",
    ### DROPPED ###
    # "SexAssignedAtBirth": "*Unspecified",
    # "GenderIdentity": "*Unspecified",
    "PreferredLanguage": {"communication_preference": {"language": "English"}},
    # "Ethnicity": "Unknown",
    # "FirstRace": "White",
    # "SecondRace": "",
    # "ThirdRace": "",
    # "FourthRace": "",
    # "FifthRace": "",
    # "MultiRacial": 0,
    # "AgeInYears": 78,
    "BirthDate": "birthdate",
    "DeathDate": "deceasedtime",
    # "DeathLocation": "*Not Applicable",
    # "Status": "Alive",
    # "City": "ARLINGTON",
    # "County": "*Unspecified",
    # "StateOrProvince": "Virginia",
    # "StateOrProvinceAbbreviation": "VA",
    # "Country": "United States of America",
    # "PostalCode": "22205",
    # "SexualOrientation": "*Unspecified",
    # "MaritalStatus": "Married",
    # "Religion": "None",
    # "SmokingStatus": "Never Assessed",
    # "PrimaryFinancialClass": "",
    # "HighestLevelOfEducation": "*Unspecified",
    # "IsCancerPatient": 1,
    # "CountryOfOrigin": "*Unspecified",
    # "IndigenousStatus": "*Unspecified",
    # "OmbEthnicity": "Unknown",
    # "OmbRace": "Unknown",
    # "Test": 0,
    # "IsValid": 1,
    # "StartDate": 1639094400000,
    # "EndDate": 4102963200000,
    # "IsCurrent": True,
    # "PreliminaryCauseOfDeathDiagnosisKey": -1,
    # "IsHistoricalPatient": 0,
    # "DualStatusCode": "",
    # "OriginalMedicareEntitlementReasonCode": "",
    # "MedicarePartAEntitlementStartDate": None,
    # "MedicarePartBEntitlementStartDate": None,
    # "ReliableSex": "Male",
    # "CensusBlockGroupFipsCode": "*Unspecified",
    # "LastImmunizationQueryInstantUtc": None,
    # "MedicareHospiceEnrollmentStartDate": None,
    # "MedicareHospiceEnrollmentEndDate": None,
    "DurableKey_e": "identifier",
}

GWDC_PROSTATE_DIAGNOSTIC_DICT = {
    # TODO?
}


def convert_gwdc_to_fhir(record):
    patient_record = {}
    for k, v in GWDC_PROSTATE_PATIENT_DICT.items():
        if type(v) is str:
            patient_record[v] = record[k]
        elif type(v) is dict:
            for sub_k, sub_v in v.items():
                patient_record[sub_k] = sub_v
    patient_record["managing_organization"] = "GWDC-PROSTATE"

    return patient_record
