import logging
import sys
import time

from argparse import ArgumentParser
from pathlib import Path

from script_utils.db_setup import load_db_connections
from script_utils.fhir_client import get_access_token, post_fhir_data
from script_utils.populate_utilities import objects_from_single_df, objects_from_joint_df

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

    fhir_items = ["DiagnosticReport"]
    chunk_size = 1000
    offset = 0

    for fhir_item in fhir_items:
        remaining = sample_count
        while remaining > 0:
            chunk_limit = min(chunk_size, remaining)
            data = dbi.get_sample_for_fhir_upload(
                data_type=fhir_item, offset=offset, limit=chunk_limit
            )
            print(f"Now on sample {offset}")

            # NOTE: FHIR conversion for GWDC1 fields is not yet validated.
            # Wiring up post_fhir_data requires testing object construction first.
            if args.dryrun:
                print(f"[dryrun] {fhir_item}: loaded {len(data['data'])} records at offset {offset}")
            else:
                raise NotImplementedError(
                    "GWDC1 FHIR field upload is not yet tested. Run with --dryrun first."
                )

            samples_count = len(data["data"])
            remaining -= samples_count
            offset += samples_count
