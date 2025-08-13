import sqlite3 as sql

import duckdb
import pandas as pd
import json

try:
    ## Import in Django
    from .fhir_converters import FHIR_CONVERTER
except:
    ## Import for command line
    from fhir_converters import FHIR_CONVERTER

SQL_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "RANDOM_SAMPLE": "SELECT * FROM {} WHERE {} in (SELECT {} FROM {} ORDER BY RANDOM() LIMIT {});",
    "GET_UNIQUE": "SELECT DISTINCT {} FROM {};",
    "MIN": "SELECT MIN({}) FROM {};",
    "MAX": "SELECT MAX({}) FROM {};",
}

DUCK_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "RANDOM_SAMPLE": "SELECT * FROM {} WHERE {} in (SELECT {} FROM {} ORDER BY RANDOM() LIMIT {});",
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
        self.fhir_converter = FHIR_CONVERTER[config["dataset"]]
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
                    uniques = self.cur.execute(
                        self.queries["GET_UNIQUE"].format(field, table)
                    ).fetchall()
                    search_obj = {"name": field, "levels": [u[0] for u in uniques]}
                    search_fields.append(search_obj)
                    # self.logger.debug(f"===> Found unique search levels for {field}: {search_obj}")
            elif cat == "numerical":
                for field in indexed_info[cat]:
                    min = self.cur.execute(
                        self.queries["MIN"].format(field, table)
                    ).fetchone()
                    max = self.cur.execute(
                        self.queries["MAX"].format(field, table)
                    ).fetchone()
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

    def get_sample(
        self, limit=30, offset=0, output_format="json", selection_string=None,
        data_type=None
    ):
        table = self.config["cannonical_table"]
        query = self.queries["SAMPLE_QUERY"]
        if output_format == "json":
            columns = ",".join(self.config["key_columns"])
        elif output_format == "fhir":
            columns = ",".join(self.config["fhir_columns"])
        if selection_string is not None:
            query += selection_string

        if limit is None:
            query += ";"
        else:
            query += f" LIMIT {limit} OFFSET {offset};"
        if output_format == "json":
            df = pd.read_sql_query(query.format(columns, table), self.con)
            return json.loads(df.to_json(orient="records"))
        elif output_format == "fhir":
            self.logger.debug(f"Data type: {data_type} ::: FHIR Converter keys: {self.fhir_converter.keys()}")
            if data_type not in self.fhir_converter.keys():
                return ["Error", f"Data type {data_type} not found in DB records"]
            data_rows = self.con.execute(query.format(columns, table)).fetchall()
            self.logger.debug(f"===> Found {len(data_rows)} data points")
            return [self.fhir_converter[data_type](dr) for dr in data_rows]

    def get_random_sample(self):
        table = self.config["cannonical_table"]
        query = self.queries["RANDOM_SAMPLE"]
        random_sampling_config = self.config["random_sampling_keys"]
        
        column_headers = self.config["key_columns"]
        
        formatted_query = query.format(
            table, random_sampling_config[0], random_sampling_config[0], 
            table, random_sampling_config[1])
        # self.logger.debug(f"Executing query: {formatted_query}")
        # print(f"Executing query: {formatted_query}")

        random_data = self.con.execute(formatted_query).fetchall()
        return random_data, column_headers

        # elif output_format == "pandas":
        #     return df
        # else:
        #     return df



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
        random_data, column_headers = dbi.get_random_sample()
        print(f"{name}: Collected {len(random_data)} samples")
        
        with open(f"{name}-RandomSamples.csv", "w") as fp:
            fp.write(",".join(column_headers) + "\n")
            for line in random_data:
                fp.write(",".join([str(l) for l in line]) + "\n")
        fp.close()

        # df = dbi.get_sample(size=None, output_format="pandas")
        # d_types = []
        # uniques = {}
        # for col in df.columns:
        #     d_types.append(df[col].dtype)
        #     print(f"{col}: {df[col].dtype}")
        #     uniques = df[col].unique()
        #     # if len(uniques) > 50:
        #     #     print(f"{col} : {uniques[:50]}")
        #     # else:
        #     print(f"{col} : {uniques}")
