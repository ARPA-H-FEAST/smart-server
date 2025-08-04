GWDC_PROSTATE_PATIENT_DICT = {
    "Sex": "gender", 
    ### DROPPED ###
    # "SexAssignedAtBirth": "*Unspecified", 
    # "GenderIdentity": "*Unspecified", 
    "PreferredLanguage": ["communication", "language", "English"], 
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

def convert_record_to_fhir(record):
    patient_record = {}
    for k, v in GWDC_PROSTATE_PATIENT_DICT.items():
        if type(v) is str:
            patient_record[k] = record[k]
        elif type(v) is list:
            patient_record[k] = {}
            tracker_pointer = patient_record[k]
            for index, key in enumerate(v):
                if index < len(v) - 1:
                    # Why must FHIR be so over-specified ...
                    patient_record[key] = {}
                    ### TODO: Pick back up here
    patient_record["managing_organization"] = "GWDC-PROSTATE"