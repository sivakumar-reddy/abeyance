#!/usr/bin/env python3
"""
Project A — Step 5: Boundary characterisation
==============================================
The label noise analysis found that 38 of 54 issue disagreements sit inside a
three-node cycle:

    Incorrect information on your report
    Improper use of your report
    Problem with a company's investigation into an existing problem

and the flow runs in BOTH directions on every edge. That rules out a simple
consumer-default explanation and points at the categories not being separable
from narrative text.

This script pulls those cases into a readable side-by-side and measures which
lexical signals actually track the disagreement, so the annotation guideline is
written from evidence rather than intuition.

Usage
-----
    python 05_boundary_analysis.py \
        --golden        human_ceiling_sample_labelled.csv \
        --disagreements docs/04_disagreements.csv \
        --outdir        docs/

Outputs
-------
    docs/05_boundary_cases.md       full narratives, paired labels, your notes
    docs/05_signal_table.csv        signal frequency by disagreement direction
    docs/05_rule_worksheet.csv      one row per case, for you to record the rule
"""

import argparse
import re
from pathlib import Path

import pandas as pd

TRIANGLE = {
    "Incorrect information on your report",
    "Improper use of your report",
    "Problem with a company's investigation into an existing problem",
}

SHORT = {
    "Incorrect information on your report": "ACCURACY",
    "Improper use of your report": "PERMISSIBLE-PURPOSE",
    "Problem with a company's investigation into an existing problem": "INVESTIGATION",
}

# Lexical signals, chosen because each maps to a distinct legal theory under
# FCRA rather than to surface wording. If a signal separates the directions,
# it is a candidate for the guideline.
SIGNALS = {
    # --- procedural history: did the consumer already try to fix this? ---
    "dispute_sent":      r"\b(disput\w+|sent (a |several |multiple )?letter|wrote to|mailed|"
                         r"certified mail|contacted (them|the bureau|the credit))\b",
    "repeated_attempts": r"\b(again|repeated\w*|multiple times|several times|numerous|"
                         r"over and over|third time|second time|continuous\w*|still)\b",
    "no_response":       r"\b(no (response|reply|answer)|never (responded|replied|heard|got|received)|"
                         r"failed to respond|have ?n[o']?t (heard|received|gotten|got)|"
                         r"did ?n[o']?t (respond|reply|answer)|ignored|no one (has )?"
                         r"(responded|replied|contacted)|still waiting|awaiting a response)\b",
    "unresolved":        r"\b(still (appears|showing|reporting|on my|there)|has ?n[o']?t been "
                         r"(removed|corrected|deleted|resolved)|remains on|continues to report)\b",
    "reinvestigation":   r"\b(reinvestigat\w+|investigat\w+|method of verification|"
                         r"frivolous|stall\w*|canned response|generic response)\b",
    "thirty_days":       r"\b(30|thirty)[- ]days?\b",

    # --- permissible purpose theory ---
    "inquiry":           r"\b(inquir\w+|hard (pull|inquiry)|soft (pull|inquiry)|credit pull)\b",
    "permission":        r"\b(permissible purpose|without (my )?(consent|permission|authoriz\w+|"
                         r"knowledge)|did ?n[o']?t (authorize|consent|give permission)|"
                         r"unauthoriz\w+|no permission)\b",

    # --- accuracy theory ---
    "not_mine":          r"\b(not mine|does ?n[o']?t belong|do ?n[o']?t recognize|never opened|"
                         r"never applied|no knowledge of (this|the) account|not my (account|debt))\b",
    "inaccurate":        r"\b(inaccurate|incorrect|erroneous|wrong information|false(ly)? report|"
                         r"misleading|does ?n[o']?t match|reporting incorrectly)\b",
    "identity_theft":    r"\b(identity theft|fraudulent|victim of (fraud|identity)|stolen identity|"
                         r"someone (else )?(used|opened))\b",

    # --- what the consumer asks for ---
    "removal_request":   r"\b(remove|removal|delete|deletion|block(ing|ed)?|expunge|strike)\b",
    "verification":      r"\b(verif\w+|validat\w+|proof|documentation|substantiat\w+|"
                         r"provide evidence)\b",
    "fcra_cite":         r"\b(1681|fcra|fair credit reporting act|15 u\.?s\.?c|section 611|609|623)\b",
}



def count_signals(text):
    t = str(text).lower()
    return {k: int(bool(re.search(p, t))) for k, p in SIGNALS.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--disagreements", required=True)
    ap.add_argument("--outdir", default="docs")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    gold = pd.read_csv(args.golden, encoding="utf-8-sig")
    dis = pd.read_csv(args.disagreements, encoding="utf-8-sig")

    # full narratives live in the golden set; the disagreements file truncates
    gold_small = gold[["case_no", "narrative"]].rename(columns={"narrative": "full_narrative"})
    dis = dis.merge(gold_small, on="case_no", how="left")

    tri = dis[
        dis["official_issue"].isin(TRIANGLE)
        & dis["my_issue"].isin(TRIANGLE)
        & (dis["official_issue"] != dis["my_issue"])   # drop product-only disagreements
    ].copy()

    if tri.empty:
        print("No triangle cases found — check that --disagreements points at 04_disagreements.csv")
        return

    tri["direction"] = (
        tri["official_issue"].map(SHORT) + " -> " + tri["my_issue"].map(SHORT)
    )
    tri = tri.sort_values(["direction", "case_no"])

    print(f"triangle cases: {len(tri)} of {len(dis)} total disagreements\n")
    print(tri["direction"].value_counts().to_string())

    # ---- signal analysis ----
    sig = pd.DataFrame([count_signals(t) for t in tri["full_narrative"]], index=tri.index)

    dead = [k for k in SIGNALS if sig[k].sum() == 0]
    if dead:
        print("\nWARNING: these signals matched zero narratives and are almost certainly")
        print("regex defects rather than findings. Do not report them:")
        for k in dead:
            print("   -", k)

    tri_sig = pd.concat([tri[["case_no", "direction"]], sig], axis=1)

    tri_sig["chose"] = tri["my_issue"].map(SHORT)
    tri_sig["official"] = tri["official_issue"].map(SHORT)

    # PRIMARY VIEW: does the signal predict the label the expert chose?
    # Three groups with real support, rather than six directions with almost none.
    by_chose = tri_sig.groupby("chose")[list(SIGNALS)].mean().round(2).T
    by_chose.columns = [f"chose_{c}" for c in by_chose.columns]
    by_chose["spread"] = (by_chose.max(axis=1) - by_chose.min(axis=1)).round(2)
    by_chose = by_chose.sort_values("spread", ascending=False)

    # SECONDARY: the same, for the consumer's own label
    by_off = tri_sig.groupby("official")[list(SIGNALS)].mean().round(2).T
    by_off.columns = [f"official_{c}" for c in by_off.columns]

    combined = by_chose.join(by_off)
    combined.to_csv(outdir / "05_signal_table.csv")

    n_by_chose = tri_sig["chose"].value_counts().to_dict()
    print("\ncases by label chosen:", n_by_chose)
    print("\nsignal presence rate by LABEL CHOSEN (ranked by separating power):")
    print(by_chose.to_string())

    # direction counts kept as context only; too thin for rates
    by_dir = tri_sig.groupby("direction")[list(SIGNALS)].mean().round(2).T

    # ---- readable dossier ----
    lines = []
    w = lines.append
    w("# 05 — Boundary case characterisation")
    w("")
    w(f"{len(tri)} cases where both the official label and the hand label fall inside")
    w("the three-node cycle. Read these to write the annotation guideline: the")
    w("question to answer for each is **what would have to be true for the other")
    w("label to be correct?**")
    w("")
    w("## Directions")
    w("")
    w("| Direction (official -> hand) | n |")
    w("|---|---|")
    for d, c in tri["direction"].value_counts().items():
        w(f"| {d} | {c} |")
    w("")
    w("## Signals that separate the directions")
    w("")
    w("Presence rate of each lexical signal, grouped by **the label the expert")
    w("chose**. This is the operative question: if a signal is far more common in")
    w("cases labelled INVESTIGATION than in cases labelled ACCURACY, it is a")
    w("candidate rule. A low spread means the signal appears everywhere and")
    w("carries no information.")
    w("")
    w("Direction-level rates are omitted deliberately: six directions across")
    w("38 cases leaves several groups at n<5, where a presence rate is forced to")
    w("0.00 or 1.00 and any spread computed from it is an artifact of the sample")
    w("size rather than a signal.")
    w("")
    w("| Signal | " + " | ".join(by_chose.columns[:-1]) + " | spread |")
    w("|" + "---|" * (len(by_chose.columns) + 1))
    for name, row in by_chose.iterrows():
        w(f"| `{name}` | " + " | ".join(f"{v:.2f}" for v in row[:-1]) + f" | **{row['spread']:.2f}** |")
    w("")
    w("---")
    w("")

    for direction, grp in tri.groupby("direction"):
        w(f"## {direction}  ({len(grp)} cases)")
        w("")
        for _, r in grp.iterrows():
            w(f"### Case {int(r['case_no'])}  ·  complaint {r['complaint_id']}")
            w("")
            w(f"- **Official:** {r['official_issue']}")
            w(f"- **Hand:** {r['my_issue']}")
            if pd.notna(r.get("notes")):
                w(f"- **Your note:** {r['notes']}")
            w("")
            narrative = str(r["full_narrative"]).strip().replace("\n", " ")
            w("> " + narrative[:2500] + ("…" if len(narrative) > 2500 else ""))
            w("")
        w("---")
        w("")

    (outdir / "05_boundary_cases.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- worksheet ----
    work = tri[["case_no", "complaint_id", "direction", "official_issue", "my_issue", "notes"]].copy()
    work["primary_grievance"] = ""       # ACCURACY / PERMISSIBLE-PURPOSE / INVESTIGATION
    work["decisive_signal"] = ""         # which phrase in the narrative decided it
    work["separable"] = ""               # YES / NO — could any rule reliably split this?
    work["rule_note"] = ""
    work.to_csv(outdir / "05_rule_worksheet.csv", index=False, encoding="utf-8")

    print(f"\nwrote {outdir/'05_boundary_cases.md'}")
    print(f"wrote {outdir/'05_signal_table.csv'}")
    print(f"wrote {outdir/'05_rule_worksheet.csv'}  ({len(work)} rows)")


if __name__ == "__main__":
    main()
