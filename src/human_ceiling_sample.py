"""
Step 7 - Human ceiling sample.

Run from the project root:
    python src/human_ceiling_sample.py

Why this exists:
    Before any model is built, we measure how often a careful human agrees with
    CFPB's own official label on the same task. That number is the realistic
    ceiling. Without it, a model scoring 88% is uninterpretable: it might be
    well below human, or well above.

Design:
    Simple random sample of 100 narratives from the modelling window, seeded
    for reproducibility. Not stratified. The estimate is of agreement on the
    operational distribution, which is what a deployed system would face, so
    the sample must mirror that distribution rather than an engineered one.

Outputs:
    data/golden/human_ceiling_sample.csv   <- you label this, no answers in it
    data/golden/human_ceiling_key.csv      <- the answers, DO NOT OPEN
    docs/taxonomy_reference.md             <- the valid label options
"""

from pathlib import Path
import csv
import sys
import duckdb

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "data" / "raw" / "complaints.parquet"
GOLDEN = ROOT / "data" / "golden"
SAMPLE_CSV = GOLDEN / "human_ceiling_sample.csv"
KEY_CSV = GOLDEN / "human_ceiling_key.csv"
TAXONOMY_MD = ROOT / "docs" / "taxonomy_reference.md"

CUTOVER = "2023-08-25"
SEED = 42
N = 100

NARR = '"Consumer complaint narrative"'
HAS_NARR = f"{NARR} IS NOT NULL AND TRIM({NARR}) <> ''"


def main():
    if not PARQUET.exists():
        sys.exit(f"Cannot find {PARQUET}. Run profile_corpus.py first.")

    if SAMPLE_CSV.exists():
        print("A sample already exists. Delete these two files to draw a new one:")
        print(f"  {SAMPLE_CSV}")
        print(f"  {KEY_CSV}")
        sys.exit(1)

    GOLDEN.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW w AS
        SELECT
            "Complaint ID"       AS complaint_id,
            TRY_CAST("Date received" AS DATE) AS dt,
            "Product"            AS product,
            "Sub-product"        AS sub_product,
            "Issue"              AS issue,
            "Sub-issue"          AS sub_issue,
            {NARR}               AS narrative
        FROM read_parquet('{PARQUET.as_posix()}')
        WHERE {HAS_NARR}
          AND TRY_CAST("Date received" AS DATE) >= DATE '{CUTOVER}'
    """)

    # ---- taxonomy reference ---------------------------------------------
    products = con.execute("""
        SELECT product, COUNT(*) FROM w GROUP BY product ORDER BY COUNT(*) DESC
    """).fetchall()

    pairs = con.execute("""
        SELECT product, issue, COUNT(*) AS n
        FROM w GROUP BY product, issue ORDER BY product, n DESC
    """).fetchall()

    lines = ["# Taxonomy Reference", "",
             f"Valid labels inside the modelling window ({CUTOVER} onwards).",
             "Use only these values when labelling. Volumes are shown so you can "
             "see which categories are common, but do not let volume influence "
             "your judgement on an individual case.", ""]

    lines += ["## Products", ""]
    lines += ["| Product | Narratives |", "|---|---|"]
    for p, n in products:
        lines.append(f"| {p} | {n:,} |")
    lines.append("")

    lines += ["## Issues by product", ""]
    current = None
    for p, i, n in pairs:
        if p != current:
            current = p
            lines += ["", f"### {p}", "", "| Issue | Narratives |", "|---|---|"]
        lines.append(f"| {i} | {n:,} |")
    lines.append("")

    TAXONOMY_MD.parent.mkdir(parents=True, exist_ok=True)
    TAXONOMY_MD.write_text("\n".join(lines), encoding="utf-8")

    # ---- the sample ------------------------------------------------------
    rows = con.execute(f"""
        SELECT complaint_id, dt, product, issue, narrative
        FROM w
        USING SAMPLE reservoir({N} ROWS) REPEATABLE ({SEED})
    """).fetchall()

    if len(rows) < N:
        sys.exit(f"Only drew {len(rows)} rows, expected {N}.")

    with SAMPLE_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["case_no", "complaint_id", "date_received",
                     "narrative", "my_product", "my_issue", "notes"])
        for k, (cid, dt, prod, iss, narr) in enumerate(rows, 1):
            flat = " ".join(str(narr).split())
            wr.writerow([k, cid, dt, flat, "", "", ""])

    with KEY_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        wr = csv.writer(f)
        wr.writerow(["case_no", "complaint_id", "true_product", "true_issue"])
        for k, (cid, dt, prod, iss, narr) in enumerate(rows, 1):
            wr.writerow([k, cid, prod, iss])

    lengths = sorted(len(str(r[4])) for r in rows)
    print(f"Sample drawn: {N} narratives, seed {SEED}, window {CUTOVER} onwards.")
    print(f"Shortest narrative: {lengths[0]:,} characters")
    print(f"Median narrative:   {lengths[len(lengths)//2]:,} characters")
    print(f"Longest narrative:  {lengths[-1]:,} characters")
    print()
    print(f"Label this file:    {SAMPLE_CSV}")
    print(f"Answer key (do not open): {KEY_CSV}")
    print(f"Valid labels:       {TAXONOMY_MD}")
    print()
    print("Fill in my_product and my_issue for all 100 rows, then run:")
    print("    python src/human_ceiling_score.py")


if __name__ == "__main__":
    main()
