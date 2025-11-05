import pandas as pd
import sqlite3 as sql

from collections import Counter

import os
import time

DATA_HOME = "/data/arpah/downloads/GWDC_BrPrLuCA"
DB_HOME = "/data/arpah/processed/GWDC_BrPrLuCA"
DB_NAME = "GWDC_BreastCancer_LungCancer_ProstateCancer.sqlite"

COLLECT_UNIQUES = False
COLLECT_STATS = True

counter = 0

counts = {}

parquets = []

for root, dirnames, files in os.walk(DATA_HOME):
    if root != DATA_HOME:
        continue
    counter += 1
    
    for f in files:
        if "parquet" not in f:
            continue
        parquets.append(f)
print(f"Found {len(parquets)} files")

def parquet_uniques(parquets):
    for f in parquets:
        start = time.time()
        # print(f"Processing {f}")
        df = pd.read_parquet(os.path.join(DATA_HOME, f))
        file_name = f.replace("parquet", "") + "tsv"
        with open(file_name, "w") as fp:
            for c in df.columns:
                try:
                    uniques = df[c].unique().tolist()
                    if len(uniques) > 10:
                        uniques = uniques[:10]
                except Exception as e:
                    raise e(f"Type of uniques was {type(uniques)} (uniques)")
                print(f"c is {c} --- uniques is {uniques}")
                output_str = "{0}\t{1}\n".format(str(c), "\t".join([str(s) for s in uniques]))
                fp.write(output_str)
        print(f"{f}: Processing complete ....")

def collect_statistics(pd_series):
    
    description = pd_series.value_counts()

    sample_count = 0
    counter = Counter()
    count_limiter = 0
    limit = 15
    too_many = False
    for idx, value in description.items():
        count_limiter += 1
        sample_count += value
        if count_limiter >= limit:
            too_many = True
        else:
            counter[idx] = value
    percentage_counter = 0.0
    for idx, stat in counter.items():
        sample_percentage = stat / sample_count * 100
        percentage_counter += sample_percentage
        print(f"{idx}\t{sample_percentage:.2f}")
    print(f"{percentage_counter:.2f}% accounted for")
    if too_many:
        print(f"Too many indices: Displaying {limit} of {len(description)} items")

def collect_deaths(pd_series):
    non_trivial_deaths = pd_series.value_counts()
    death_counter = 0
    sample_size = len(pd_series)
    for _, count in non_trivial_deaths.items():
        death_counter += count
    print(f"Deaths\t{death_counter/sample_size * 100:.2f}\nLiving\t{(sample_size-death_counter)/sample_size*100:.2f} ")

'''
    XXX - Patient jazz
    "PatientDim": [
        "DurableKey_e", "AgeInYears", 
        {"StateOrProvince": collect_statistics},
        {"DeathDate": collect_deaths},
        {"FirstRace": collect_statistics},
        {"SecondRace": collect_statistics},
        {"Sex": collect_statistics},
        {"SexualOrientation": collect_statistics}, 
        {"MaritalStatus": collect_statistics}, 
        {"SmokingStatus": collect_statistics},
        {"IsCancerPatient": collect_statistics}, 
        # {"FifthRace": lambda series: collect_statistics()}, 
        # {"OmbRace": lambda series: series.unique()},
        ]
'''

'''
    XXX - Diagnosis jazz
    "DiagnosisDim": [
        {"DiagnosisKey": lambda series: series.value_counts()}, 
        {"ClinicalClassificationSoftwareGroupName": collect_statistics},
        {"ClinicalClassificationLevelOne": collect_statistics}, 
        {"ClinicalClassificationLevelTwo": collect_statistics},
        {"ClinicalClassificationLevelThree": collect_statistics}, 
        {"ClinicalClassificationLevelFour": collect_statistics},
        ],
    "DiagnosisEventFact": [
        {"DiagnosisKey": lambda s: print(len(s))}, 
        # "DiagnosisEventKey", "EncounterKey", 
        {"StartDateKey": collect_statistics},
        {"EndDateKey": collect_statistics},
        ],
    "DiagnosisSetDim": [
        {"DiagnosisSetKey": lambda s: print(len(s))}, 
        {"DiagnosisKey": lambda s: print(len(s))},
        {"Name": collect_statistics}, 
        {"DisplayName": collect_statistics},
        ],
    "DiagnosisTerminologyDim": [
        {"DiagnosisTerminologyKey": lambda s: s.unique()}, 
        # "DiagnosisKey", 
        {"Type": collect_statistics}, 
        {"Value": collect_statistics}, 
        {"DisplayString": collect_statistics},
        {"NameAndCode": collect_statistics},
        ],
'''

'''
XXX - Procedue jazz
    "ProcedureDim": [
        {"ProcedureKey": lambda s: print(len(s))}, 
        # "ProcedureEpicId", 
        {"Name": collect_statistics}, 
        {"ShortName": collect_statistics},
        {"PatientFriendlyName": collect_statistics},
        {"Category": collect_statistics},
        {"Code": collect_statistics},
        {"CodeSet": collect_statistics},
        {"HcpcsCode": collect_statistics},
        {"CptCode": collect_statistics},
        {"AdaCode": collect_statistics},
        {"AsaCode": collect_statistics},
        {"Level": collect_statistics},
        {"PrimaryValueSetName": collect_statistics},
        {"PrimaryValueSetDetailName": collect_statistics},
        {"ClinicalClassificationLevelOne": collect_statistics},
        {"ClinicalClassificationLevelTwo": collect_statistics},
        {"ClinicalClassificationLevelThree": collect_statistics}, 
        {"StartDate": collect_statistics},
        {"EndDate": collect_statistics},
    ],
'''


stats_to_collect = {
    "EncounterFact": [
        {"EncounterKey": lambda s: print(len(s))},
        {"PrimaryDiagnosisKey": lambda s: print(s.value_counts())}, 
        {"Type": collect_statistics},
        {"AdmissionSource": collect_statistics},
        {"ChiefComplaintComboKey": lambda s: print(s.value_counts())},
        {"DischargeDisposition": collect_statistics},
        {"DerivedOutpatientVisitType": collect_statistics},
        {"DerivedOutpatientVisitSubType": collect_statistics},
        {"VisitType": collect_statistics},
        {"PatientSelectedLocation": collect_statistics},
        {"PatientSelectedSublocation": collect_statistics},
    ],
    "MedicationOrderFact": [
        {"MedicationKey": lambda s: print(len(s))}, 
        {"OrderName": collect_statistics},
        "StartDateKey", "EndDateKey",
        {"FirstPrnReason": collect_statistics},
        {"SecondPrnReason": collect_statistics},
        {"ThirdPrnReason": collect_statistics},
        {"FourthPrnReason": collect_statistics},
        {"FirstIndicationForUse": collect_statistics},
        {"SecondIndicationForUse": collect_statistics},
        {"ThirdIndicationForUse": collect_statistics},
        {"FourthIndicationForUse": collect_statistics},
    ],
}

def parquet_stats(parquets):
    for f in parquets:
        table_name = f.split(".")[0]
        if table_name not in stats_to_collect.keys():
            # print(f"\nSkipping parquet {table_name} (from file {f})\n")
            continue
        else:
            cols = stats_to_collect[table_name]
            df = pd.read_parquet(os.path.join(DATA_HOME, f))
            for c in cols:
                if type(c) is str:
                    data_series = df[c]
                    description = data_series.describe()
                    print("*"*40)
                    print(f"Table: {table_name} Col: {c}")
                    for idx, value in description.items():
                        print(f"{idx},{value}")
                    print("*"*40)
                elif type(c) is dict:
                    # print(f"===> Got dict: value is {c}")
                    for col, func in c.items():
                        data_series = df[col]
                        print("*"*40)
                        print(f"Table: {table_name} Col: {col}")
                        func(data_series)
                        # print(f"{col}: {value} (type {type(value)}")
                        # collect_statistics(value)
                        print("*"*40)


if COLLECT_UNIQUES:
    parquet_uniques(parquets)

if COLLECT_STATS:
    parquet_stats(parquets)

