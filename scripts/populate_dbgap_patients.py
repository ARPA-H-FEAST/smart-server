import json
import logging
import sys
import time
import uuid as _uuid
from argparse import ArgumentParser
from pathlib import Path

import pandas as pd
import requests

from script_utils.db_setup import PROJECT_ROOT
from script_utils.fhir_client import get_access_token, build_if_none_exist

import sys as _sys
_sys.path.insert(0, str(PROJECT_ROOT))
from data_api.db_interfaces.fhir_converters import dbgap_patient, dbgap_genomicStudy

logger = logging.getLogger("dbgap_populate")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

_VCF_BASE_CANDIDATES = [
    Path("/data/arpah/dbgap-data/"),
    PROJECT_ROOT / "datadir/dbgap/dbgap-data/",
]
_CONFIG_CANDIDATES = [
    Path("/data/arpah/dbgap-data/study_config.json"),
    PROJECT_ROOT / "datadir/dbgap/dbgap-data/study_config.json",
]


def _bundle_entry(fhir_object, resource_type, full_url=None):
    entry = {
        "resource": fhir_object,
        "request": {"method": "POST", "url": resource_type},
    }
    if full_url:
        entry["fullUrl"] = full_url
    if_none_exist = build_if_none_exist(fhir_object)
    if if_none_exist:
        entry["request"]["ifNoneExist"] = if_none_exist
    return entry


def _post_bundle(fhir_url, access_token, entries):
    bundle = {"resourceType": "Bundle", "type": "transaction", "entry": entries}
    headers = {"Content-Type": "application/fhir+json"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    resp = requests.post(fhir_url, json=bundle, headers=headers)
    return resp.json()


def _count_bundle_response(resp):
    if resp.get("resourceType") != "Bundle":
        logger.warning(f"Unexpected bundle response: {resp}")
        return 0, 0, 1
    patients_ok = genomics_ok = errors = 0
    for i, entry in enumerate(resp.get("entry", [])):
        status = entry.get("response", {}).get("status", "")
        ok = status.startswith("200") or status.startswith("201")
        if i % 2 == 0:  # Patient entries (even indices)
            if ok:
                patients_ok += 1
            else:
                logger.warning(f"  Patient entry failed: {entry.get('response')}")
                errors += 1
        else:  # GenomicStudy entries (odd indices)
            if ok:
                genomics_ok += 1
            else:
                logger.warning(f"  GenomicStudy entry failed: {entry.get('response')}")
                errors += 1
    return patients_ok, genomics_ok, errors


def _find_path(candidates):
    for p in candidates:
        if p.exists():
            return p
    sys.exit(f"Could not locate any of: {candidates}")


def _load_phenotype(pheno_path):
    return pd.read_csv(pheno_path, sep="\t", comment="#", dtype=str)


def _process_study(study_id, cfg, vcf_base, args, access_token, fhir_url):
    cfg["_study_id"] = study_id
    pheno_path = vcf_base / "metadata" / cfg["phenotype_file"]
    df = _load_phenotype(pheno_path)

    subject_id_col = cfg["phenotype_subject_id_column"]
    if subject_id_col not in df.columns:
        logger.error(f"{study_id}: subject ID column '{subject_id_col}' not found; skipping")
        return

    logger.info(f"{study_id} ({cfg['study_name']}): {len(df)} subjects")

    if not args.live_run:
        sample_row = next(df.itertuples(index=False))
        logger.info(f"  [dryrun] sample Patient: {dbgap_patient(sample_row, cfg).as_json()}")
        logger.info(f"  [dryrun] Would post {len(df)} Patient + {len(df)} GenomicStudy records")
        return

    patients_posted = genomic_studies_posted = errors = 0
    batch = []

    for row in df.itertuples(index=False):
        patient_uuid = f"urn:uuid:{_uuid.uuid4()}"
        patient_obj = dbgap_patient(row, cfg)
        genomic_obj = dbgap_genomicStudy(row, cfg, patient_uuid, vcf_base=vcf_base)

        batch.append(_bundle_entry(patient_obj.as_json(), "Patient", full_url=patient_uuid))
        batch.append(_bundle_entry(genomic_obj.as_json(), "GenomicStudy"))

        if len(batch) >= args.batch_size * 2:
            resp = _post_bundle(fhir_url, access_token, batch)
            p, g, e = _count_bundle_response(resp)
            patients_posted += p
            genomic_studies_posted += g
            errors += e
            batch = []

    if batch:
        resp = _post_bundle(fhir_url, access_token, batch)
        p, g, e = _count_bundle_response(resp)
        patients_posted += p
        genomic_studies_posted += g
        errors += e

    logger.info(
        f"  Posted {patients_posted} Patient + {genomic_studies_posted} GenomicStudy records"
        + (f" ({errors} errors)" if errors else "")
    )


if __name__ == "__main__":
    parser = ArgumentParser(description="Populate FHIR server with dbGaP Patient + GenomicStudy records")
    parser.add_argument("--live-run", "-l", action="store_true",
                        help="Actually POST to the FHIR server (default: dry-run)")
    parser.add_argument("--study", metavar="STUDY_ID",
                        help="Process only this study (e.g. phs001044)")
    parser.add_argument("--server", metavar="URL", default=None,
                        help="FHIR base URL (e.g. http://localhost:8080/fhir/). "
                             "Overrides the default remote server; skips OAuth.")
    parser.add_argument("--batch-size", metavar="N", type=int, default=200,
                        help="Subjects per transaction bundle (default: 200)")
    args = parser.parse_args()

    vcf_base = _find_path(_VCF_BASE_CANDIDATES)
    config_path = _find_path(_CONFIG_CANDIDATES)

    with open(config_path) as f:
        all_configs = json.load(f)

    if args.study:
        if args.study not in all_configs:
            sys.exit(f"Study '{args.study}' not found in config. Known: {list(all_configs)}")
        studies = {args.study: all_configs[args.study]}
    else:
        studies = all_configs

    _REMOTE_FHIR_URL = "https://feast.mgpc.biochemistry.gwu.edu/fhir/"
    if args.server:
        fhir_url = args.server if args.server.endswith("/") else args.server + "/"
        access_token = None
    else:
        fhir_url = _REMOTE_FHIR_URL
        access_token = None
        if args.live_run:
            access_info = get_access_token()
            access_token = access_info.get("access_token")
            if not access_token:
                sys.exit(f"Failed to get access token: {access_info}")

    start = time.time()
    for study_id, cfg in studies.items():
        _process_study(study_id, cfg, vcf_base, args, access_token, fhir_url)

    logger.info(f"Done in {time.time() - start:.1f}s")
