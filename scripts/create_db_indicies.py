import sys
print("*"*80)
print("""
.... this file has been fully deprecated. Neither SQLite nor DuckDB
proved able to ingest the data, likely due to broken foriegn-key
relations that were induced from the original data dump.

This file is kept here only as a guide to prevent further upload attempts.
"""
)
print("*"*80)
sys.exit()

import duckdb

import os

DB_HOME = "/data/arpah/processed/GWDC_BrPrLuCA"
DB_NAME = "GWDC_BrPrLu.duckdb"

DB_PATH = os.path.join(DB_HOME, DB_NAME)

indicies_to_create = {
    "DiagnosisKey": [
        "DiagnosisEventFact", "DiagnosisDim", 
        "DiagnosisSetDim",
    ],
    "ProcedureKey": [
        "ProcedureEventFact", "ProcedureDim",
    ],
    "LabComponentKey": [
        "LabComponentResultFact", "LabComponentMappingDim",
        "LabComponentSetDim", "LabComponentDim",
        "LabCounts",
    ],
    "MedicationKey": [
        "MedicationAdministrationFact", "MedicationCodeDim",
        "MedicationDim",
    ]
}

INDEX_COMMAND = "CREATE INDEX {} ON {} ({});"
DESCRIBE_COMMAND = "DESCRIBE {}"
SELECT_COMMAND = "SELECT ({}) FROM {} LIMIT 5"
db_conn = duckdb.connect(DB_PATH)

for index_key_name in indicies_to_create.keys():
    tables_with_key = indicies_to_create[index_key_name]
    for t in tables_with_key:
        cmd = INDEX_COMMAND.format(f"idx_{index_key_name}", t, index_key_name)
        # cmd = DESCRIBE_COMMAND.format(t)
        # cmd = SELECT_COMMAND.format(index_key_name, t)
        print(f"Executing command: {cmd}")
        print(db_conn.sql(cmd))

db_conn.close()