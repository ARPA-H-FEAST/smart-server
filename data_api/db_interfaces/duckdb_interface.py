import duckdb
import pandas as pd

SAMPLE_QUERY = "SELECT * FROM {} LIMIT 20;"
DESCRIPTION_QUERY = "DESCRIBE {};"

class DuckInterface:

    def __init__(self, db_path, config, logger):
        self.con = duckdb.connect(db_path)
        self.cur = self.con.cursor()
        self.config = config
        table = config["cannonical_table"]

        self.headers = self.cur.execute(DESCRIPTION_QUERY.format(table)).df()

        self.logger = logger

    def __del__(self):
        self.con.close()

    def get_sample(self):
        table = self.config["cannonical_table"]
        df = self.cur.execute(SAMPLE_QUERY.format(table)).df().to_json(
            orient="records"
        )
        return df

