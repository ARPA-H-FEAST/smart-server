import os
import pandas as pd
from collections import namedtuple
from functools import reduce


def _dedupe_fields(fields):
    seen = {}
    result = []
    for f in fields:
        if f in seen:
            seen[f] += 1
            result.append(f"{f}_{seen[f]}")
        else:
            seen[f] = 0
            result.append(f)
    return result


def make_fhir_record_type(resource_name, column_config):
    """Build a namedtuple type from a fhir_columns config entry.

    Flat list  → bare field names (e.g. BirthDate).
    Dict       → TableName__ColumnName prefixed names to avoid collisions
                 across joined tables (e.g. DiagnosisDim__Name).
    Duplicate bare names (e.g. PrimaryDiagnosisKey appearing twice in
    Encounter) are suffixed _1, _2, … so namedtuple creation never fails.
    """
    if isinstance(column_config, list):
        fields = _dedupe_fields(column_config)
    else:
        fields = []
        for table_name, cols in column_config.items():
            fields.extend(f"{table_name}__{col}" for col in cols)
    return namedtuple(resource_name, fields)

def single_parquet_to_df(file_location, file_name, columns=None):
        # columns = self.config["fhir_columns"][data_type]
        # print(f"---> Isolating to columns\n{columns}")
        file_name = file_name + ".parquet"
        try:
            file_path = os.path.join(file_location, file_name)
            if columns is None:
                 return pd.read_parquet(file_path)
            return pd.read_parquet(file_path, columns=columns)
        except Exception as e:
            try:
                file_name = ".BrPrLu.".join(file_name.split("."))
                print(f"Testing for file {file_name}")
                if columns is None:
                    return pd.read_parquet(os.path.join(file_location, file_name))
                return pd.read_parquet(os.path.join(file_location, file_name), columns=columns)
            except:
                raise

def single_table_query_to_string(
        base_query, query_args, select_func, columns,
        table_alias, limit=None, offset=None
    ):
    query = base_query
    cols = ",".join(columns)
    if query_args is not None:
       query += select_func(query_args)

    if limit is None:
        query += ";"
    else:
        query += f" LIMIT {limit} OFFSET {offset};"
    return query.format(cols, table_alias)

def join_tables_no_select(base_query, query_args, columns, join_func):
    query = base_query

    select_str, from_join_str = join_func(query_args, columns)

    query = base_query.format(select_str, from_join_str)

    print(f"Got a query: {query}")

    return query

def join_parquet_tables(base_path, table_config):
    print(f"---> BASE PATH: {base_path}")
    print(f"---> TABLE CONFIG: {table_config}")
    primary_table = table_config["primary_table"]
    join_tables = table_config["other_tables"]
    fk = table_config["fk"]
    try:
        dfs = [single_parquet_to_df(base_path, primary_table)]
        dfs.extend([single_parquet_to_df(base_path, t) for t in join_tables])
        final_df = reduce(lambda left, right: pd.merge(left, right, on=fk), dfs)
        return final_df
    except Exception as e:
        raise
