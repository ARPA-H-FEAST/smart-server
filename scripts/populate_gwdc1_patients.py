import logging
import sys
import time

from argparse import ArgumentParser
from pathlib import Path

from script_utils.db_setup import load_db_connections
from script_utils.fhir_client import get_access_token, post_fhir_data
from script_utils.populate_utilities import patients_from_df

DB_HOME = Path("/data/arpah/processed")
BCO_ID = "FEAST_000004"

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--dryrun", "-d", action="store_true")
    args = parser.parse_args()

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
    sample_count = metadata["size"]

    chunk_size = 1000
    offset = 0
    while sample_count > 0:
        chunk_limit = min(chunk_size, sample_count)
        data = dbi.get_sample_for_fhir_upload(
            data_type="Patient", offset=offset, limit=chunk_limit
        )
        print(f"Now on sample {offset}")
        patient_objects = patients_from_df(data["data"], data["converter"])
        if args.dryrun:
            print(f"[dryrun] Would POST {len(patient_objects)} Patient records")
        else:
            for d in patient_objects:
                post_success = post_fhir_data(access_token, d.as_json(), "Patient")
            print(post_success)
        samples_uploaded = len(patient_objects)
        sample_count -= samples_uploaded
        offset += samples_uploaded

    with open("gwdc1-patients.txt", "w") as log:
        log.write(f"GWDC Prostate: Wrote {metadata['size']} patient logs\n")
