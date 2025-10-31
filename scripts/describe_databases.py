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

MODE = "dev"

if MODE != "dev":
    DATA_HOME = Path("/data/arpah/processed/")
else:
    DATA_HOME = PROJECT_HOME / "datadir/processed"
DBs = {
    "GWDC1": [DATA_HOME / "GWDC/GDWC.duckdb", "FEAST_000004"],
    "GWDC2": [DATA_HOME / "GWDC_BrPrLuCA", ""],
    "NBCC": [DATA_HOME / " nbcc/nbcc_db/nbcc.db", "FEAST_000012"],
}

db_config_path = PROJECT_HOME / "data_api/db_interfaces/db_config.json"
with open(str(db_config_path), "r") as fp:
    db_configs = json.load(fp)

for DB in ["GWDC1", "GWDC2", "NBCC"]:
    # Get the DB interface
    db_bco = DBs[DB][1]
    if not db_bco:
        continue
    dbi = DBInterface(str(DBs[DB][0]), db_configs[db_bco], logger)
    # tables = dbi._get_tables()
    # print(f"{DB}: Got tables\n{tables}")

    for t in tables:
        dbi.get_sample(table=t, limit=1, offset=0)