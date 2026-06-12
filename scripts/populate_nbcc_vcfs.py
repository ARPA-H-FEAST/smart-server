import csv
import logging
import sqlite3
import sys
import time

from argparse import ArgumentParser
from collections import namedtuple
from pathlib import Path

from script_utils.db_setup import PROJECT_ROOT
from script_utils.fhir_client import get_access_token, post_fhir_data, query_single_patient, FHIR_URL

BCO_ID = "FEAST_000012"

_SCRIPT_DIR = Path(__file__).parent

# Primary: production path. Fallbacks: dev paths.
_DB_CANDIDATES = [
    Path("/data/arpah/processed/nbcc/nbcc_db/nbcc.db"),
    PROJECT_ROOT / "datadir/processed/nbcc/nbcc_db/nbcc.db",
    PROJECT_ROOT / "../data/nbcc/nbcc_db/nbcc.db",
]

_POSITIONS_PATH = _SCRIPT_DIR / "rsid_positions_hg19.tsv"
_VCF_DIR = _SCRIPT_DIR / "vcfs"

logger = logging.getLogger("dbi_logging")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

GenomicStudyRecord = namedtuple("GenomicStudyRecord", ["dnl_user", "nbcc_userinfo_id", "filetype"])

_QUERY = """
    SELECT DISTINCT
        fu.sample_id   AS dnl_user,
        ui.id          AS nbcc_userinfo_id,
        fu.filetype
    FROM file_uploads fu
    JOIN user_info ui ON ui.user_profile_id = fu.user_profile_id
    WHERE fu.sample_id IN (SELECT DISTINCT dnl_user FROM user_snps)
    ORDER BY ui.id
"""


def _find_db():
    for p in _DB_CANDIDATES:
        if p.exists():
            return p
    return None


def _load_converters():
    sys.path.append(str(PROJECT_ROOT))
    from data_api.db_interfaces.fhir_converters import FHIR_CONVERTER
    nbcc = FHIR_CONVERTER["nbcc"]
    return nbcc["GenomicStudy"], nbcc["DocumentReference"]


def _query_db(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute(_QUERY).fetchall()
    conn.close()
    return [GenomicStudyRecord(*r) for r in rows]


def _load_positions():
    if not _POSITIONS_PATH.exists():
        raise FileNotFoundError(
            f"Position table not found: {_POSITIONS_PATH}\n"
            "Run fetch_rsid_positions.py first."
        )
    positions = {}
    with open(_POSITIONS_PATH) as f:
        for row in csv.DictReader(f, delimiter="\t"):
            positions[row["rsid"]] = (row["chrom"], row["pos"], row["ref"], row["alt"].split(","))
    return positions


def _gt(a1, a2, ref, alts):
    idx = {ref.upper(): "0"}
    for i, a in enumerate(alts):
        idx[a.upper()] = str(i + 1)
    return f"{idx.get(a1.upper(), '.')}/{idx.get(a2.upper(), '.')}"


def _write_vcf(path, dnl_user, snps, positions):
    lines = [
        "##fileformat=VCFv4.1",
        "##reference=GRCh37",
        "##source=NBCC_FEAST",
        f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{dnl_user}",
    ]
    for rsid, a1, a2 in snps:
        pos_info = positions.get(rsid)
        if pos_info is None:
            continue
        chrom, pos, ref, alts = pos_info
        lines.append(
            f"{chrom}\t{pos}\t{rsid}\t{ref}\t{','.join(alts)}\t.\tPASS\t.\tGT\t{_gt(a1, a2, ref, alts)}"
        )
    path.write_text("\n".join(lines) + "\n")


def _generate_vcfs(db_path, positions, truncated=False):
    _VCF_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT dnl_user, snp, a1, a2 FROM user_snps ORDER BY dnl_user, snp"
    )

    current_user = None
    current_snps = []
    count = 0

    for dnl_user, rsid, a1, a2 in cursor:
        if dnl_user != current_user:
            if current_user is not None:
                _write_vcf(_VCF_DIR / f"{current_user}.vcf", current_user, current_snps, positions)
                count += 1
                if truncated and count >= 10:
                    break
            current_user = dnl_user
            current_snps = []
        current_snps.append((rsid, a1, a2))

    if current_user is not None and (not truncated or count < 10):
        _write_vcf(_VCF_DIR / f"{current_user}.vcf", current_user, current_snps, positions)
        count += 1

    conn.close()
    return count


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--live-run", "-l", action="store_true",
                        help="POST objects to the FHIR server (default: dryrun)")
    parser.add_argument("--db-only", "-d", action="store_true",
                        help="Query DB and build objects only; skip auth and all network calls")
    parser.add_argument("--generate-vcfs", "-g", action="store_true",
                        help="Generate per-patient VCF files into scripts/vcfs/ (requires rsid_positions_hg19.tsv)")
    parser.add_argument("--truncated-run", "-t", action="store_true",
                        help="Stop after the first batch (for testing)")
    args = parser.parse_args()

    big_start = time.time()

    # ── DB phase (no network) ──────────────────────────────────────────────────
    db_path = _find_db()
    if db_path is None:
        sys.exit(f"NBCC database not found. Tried: {[str(p) for p in _DB_CANDIDATES]}")
    logger.info(f"Using DB at {db_path}")

    records = _query_db(db_path)
    logger.info(f"{BCO_ID} - genomic study candidates: {len(records)}")

    gs_converter, dr_converter = _load_converters()

    if args.db_only:
        for rec in records[:3]:
            obj = gs_converter(rec, "Patient/unknown")
            logger.info(f"[db-only] sample object: {obj.as_json()}")
        logger.info(f"[db-only] DB OK — {len(records)} records, object construction OK")
        sys.exit(0)

    if args.generate_vcfs:
        positions = _load_positions()
        logger.info(f"Loaded {len(positions)} rsID positions from {_POSITIONS_PATH}")
        count = _generate_vcfs(db_path, positions, truncated=args.truncated_run)
        logger.info(f"[generate-vcfs] Wrote {count} VCF files to {_VCF_DIR}")
        sys.exit(0)

    # ── Network phase ──────────────────────────────────────────────────────────
    access_info = get_access_token()
    access_token = access_info.get("access_token")
    if not access_token:
        sys.exit("Access token error! Aborting")

    chunk_size = 10
    total_posted = 0
    total_missing = 0

    for chunk_start in range(0, len(records), chunk_size):
        chunk = records[chunk_start : chunk_start + chunk_size]

        resource_url_strings = {}
        for rec in chunk:
            response = query_single_patient(access_token, rec.nbcc_userinfo_id)
            if response.get("resourceType") != "Bundle":
                logger.warning(f"Unexpected response for {rec.nbcc_userinfo_id}: {response.get('resourceType')}")
                continue
            entry = response.get("entry")
            if not entry:
                logger.debug(f"MISSING ID - {rec.nbcc_userinfo_id}: no Patient found")
                logger.debug(f"FAILED URL: {FHIR_URL}Patient?identifier={rec.nbcc_userinfo_id}")
                total_missing += 1
            else:
                resource_url_strings[rec.nbcc_userinfo_id] = [
                    "/".join(e["fullUrl"].split("/")[-2:]) for e in entry
                ]

        for rec in chunk:
            p_refs = resource_url_strings.get(rec.nbcc_userinfo_id)
            if p_refs is None:
                continue
            vcf_path = _VCF_DIR / f"{rec.dnl_user}.vcf"

            for p_ref in p_refs:
                if not args.live_run:
                    logger.info(
                        f"[dryrun] chunk {chunk_start}: would POST DocumentReference + GenomicStudy "
                        f"for {rec.dnl_user} (VCF exists: {vcf_path.exists()})"
                    )
                    continue

                dr_obj = dr_converter(vcf_path, p_ref, rec.dnl_user)
                dr_result = post_fhir_data(access_token, dr_obj.as_json(), "DocumentReference")
                dr_id = dr_result.get("id")
                if dr_id is None:
                    logger.error(f"DocumentReference POST failed for {rec.dnl_user}: {dr_result}")
                    continue

                gs_obj = gs_converter(rec, p_ref, doc_ref_id=dr_id)
                gs_result = post_fhir_data(access_token, gs_obj.as_json(), "GenomicStudy")
                if gs_result.get("resourceType") != "GenomicStudy":
                    logger.error(f"GenomicStudy POST failed for {rec.dnl_user}: {gs_result}")
                else:
                    total_posted += 1
                    logger.debug(f"POSTed GenomicStudy {gs_result.get('id')} for {rec.dnl_user}")

        if args.truncated_run:
            logger.info("--truncated-run: stopping after first batch")
            break

    elapsed = time.time() - big_start
    logger.info(f"Done. Posted: {total_posted}, missing patients: {total_missing}, time: {elapsed:.1f}s")
