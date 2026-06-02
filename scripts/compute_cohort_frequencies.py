import json
import logging
import sys
import time
from argparse import ArgumentParser
from collections import defaultdict
from pathlib import Path

import duckdb
import pandas as pd

from script_utils.db_setup import PROJECT_ROOT

logger = logging.getLogger("cohort_freq")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))

_VCF_BASE_CANDIDATES = [
    Path("/data/arpah/dbgap-data/"),
    PROJECT_ROOT / "datadir/dbgap/dbgap-data/",
]
_DB_CANDIDATES = [
    Path("/data/arpah/processed/dbgap/cohort_frequencies.duckdb"),
    PROJECT_ROOT / "datadir/processed/dbgap/cohort_frequencies.duckdb",
]
_CONFIG_CANDIDATES = [
    Path("/data/arpah/dbgap-data/study_config.json"),
    PROJECT_ROOT / "datadir/dbgap/dbgap-data/study_config.json",
]

_CREATE_FREQUENCIES = """
CREATE TABLE IF NOT EXISTS cohort_frequencies (
    study_id      VARCHAR,
    cancer_type   VARCHAR,
    chrom         VARCHAR,
    pos           INTEGER,
    rsid          VARCHAR,
    ref           VARCHAR,
    alt           VARCHAR,
    variant_type  VARCHAR,
    cohort_dim    VARCHAR,
    cohort_label  VARCHAR,
    alt_count     INTEGER,
    total_alleles INTEGER,
    alt_freq      REAL
)
"""
_CREATE_SAMPLE_COUNTS = """
CREATE TABLE IF NOT EXISTS cohort_sample_counts (
    study_id     VARCHAR,
    cancer_type  VARCHAR,
    cohort_dim   VARCHAR,
    cohort_label VARCHAR,
    sample_count INTEGER
)
"""

# ── Derived column functions ───────────────────────────────────────────────────

def _gleason_group(row):
    try:
        g1, g2 = int(row["bx_gleason1"]), int(row["bx_gleason2"])
    except (ValueError, KeyError, TypeError):
        return None
    if g1 == 3 and g2 == 3: return "GG1"
    if g1 == 3 and g2 == 4: return "GG2"
    if g1 == 4 and g2 == 3: return "GG3"
    if g1 + g2 == 8:        return "GG4"
    if g1 + g2 >= 9:        return "GG5"
    return None

DERIVED_FNS = {
    "gleason_group": _gleason_group,
}

_MISSING = {"", "Not Provided", "N/A", "-9", "-1"}

# ── Phenotype parsing ──────────────────────────────────────────────────────────

def parse_phenotype_file(path):
    rows = []
    headers = None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("##") or line.startswith("#"):
                continue
            fields = line.split("\t")
            if headers is None:
                headers = fields
                continue
            rows.append(dict(zip(headers, fields)))
    return rows


def parse_sample_manifest(path, sample_id_col, subject_id_col):
    """Returns {vcf_sample_id: subject_id} from a dbGaP Sample.MULTI file."""
    mapping = {}
    headers = None
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("##") or line.startswith("#"):
                continue
            fields = line.split("\t")
            if headers is None:
                headers = fields
                continue
            row = dict(zip(headers, fields))
            sample_id = row.get(sample_id_col, "")
            subject_id = row.get(subject_id_col, "")
            if sample_id and subject_id:
                mapping[sample_id] = subject_id
    return mapping


def build_sample_cohort_map(phenotype_rows, study_cfg, vcf_base=None):
    """Returns {vcf_sample_id: {cohort_dim_label: cohort_value}}."""
    subject_col = study_cfg["phenotype_subject_id_column"]
    transform = study_cfg.get("vcf_sample_id_transform", {"type": "direct"})
    dimensions = study_cfg["cohort_dimensions"]

    # Build subject_id -> cohorts from phenotype rows first
    subject_cohorts = {}
    for row in phenotype_rows:
        subject_id = row.get(subject_col, "")
        if not subject_id:
            continue
        cohorts = {}
        for dim in dimensions:
            dim_label = dim["label"]
            if "derived_fn" in dim:
                val = DERIVED_FNS[dim["derived_fn"]](row)
            else:
                val = row.get(dim["column"], "")
            if val is not None and str(val) not in _MISSING:
                if "value_map" in dim:
                    val = dim["value_map"].get(str(val))
                if val is not None:
                    cohorts[dim_label] = str(val)
        if cohorts:
            subject_cohorts[subject_id] = cohorts

    if transform["type"] == "sample_manifest":
        manifest_path = vcf_base / "metadata" / transform["file"]
        sample_to_subject = parse_sample_manifest(
            manifest_path, transform["sample_id_column"], transform["subject_id_column"]
        )
        return {
            sample_id: subject_cohorts[subject_id]
            for sample_id, subject_id in sample_to_subject.items()
            if subject_id in subject_cohorts
        }

    # direct or strip_prefix: vcf_id derived from subject_id
    if transform["type"] == "strip_prefix":
        prefix = transform["prefix"]
        return {
            subject_id.removeprefix(prefix): cohorts
            for subject_id, cohorts in subject_cohorts.items()
        }
    return subject_cohorts

# ── VCF processing ─────────────────────────────────────────────────────────────

def _variant_type(ref, alt):
    return "snp" if len(ref) == 1 and len(alt) == 1 else "indel"


def _parse_gt(gt_field):
    gt = gt_field.split(":")[0].replace("|", "/")
    alleles = gt.split("/")
    if "." in alleles:
        return 0, 0
    return sum(1 for a in alleles if a != "0"), len(alleles)


def process_vcf(vcf_path, sample_cohort_map, study_id, cancer_type):
    counts = defaultdict(lambda: [0, 0])
    sample_cols = None
    unmatched = set()
    n_variants = 0

    with open(vcf_path) as f:
        for line in f:
            if line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                sample_cols = line.rstrip("\n").split("\t")[9:]
                continue
            if sample_cols is None:
                continue

            fields = line.rstrip("\n").split("\t")
            if len(fields) < 9:
                continue

            chrom, pos_s, rsid, ref, alt = fields[0], fields[1], fields[2], fields[3], fields[4]
            pos = int(pos_s)
            if rsid == ".":
                rsid = f"{chrom}:{pos}"
            vtype = _variant_type(ref, alt)
            n_variants += 1

            for i, sample_id in enumerate(sample_cols):
                cohorts = sample_cohort_map.get(sample_id)
                if cohorts is None:
                    unmatched.add(sample_id)
                    continue
                if 9 + i >= len(fields):
                    continue
                alt_c, total = _parse_gt(fields[9 + i])
                if total == 0:
                    continue
                for dim, label in cohorts.items():
                    counts[(chrom, pos, rsid, ref, alt, vtype, dim, label)][0] += alt_c
                    counts[(chrom, pos, rsid, ref, alt, vtype, dim, label)][1] += total

    if unmatched:
        logger.warning(f"  {len(unmatched)} VCF sample IDs had no phenotype match")
    logger.info(f"  {n_variants} variants processed, {len(counts)} (variant, cohort) combinations")

    rows = []
    for (chrom, pos, rsid, ref, alt, vtype, dim, label), (alt_c, total) in counts.items():
        freq = alt_c / total if total > 0 else 0.0
        rows.append((study_id, cancer_type, chrom, pos, rsid, ref, alt, vtype,
                     dim, label, alt_c, total, freq))
    return rows

# ── Main ───────────────────────────────────────────────────────────────────────

def _find(candidates):
    for p in candidates:
        if Path(p).exists():
            return Path(p)
    return None


def main():
    parser = ArgumentParser(description="Pre-compute cohort allele frequencies from dbGaP VCFs")
    parser.add_argument("--study", "-s", help="Process only this study ID")
    parser.add_argument("--rebuild", "-r", action="store_true",
                        help="Drop and recreate tables before processing")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Parse and count without writing to DuckDB")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Remove stale DuckDB lock files before connecting")
    args = parser.parse_args()

    config_path = _find(_CONFIG_CANDIDATES)
    if config_path is None:
        sys.exit(f"study_config.json not found. Tried: {_CONFIG_CANDIDATES}")

    vcf_base = _find(_VCF_BASE_CANDIDATES)
    if vcf_base is None:
        sys.exit(f"VCF base directory not found. Tried: {_VCF_BASE_CANDIDATES}")

    with open(config_path) as f:
        studies = json.load(f)

    if args.study:
        if args.study not in studies:
            sys.exit(f"Study {args.study!r} not in config. Available: {list(studies)}")
        studies = {args.study: studies[args.study]}

    if args.dry_run:
        _run_studies(studies, vcf_base, conn=None)
        return

    db_path = _find(_DB_CANDIDATES) or _DB_CANDIDATES[-1]
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if args.force:
        wal = Path(str(db_path) + ".wal")
        if wal.exists():
            wal.unlink()
            logger.info(f"Removed stale WAL file: {wal.name}")
    with duckdb.connect(str(db_path)) as conn:
        if args.rebuild:
            conn.execute("DROP TABLE IF EXISTS cohort_frequencies")
            conn.execute("DROP TABLE IF EXISTS cohort_sample_counts")
        conn.execute(_CREATE_FREQUENCIES)
        conn.execute(_CREATE_SAMPLE_COUNTS)
        _run_studies(studies, vcf_base, conn)


def _run_studies(studies, vcf_base, conn):
    for study_id, cfg in studies.items():
        blocked = cfg.get("status", "")
        if blocked.startswith("blocked"):
            logger.warning(f"Skipping {study_id}: {blocked}")
            continue

        logger.info(f"=== {study_id} ({cfg['cancer_type']}) ===")
        t0 = time.time()

        pheno_path = vcf_base / "metadata" / cfg["phenotype_file"]
        phenotype_rows = parse_phenotype_file(pheno_path)
        sample_cohort_map = build_sample_cohort_map(phenotype_rows, cfg, vcf_base)
        logger.info(f"  {len(sample_cohort_map)} samples with phenotype data")

        sample_counts = defaultdict(lambda: defaultdict(int))
        for cohorts in sample_cohort_map.values():
            for dim, label in cohorts.items():
                sample_counts[dim][label] += 1
        for dim, labels in sample_counts.items():
            for label, n in sorted(labels.items()):
                logger.info(f"  {dim}={label!r}: {n} samples")

        all_rows = []
        if "vcf_paths" in cfg:
            for rel_path in cfg["vcf_paths"]:
                vcf_path = vcf_base / rel_path
                logger.info(f"  Reading {vcf_path.name}...")
                all_rows.extend(process_vcf(vcf_path, sample_cohort_map, study_id, cfg["cancer_type"]))
        elif "vcf_dir" in cfg:
            for vcf_path in sorted((vcf_base / cfg["vcf_dir"]).glob("*.vcf")):
                logger.info(f"  Reading {vcf_path.name}...")
                all_rows.extend(process_vcf(vcf_path, sample_cohort_map, study_id, cfg["cancer_type"]))

        logger.info(f"  Total rows: {len(all_rows)}  ({time.time()-t0:.1f}s)")

        if conn is not None and all_rows:
            freq_df = pd.DataFrame(all_rows, columns=[
                "study_id", "cancer_type", "chrom", "pos", "rsid",
                "ref", "alt", "variant_type", "cohort_dim", "cohort_label",
                "alt_count", "total_alleles", "alt_freq",
            ])
            count_rows = [
                (study_id, cfg["cancer_type"], dim, label, n)
                for dim, labels in sample_counts.items()
                for label, n in labels.items()
            ]
            counts_df = pd.DataFrame(count_rows, columns=[
                "study_id", "cancer_type", "cohort_dim", "cohort_label", "sample_count",
            ])
            conn.execute("DELETE FROM cohort_frequencies WHERE study_id = ?", [study_id])
            conn.execute("INSERT INTO cohort_frequencies SELECT * FROM freq_df")
            conn.execute("DELETE FROM cohort_sample_counts WHERE study_id = ?", [study_id])
            conn.execute("INSERT INTO cohort_sample_counts SELECT * FROM counts_df")
            conn.commit()
            logger.info(f"  Written to DuckDB.")


if __name__ == "__main__":
    main()
