import json
import os
import sys

from pathlib import Path

# PROJECT_ROOT is the smart-server directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_db_connections(bco_id, db_home, logger):
    """Load DBInterface connections from db_config.json.

    bco_id: the BCO ID string to load, or None to load all.
    db_home: Path to the processed data directory.
    logger: logger instance passed to DBInterface.

    Returns a dict mapping bco_id -> DBInterface.
    """
    sys.path.append(str(PROJECT_ROOT))
    from data_api.db_interfaces import DBInterface

    db_config_path = PROJECT_ROOT / "data_api/db_interfaces/db_config.json"
    with open(db_config_path, "r") as fp:
        config = json.load(fp)

    db_connections = {}
    for cfg_bco_id, dataset_config in config.items():
        if bco_id is not None and cfg_bco_id != bco_id:
            continue

        db_location = dataset_config["db_location"]
        if type(db_location) is not list:
            db_path = os.path.join(db_home, db_location)
        else:
            db_path = str(Path(db_home).parent / db_location[1])

        try:
            dbi = DBInterface(db_path, dataset_config, logger)
            db_connections[cfg_bco_id] = dbi
        except Exception as e:
            # Alternate path for NBCC sqlite DB
            if cfg_bco_id == "FEAST_000012":
                alt_path = str(Path(__file__).parent.parent / "nbcc.db")
                dataset_config["db_location"] = "nbcc.db"
                dbi = DBInterface(alt_path, dataset_config, logger)
                db_connections[cfg_bco_id] = dbi
                continue
            # Alternate path for GWDC1 duckdb
            if cfg_bco_id == "FEAST_000004" and os.path.exists("GDWC.duckdb"):
                print(f"Attempting alternate DB load on duckdb")
                alt_path = str(Path(__file__).parent.parent / "GDWC.duckdb")
                dataset_config["db_location"] = "GDWC.duckdb"
                dbi = DBInterface(alt_path, dataset_config, logger)
                db_connections[cfg_bco_id] = dbi
                continue
            print(f"---> EXCEPTION ON DB {cfg_bco_id}: {e}")
            print(f"...moving on...")

    return db_connections
