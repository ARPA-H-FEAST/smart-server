import sqlite3 as sql

import duckdb
import pandas as pd
import json
import os

from .utilities import (
    make_fhir_record_type,
    single_parquet_to_df,
    single_table_query_to_string,
    join_tables_no_select,
    join_parquet_tables
)

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
    "COUNT": "SELECT COUNT(*) FROM {};",
}

DUCK_QUERIES = {
    "SAMPLE_QUERY": "SELECT {} FROM {}",
    "RANDOM_SAMPLE": "SELECT {} FROM {} WHERE {} in (SELECT {} FROM {} ORDER BY RANDOM() LIMIT {});",
    "GET_UNIQUE": "SELECT DISTINCT {} FROM {};",
    "MIN": "SELECT MIN({}) FROM {};",
    "MAX": "SELECT MAX({}) FROM {};",
    "TABLES": "SHOW TABLES;",
    "COUNT": "SELECT COUNT(*) FROM {};",
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

def duck_join(join_config, columns):
    print(f"---> DUCK Config: {join_config}")
    print(f"---> Columns: {columns}")
    primary_table = join_config["primary_table"]
    other_tables = join_config["other_tables"]
    primary_cols = columns[primary_table]

    fk = join_config["fk"]
    select_str = ""
    for col in primary_cols:
        select_str += f"t1.{col} AS {primary_table}__{col},"
    for idx, table in enumerate(other_tables):
        for col in columns[table]:
            select_str += f"t{idx+2}.{col} AS {table}__{col},"
    select_str = select_str.rstrip(",")
    print(f"Running select string: {select_str}")

    from_join_str = ""
    tables = [primary_table]
    tables.extend(other_tables)
    for idx, table_name in enumerate(tables):
        if idx == 0:
            from_join_str += f" {table_name} AS t{idx+1} "
        else:
            from_join_str += f" JOIN {table_name} AS t{idx+1} ON t{idx}.{fk} = t{idx+1}.{fk} "

    return select_str, from_join_str

def sql_select(filters: dict):
    query_str = " WHERE\n\t"
    col_counter = 0
    for column, values in filters.items():
        if col_counter > 0:
            query_str += "\tAND "
        query_str += "{} IN ({})\n".format(column, ",".join(values))
        col_counter += 1

    return query_str

def sql_join(join_config: dict):
    print(f"---> SQL Config: {join_config}")
    return True

class DBInterface:

    def __init__(self, db_path, config, logger):

        db_class = config["db_class"]
        if db_class == "duckdb":
            self.con = duckdb.connect(db_path)
            self.cur = self.con.cursor()
            self.queries = DUCK_QUERIES
            self.select_function = duck_select
            self.join_function = duck_join

        elif db_class == "sqlite3":
            try:
                self.con = sql.connect(db_path, check_same_thread=False)
            except Exception as e:
                logger.error(f"Connection error: DB is {db_path}")
                raise
            self.cur = self.con.cursor()
            self.queries = SQL_QUERIES
            self.select_function = sql_select
            logger.error(f"---> SQLite3: DB path is {db_path}")
            self.join_function = sql_join

        elif db_class == "parquet":
            self.con = None
            self.cur = None
            self.queries = None
            self.select_function = None
            self.join_function = None
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
        search_fields = []
        range_fields = []
        table_alias = self.config["entry_table"] if table is None else table
        table = self.config["searchable_tables"][table_alias]

        if self.cur is None:
            # Parquet special handling
            if type(table) is str:
                df = single_parquet_to_df(self.file_location, table)
                table_size = df.shape
                # print(f"---> Parquet: Got table size {table_size}")
                return {"size": table_size[0], "search_fields": [], "range_fields": []}
            elif type(table) is dict:
                self.logger.debug(f"Handling a dict table def with configuration\n{table}")
        try:
            table_size = self.cur.execute(self.queries["COUNT"].format(table)).fetchall()[0][0]
        except Exception as e:
            self.logger.error(f"Exception: {e}")
            self.logger.error(f"---> See above for file...")
            self.logger.error(f"My config:\n{self.config}")
            tables_available = self._get_tables()
            print(f"---> Tables available: {tables_available}")
            raise

        # XXX - Performance hit
        # for cat in indexed_info[table_alias].keys():
        #     if cat == "categorical":
        #         for field in indexed_info[table_alias][cat]:
        #             # self.logger.debug(f"===> Looking for unique field {field} in table {table}")
        #             uniques = self.cur.execute(
        #                 self.queries["GET_UNIQUE"].format(field, table)
        #             ).fetchall()
        #             search_obj = {"name": field, "levels": [u[0] for u in uniques]}
        #             search_fields.append(search_obj)
        #             # self.logger.debug(f"===> Found unique search levels for {field}: {search_obj}")
        #     elif cat == "numerical":
        #         for field in indexed_info[table_alias][cat]:
        #             min = self.cur.execute(
        #                 self.queries["MIN"].format(field, table)
        #             ).fetchone()
        #             max = self.cur.execute(
        #                 self.queries["MAX"].format(field, table)
        #             ).fetchone()
        #             # self.logger.debug(f"===> Found MIN/MAX search levels for {field}: {min}/{max}")
        #             range_fields.append({"name": field, "range": [min, max]})
        #     else:
        #         # raise Exception(f"===> Please implement support for field {cat}!!")
        #         self.logger.debug(f"===> Please implement support for field {cat}!!")

        return {
            "size": table_size,
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
            if not os.path.exists(file_path):
                table_name = ".BrPrLu.".join(table.split("."))
                file_path = os.path.join(self.file_location, table_name)

            columns = self.config["fhir_columns"][data_type]
            # print(f"---> Isolating to columns\n{columns}")
            df = pd.read_parquet(file_path, columns=columns)
            return {
                "data": [
                    self.fhir_converter[data_type](dr)
                    for dr
                    in df.itertuples(index=False)
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
        # self.logger.debug(f"=> Template query:\n{query}")

        final_query = query.format(columns, table)
        # self.logger.debug(f"=> Final query:\n{final_query}")
        if output_format == "json":
            df = pd.read_sql_query(final_query, self.con)
            response = {
                "data": df.to_dict(orient="records"),
                "pagination": {"sample_size": limit, "offset": offset},
            }
            return response
        elif output_format == "fhir":
            column_config = self.config["fhir_columns"][data_type]
            record_type = make_fhir_record_type(data_type, column_config)
            data_rows = self.con.execute(final_query).fetchall()
            data = []
            for dr in data_rows:
                try:
                    d = self.fhir_converter[data_type](record_type(*dr))
                    data.append(d)
                except Exception as e:
                    self.logger.error(f"===> 272 Exception: {e}")
                    self.logger.error(f"Data row: {dr}")
                    self.logger.error(f"Query was {final_query}")
                    raise

            response = {
                "data": data,
                "pagination": {"sample_size": limit, "offset": offset},
            }
            return response

    def get_sample_for_fhir_upload(
        self,
        limit=100,
        offset=0,
        query_dict=None,
        data_type=None,
    ):
        table_alias = self.config["fhir_tables"].get(data_type, None)
        if not table_alias:
            self.logger.error("No FHIR table configured, no data available")
            return {"data": ["dummy"], "pagination": {}}


        if self.cur is None:
            # Parquet handling
            if type(table_alias) is str:
                columns = self.config["fhir_columns"][data_type]
                df = single_parquet_to_df(self.file_location, table_alias, columns=columns)
                # print(f"---> Isolating to columns\n{columns}")
                return {
                    "data": df,
                    "pagination": {"sample_size": df.shape, "offset": 0},
                    "converter": self.fhir_converter,
                }
            elif type(table_alias) is dict:
                column_config = self.config["fhir_columns"][data_type]
                table_config = table_alias
                dfs = {}
                primary_table_name = table_config['primary_table']
                primary_columns = column_config[primary_table_name]
                dfs['primary'] = single_parquet_to_df(
                    self.file_location, primary_table_name, columns=primary_columns
                )
                for tn in table_config['other_tables']:
                    columns = column_config[tn]
                    dfs[tn] = single_parquet_to_df(
                        self.file_location, tn, columns=columns
                        )
                shapes = {}
                for k, v in dfs.items():
                    shapes[k] = v.shape
                # data = [
                #     self.fhir_converter[data_type](dr) 
                #     for dr
                #     in final_df.itertuples(index=False, name=None)
                # ]
                return {
                    "data": dfs, 
                    "pagination": {"sample_size": shapes, "offset": 0},
                    "converter": self.fhir_converter,
                    "config": table_config,
                    }

        if type(table_alias) is str:
            columns = self.config["fhir_columns"][data_type]
            final_query = single_table_query_to_string(
                self.queries["SAMPLE_QUERY"], query_dict, self.select_function,
                columns, table_alias, limit=limit, offset=offset
            )
        elif type(table_alias) is dict:
            base_query = self.queries["SAMPLE_QUERY"]
            column_config = self.config["fhir_columns"][data_type]
            table_config = table_alias
            final_query = join_tables_no_select(
                base_query, table_config, column_config, self.join_function
            )
        else:
            raise Exception("Illegal definition")
        self.logger.debug(f"=> Final query:\n{final_query}")
        column_config = self.config["fhir_columns"][data_type]
        record_type = make_fhir_record_type(data_type, column_config)
        data_rows = self.con.execute(final_query).fetchall()
        data = []
        for dr in data_rows:
            try:
                d = self.fhir_converter[data_type](record_type(*dr))
                data.append(d)
            except Exception as e:
                self.logger.error(f"===> 362 Exception: {e}")
                self.logger.error(f"Data row: {dr}")
                raise

        response = {
            "data": data,
            "pagination": {"sample_size": limit, "offset": offset},
        }
        return response

    def get_random_sample(self, size=100, table=None, data_type=None):

        table_alias = self.config["entry_table"] if table is None else table
        table = self.config["searchable_tables"][table_alias]

        if self.con is None:
            # Yet another exception for parquets
            if type(table_alias) is str:
                columns = self.config["fhir_columns"][data_type]
                df = single_parquet_to_df(self.file_location, table, columns=columns)
                # print(f"---> Isolating to columns\n{columns}")
                sample = df.sample(n=100)
                random_samples = []
                for s in sample.itertuples(index=False):
                    random_samples.append(s)
                return random_samples, columns

            elif type(table_alias) is dict:
                column_config = self.config["fhir_columns"][data_type]
                table_config = table_alias
                dfs = {}
                primary_table_name = table_config['primary_table']
                primary_columns = column_config[primary_table_name]
                dfs['primary'] = single_parquet_to_df(
                    self.file_location, primary_table_name, columns=primary_columns
                )
                for tn in table_config['other_tables']:
                    columns = column_config[tn]
                    dfs[tn] = single_parquet_to_df(
                        self.file_location, tn, columns=columns
                        )
                shapes = {}
                for k, v in dfs.items():
                    shapes[k] = v.shape
                # data = [
                #     self.fhir_converter[data_type](dr) 
                #     for dr
                #     in final_df.itertuples(index=False, name=None)
                # ]
                return {
                    "data": dfs, 
                    "pagination": {"sample_size": shapes, "offset": 0},
                    "converter": self.fhir_converter,
                    "config": table_config,
                    }
            return

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
