from pathlib import Path

import duckdb

_TOP_N_SQL = """
SELECT chrom, pos, rsid, ref, alt, variant_type,
       alt_count, total_alleles, alt_freq
FROM cohort_frequencies
WHERE study_id = ? AND cohort_dim = ? AND cohort_label = ?
{variant_filter}
ORDER BY alt_freq DESC
LIMIT ?
"""

_DIMENSIONS_SQL = """
SELECT DISTINCT cohort_dim, cohort_label
FROM cohort_frequencies
WHERE study_id = ?
ORDER BY cohort_dim, cohort_label
"""

_STUDIES_SQL = """
SELECT DISTINCT study_id, cancer_type
FROM cohort_frequencies
ORDER BY cancer_type, study_id
"""

_SAMPLE_COUNT_SQL = """
SELECT sample_count
FROM cohort_sample_counts
WHERE study_id = ? AND cohort_dim = ? AND cohort_label = ?
"""


class CohortDB:
    def __init__(self, db_path):
        self.con = duckdb.connect(str(db_path), read_only=True)

    def close(self):
        self.con.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def studies(self):
        """Returns list of (study_id, cancer_type) tuples."""
        return self.con.execute(_STUDIES_SQL).fetchall()

    def dimensions(self, study_id):
        """Returns list of (cohort_dim, cohort_label) tuples for a study."""
        return self.con.execute(_DIMENSIONS_SQL, [study_id]).fetchall()

    def top_variants(self, study_id, cohort_dim, cohort_label, limit=20, variant_type=None):
        """Returns top-N variants by alt_freq as a list of dicts."""
        if variant_type and variant_type != "all":
            sql = _TOP_N_SQL.format(variant_filter="AND variant_type = ?")
            params = [study_id, cohort_dim, cohort_label, variant_type, limit]
        else:
            sql = _TOP_N_SQL.format(variant_filter="")
            params = [study_id, cohort_dim, cohort_label, limit]

        rows = self.con.execute(sql, params).fetchall()
        return [
            {
                "chrom": r[0], "pos": r[1], "rsid": r[2],
                "ref": r[3], "alt": r[4], "variant_type": r[5],
                "alt_count": r[6], "total_alleles": r[7], "alt_freq": r[8],
            }
            for r in rows
        ]

    def sample_count(self, study_id, cohort_dim, cohort_label):
        row = self.con.execute(_SAMPLE_COUNT_SQL, [study_id, cohort_dim, cohort_label]).fetchone()
        return row[0] if row else None
