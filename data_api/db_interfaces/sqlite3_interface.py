import sqlite3 as sql
import pandas as pd

SAMPLE_QUERY = "SELECT * FROM {} LIMIT 20;"

class SQLiteInterface:

    def __init__(self, db_path, config, logger):
        self.con = sql.connect(db_path, check_same_thread=False)
        self.cur = self.con.cursor()
        self.config = config


        self.logger = logger
    
    def __del__(self):
        self.con.close()

    def get_sample(self):
        table = self.config["cannonical_table"]

        df = pd.read_sql_query(SAMPLE_QUERY.format(table), self.con).to_json(
            orient="records"
        )
        return df
