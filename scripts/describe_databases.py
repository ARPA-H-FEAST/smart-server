import pandas as pd
import sqlite3 as sql
import duckdb as duck

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
            output_name = table_name + ".parquet"
            print(f"Table {table_name}: Required {time.time() - start:.2f}s")
            df = df.iloc[[0]]
            df.to_parquet(f"./{output_name}")

for DB in ["GWDC1", "GWDC2", "NBCC"]:
    if DB == "GWDC2":
        # Handle using parquets directly
        
        #### parquets complete

        # db_samples_from_parquets()
        continue

    db_name = DB + ".db"

    if os.path.exists(db_name):
        os.remove(db_name)

    con = None
    if DB == "GWDC1":
        con = duck.connect(database=db_name)
        mode = "duck"
    elif DB == "NBCC":
        con = sql.connect(db_name)
        mode = "sql"
    assert con is not None

    # Get the DB interface
    db_bco = DBs[DB][1]
    dbi = DBInterface(str(DBs[DB][0]), db_configs[db_bco], logger)

    tables = dbi._get_tables()
    print(f"{DB}: Got tables\n{tables}")

    for t in tables:
        df = None
        df = dbi._singleton_sample_and_columns(t)
        # print(f"Got response: {df}")
        if mode == "duck":
            con.execute(f"CREATE TABLE {t} AS SELECT * FROM df")
        elif mode == "sql":
            try:
                replacements = {}
                for idx, c in enumerate(df.columns):
                    if not c:
                        print(f"Found a non-column {c} in columns")
                        print(f"Series values include {df[c]}")
                        replacements[c] = "replaced"
                for c in replacements:
                    df = df.rename(columns=replacements)
                df.to_sql(t, con)
            except Exception as e:
                print(f"Exception: {e}")
                print(f"Table was {t}, df was {df}")
                print(f"Headers were {df.columns}")
                raise

    con.close()
