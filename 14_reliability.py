#!/usr/bin/env python3
"""
Project A — Step 14: Intra-rater reliability
=============================================
Scores the blind re-label against the first pass and produces the reliability
figure that `10_findings.md` §8 and `12_brd.md` ASM-1 both depend on.

Every claim in the study rests on the hand labels being the more reliable side
of the 46% disagreement with CFPB. This is the measurement that establishes it.

Design caveat, recorded rather than hidden
------------------------------------------
The intended protocol was a 48-hour gap between passes. The re-label was
performed the same day, and 8 of the 25 cases had additionally been re-read
hours earlier during the boundary worksheet with the first-pass labels visible.

Those 8 cases are therefore anchored twice over. The analysis is stratified:

    PRIMARY   17 cases never re-read with labels visible
    SECONDARY  8 cases reviewed in the worksheet with labels visible

The gap between the two strata estimates the size of the anchoring effect. If
the contaminated stratum agrees at a materially higher rate, the pooled figure
is an overestimate and only the primary stratum should be quoted.

Usage
-----
    python 14_reliability.py \
        --relabel blind_relabel_25.csv \
        --key     blind_relabel_25_KEY_DO_NOT_OPEN.csv \
        --outdir  docs/
"""

import argparse
import math
from pathlib import Path

import pandas as pd

# Cases re-read during the 05 boundary worksheet with first-pass labels visible
WORKSHEET_SEEN = {2, 23, 40, 47, 50, 51, 61, 75}


def wilson(k, n, z=1.96):
    """Wilson score interval — behaves sensibly at small n, unlike normal approx."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def cohen_kappa(a, b):
    """Chance-corrected agreement between two label sequences."""
    labels = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((list(a).count(l) / n) * (list(b).count(l) / n) for l in labels)
    if abs(1 - pe) < 1e-12:
        return float("nan")
    return (po - pe) / (1 - pe)


def block(name, df, col1, col2):
    n = len(df)
    k = int((df[col1] == df[col2]).sum())
    lo, hi = wilson(k, n)
    kap = cohen_kappa(df[col1].tolist(), df[col2].tolist())
    print(f"  {name:<38} {k:>2}/{n:<3} = {k/n if n else float('nan'):>6.1%}   "
          f"95% CI [{lo:.1%}, {hi:.1%}]   kappa {kap:.3f}")
    return {"stratum": name, "n": n, "agree": k,
            "rate": k / n if n else float("nan"),
            "ci_low": lo, "ci_high": hi, "kappa": kap}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--relabel", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--outdir", default="docs")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)

    rl = pd.read_csv(args.relabel, encoding="utf-8-sig")
    key = pd.read_csv(args.key, encoding="utf-8-sig")

    blank = rl["my_issue"].isna().sum()
    if blank:
        raise SystemExit(f"{blank} rows in the re-label are still unlabelled. "
                         "Fill every row before scoring.")

    df = rl.merge(key, on="relabel_no", how="inner", suffixes=("_p2", "_key"))
    if len(df) != len(rl):
        raise SystemExit(f"join produced {len(df)} rows from {len(rl)} — check relabel_no")

    for c in ("my_issue", "my_product"):
        df[f"{c}_p2"] = df[f"{c}"].astype(str).str.strip() if c in df.columns else None
    df["pass1_issue"] = df["pass1_issue"].astype(str).str.strip()
    df["pass1_product"] = df["pass1_product"].astype(str).str.strip()
    df["p2_issue"] = df["my_issue"].astype(str).str.strip()
    df["p2_product"] = df["my_product"].astype(str).str.strip()
    df["contaminated"] = df["original_case_no"].isin(WORKSHEET_SEEN)

    clean = df[~df["contaminated"]]
    dirty = df[df["contaminated"]]

    print(f"re-labelled cases: {len(df)}")
    print(f"  primary stratum   (never re-read with labels visible): {len(clean)}")
    print(f"  secondary stratum (seen in the 05 worksheet):          {len(dirty)}")

    print("\nISSUE agreement between pass 1 and pass 2")
    rows = [
        block("PRIMARY  — clean cases", clean, "pass1_issue", "p2_issue"),
        block("SECONDARY— worksheet-anchored", dirty, "pass1_issue", "p2_issue"),
        block("POOLED   — all 25 (do not quote)", df, "pass1_issue", "p2_issue"),
    ]

    print("\nPRODUCT agreement")
    prod = [
        block("PRIMARY  — clean cases", clean, "pass1_product", "p2_product"),
        block("POOLED   — all 25", df, "pass1_product", "p2_product"),
    ]

    anchor = rows[1]["rate"] - rows[0]["rate"]
    print(f"\nanchoring effect (secondary - primary): {anchor:+.1%}")

    prim = rows[0]
    print(f"\nCOMPARISON")
    print(f"  self-agreement, primary stratum: {prim['rate']:.1%}  "
          f"CI [{prim['ci_low']:.1%}, {prim['ci_high']:.1%}]")
    print(f"  agreement with CFPB intake tags: 46.0%")
    verdict = ("SUPPORTED" if prim["ci_low"] > 0.46
               else "NOT SUPPORTED — CI overlaps the CFPB agreement rate")
    print(f"  ASM-1 (hand labels are the more reliable side): {verdict}")

    # per-case detail
    cid = "complaint_id" if "complaint_id" in df.columns else "complaint_id_key"
    detail = df[["relabel_no", "original_case_no", cid, "contaminated",
                 "pass1_issue", "p2_issue", "pass1_product", "p2_product"]].copy()
    detail = detail.rename(columns={cid: "complaint_id"})
    detail["issue_match"] = detail["pass1_issue"] == detail["p2_issue"]
    detail = detail.sort_values(["contaminated", "original_case_no"])
    detail.to_csv(outdir / "14_reliability_detail.csv", index=False, encoding="utf-8")

    pd.DataFrame(rows + prod).to_csv(outdir / "14_reliability_summary.csv", index=False)

    # ---- report ----
    L = []; w = L.append
    w("# 14 — Intra-rater reliability")
    w("")
    w("Establishes whether the hand labels are the more reliable side of the 46%")
    w("disagreement with CFPB intake tags. `10_findings.md` §8 and `12_brd.md`")
    w("ASM-1 both depend on this figure.")
    w("")
    w("## Protocol deviation, disclosed")
    w("")
    w("The intended design was a 48-hour gap between passes. **The re-label was")
    w("performed the same day.** In addition, 8 of the 25 cases had been re-read")
    w("hours earlier during the boundary worksheet with the first-pass labels")
    w("visible in the `my_issue` column.")
    w("")
    w("The analysis is therefore stratified. The pooled figure across all 25 is")
    w("reported for completeness and **should not be quoted**.")
    w("")
    w("## Issue agreement")
    w("")
    w("| Stratum | n | Agree | Rate | 95% CI | Cohen's kappa |")
    w("|---|---|---|---|---|---|")
    for r in rows:
        w(f"| {r['stratum']} | {r['n']} | {r['agree']} | {r['rate']:.1%} | "
          f"[{r['ci_low']:.1%}, {r['ci_high']:.1%}] | {r['kappa']:.3f} |")
    w("")
    w(f"**Anchoring effect:** the worksheet-anchored stratum agrees "
      f"{anchor:+.1%} relative to the clean stratum.")
    w("")
    w("## Product agreement")
    w("")
    w("| Stratum | n | Agree | Rate | 95% CI |")
    w("|---|---|---|---|---|")
    for r in prod:
        w(f"| {r['stratum']} | {r['n']} | {r['agree']} | {r['rate']:.1%} | "
          f"[{r['ci_low']:.1%}, {r['ci_high']:.1%}] |")
    w("")
    w("## Verdict on ASM-1")
    w("")
    w(f"Self-agreement on the primary stratum is **{prim['rate']:.1%}** "
      f"(95% CI [{prim['ci_low']:.1%}, {prim['ci_high']:.1%}], n={prim['n']}), "
      f"against **46.0%** agreement with CFPB intake tags.")
    w("")
    w(f"**ASM-1: {verdict}**")
    w("")
    w("## Limitations")
    w("")
    w(f"- Primary stratum is n={prim['n']}. The confidence interval is wide and no")
    w("  precise reliability figure should be claimed from it.")
    w("- Same-day re-labelling means even the primary stratum retains some recall")
    w("  advantage over a true 48-hour protocol. The figure is best read as an")
    w("  **upper bound** on self-consistency.")
    w("- Single rater. Inter-rater reliability with a second labeller would be a")
    w("  stronger test and was out of scope.")
    (outdir / "14_reliability.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {outdir/'14_reliability.md'}")
    print(f"wrote {outdir/'14_reliability_detail.csv'}")


if __name__ == "__main__":
    main()
