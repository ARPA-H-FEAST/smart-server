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

_PATIENT_LIST_SQL = """
SELECT p.subject_id, d.sex, d.race, d.age, p.cancer_type, p.study_id,
       p.snp_count, p.indel_count
FROM patient_snp_counts p
LEFT JOIN patient_demographics d USING (study_id, subject_id)
{where_clause}
ORDER BY p.study_id, p.subject_id
LIMIT ? OFFSET ?
"""

_PATIENT_COUNT_SQL = """
SELECT COUNT(*) FROM patient_snp_counts
{where_clause}
"""

_CARRIER_COUNT_SQL = """
SELECT rsid, chrom, pos, ref, alt, variant_type, SUM(carrier_count) AS carrier_count
FROM variant_carrier_counts
{where_clause}
GROUP BY rsid, chrom, pos, ref, alt, variant_type
ORDER BY carrier_count DESC
"""

_MUTATION_BY_RSID_SQL = """
SELECT rsid, chrom, pos, ref, alt, variant_type, SUM(carrier_count) AS carrier_count
FROM variant_carrier_counts
WHERE rsid = ?
GROUP BY rsid, chrom, pos, ref, alt, variant_type
"""

_MUTATION_BY_COORDS_SQL = """
SELECT rsid, chrom, pos, ref, alt, variant_type, SUM(carrier_count) AS carrier_count
FROM variant_carrier_counts
WHERE chrom = ? AND pos = ? AND ref = ? AND alt = ?
GROUP BY rsid, chrom, pos, ref, alt, variant_type
"""

_MUTATION_COHORT_FREQS_BY_RSID_SQL = """
SELECT study_id, cancer_type, cohort_dim, cohort_label,
       alt_count, total_alleles, alt_freq
FROM cohort_frequencies
WHERE rsid = ?
ORDER BY study_id, cohort_dim, cohort_label
"""

_MUTATION_COHORT_FREQS_BY_COORDS_SQL = """
SELECT study_id, cancer_type, cohort_dim, cohort_label,
       alt_count, total_alleles, alt_freq
FROM cohort_frequencies
WHERE chrom = ? AND pos = ? AND ref = ? AND alt = ?
ORDER BY study_id, cohort_dim, cohort_label
"""

_MUTATION_SEARCH_SQL = """
SELECT rsid, chrom, pos, ref, alt, variant_type, SUM(carrier_count) AS carrier_count
FROM variant_carrier_counts
{where_clause}
GROUP BY rsid, chrom, pos, ref, alt, variant_type
ORDER BY carrier_count DESC
LIMIT ? OFFSET ?
"""

_MUTATION_SEARCH_COUNT_SQL = """
SELECT COUNT(*) FROM (
    SELECT DISTINCT rsid, chrom, pos, ref, alt
    FROM variant_carrier_counts
    {where_clause}
)
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

    def _patient_where(self, study_id, cancer_type):
        conditions, params = [], []
        if study_id:
            conditions.append("study_id = ?")
            params.append(study_id)
        if cancer_type:
            conditions.append("cancer_type = ?")
            params.append(cancer_type)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return where, params

    def patient_list(self, study_id=None, cancer_type=None, limit=100, offset=0):
        where, params = self._patient_where(study_id, cancer_type)
        sql = _PATIENT_LIST_SQL.format(where_clause=where)
        rows = self.con.execute(sql, params + [limit, offset]).fetchall()
        return [
            {
                "subject_id": r[0], "sex": r[1], "race": r[2], "age": r[3],
                "cancer_type": r[4], "study_id": r[5],
                "snp_count": r[6], "indel_count": r[7],
            }
            for r in rows
        ]

    def patient_count(self, study_id=None, cancer_type=None):
        where, params = self._patient_where(study_id, cancer_type)
        sql = _PATIENT_COUNT_SQL.format(where_clause=where)
        row = self.con.execute(sql, params).fetchone()
        return row[0] if row else 0

    def mutation_by_rsid(self, rsid):
        row = self.con.execute(_MUTATION_BY_RSID_SQL, [rsid]).fetchone()
        if not row:
            return None
        return {"rsid": row[0], "chrom": row[1], "pos": row[2], "ref": row[3],
                "alt": row[4], "variant_type": row[5], "carrier_count": row[6]}

    def mutation_by_coords(self, chrom, pos, ref, alt):
        row = self.con.execute(_MUTATION_BY_COORDS_SQL, [chrom, pos, ref, alt]).fetchone()
        if not row:
            return None
        return {"rsid": row[0], "chrom": row[1], "pos": row[2], "ref": row[3],
                "alt": row[4], "variant_type": row[5], "carrier_count": row[6]}

    def mutation_cohort_freqs_by_rsid(self, rsid):
        rows = self.con.execute(_MUTATION_COHORT_FREQS_BY_RSID_SQL, [rsid]).fetchall()
        return [{"study_id": r[0], "cancer_type": r[1], "cohort_dim": r[2],
                 "cohort_label": r[3], "alt_count": r[4],
                 "total_alleles": r[5], "alt_freq": r[6]} for r in rows]

    def mutation_cohort_freqs_by_coords(self, chrom, pos, ref, alt):
        rows = self.con.execute(_MUTATION_COHORT_FREQS_BY_COORDS_SQL,
                                [chrom, pos, ref, alt]).fetchall()
        return [{"study_id": r[0], "cancer_type": r[1], "cohort_dim": r[2],
                 "cohort_label": r[3], "alt_count": r[4],
                 "total_alleles": r[5], "alt_freq": r[6]} for r in rows]

    def _mutation_search_where(self, rsids, cancer_type, study_id, variant_type):
        conditions, params = [], []
        if rsids:
            placeholders = ", ".join("?" * len(rsids))
            conditions.append(f"rsid IN ({placeholders})")
            params.extend(rsids)
        if cancer_type:
            conditions.append("cancer_type = ?")
            params.append(cancer_type)
        if study_id:
            conditions.append("study_id = ?")
            params.append(study_id)
        if variant_type and variant_type != "all":
            conditions.append("variant_type = ?")
            params.append(variant_type)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        return where, params

    def mutation_search(self, rsids=None, cancer_type=None, study_id=None,
                        variant_type=None, limit=20, offset=0):
        where, params = self._mutation_search_where(rsids, cancer_type, study_id, variant_type)
        sql = _MUTATION_SEARCH_SQL.format(where_clause=where)
        rows = self.con.execute(sql, params + [limit, offset]).fetchall()
        return [{"rsid": r[0], "chrom": r[1], "pos": r[2], "ref": r[3],
                 "alt": r[4], "variant_type": r[5], "carrier_count": r[6]}
                for r in rows]

    def mutation_search_count(self, rsids=None, cancer_type=None,
                              study_id=None, variant_type=None):
        where, params = self._mutation_search_where(rsids, cancer_type, study_id, variant_type)
        sql = _MUTATION_SEARCH_COUNT_SQL.format(where_clause=where)
        row = self.con.execute(sql, params).fetchone()
        return row[0] if row else 0

    def carrier_counts(self, rsids, study_id=None, cancer_type=None):
        """Return per-rsID carrier counts across studies, optionally filtered."""
        if not rsids:
            return []
        placeholders = ", ".join("?" * len(rsids))
        conditions = [f"rsid IN ({placeholders})"]
        params = list(rsids)
        if study_id:
            conditions.append("study_id = ?")
            params.append(study_id)
        if cancer_type:
            conditions.append("cancer_type = ?")
            params.append(cancer_type)
        where = "WHERE " + " AND ".join(conditions)
        sql = _CARRIER_COUNT_SQL.format(where_clause=where)
        rows = self.con.execute(sql, params).fetchall()
        return [
            {
                "rsid": r[0], "chrom": r[1], "pos": r[2],
                "ref": r[3], "alt": r[4], "variant_type": r[5],
                "carrier_count": r[6],
            }
            for r in rows
        ]
