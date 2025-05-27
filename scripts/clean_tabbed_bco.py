import json
import os

from pathlib import Path

BCO_ID = 4

BCO_NAME = f"FEAST_{BCO_ID:06}.json"

DATA_DIR = "datadir/releases/current/jsondb/bcodb"

cwd = os.getcwd()

parent = Path(cwd).parent

bco_path = os.path.join(parent, DATA_DIR, BCO_NAME)

with open(bco_path, "r") as fp:
    json_data = json.load(fp)

with open(bco_path, "w") as fp:
    json.dump(json_data, fp, indent=2)
