import datetime
import logging
import pandas as pd
import sys
import time

from argparse import ArgumentParser
from collections import Counter
from pathlib import Path
import script_utils.fhir_client as fhir_client
from script_utils.db_setup import PROJECT_ROOT, load_db_connections
from script_utils.fhir_client import get_access_token, post_fhir_data, query_single_patient
from script_utils.populate_utilities import (
    catalog_objects_from_joint_df,
    objects_from_single_df,
    objects_from_joint_df,
)

DB_HOME = PROJECT_ROOT / "datadir/processed"
BCO_ID = "FEAST_000013"

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

PATIENT_ITEMS = [
    "MedicationRequest",
    "MedicationAdministration",
    "MedicationDispense",
    "MedicationStatement",
]

if __name__ == "__main__":
    big_start = time.time()

    parser = ArgumentParser()
    parser.add_argument(
        "--index", "-i", default=-1, type=int,
        help="Index 1-12; or default -1 for testing only"
    )
    parser.add_argument("--live-run", "-l", action="store_true")
    parser.add_argument("--truncated-run", "-t", action="store_true")
    parser.add_argument(
        "--skip-catalog", action="store_true",
        help="Skip the Medication catalog upload (e.g., already done)"
    )
    parser.add_argument(
        "--server", "-s", default=None,
        help="Override FHIR base URL (e.g. http://localhost:8080/fhir/). Skips OAuth."
    )
    parser.add_argument(
        "--db-home", default=None,
        help="Override data directory (parent of downloads/GWDC_BrPrLuCA/). "
             "Default: <project_root>/datadir/processed"
    )
    args = parser.parse_args()

    allowed_index = {-1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}
    if args.index not in allowed_index:
        sys.exit(f"Index {args.index} not valid (valid: {sorted(allowed_index)})")

    db_connections = load_db_connections(BCO_ID, Path(args.db_home) if args.db_home else DB_HOME, logger)
    if not db_connections:
        sys.exit("No DB connections available, aborting")

    if args.server:
        fhir_client.FHIR_URL = args.server.rstrip("/") + "/"
        access_token = ""
        print(f"Using server override: {fhir_client.FHIR_URL} (no OAuth)")
    else:
        access_info = get_access_token()
        access_token = access_info["access_token"]
        if not access_token:
            sys.exit("Access token error! Aborting")

    dbi = db_connections[BCO_ID]
    metadata = dbi.get_db_metadata()
    print(f"{BCO_ID} - DB size: {metadata['size']}")

    # ------------------------------------------------------------------ #
    # Phase 1: Medication catalog (non-patient resource, upload once)
    # ------------------------------------------------------------------ #
    if not args.skip_catalog:
        print("Phase 1: Uploading Medication catalog...")
        cat_start = time.time()
        med_data = dbi.get_sample_for_fhir_upload(data_type="Medication")
        med_converter = med_data["converter"]
        med_objects = catalog_objects_from_joint_df(med_data, "Medication", med_converter)
        print(f"---> Found {len(med_objects)} Medication catalog entries")
        if not args.live_run:
            print(f"[dryrun] Medication: would upload {len(med_objects)} objects")
        else:
            errors = 0
            for idx, obj in enumerate(med_objects):
                resp = post_fhir_data(access_token, obj.as_json(), "Medication")
                if "resourceType" not in resp:
                    logger.error(f"BAD RESPONSE: {resp}")
                    errors += 1
                elif resp["resourceType"] != "Medication":
                    logger.error(f"MISMATCHED ITEM for Medication: {resp}")
                    errors += 1
                if args.truncated_run and idx >= 10:
                    break
            print(f"Medication catalog: {idx + 1} uploaded, {errors} errors in {time.time() - cat_start:.2f}s")
    else:
        print("Phase 1: Skipping Medication catalog (--skip-catalog)")

    # ------------------------------------------------------------------ #
    # Phase 2: Patient data load + index calculation
    # ------------------------------------------------------------------ #
    print("Phase 2: Loading patient list...")
    offset = 0
    chunk_size = 10

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

    # ------------------------------------------------------------------ #
    # Phase 3: Per-patient FHIR items
    # ------------------------------------------------------------------ #
    print(f"Phase 3: Uploading patient-specific items: {PATIENT_ITEMS}")
    record_counter = Counter()

    for fhir_item in PATIENT_ITEMS:
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
                    log.debug(f"FAILED URL: {fhir_client.FHIR_URL}Patient?identifier={pid}")
                elif type(entry) is not list:
                    raise Exception(f"Unknown entry shape: {entry}")
                elif len(entry) > 0:
                    resource_url_strings[pid] = [
                        "/".join(e["fullUrl"].split("/")[-2:]) for e in entry
                    ]
                else:
                    log.debug(f"Missing resource? {response}")

            if type(data["data"]) is dict:
                objects = objects_from_joint_df(data, fhir_item, pids, converter, resource_url_strings)
                if not args.live_run:
                    log.debug(f"[dryrun] {fhir_item}: would upload {len(objects)} objects for {len(pids)} patients")
                else:
                    log.debug(f"---> Found {len(objects)} total objects for upload...")
                    log.debug(f"\t(Estimate {len(objects) / 3000:.1f} minutes to complete)")
                    post_start = time.time()
                    for idx, o in enumerate(objects):
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        if "resourceType" not in post_success:
                            log.error(f"BAD RESPONSE: {post_success}")
                        elif post_success["resourceType"] != fhir_item:
                            log.error(f"MISMATCHED ITEM for {fhir_item}: {post_success}")
                        if args.truncated_run and idx >= 10:
                            break
                    log.debug(f"{fhir_item}: POSTed {len(pids)} patient IDs, {idx + 1} objects in {time.time() - post_start:.2f}s")
                    log.debug(f"====> PIDs were {', '.join(pids)}")

            elif type(data["data"]) is pd.DataFrame:
                objects = objects_from_single_df(data, fhir_item, pids, converter, resource_url_strings)
                if not args.live_run:
                    log.debug(f"[dryrun] {fhir_item}: would upload {len(objects)} objects for {len(pids)} patients")
                else:
                    log.debug(f"---> Found {len(objects)} total objects for upload...")
                    log.debug(f"\t(Estimate {len(objects) / 3000:.1f} minutes to complete)")
                    post_start = time.time()
                    for idx, o in enumerate(objects):
                        post_success = post_fhir_data(access_token, o.as_json(), fhir_item)
                        if "resourceType" not in post_success:
                            log.error(f"BAD RESPONSE: {post_success}")
                        elif post_success["resourceType"] != fhir_item:
                            log.error(f"MISMATCHED ITEM for {fhir_item}: {post_success}")
                        if args.truncated_run and idx >= 10:
                            break
                    log.debug(f"{fhir_item}: POSTed {len(pids)} patient IDs, {idx + 1} objects in {time.time() - post_start:.2f}s")
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
