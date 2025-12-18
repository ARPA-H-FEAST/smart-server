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


import pandas as pd
import sqlite3 as sql
import duckdb

import os

DATA_HOME = "/data/arpah/downloads/GWDC_BrPrLuCA"
DB_HOME = "/data/arpah/processed/GWDC_BrPrLuCA"
# DB_NAME = "GWDC_BreastCancer_LungCancer_ProstateCancer.sqlite"
ERROR_LOG = "BrPrLu_errors.log"
ERROR_PATH = os.path.join(DB_HOME, ERROR_LOG)

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

DB_MODE = "SQL"  # SQL | DUCK

if DB_MODE == "SQL":
    ### SQLITE
    DB_NAME = "GWDC_BrPrLu.sqlite"
    db_conn = sql.connect(database=os.path.join(DB_HOME, DB_NAME))
    cur = db_conn.cursor()
    TYPE_MAP = {
        'int32':  'INTEGER',
        'int64':  'INTEGER',
        'object': 'TEXT',
        'bool': 'INTEGER',
        'float64': 'REAL',
        'datetime64[us, UTC]': 'TEXT',
    }

elif DB_MODE == "DUCK":
    ### DUCKDB
    DB_NAME = "GWDC_BrPrLu.duckdb"
    db_conn = duckdb.connect(os.path.join(DB_HOME, DB_NAME))
    TYPE_MAP = {
        'int32':  'BIGINT',
        'int64':  'BIGINT',
        'object': 'VARCHAR',
        'bool': 'BOOLEAN',
        'float64': 'DOUBLE',
        'datetime64[us, UTC]': 'TIMESTAMP',
    }

else:
    import sys
    sys.exit("Fork ...")

CREATE_STATEMENT = "CREATE TABLE {} ({});"


def primary_key_string(key_name, key_type):
    return f"{key_name} {key_type} PRIMARY KEY,"

def foreign_key_string(key_name, key_type, foreign_table, fk_name):
    out_str = f"\t{key_name} {key_type},"
    out_str += f"\n\tFOREIGN KEY ({key_name})"
    out_str += f" REFERENCES {foreign_table}({fk_name})"
    return out_str

def unique_column(key_name, key_type):
    if key_name == "DiagnosisKey":
        return f"{key_name} BIGINT UNIQUE NOT NULL,"
    elif key_name == "ProcedureKey":
        return f"{key_name} BIGINT UNIQUE NOT NULL,"
    elif key_name == "MedicationKey":
        return f"{key_name} BIGINT UNIQUE NOT NULL,"
    return f"{key_name} {key_type} UNIQUE NOT NULL,"

def create_basic_column(col, tipo):

    if col == "ProcedureKey":
        return f"{col} BIGINT,\n"
    else:
        f"Creating column: {col} {tipo},\n"
        stryng = f"{col} {tipo},\n"
        return stryng

foreign_table_relations = {
    "PatientRegistryValueFact": {"PatientDurableKey_e": ["PatientDim", "DurableKey_e"]},
    "DiagnosisEventFact": {
        "PatientDurableKey_e": ["PatientDim", "DurableKey_e"],
        "EncounterKey": ["EncounterFact", "EncounterKey"],
    },
    "DiagnosisDim": {"DiagnosisKey": ["DiagnosisEventFact", "DiagnosisKey"]},
    "DiagnosisSetDim": {"DiagnosisKey": ["DiagnosisEventFact", "DiagnosisKey"]},
    "DiagnosisTerminologyDim": {"DiagnosisKey": ["DiagnosisEventFact", "DiagnosisKey"]},
    "ProcedureEventFact": {
        "PatientDurableKey_e": ["PatientDim", "DurableKey_e"],
        "EncounterKey": ["EncounterFact", "EncounterKey"],
    },
    "ProcedureDim": {"ProcedureKey": ["ProcedureEventFact", "ProcedureKey"]},
    "EncounterFact": {"PatientDurableKey_e": ["PatientDim", "DurableKey_e"]},
    "LabComponentResultFact": {
        "PatientDurableKey_e": ["PatientDim", "DurableKey_e"],
        "EncounterKey": ["EncounterFact", "EncounterKey"],
        "ProcedureKey": ["ProcedureEventFact", "ProcedureKey"],
    },
    "LabComponentMappingDim": {"LabComponentKey": ["LabComponentResultFact", "LabComponentKey"]},
    "LabComponentSetDim": {"LabComponentKey": ["LabComponentResultFact", "LabComponentKey"]},
    "LabComponentDim":  {"LabComponentKey": ["LabComponentResultFact", "LabComponentKey"]},
    "LabCounts": {"LabComponentKey": ["LabComponentResultFact", "LabComponentKey"]},
    "LabOrganism": {"LabComponentKey": ["LabComponentResultFact", "LabComponentKey"]},
    "MedicationAdministrationFact": {
        "PatientDurableKey_e": ["PatientDim", "DurableKey_e"],
        "EncounterKey": ["EncounterFact", "EncounterKey"],
        "ProcedureKey": ["ProcedureEventFact", "ProcedureKey"],
    },
    "MedicationCodeDim": {"MedicationKey": ["MedicationAdministrationFact", "MedicationKey"]} , 
    "MedicationDim": {"MedicationKey":  ["MedicationAdministrationFact", "MedicationKey"]} , 
    "MedicationOrderFact": {"MedicationKey":  ["MedicationAdministrationFact", "MedicationKey"]} , 
    "MedicationSetDim": {"MedicationKey":  ["MedicationAdministrationFact", "MedicationKey"]} , 
}

table_keys = {
    ### PATIENT
    "PatientDim": {"DurableKey_e": "primary" },  #  "DurableKey_e {} PRIMARY KEY\n"
    "PatientRegistryValueFact": {"PatientDurableKey_e": "foreign"},
    
    ### DIAGNOSIS
    "DiagnosisEventFact": {
        "DiagnosisEventKey": "primary",
        "PatientDurableKey_e": "foreign",
        # "EncounterKey": "foreign",
        # "DiagnosisKey": "unique",
    },
    "DiagnosisDim": {},  # {"DiagnosisKey": "foreign"},
    "DiagnosisSetDim": {},  # { "DiagnosisKey": "foreign"}, 
    "DiagnosisTerminologyDim": {},  # {"DiagnosisKey": "foreign"},

    ### PROCEDURE
    "ProcedureEventFact": {
        "PatientDurableKey_e": "foreign",
        # "EncounterKey": "foreign",
        "ProcedureEventKey": "primary",
    },
    "ProcedureDim": {},  # {"ProcedureKey": "foreign"},
    "ProcedureTerminologyDim": {},  # {"ProcedureKey": "foreign"},
    
    ### ENCOUNTER
    "EncounterFact": {
        "EncounterKey": "primary",
        "PatientDurableKey_e": "foreign"
    },

    ### LABCOMPONENT
    "LabComponentResultFact": {
        "LabComponentResultKey": "primary",
        "PatientDurableKey_e": "foreign",
        # "EncounterKey": "foreign",
        # "ProcedureKey": "foreign",
        # "LabComponentKey": "unique",
    },
    "LabComponentMappingDim": {},  # {"LabComponentKey": "foreign"},
    "LabComponentSetDim": {},  # {"LabComponentKey": "foreign"},
    "LabComponentDim": {},  # {"LabComponentKey": "foreign"},
    "LabCounts": {},  # {"LabComponentKey": "foreign"},
    "LabOrganism": {},  # {"LabComponentKey": "foreign"},
   
    ### MEDICATION
    "MedicationAdministrationFact": {
        "MedicationAdministrationKey": "primary",
        "PatientDurableKey_e": "foreign",
        # "EncounterKey": "foreign",
        # "MedicationKey": "unique",
    },
    "MedicationCodeDim": {},  # {"MedicationKey": "foreign"},
    "MedicationDim": {},  # {"MedicationKey": "foreign"},
    "MedicationOrderFact": {},  # {"MedicationKey": "foreign"},
    "MedicationSetDim": {},  # {"MedicationKey": "foreign"},
}

UNIQUE_ENFORCEMENT = {
    "DiagnosisEventFact": [
        # "EncounterKey", "DiagnosisKey", "DiagnosisEventKey", "PatientDurableKey_e"
        # "DiagnosisKey", "PatientDurableKey_e"
        "DiagnosisEventKey"
    ],
    "ProcedureEventFact": [
        # "ProcedureKey", "PatientDurableKey_e"
        # "EncounterKey", "ProcedureKey", "ProcedureDurableKey", "PatientDurableKey_e"
        "ProcedureEventKey"
    ],
    "LabComponentResultFact": [
        # "EncounterKey", "ProcedureKey", "LabComponentResultKey", "LabComponentKey", "PatientDurableKey_e"
        # "LabComponentKey", "PatientDurableKey_e"
        "LabComponentResultKey"
    ],
    "MedicationAdministrationFact": [
        # "EncounterKey", "MedicationKey", "MedicationAdministrationKey", "PatientDurableKey_e"
        # "MedicationKey", "PatientDurableKey_e"
        "MedicationAdministrationKey"
    ],
    # "EncounterFact": ["EncounterKey", "PatientDurableKey_e"],

}

PRIMARY_ORDER = [
    "PatientDim.BrPrLu.parquet",
    "EncounterFact.BrPrLu.parquet",
    "DiagnosisEventFact.BrPrLu.parquet", 
    "ProcedureEventFact.BrPrLu.parquet", 
    "LabComponentResultFact.BrPrLu.parquet",
    "MedicationAdministrationFact.BrPrLu.parquet", 
]
SECONDARY_ORDER = [
    "PatientRegistryValueFact.BrPrLu.parquet",

    "DiagnosisDim.parquet", "DiagnosisSetDim.parquet", 
    "DiagnosisTerminologyDim.parque",
    
    "ProcedureDim.parquet", 
    "ProcedureTerminologyDim.parquet",
    
    "LabComponentMappingDim.parquet",
    "LabComponentSetDim.parquet", "LabComponentDim.parquet", "LabCounts.parquet",
    # "LabOrganism.parquet",

    "MedicationCodeDim.parquet", "MedicationDim.parquet", 
    "MedicationOrderFact.parquet", "MedicationSetDim.parquet",
    ]

LOAD_ORDER = PRIMARY_ORDER
for s in SECONDARY_ORDER:
    LOAD_ORDER.append(s)

for root, dirnames, files in os.walk(DATA_HOME):
    if root != DATA_HOME:
        continue
    counter += 1
    for f in LOAD_ORDER:
        if "parquet" not in f:
            continue
        table_name = table_names.get(f, None)
        print(f"Processing {f} - table name {table_name}")
        if table_name is None:
            print(f"----> SKIPPING TABLE {table_name}")
            print(f"---> Keys available were {table_keys.keys()}")
            continue
        df = pd.read_parquet(os.path.join(DATA_HOME, f))
        
        # XXX?
        # if table_name in UNIQUE_ENFORCEMENT.keys():
        #     cols_to_drop = UNIQUE_ENFORCEMENT[table_name]
        #     print(f"---> DROPPING DUPLICATES <----")
        #     print(f"Initial shape: {df.shape}")
        #     print(f"{cols_to_drop}")
            # for c in cols_to_drop:
            #     if c == "PatientDurableKey_e":
            #         print(f"===> Skipping PatientDurableKey...")
            #         continue
            #     # df.drop_duplicates(subset=c, inplace=True, keep='first')
            #     print(f"---> OVER -1 {df[df[c] >= 0].shape}")
            #     print(f"---> DUPLICATE COUNT: {len(df[c]-len(df[c].drop_duplicates(keep='first')))}")
            #     print(f"---> Column {c} uniques: {len(df[c].unique())}")
            #     print(f"---> UNDER 0 {df[df[c] < 0].shape}")
            #     df_missing = df.drop(df[df[c] >= 0].index)
            #     df = df.drop(df[df[c] < 0].index)
            # print(f"---> Column {cols_to_drop} uniques: {len(df[cols_to_drop].uniques())}")
        #     df.drop_duplicates(subset=cols_to_drop, inplace=True)
        #     print(f"Final shape: {df.shape}")
        #     print(f"---------------------------")
        # else:
        #     print(f"---> NOT DROPPING COLUMNS <----")
        #     print(f"---> TABLE WAS {table_name}")
        #     print(f"---------------------------")
        # db_conn.sql(f"CREATE TABLE {table_name} AS SELECT * FROM df")

        create_string = ""
        special_fields = table_keys[table_name]
        for c in df.columns:
            dt = TYPE_MAP[df[c].dtype.name]
            if c in special_fields.keys():
                sf_type = special_fields[c]
                if sf_type == "primary":
                    create_string += primary_key_string(c, dt) + "\n"
                elif sf_type == "foreign":
                    # Get foreign table relation
                    try:
                        ft_relation = foreign_table_relations[table_name][c]
                    except Exception as e:
                        print(f"--->BOOM: {e}")
                        print(f"===> Table {table_name} || Relation {c}")
                        print(f"ft relation level 1: {foreign_table_relations[table_name]}")
                        print(f"----> Current list: {foreign_table_relations[table_name]}")
                        raise
                    # print(f"FT RELATION: {ft_relation}")
                    # Get the definition string
                    try:
                        create_string += foreign_key_string(c, dt, *ft_relation) + ",\n"
                    except Exception as e:
                        print(f"{e}")
                        raise
                elif sf_type == "unique":
                    create_string += unique_column(c, dt) + "\n"
                else:
                    import sys
                    sys.exit("Blowing up ---- why am I here?")
            else:
                create_string += create_basic_column(c, dt)
        fs = CREATE_STATEMENT.format(table_name, create_string)
        fs = fs.replace(",\n);", "\n);")
        # print(f"Final create statement: {fs}")

        # XXX?
        # create_string = ""
        # for c in df.columns:
        #     dt = TYPE_MAP[df[c].dtype.name]
        #     create_string += create_basic_column(c, dt)
        # fs = CREATE_STATEMENT.format(table_name, create_string)
        # print(f"Final create statement: {fs}")

        if DB_MODE == "DUCK":
            #### DUCKDB
            try:
                db_conn.sql(fs)
            except Exception as e:
                print("*"*80)
                print(f"EXCEPTION: {e}")
                db_response = db_conn.sql(f"DESCRIBE {table_name}")
                print(f"{db_response}")
                print("*"*80)
                raise
            try:
                db_conn.sql(f"INSERT INTO {table_name} SELECT * FROM df")
            except Exception as e:
                out_str = "*"*80 + f"\nEXCEPTION: {e}\n" 
                out_str += f"... Table was {table_name} - bypassing for now...\n" 
                out_str += "*"*80 + "\n"
                with open(ERROR_PATH, "a") as err_p:
                    err_p.write(out_str)
                print(out_str)
                continue
        elif DB_MODE == "SQL":
            #### SQLITE
            # print(f"Creation command:\n{fs}")
            cur.execute(fs)
            df.to_sql(table_name, db_conn, if_exists='append', index=False)
        else:
            ...
db_conn.close()

