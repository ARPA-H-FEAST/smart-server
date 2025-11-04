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
    parquet_home = str(DATA_HOME.parent / "downloads/GWDC_BrPrLuCA/")
    file_name = "GWDC2.tsv"
    with open(file_name, "w") as fp:
        for root, directories, files in os.walk(parquet_home):
            if root != parquet_home:
                continue
            print(f"**** {root} ****")
            print(f"Dirs: {directories}")
            print(f"files: {files}")
            for f in files:
                if "parquet" not in f:
                    continue
                start = time.time()
                parquet_path = os.path.join(parquet_home, f)
                df = pd.read_parquet(parquet_path)
                table_name = f.replace(".parquet","").replace(".BrPrLu","")
                headers = df.columns
                # print(f"{table_name} headers: {list(headers)}")
                # print(f"First row: {list(df.iloc[0])}")
                fp.write(f"Table {table_name}\n")
                fp.write("{}\n".format("\t".join(list(headers))))
                sample_list = list(df.iloc[0])
                fp.write("{}\n".format("\t".join([str(s) for s in sample_list])))
                print(f"Table {table_name}: Required {time.time() - start:.2f}s")
    fp.close()

for DB in ["GWDC1", "GWDC2", "NBCC"]:
    if DB == "GWDC2":
        # Handle using parquets directly
        db_samples_from_parquets()
        continue
    # XXX
    continue
    # Get the DB interface
    db_bco = DBs[DB][1]
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
    
