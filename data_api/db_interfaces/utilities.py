import os
import pandas as pd
from functools import reduce

def single_parquet_to_df(file_location, file_name, columns=None):
        # columns = self.config["fhir_columns"][data_type]
        # print(f"---> Isolating to columns\n{columns}")
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
