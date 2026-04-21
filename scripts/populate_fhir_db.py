import logging
import pandas as pd
import sys
import time

from argparse import ArgumentParser
from pathlib import Path

from script_utils.db_setup import load_db_connections
from script_utils.fhir_client import get_access_token, post_fhir_data, query_single_patient
from script_utils.populate_utilities import (
    objects_from_single_df,
    objects_from_joint_df,
    patients_from_df,
)

DB_HOME = Path("/data/arpah/processed")

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--live-run", "-l", action="store_true")
    args = parser.parse_args()

    access_info = get_access_token()
    access_token = access_info["access_token"]
    if not access_token:
        sys.exit("Access token error! Aborting")
    print(f"\tAccess token: {access_token}")

    db_connections = load_db_connections(None, DB_HOME, logger)
    if not db_connections:
        sys.exit("No DB connections available, aborting")

    for db_bco, dbi in db_connections.items():
        print(f"---> Checking in on BCO {db_bco}")
        metadata = dbi.get_db_metadata()
        print(f"{db_bco} - DB size: {metadata['size']}")

        fhir_items = ["Procedure", "DiagnosticReport", "Encounter"]
        offset = 0
        chunk_size = 10
        SAMPLE_SIZE = 1

        patient_data = dbi.get_sample_for_fhir_upload(
            data_type="Patient", offset=offset, limit=chunk_size
        )
        converter = patient_data["converter"]
        patient_objects = patients_from_df(patient_data["data"], converter)

        if not args.live_run:
            print(f"[dryrun] {db_bco}: would POST {len(patient_objects)} Patient records")
        else:
            for o in patient_objects[:10]:
                post_results = post_fhir_data(access_token, o.as_json(), "Patient")
                print(f"Patient POST: {post_results}")

        patient_ids = patient_data["data"]["DurableKey_e"].unique()
        print(f"---> Found {len(patient_ids)} patient IDs.")
        pids = patient_ids[:SAMPLE_SIZE]

        for fhir_item in fhir_items:
            data_time = time.time()
            data = dbi.get_sample_for_fhir_upload(
                data_type=fhir_item, offset=offset, limit=chunk_size
            )
            print(f"Loading {fhir_item} data required {time.time() - data_time:.2f}s")

            resource_url_strings = {}
            for pid in pids:
                response = query_single_patient(access_token, pid)
                if response["resourceType"] != "Bundle":
                    raise Exception(f"Unexpected response type: {response['resourceType']}")
                entry = response.get("entry", None)
                if entry and type(entry) is list and len(entry) > 0:
                    resource_url_strings[pid] = [
                        "/".join(e["fullUrl"].split("/")[-2:]) for e in entry
                    ]

            if type(data["data"]) is dict:
                objects = objects_from_joint_df(data, fhir_item, pids, converter, resource_url_strings)
            elif type(data["data"]) is pd.DataFrame:
                objects = objects_from_single_df(data, fhir_item, pids, converter, resource_url_strings)
            else:
                print(f"Skipping {fhir_item}: unexpected data shape")
                continue

            if not args.live_run:
                print(f"[dryrun] {db_bco} {fhir_item}: would POST {len(objects)} objects")
            else:
                post_start = time.time()
                for o in objects:
                    print(post_fhir_data(access_token, o.as_json(), fhir_item))
                print(f"{fhir_item}: POSTed {len(objects)} samples in {time.time() - post_start:.2f}s")
