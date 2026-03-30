import json
import logging
import os
import socket
import sys

from argparse import ArgumentParser
from pathlib import Path

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
BCO_ID = "FEAST_000013"

from data_api.db_interfaces import DBInterface

if __name__ == "__main__":

    hostname = socket.gethostname()
    print(f"Hostname is {hostname}")
    if hostname == "mgpc":
        DB_HOME = Path("/data/arpah/processed")
    else:
        DB_HOME = os.path.expanduser("~/gwu-src/feast/data")
    logger = logging.getLogger()

    parser = ArgumentParser()
    parser.add_argument("-b", "--bco-target", required=True, help="BCO of target data set to draw samples from")
    args = parser.parse_args()
    bco_target = args.bco_target

    connections = {}
    db_config_path = os.path.join(PROJECT_ROOT, "data_api/db_interfaces/db_config.json")
    with open(db_config_path, "r") as config_p:
        config = json.load(config_p)
    for bco_id, dataset_config in config.items():
        if bco_id != bco_target:
            continue
        # Carve-out for parquets
        db_location = dataset_config["db_location"]
        if type(db_location) is not list:
            db_path = os.path.join(DB_HOME, db_location)
        else:
            db_path = str(Path(DB_HOME).parent / db_location[1])
        connections[bco_id] = DBInterface(db_path, dataset_config, logger)

    print(f"---- {bco_target} ----")
    dbi = connections[bco_target]
    random_data, column_headers = dbi.get_random_sample(data_type="Patient")
    print(f"{bco_target}: Collected {len(random_data)} samples")

    with open(f"{bco_target}-RandomSamples.csv", "w") as fp:
        fp.write(",".join(column_headers) + "\n")
        for line in random_data:
            fp.write(",".join([str(l) for l in line]) + "\n")
    fp.close()