import duckdb

SAMPLE_QUERY = "SELECT * FROM {} LIMIT 20;"

class DuckInterface:

    def __init__(self, db_path, config):
        self.con = duckdb.connect(db_path)
        self.cur = self.con.cursor()
        self.config = config

    def __del__(self):
        self.con.close()

    def get_sample(self):
        table = self.config["cannonical_table"]
        return self.cur.execute(SAMPLE_QUERY.format(table)).fetchall()
