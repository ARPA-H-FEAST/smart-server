"""One-time script: fetch hg19/GRCh37 positions for NBCC rsIDs from Ensembl.

Writes scripts/rsid_positions_hg19.tsv which populate_nbcc_vcfs.py depends on.
"""
import sqlite3
import sys
import time
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).parent

OUTPUT_TSV = SCRIPT_DIR / "rsid_positions_hg19.tsv"

_ENSEMBL_URL = "https://grch37.rest.ensembl.org/variation/homo_sapiens"
_BATCH_SIZE = 200

_DB_CANDIDATES = [
    Path("/data/arpah/processed/nbcc/nbcc_db/nbcc.db"),
    SCRIPT_DIR.parent / "datadir/processed/nbcc/nbcc_db/nbcc.db",
    SCRIPT_DIR / "nbcc.db",
]


def _find_db():
    for p in _DB_CANDIDATES:
        if p.exists():
            return p
    return None


def _get_rsids(db_path):
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT DISTINCT snp FROM user_snps ORDER BY snp").fetchall()
    conn.close()
    return [r[0] for r in rows]


def _fetch_batch(rsids):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    resp = requests.post(
        _ENSEMBL_URL,
        json={"ids": rsids},
        headers=headers,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def _parse_position(data):
    """Return (chrom, pos, ref, alt) for a single rsID Ensembl response, or None."""
    for m in data.get("mappings", []):
        if m.get("assembly_name") != "GRCh37":
            continue
        location = m.get("location", "")
        allele_string = m.get("allele_string", "")
        if ":" not in location or "-" not in location:
            continue
        chrom, coords = location.split(":", 1)
        pos = coords.split("-")[0]
        alleles = allele_string.split("/")
        if len(alleles) < 2:
            continue
        ref = alleles[0]
        alt = ",".join(alleles[1:])
        return chrom, pos, ref, alt
    return None


if __name__ == "__main__":
    db_path = _find_db()
    if db_path is None:
        sys.exit("NBCC database not found")
    print(f"Using DB: {db_path}")

    rsids = _get_rsids(db_path)
    print(f"Fetching GRCh37 positions for {len(rsids)} rsIDs...")

    results = {}
    failed = []

    for i in range(0, len(rsids), _BATCH_SIZE):
        batch = rsids[i : i + _BATCH_SIZE]
        print(f"  batch {i}–{i + len(batch) - 1}...", end=" ", flush=True)
        try:
            data = _fetch_batch(batch)
            for rsid in batch:
                entry = data.get(rsid)
                if entry is None:
                    failed.append(rsid)
                    continue
                parsed = _parse_position(entry)
                if parsed is None:
                    failed.append(rsid)
                else:
                    results[rsid] = parsed
            print(f"ok ({len(data)} returned)")
        except Exception as e:
            print(f"ERROR: {e}")
            failed.extend(batch)
        time.sleep(0.5)

    with open(OUTPUT_TSV, "w") as fp:
        fp.write("rsid\tchrom\tpos\tref\talt\n")
        for rsid, (chrom, pos, ref, alt) in sorted(results.items()):
            fp.write(f"{rsid}\t{chrom}\t{pos}\t{ref}\t{alt}\n")

    print(f"\nWrote {len(results)} positions to {OUTPUT_TSV}")
    if failed:
        print(f"Failed ({len(failed)}): {failed[:10]}{'...' if len(failed) > 10 else ''}")
