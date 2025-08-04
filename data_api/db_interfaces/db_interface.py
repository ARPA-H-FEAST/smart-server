import sqlite3 as sql

import duckdb
import pandas as pd
import json

SQL_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "GET_UNIQUE": "SELECT DISTINCT {} FROM {};",
    "MIN": "SELECT MIN({}) FROM {};",
    "MAX": "SELECT MAX({}) FROM {};",
    }

DUCK_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "GET_UNIQUE": "SELECT DISTINCT {} FROM {};",
    "MIN": "SELECT MIN({}) FROM {};",
    "MAX": "SELECT MAX({}) FROM {};",
    }
class DBInterface:

    def __init__(self, db_path, config, logger):

        db_class = config["db_class"]
        if db_class == "duckdb":
            self.con = duckdb.connect(db_path)
            self.cur = self.con.cursor()
            self.queries = DUCK_QUERIES
        elif db_class == "sqlite3":
            self.con = sql.connect(db_path, check_same_thread=False)
            self.cur = self.con.cursor()
            self.queries = SQL_QUERIES
        else:
            raise Exception(f"Invalid DB configuration: Unknown DB {db_class}")
        self.config = config
        self.logger = logger
    
    def __del__(self):
        if hasattr(self, "con"):
            self.con.close()

    def get_db_metadata(self):

        indexed_info = self.config["search_fields"]

        search_fields = []
        range_fields = []
        table = self.config["cannonical_table"]

        for cat in indexed_info.keys():
            if cat == "categorical":
                for field in indexed_info[cat]:
                    # self.logger.debug(f"===> Looking for unique field {field} in table {table}")
                    uniques = self.cur.execute(self.queries["GET_UNIQUE"].format(field, table)).fetchall()
                    search_obj = {"name": field, "levels": [u[0] for u in uniques]}
                    search_fields.append(search_obj)
                    self.logger.debug(f"===> Found unique search levels for {field}: {search_obj}")
            elif cat == "numerical":
                for field in indexed_info[cat]:
                    min = self.cur.execute(self.queries["MIN"].format(field, table)).fetchone()
                    max = self.cur.execute(self.queries["MAX"].format(field, table)).fetchone()
                    # self.logger.debug(f"===> Found MIN/MAX search levels for {field}: {min}/{max}")
                    range_fields.append({"name": field, "range": [min, max]})
            else:
                # raise Exception(f"===> Please implement support for field {cat}!!")
                self.logger.debug(f"===> Please implement support for field {cat}!!")

        return {
            "size": self.config["patients"],
            "search_fields": search_fields,
            "range_fields": range_fields,
        }

    def get_sample(self, limit=30, offset=0, output_format="json", selection_string=None):
        table = self.config["cannonical_table"]
        columns = ",".join(self.config["key_columns"])
        query = self.queries["SAMPLE_QUERY"]
        
        if selection_string is not None:
            query += selection_string

        if limit is None:
            query += ";"
        else:
            query += f" LIMIT {limit} OFFSET {offset};"
        df = pd.read_sql_query(query.format(columns, table), self.con)
        if output_format == "json":
            return json.loads(df.to_json(orient="records"))
        elif output_format == "pandas":
            return df
        else:
            return df

if __name__ == "__main__":

    import json
    import logging
    import os

    DB_HOME = os.path.expanduser("~/gwu-src/feast/data")

    logger = logging.getLogger()

    connections = {}
    with open("db_config.json") as config_p:
        config = json.load(config_p)
    for bco_id, dataset_config in config.items():
        db_path = os.path.join(DB_HOME, dataset_config["db_location"])
        connections[bco_id] = DBInterface(db_path, dataset_config, logger)

    for name, dbi in connections.items():
        print(f"---- {name} ----")
        df = dbi.get_sample(size=None, output_format="pandas")
        d_types = []
        uniques = {}
        for col in df.columns:
            d_types.append(df[col].dtype)
            print(f"{col}: {df[col].dtype}")
            uniques = df[col].unique()
            # if len(uniques) > 50:
            #     print(f"{col} : {uniques[:50]}")
            # else:
            print(f"{col} : {uniques}")
    