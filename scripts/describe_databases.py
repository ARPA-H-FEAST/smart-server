import pandas as pd
import sqlite3 as sql

from pathlib import Path

import json
import logging
import os
import sys
import time

logger = logging.getLogger(__file__)

PROJECT_HOME = Path(__file__).parent.parent

sys.path.append(str(PROJECT_HOME))

from data_api.db_interfaces import DBInterface

MODE = "MPGC"

if MODE != "dev":
    DATA_HOME = Path("/data/arpah/processed/")
else:
    DATA_HOME = PROJECT_HOME / "datadir/processed"
DBs = {
    "GWDC1": [DATA_HOME / "GWDC/GDWC.duckdb", "FEAST_000004"],
    "NBCC": [DATA_HOME / "nbcc/nbcc_db/nbcc.db", "FEAST_000012"],
}

db_config_path = PROJECT_HOME / "data_api/db_interfaces/db_config.json"
with open(str(db_config_path), "r") as fp:
    db_configs = json.load(fp)

def db_samples_from_parquets():
    parquet_home = DATA_HOME.parent / "downloads/GWDC_BrPrLuCA/"
    for root, directories, files in os.walk(str(parquet_home)):
        print(f"**** {root} ****")
        print(f"Dirs: {directories}")
        print(f"files: {files}")

for DB in ["GWDC1", "GWDC2", "NBCC"]:
    # Get the DB interface
    db_bco = DBs[DB][1]
    if DB == "GWDC2":
        # Handle using parquets directly
        db_samples_from_parquets()
        continue
    # XXX
    continue
    dbi = DBInterface(str(DBs[DB][0]), db_configs[db_bco], logger)
    tables = dbi._get_tables()
    print(f"{DB}: Got tables\n{tables}")

    tsv_name = DB + ".tsv"

    if os.path.exists(tsv_name):
        os.remove(tsv_name)

    for t in tables:
        dbi_response = dbi._singleton_sample_and_columns(t)
        print(f"Got response:\nHeaders: {dbi_response['headers']}\nSample: {dbi_response['sample']}")
        with open(tsv_name, "a") as fp:
            fp.write(f"Table {t}\n")
            fp.write("\t".join(dbi_response["headers"])+"\n")
            fp.write("\t".join(dbi_response["sample"])+"\n")
    
