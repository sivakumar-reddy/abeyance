#!/usr/bin/env python3
"""
Project A — Step 4: Label noise analysis
=========================================
Joins the 100-case hand-labelled golden set against CFPB's own product/issue
labels and quantifies how far consumer-selected intake labels diverge from
expert judgement.

This is the finding that justifies the intervention: any model trained on the
official labels inherits this noise floor, so the measured ceiling of a
classifier is bounded by it.

Usage
-----
    python 04_label_noise_analysis.py \
        --golden  human_ceiling_sample_labelled.csv \
        --parquet data/complaints.parquet \
        --outdir  docs/

Outputs
-------
    docs/04_label_noise.md            report
    docs/04_disagreements.csv         every disagreeing case, for inspection
    docs/04_issue_confusion.csv       confusion matrix, official x mine
"""

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd


# --------------------------------------------------------------------------
# Column resolution — the parquet keeps CFPB's original header names, but be
# tolerant in case the DuckDB conversion normalised them.
# --------------------------------------------------------------------------
CANDIDATES = {
    "complaint_id": ["Complaint ID", "complaint_id", "complaint id", "ComplaintID"],
    "product":      ["Product", "product"],
    "sub_product":  ["Sub-product", "sub_product", "Sub product"],
    "issue":        ["Issue", "issue"],
    "sub_issue":    ["Sub-issue", "sub_issue", "Sub issue"],
    "narrative":    ["Consumer complaint narrative", "consumer_complaint_narrative", "narrative"],
    "date":         ["Date received", "date_received", "Date Received"],
}


def resolve_columns(con, parquet):
    cols = [r[0] for r in con.execute(
        f"SELECT column_name FROM (DESCRIBE SELECT * FROM read_parquet('{parquet}') LIMIT 0)"
    ).fetchall()]
    lower = {c.lower(): c for c in cols}
    resolved = {}
    for key, options in CANDIDATES.items():
        hit = next((lower[o.lower()] for o in options if o.lower() in lower), None)
        if hit is None and key in ("complaint_id", "product", "issue"):
            sys.exit(f"FATAL: could not find a column for '{key}'. Parquet columns:\n  " + "\n  ".join(cols))
        resolved[key] = hit
    return resolved


# --------------------------------------------------------------------------
# Taxonomy normalisation
# --------------------------------------------------------------------------
# The window is locked at 2023-08-25, after the final rename, so in principle
# no legacy names should appear. Applied defensively — if any of these fire,
# the window assumption is wrong and the run should be treated as suspect.
PRODUCT_RENAMES = {
    "Credit reporting, credit repair services, or other personal consumer reports":
        "Credit reporting or other personal consumer reports",
    "Credit reporting":
        "Credit reporting or other personal consumer reports",
    "Money transfers":
        "Money transfer, virtual currency, or money service",
    "Virtual currency":
        "Money transfer, virtual currency, or money service",
    "Payday loan":
        "Payday loan, title loan, personal loan, or advance loan",
    "Payday loan, title loan, or personal loan":
        "Payday loan, title loan, personal loan, or advance loan",
    "Credit card or prepaid card":
        "Credit card",
    "Bank account or service":
        "Checking or savings account",
}


def normalise(series, mapping):
    s = series.astype("string").str.strip()
    fired = s.isin(mapping.keys()).sum()
    return s.replace(mapping), int(fired)


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True, help="labelled 100-case CSV")
    ap.add_argument("--parquet", required=True, help="CFPB complaints parquet")
    ap.add_argument("--outdir", default="docs")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # ---- load golden set ----
    gold = pd.read_csv(args.golden, encoding="utf-8-sig")
    required = {"case_no", "complaint_id", "my_product", "my_issue"}
    missing = required - set(gold.columns)
    if missing:
        sys.exit(f"FATAL: golden set is missing columns: {sorted(missing)}")

    n = len(gold)
    if gold["complaint_id"].duplicated().any():
        sys.exit("FATAL: duplicate complaint_id in golden set")
    print(f"golden set: {n} cases")

    # ---- pull the matching rows from parquet ----
    con = duckdb.connect()
    cols = resolve_columns(con, args.parquet)
    print("resolved columns:", {k: v for k, v in cols.items() if v})

    ids = ",".join(f"'{str(i).strip()}'" for i in gold["complaint_id"])
    select = ", ".join(
        f'"{cols[k]}" AS {k}' for k in
        ["complaint_id", "product", "sub_product", "issue", "sub_issue", "date"]
        if cols.get(k)
    )
    official = con.execute(
        f'SELECT {select} FROM read_parquet(?) '
        f'WHERE CAST("{cols["complaint_id"]}" AS VARCHAR) IN ({ids})',
        [args.parquet],
    ).df()
    print(f"matched in parquet: {len(official)} / {n}")

    # The parquet stores Complaint ID as text; the golden CSV reads it as int64.
    # Normalise both to stripped strings so the merge key is comparable.
    gold["complaint_id"] = gold["complaint_id"].astype(str).str.strip()
    official["complaint_id"] = official["complaint_id"].astype(str).str.strip()

    if len(official) < n:
        missing_ids = set(gold["complaint_id"]) - set(official["complaint_id"])
        print(f"WARNING: {len(missing_ids)} ids not found — check the window filter")
        print("  ", sorted(missing_ids)[:10])

    # ---- join ----
    df = gold.merge(official, on="complaint_id", how="left", validate="one_to_one")

    df["official_product"], p_fired = normalise(df["product"], PRODUCT_RENAMES)
    df["official_issue"] = df["issue"].astype("string").str.strip()
    df["my_product"] = df["my_product"].astype("string").str.strip()
    df["my_issue"] = df["my_issue"].astype("string").str.strip()

    if p_fired:
        print(f"WARNING: {p_fired} rows carried a legacy product name — "
              "the 2023-08-25 window assumption may be wrong")

    df["product_match"] = df["official_product"] == df["my_product"]
    df["issue_match"] = df["official_issue"] == df["my_issue"]
    df["both_match"] = df["product_match"] & df["issue_match"]

    matched = df["official_product"].notna().sum()
    p_agree = df["product_match"].mean()
    i_agree = df["issue_match"].mean()
    b_agree = df["both_match"].mean()

    # issue agreement conditional on the product being right — the more
    # honest number, since a wrong product makes the issue trivially wrong
    sub = df[df["product_match"]]
    i_agree_cond = sub["issue_match"].mean() if len(sub) else float("nan")

    print(f"\nproduct agreement      {p_agree:.1%}")
    print(f"issue agreement        {i_agree:.1%}")
    print(f"issue | product right  {i_agree_cond:.1%}  (n={len(sub)})")
    print(f"both                   {b_agree:.1%}")

    # ---- confusion matrix on issue ----
    confusion = pd.crosstab(df["official_issue"], df["my_issue"], dropna=False)
    confusion.to_csv(outdir / "04_issue_confusion.csv")

    # ---- disagreements, for inspection ----
    dis = df.loc[~df["both_match"], [
        "case_no", "complaint_id", "official_product", "my_product",
        "official_issue", "my_issue", "product_match", "issue_match",
        "notes", "narrative",
    ]].copy()
    dis["narrative"] = dis["narrative"].astype("string").str.slice(0, 400)
    dis = dis.sort_values("case_no")
    dis.to_csv(outdir / "04_disagreements.csv", index=False)

    # most common directional confusions
    pairs = (df.loc[~df["issue_match"], ["official_issue", "my_issue"]]
               .value_counts().head(12).reset_index(name="n"))

    # ---- report ----
    lines = []
    w = lines.append
    w("# 04 — Label noise analysis")
    w("")
    w(f"Golden set: **{n} hand-labelled cases**. Matched in parquet: **{matched}**.")
    w("")
    w("## Headline")
    w("")
    w("| Measure | Agreement |")
    w("|---|---|")
    w(f"| Product | {p_agree:.1%} |")
    w(f"| Issue | {i_agree:.1%} |")
    w(f"| Issue, conditional on product agreeing (n={len(sub)}) | {i_agree_cond:.1%} |")
    w(f"| Both | {b_agree:.1%} |")
    w("")
    w("CFPB product and issue labels are selected by the consumer at intake, not")
    w("assigned by a reviewer. Divergence from expert reading is therefore expected")
    w("and is a property of the data, not an error in either party. The size of the")
    w("divergence bounds what any classifier trained on these labels can achieve:")
    w("a model scored against the official labels cannot exceed this agreement rate")
    w("without learning the intake artefact rather than the underlying grievance.")
    w("")
    w("## Most frequent issue confusions")
    w("")
    w("| Official (consumer-selected) | Hand label | n |")
    w("|---|---|---|")
    for _, r in pairs.iterrows():
        w(f"| {r['official_issue']} | {r['my_issue']} | {r['n']} |")
    w("")
    w("## Files")
    w("")
    w("- `04_disagreements.csv` — every disagreeing case with truncated narrative")
    w("- `04_issue_confusion.csv` — full confusion matrix, official rows x hand-label columns")
    w("")
    w("## Caveats")
    w("")
    w(f"- Support is concentrated: the golden set covers {df['my_issue'].nunique()} of 89 issues "
      f"and {df['my_product'].nunique()} of 13 products.")
    w("- Nine issue classes have n=1; no per-class rate should be quoted for them.")
    w("- Single labeller, single pass. Intra-rater reliability is measured separately")
    w("  by the blind re-label subset and is required before any human ceiling is claimed.")

    (outdir / "04_label_noise.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {outdir/'04_label_noise.md'}")
    print(f"wrote {outdir/'04_disagreements.csv'}  ({len(dis)} rows)")
    print(f"wrote {outdir/'04_issue_confusion.csv'}")


if __name__ == "__main__":
    main()
