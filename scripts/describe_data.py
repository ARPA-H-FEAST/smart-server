import pandas as pd
import sqlite3 as sql

import os
import time

DATA_HOME = "/data/arpah/downloads/GWDC_BrPrLuCA"
DB_HOME = "/data/arpah/processed/GWDC_BrPrLuCA"
DB_NAME = "GWDC_BreastCancer_LungCancer_ProstateCancer.sqlite"

counter = 0

counts = {}

## SQLite - DEPRECATED
"""
db_conn = sql.connect(database=os.path.join(DB_HOME, DB_NAME))

cursor = db_conn.cursor()
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()

big_start = time.time()

print(f"Found {len(tables)} tables\n{tables}")

for t in tables:
    start = time.time()
    table_name = t[0]
    # row_count = cursor.execute(f'SELECT COUNT(*) FROM {table_name};').fetchall()[0][0]
    # print(f"{t}: Found {row_count} samples")
    # counts[table_name+"DB"] = row_count
    # print(f"{table_name}: Required {time.time() - start:.2f}s")
    df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5;", db_conn)
    print(f"{table_name}:\n{df}")


db_conn.close()
"""

## PARQUETS - INITIAL DATA

parquets = []

for root, dirnames, files in os.walk(DATA_HOME):
    if root != DATA_HOME:
        continue
    counter += 1
    
    for f in files:
        if "parquet" not in f:
            continue
        parquets.append(f)
print(f"Found {len(parquets)} files")

# output_file = "header_descriptions.csv"

for f in parquets:
    start = time.time()
    # print(f"Processing {f}")
    df = pd.read_parquet(os.path.join(DATA_HOME, f))
    file_name = f.replace("parquet", "") + "tsv"
    with open(file_name, "w") as fp:
        for c in df.columns:
            try:
                uniques = df[c].unique().tolist()
                if len(uniques) > 10:
                    uniques = uniques[:10]
            except Exception as e:
                raise e(f"Type of uniques was {type(uniques)} (uniques)")
            print(f"c is {c} --- uniques is {uniques}")
            output_str = "{0}\t{1}\n".format(str(c), "\t".join([str(s) for s in uniques]))
            fp.write(output_str)
    # df[:5].to_csv(file_name, index=False)
    # print(f"{f}: Size {df.shape}")
    print(f"{f}: Processing complete ....")
    # print(f"{f}: {sorted(list(df.columns))}")
    # with open(output_file, "a") as fp:
    #     fp.write("{}\t{}\n".format(f, '\t'.join(list(df.columns))))
    # counts[f] = df.shape[0]
    # print(f"Required {time.time() - start:.2f}s")



