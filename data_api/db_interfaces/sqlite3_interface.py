import sqlite3 as sql

SAMPLE_QUERY = "SELECT * FROM {} LIMIT 20;"

class SQLiteInterface:

    def __init__(self, db_path, config):
        self.con = sql.connect(db_path)
        self.cur = self.con.cursor()
        self.config = config
    
    def __del__(self):
        self.con.close()

    def get_sample(self, table):
        table = self.config["cannonical_table"]
        return self.cur.execute(SAMPLE_QUERY.format(table)).fetchall()
