import pandas as pd
import sqlite3 as sql

import os

DATA_HOME = "/data/arpah/downloads/GWDC_BrPrLuCA"
DB_HOME = "/data/arpah/processed/GWDC_BrPrLuCA"
DB_NAME = "GWDC_BreastCancer_LungCancer_ProstateCancer.sqlite"

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

db_conn = sql.connect(database=os.path.join(DB_HOME, DB_NAME))

for root, dirnames, files in os.walk(DATA_HOME):
    if root != DATA_HOME:
        continue
    counter += 1
    for f in files:
        if "parquet" not in f:
            continue
        print(f"Processing {f}")
        df = pd.read_parquet(os.path.join(DATA_HOME, f))
        table_name = table_names[f]
        num_rows_inserted = df.to_sql(table_name, db_conn, index=False)
        print(f"{f}: Inserted {num_rows_inserted}")

db_conn.close()

