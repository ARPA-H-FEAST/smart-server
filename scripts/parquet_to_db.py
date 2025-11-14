import pandas as pd
import sqlite3 as sql
import duckdb

import os

DATA_HOME = "/data/arpah/downloads/GWDC_BrPrLuCA"
DB_HOME = "/data/arpah/processed/GWDC_BrPrLuCA"
# DB_NAME = "GWDC_BreastCancer_LungCancer_ProstateCancer.sqlite"
DB_NAME = "GWDC_BrPrLu.duckdb"

counter = 0

table_names = {
        'PatientDim.BrPrLu.parquet': 'PatientDim', 
        'MedicationDim.parquet': 'MedicationDim',
        'EncounterFact.BrPrLu.parquet': 'EncounterFact',
        'PatientRegistryValueFact.BrPrLu.parquet': 'PatientRegistryValueFact',
        'FlowsheetValueFact.BrPrLu.parquet': 'FlowsheetValueFact',
        'ProcedureEventFact.BrPrLu.parquet': 'ProcedureEventFact', 
        'MedicationSetDim.parquet': 'MedicationSetDim',
        'DiagnosisEventFact.BrPrLu.parquet': 'DiagnosisEventFact',
        'RegistryMetricDim.parquet': 'RegistryMetricDim',
        'MedicationOrderFact.BrPrLu.parquet': 'MedicationOrderFact',
        'FlowsheetRowDim.parquet': 'FlowsheetRowDim',
        'LabComponentResultFact.BrPrLu.parquet': 'LabComponentResultFact',
        'DiagnosisSetDim.parquet': 'DiagnosisSetDim',
        'CancerStagingFact.BrPrLu.parquet': 'CancerStagingFact',
        'DiagnosisDim.parquet': 'DiagnosisDim',
        'LabComponentDim.parquet': 'LabComponentDim',
        'TerminologyConceptDim.parquet': 'TerminologyConceptDim',
        'ProcedureDim.parquet': 'ProcedureDim',
        'MedicationAdministrationFact.BrPrLu.parquet': 'MedicationAdministrationFact',
        'LabOrganismDim.parquet': 'LabOrganismDim',
        'LabCounts.parquet': 'LabCounts',
        'MedicationCodeDim.parquet': 'MedicationCodeDim',
        'GWDC_BrPrLuCA.Rproj': 'GWDC_BrPrLuCA',
        'LabComponentMappingDim.parquet': 'LabComponentMappingDim',
        'LabComponentSetDim.parquet': 'LabComponentSetDim',
        'ProcedureTerminologyDim.parquet': 'ProcedureTerminologyDim',
        'DiagnosisTerminologyDim.parquet': 'DiagnosisTerminologyDim',
        }

db_name = os.path.join(DB_HOME, DB_NAME)
# db_conn = sql.connect(database=os.path.join(DB_HOME, DB_NAME))
db_conn = duckdb.connect(db_name)

CREATE_STATEMENT = "CREATE TABLE {} ({})"

TYPE_MAP = {
    'int32':  'INTEGER',
    'int64':  'BIGINT',
    'object': 'VARCHAR',
    'bool': 'BOOLEAN',
    'float64': 'DOUBLE',
    'datetime64[us, UTC]': 'TIMESTAMP',
}

table_keys = {
    "PatientDim": {"DurableKey_e": "DurableKey_e {} PRIMARY KEY\n"},
    "PatientRegistryValueFact": {
        "PatientDurableKey_e":
"""
    PatientDurableKey_e {},
    FOREIGN KEY (PatientDurableKey_e) REFERENCES PatientDim(DurableKey_e),
"""
    },
    "DiagnosisEventFact": {
        "DiagnosisEventKey": "DiagnosisEventKey {} PRIMARY KEY\n",
        "PatientDurableKey_e": 
"""
    PatientDurableKey_e {},
    FOREIGN KEY (PatientDurableKey_e) REFERENCES PatientDim(DurableKey_e),
""",
        },
    "DiagnosisDim": {
        "DiagnosisDim": 
"""
    DiagnosisKey {},
    FOREIGN KEY (DiagnosisKey) REFERENCES DiagnosisEventFact(DiagnosisKey),
""",
    },
    "DiagnosisTerminologyDim": {
        "DiagnosisTerminologyDim": {
            "DiagnosisKey": 
"""
    DiagnosisKey {},
    FOREIGN KEY (DiagnosisKey) REFERENCES DiagnosisEventFact(DiagnosisKey),
""",
        "DiagnosisTerminologyKey ": "DiagnosisTerminologyKey {} PRIMARY KEY,\n",
        }
    },
    "ProcedureEventFact": {
        "PatientDurableKey_e": 
"""
    PatientDurableKey_e {},
    FOREIGN KEY (PatientDurableKey_e) REFERENCES PatientDim(DurableKey_e),
""",
    },
    "ProcedureDim": {
        "ProcedureKey":
"""
    ProcedureKey {},
    FOREIGN KEY (ProcedureKey) REFERENCES ProcedureEventFact(ProcedureKey),
""",
    "ProcedureTerminologyDim":
"""
    ProcedureKey {},
    FOREIGN KEY (ProcedureKey) REFERENCES ProcedureEventFact(ProcedureKey),
""",
    }
}

LOAD_ORDER = [
    "PatientDim.BrPrLu.parquet", "PatientRegistryValueFact.BrPrLu.parquet",
    
    "DiagnosisEventFact.BrPrLu.parquet", "DiagnosisDim.parquet", 
    "DiagnosisSetDim.parquet", "DiagnosisTerminologyDim.parque",

    "ProcedureEventFact", "ProcedureDim", "ProcedureTerminologyDim",

]

for root, dirnames, files in os.walk(DATA_HOME):
    if root != DATA_HOME:
        continue
    counter += 1
    for f in LOAD_ORDER:
        if "parquet" not in f:
            continue
        table_name = table_names[f]
        print(f"Processing {f} - table name {table_name}")
        if table_name not in table_keys.keys():
            continue
        df = pd.read_parquet(os.path.join(DATA_HOME, f))
        # print(f"Columnns available: {df.columns}")
        # db_conn.sql(f"CREATE TABLE {table_name} AS SELECT * FROM df")
        
        create_string = ""
        special_fields = table_keys[table_name]
        for c in df.columns:
            dt = df[c].dtype.name
            if c in special_fields.keys():
                create_string += special_fields[c].format(TYPE_MAP[dt]) + ",\n"
            else:
                create_string += f"{c} {TYPE_MAP[dt]},\n"

        fs = CREATE_STATEMENT.format(table_name, create_string)
        print(f"Final create statement: {fs}")
        db_conn.sql(fs)
        db_conn.sql(f"INSERT INTO {table_name} SELECT * FROM df")

db_conn.close()

