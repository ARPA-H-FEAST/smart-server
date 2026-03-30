import datetime
import logging
import pandas as pd
import sys
import time

from argparse import ArgumentParser
from collections import Counter
from pathlib import Path

from script_utils.db_setup import load_db_connections
from script_utils.fhir_client import get_access_token, post_fhir_data, query_single_patient, FHIR_URL
from script_utils.populate_utilities import (
    objects_from_single_df,
    objects_from_joint_df,
    describe_object_fields,
)

DB_HOME = Path("/data/arpah/processed")
BCO_ID = "FEAST_000013"

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

if __name__ == "__main__":
    big_start = time.time()

    parser = ArgumentParser()
    parser.add_argument(
        "--index", "-i", default=-1, type=int,
        help="Index 1-12; or default -1 for testing only"
    )
    parser.add_argument("--dryrun", "-d", action="store_true")
    parser.add_argument("--truncated_run", "-t", action="store_true")
    args = parser.parse_args()

    allowed_index = {-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    if args.index not in allowed_index:
        sys.exit(f"Index {args.index} not valid (valid: {sorted(allowed_index)})")

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

    fhir_items = ["Procedure", "DiagnosticReport", "Encounter"]
    offset = 0
    chunk_size = 10
    print("Handling parquets...")

    patient_data = dbi.get_sample_for_fhir_upload(
        data_type="Patient", offset=offset, limit=chunk_size
    )
    converter = patient_data["converter"]
    patient_ids = patient_data["data"]["DurableKey_e"].unique()
    print(f"---> Found a total of {len(patient_ids)} patient IDs.")
    patient_count = len(patient_ids)

    if args.index == -1:
        LOOP_LIMIT = 1
        SAMPLE_SIZE = 10
        START_PATIENT = 0
        patient_count = 10
    else:
        patient_indices = [
            0, 7500, 15000, 22500, 30000, 37500, 45000,
            52500, 60000, 67500, 75000, 82500, patient_count
        ]
        LOOP_LIMIT = None
        SAMPLE_SIZE = 10
        START_PATIENT = patient_indices[args.index - 1]
        patient_count = patient_indices[args.index] - START_PATIENT

    record_counter = Counter()

    for fhir_item in fhir_items:
        PATIENTS_REMAINING = patient_count
        PATIENT_INDEX = START_PATIENT
        item_limit = LOOP_LIMIT

        base_name = f"{fhir_item}-{args.index}"
        log_name = f"upload_records/{base_name}.log"
        log = logging.getLogger(base_name)
        log.setLevel(logging.DEBUG)
        log.addHandler(logging.FileHandler(log_name))

        data_time = time.time()
        data = dbi.get_sample_for_fhir_upload(
            data_type=fhir_item, offset=offset, limit=chunk_size
        )
        log.debug(f" {base_name} : Beginning processing at {datetime.datetime.now()}")
        log.debug(f"---> Looping: Starting at index {START_PATIENT} for {patient_count} patients")
        log.debug(f"Loading data required {time.time() - data_time:.2f}s")

        start = time.time()
        while PATIENTS_REMAINING > 0:
            if item_limit is not None:
                item_limit -= 1
                if item_limit < 0:
                    PATIENTS_REMAINING = 0
                    break

            if PATIENTS_REMAINING < SAMPLE_SIZE:
                pids = patient_ids[PATIENT_INDEX:]
            else:
                pids = patient_ids[PATIENT_INDEX:PATIENT_INDEX + SAMPLE_SIZE]

            resource_url_strings = {}
            for pid in pids:
                response = query_single_patient(access_token, pid)
                if response["resourceType"] != "Bundle":
                    raise Exception(f"Unexpected response type: {response['resourceType']}")
                entry = response.get("entry", None)
                if entry is None:
                    log.debug(f"MISSING ID - PID {pid}: No entry found. Response was {response}")
                    log.debug(f"FAILED URL: {FHIR_URL}Patient?identifier={pid}")
                elif type(entry) is not list:
                    raise Exception(f"Unknown entry shape: {entry}")
                elif len(entry) > 0:
                    resource_url_strings[pid] = [
                        "/".join(e["fullUrl"].split("/")[-2:]) for e in entry
                    ]
                else:
                    log.debug(f"Missing resource? {response}")

            if type(data["data"]) is dict:
                if args.dryrun:
                    objects = objects_from_joint_df(data, fhir_item, pids, converter, resource_url_strings)
                    log.debug(f"[dryrun] {fhir_item}: would upload {len(objects)} objects for {len(pids)} patients")
                else:
                    objects = objects_from_joint_df(data, fhir_item, pids, converter, resource_url_strings)
                    log.debug(f"---> Found {len(objects)} total objects for upload...")
                    log.debug(f"\t(Estimate {len(objects) / 3000:.1f} minutes to complete)")
                    post_start = time.time()
                    for idx, o in enumerate(objects):
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        if "resourceType" not in post_success:
                            log.error(f"BAD RESPONSE: {post_success}")
                        elif post_success["resourceType"] != fhir_item:
                            log.error(f"MISMATCHED ITEM for {fhir_item}: {post_success}")
                        if args.truncated_run and idx > 10:
                            break
                    log.debug(f"{fhir_item}: POSTed {len(pids)} patient IDs, {idx} samples in {time.time() - post_start:.2f}s")
                    log.debug(f"====> PIDs were {', '.join(pids)}")

            elif type(data["data"]) is pd.DataFrame:
                if args.dryrun:
                    objects = objects_from_single_df(data, fhir_item, pids, converter, resource_url_strings)
                    log.debug(f"[dryrun] {fhir_item}: would upload {len(objects)} objects for {len(pids)} patients")
                else:
                    objects = objects_from_single_df(data, fhir_item, pids, converter, resource_url_strings)
                    log.debug(f"---> Found {len(objects)} total objects for upload...")
                    log.debug(f"\t(Estimate {len(objects) / 3000:.1f} minutes to complete)")
                    post_start = time.time()
                    for idx, o in enumerate(objects):
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        if "resourceType" not in post_success:
                            log.error(f"BAD RESPONSE: {post_success}")
                        elif post_success["resourceType"] != fhir_item:
                            log.error(f"MISMATCHED ITEM for {fhir_item}: {post_success}")
                        if args.truncated_run and idx > 10:
                            break
                    log.debug(f"{fhir_item}: POSTed {len(pids)} patient IDs, {idx} samples in {time.time() - post_start:.2f}s")
                    log.debug(f"====> PIDs were {', '.join(pids)}")

            PATIENTS_REMAINING -= len(pids)
            PATIENT_INDEX += len(pids)
            record_counter[fhir_item] += len(pids)
            log.debug(f"---> {fhir_item}: Now at index {PATIENT_INDEX}")

        log.debug(f"---> FHIR Item {fhir_item}: {PATIENT_INDEX} samples required {time.time() - start:.2f}s")

    for k, v in record_counter.items():
        log.debug(f"{k}: {v} records recorded.")
    log.debug("*" * 80)
    log.debug(f"{base_name} : Halting processing at {datetime.datetime.now()}")
    log.debug(f"\tTotal processing time was {(time.time() - big_start) / 60:.1f} minutes")
    log.debug("*" * 80)
