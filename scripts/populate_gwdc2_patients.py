import logging
import sys
import time

from argparse import ArgumentParser
from pathlib import Path

from script_utils.db_setup import load_db_connections
from script_utils.fhir_client import get_access_token, post_fhir_data
from script_utils.populate_utilities import patients_from_df

DB_HOME = Path("/data/arpah/processed")
BCO_ID = "FEAST_000013"

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--live-run", "-l", action="store_true")
    args = parser.parse_args()

    big_start = time.time()

    db_connections = load_db_connections(BCO_ID, DB_HOME, logger)
    if not db_connections:
        sys.exit("No DB connections available, aborting")

    access_info = get_access_token()
    access_token = access_info["access_token"]
    if not access_token:
        sys.exit("Access token error! Aborting")

    dbi = db_connections[BCO_ID]
    metadata = dbi.get_db_metadata()
    print(f"{BCO_ID} - DB size: {metadata['size']}")

    chunk_size = 10
    offset = 0
    print("Handling parquets...")

    patient_data = dbi.get_sample_for_fhir_upload(
        data_type="Patient", offset=offset, limit=chunk_size
    )
    patient_objects = patients_from_df(patient_data["data"], patient_data["converter"])
    if not args.live_run:
        print(f"[dryrun] Would POST {len(patient_objects)} Patient records")
    else:
        start = time.time()
        for o in patient_objects:
            post_results = post_fhir_data(access_token, o.as_json(), "Patient")
        print(f"Loading patients required {time.time() - start:.2f}s")

    with open("upload_records/gwdc2-patients.log", "w") as log:
        log.write(f"GWDC2: Wrote {metadata['size']} patient records\n")
        log.write(f"Total time required was {time.time() - big_start:.2f}\n")
