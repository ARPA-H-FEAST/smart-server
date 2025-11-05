import sqlite3 as sql

import duckdb
import pandas as pd
import json
import os

try:
    ## Import in Django
    from .fhir_converters import FHIR_CONVERTER
except:
    ## Import for command line
    from fhir_converters import FHIR_CONVERTER

SQL_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "RANDOM_SAMPLE": "SELECT {} FROM {} WHERE {} in (SELECT {} FROM {} ORDER BY RANDOM() LIMIT {});",
    "GET_UNIQUE": "SELECT DISTINCT {} FROM {};",
    "MIN": "SELECT MIN({}) FROM {};",
    "MAX": "SELECT MAX({}) FROM {};",
    "TABLES": "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;",
}

DUCK_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "RANDOM_SAMPLE": "SELECT {} FROM {} WHERE {} in (SELECT {} FROM {} ORDER BY RANDOM() LIMIT {});",
    "GET_UNIQUE": "SELECT DISTINCT {} FROM {};",
    "MIN": "SELECT MIN({}) FROM {};",
    "MAX": "SELECT MAX({}) FROM {};",
    "TABLES": "SHOW TABLES;"
}


def duck_select(filters: dict):
    query_str = " WHERE\n\t"
    col_counter = 0
    for column, values in filters.items():
        value_counter = 0
        if col_counter > 0:
            query_str += "\tAND "
        for v in values:
            if value_counter > 0:
                query_str += "\tOR "
            query_str += "{} LIKE '%{}%'\n".format(column, v.replace('"', ""))
            value_counter += 1
        col_counter += 1

    return query_str


def sql_select(filters: dict):
    query_str = " WHERE\n\t"
    col_counter = 0
    for column, values in filters.items():
        if col_counter > 0:
            query_str += "\tAND "
        query_str += "{} IN ({})\n".format(column, ",".join(values))
        col_counter += 1

    return query_str


class DBInterface:

    def __init__(self, db_path, config, logger):

        db_class = config["db_class"]
        if db_class == "duckdb":
            self.con = duckdb.connect(db_path)
            self.cur = self.con.cursor()
            self.queries = DUCK_QUERIES
            self.select_function = duck_select

        elif db_class == "sqlite3":
            self.con = sql.connect(db_path, check_same_thread=False)
            self.cur = self.con.cursor()
            self.queries = SQL_QUERIES
            self.select_function = sql_select
        elif db_class == "parquet":
            self.con = None
            self.cur = None
            self.queries = None
            self.select_function = None
            self.file_location = db_path
        else:
            raise Exception(f"Invalid DB configuration: Unknown DB {db_class}")
        self.fhir_converter = FHIR_CONVERTER[config["dataset"]]
        self.config = config
        self.logger = logger

    def __del__(self):
        if hasattr(self, "con") and self.con is not None:
            self.con.close()

    def get_db_metadata(self, table=None):

        indexed_info = self.config.get("search_fields", None)
        if not indexed_info:
            return {"size": 1, "search_fields": [], "range_fields": []}
        search_fields = []
        range_fields = []
        table_alias = self.config["entry_table"] if table is None else table
        table = self.config["searchable_tables"][table_alias]

        for cat in indexed_info[table_alias].keys():
            if cat == "categorical":
                for field in indexed_info[table_alias][cat]:
                    # self.logger.debug(f"===> Looking for unique field {field} in table {table}")
                    uniques = self.cur.execute(
                        self.queries["GET_UNIQUE"].format(field, table)
                    ).fetchall()
                    search_obj = {"name": field, "levels": [u[0] for u in uniques]}
                    search_fields.append(search_obj)
                    # self.logger.debug(f"===> Found unique search levels for {field}: {search_obj}")
            elif cat == "numerical":
                for field in indexed_info[table_alias][cat]:
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
        self,
        table=None,
        limit=30,
        offset=0,
        output_format="json",
        query_dict=None,
        data_type=None,
    ):
        table_alias = self.config["entry_table"] if table is None else table
        table = self.config["searchable_tables"][table_alias]
        if self.cur is None:
            # Parquet handling
            file_path = os.path.join(self.file_location, table)
            columns = self.config["fhir_columns"][data_type]
            # print(f"---> Isolating to columns\n{columns}")
            df = pd.read_parquet(file_path, columns=columns)
            return {
                "data": [
                    self.fhir_converter[data_type](dr) 
                    for dr 
                    in df.itertuples(index=False, name=None)
                ],
                "pagination": {"sample_size": df.shape, "offset": 0},
            }

        query = self.queries["SAMPLE_QUERY"]
        if output_format == "json":
            columns = ",".join(self.config["key_columns"][table_alias])
        elif output_format == "fhir":
            columns = ",".join(self.config["fhir_columns"][table_alias])

        if query_dict is not None:
            query += self.select_function(query_dict)

        if limit is None:
            query += ";"
        else:
            query += f" LIMIT {limit} OFFSET {offset};"
        self.logger.debug(f"=> Template query:\n{query}")

        final_query = query.format(columns, table)
        self.logger.debug(f"=> Final query:\n{final_query}")
        if output_format == "json":
            df = pd.read_sql_query(query.format(columns, table), self.con)
            response = {
                "data": df.to_dict(orient="records"),
                "pagination": {"sample_size": limit, "offset": offset},
            }
            return response
        elif output_format == "fhir":
            self.logger.debug(
                f"Data type: {data_type} ::: FHIR Converter keys: {self.fhir_converter.keys()}"
            )
            if data_type not in self.fhir_converter.keys():
                return ["Error", f"Data type {data_type} not found in DB records"]
            data_rows = self.con.execute(query.format(columns, table)).fetchall()
            self.logger.debug(f"===> Found {len(data_rows)} data points")
            response = {
                "data": [self.fhir_converter[data_type](dr) for dr in data_rows],
                "pagination": {"sample_size": limit, "offset": offset},
            }
            return response

    def get_random_sample(self):
        table = self.config["entry_table"]
        query = self.queries["RANDOM_SAMPLE"]
        random_sampling_config = self.config["random_sampling_keys"]

        column_headers = self.config["key_columns"][table]

        formatted_query = query.format(
            ",".join(column_headers),
            table,
            random_sampling_config[0],
            random_sampling_config[0],
            table,
            random_sampling_config[1],
        )
        # self.logger.debug(f"Executing query: {formatted_query}")
        print(f"Executing query: {formatted_query}")

        random_data = self.con.execute(formatted_query).fetchall()
        return random_data, column_headers

        # elif output_format == "pandas":
        #     return df
        # else:
        #     return df

    def _get_tables(self):
        if self.cur is not None:
            query = self.queries["TABLES"]
            tables = self.cur.execute(query).fetchall()
            return [table[0] for table in tables]
        else:
            # Parquet special handling
            tables = []
            for root, dirs, files in os.walk(self.file_location):
                for f in files:
                    if f.split(".")[-1] == "parquet":
                        tables.append(f)
            return tables

    def _singleton_sample_and_columns(self, table):
        query = self.queries["SAMPLE_QUERY"]
        query = query.format("*", table) + " LIMIT 1;"
        
        df = pd.read_sql_query(query, self.con)
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
        random_data, column_headers = dbi.get_random_sample()
        print(f"{name}: Collected {len(random_data)} samples")

        with open(f"{name}-RandomSamples.csv", "w") as fp:
            fp.write(",".join(column_headers) + "\n")
            line_count = 0
            for line in random_data:
                fp.write(",".join([str(l) for l in line]) + "\n")
                line_count += 1
                if line_count > 9:
                    break
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
