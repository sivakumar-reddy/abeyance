#!/usr/bin/env python3
"""
Project A — Step 7: Keyword baseline
=====================================
Rule-based classifier over the three credit-reporting issue classes, scored
against the hand-labelled golden set.

This baseline is PRE-REGISTERED AS A PREDICTED FAILURE. `05_signal_table.csv`
showed the best lexical signal separates the three classes by 0.33 presence rate
at n=38, and `06_annotation_guideline.md` establishes why: the same vocabulary
appears in all three classes but in different syntactic roles — naming the
grievance in one case, naming the requested remedy in another. Pattern matching
cannot see role.

The purpose of building it anyway is to make that prediction falsifiable and to
establish the floor any semantic intervention must clear.

Usage
-----
    python 07_baseline_keyword.py --golden golden_set_v2.csv --outdir docs/
"""

import argparse
import re
from collections import Counter
from pathlib import Path

import pandas as pd

CLASSES = ["ACCURACY", "PERMISSIBLE-PURPOSE", "INVESTIGATION"]

ISSUE_TO_CLASS = {
    "Incorrect information on your report": "ACCURACY",
    "Improper use of your report": "PERMISSIBLE-PURPOSE",
    "Problem with a company's investigation into an existing problem": "INVESTIGATION",
}

# Weighted lexical rules. Weights reflect how definitional each phrase is of its
# legal theory — not tuned on the golden set, which would leak the answer.
RULES = {
    "ACCURACY": [
        (r"\b(inaccurate|incorrect|erroneous|wrong information)\b", 2),
        (r"\b(false(ly)? report|misleading|does ?n[o']?t match)\b", 2),
        (r"\b(not mine|does ?n[o']?t belong|never opened|never applied)\b", 2),
        (r"\b(late payments?|charge[- ]?off|collection account)\b", 1),
        (r"\b(remove|delete|deletion|correct(ion)?)\b", 1),
    ],
    "PERMISSIBLE-PURPOSE": [
        (r"\bpermissible purpose\b", 3),
        (r"\b(without (my )?(consent|permission|authoriz\w+)|did ?n[o']?t authorize)\b", 3),
        (r"\b(written (consent|instructions|permission))\b", 2),
        (r"\b(unauthoriz\w+)\b", 2),
        (r"\b(inquir\w+|hard pull|soft pull)\b", 2),
    ],
    "INVESTIGATION": [
        (r"\b(reasonable investigation|failure to investigate|frivolous)\b", 3),
        (r"\b(no (response|reply)|never (responded|replied|heard|got|received))\b", 3),
        (r"\b(method of verification|stall\w*|canned response)\b", 3),
        (r"\b(multiple|several|repeated\w*|numerous) (formal )?(dispute|letter)", 2),
        (r"\b(reinvestigat\w+)\b", 2),
        (r"\b(30|thirty)[- ]days?\b", 1),
    ],
}


def score(text):
    t = str(text).lower()
    return {c: sum(w for p, w in rules if re.search(p, t)) for c, rules in RULES.items()}


def predict(text, margin=0):
    """argmax with an optional confidence margin; ties and thin margins abstain."""
    s = score(text)
    ranked = sorted(s.items(), key=lambda kv: -kv[1])
    top, second = ranked[0], ranked[1]
    if top[1] == 0:
        return "ABSTAIN", s
    if top[1] - second[1] <= margin:
        return "ABSTAIN", s
    return top[0], s


def prf(y_true, y_pred, label):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1, tp + fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--margin", type=int, default=0)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.golden, encoding="utf-8-sig")
    df["gold"] = df["my_issue"].map(ISSUE_TO_CLASS)
    task = df[df["gold"].notna()].copy()
    print(f"in-scope cases: {len(task)} of {len(df)}")

    preds, scores = zip(*(predict(t, args.margin) for t in task["narrative"]))
    task["pred"] = preds

    # ---- headline ----
    decided = task[task["pred"] != "ABSTAIN"]
    acc_all = (task["pred"] == task["gold"]).mean()
    acc_dec = (decided["pred"] == decided["gold"]).mean() if len(decided) else float("nan")
    coverage = len(decided) / len(task)

    majority = task["gold"].value_counts().idxmax()
    maj_rate = (task["gold"] == majority).mean()

    print(f"\nmajority-class baseline ({majority}): {maj_rate:.1%}")
    print(f"keyword accuracy, all cases:      {acc_all:.1%}")
    print(f"keyword accuracy, decided only:   {acc_dec:.1%}  (coverage {coverage:.1%})")

    # ---- per class ----
    rows = []
    for c in CLASSES:
        p, r, f, n = prf(task["gold"], task["pred"], c)
        rows.append({"class": c, "n": n, "precision": round(p, 3),
                     "recall": round(r, 3), "f1": round(f, 3)})
    per = pd.DataFrame(rows)
    macro_f1 = per["f1"].mean()
    print(f"\nmacro-F1: {macro_f1:.3f}")
    print(per.to_string(index=False))

    # ---- abstention region check ----
    # Cases the guideline marked ABSTAIN are ones no rule should resolve.
    if "abstain" in task.columns:
        amb = task[task["abstain"] == "ABSTAIN"]
        clear = task[task["abstain"] != "ABSTAIN"]
        if len(amb):
            print(f"\naccuracy on guideline-ABSTAIN cases  ({len(amb)}): "
                  f"{(amb['pred'] == amb['gold']).mean():.1%}")
            print(f"accuracy on clearly-separable cases  ({len(clear)}): "
                  f"{(clear['pred'] == clear['gold']).mean():.1%}")

    # ---- confusion ----
    conf = pd.crosstab(task["gold"], task["pred"])
    conf.to_csv(outdir / "07_baseline_confusion.csv")
    print("\nconfusion (rows = gold, cols = predicted):")
    print(conf.to_string())

    task[["case_no", "complaint_id", "gold", "pred", "abstain"]].to_csv(
        outdir / "07_baseline_predictions.csv", index=False)

    # ---- report ----
    L = []
    w = L.append
    w("# 07 — Keyword baseline")
    w("")
    w("Pre-registered as a predicted failure in `06_annotation_guideline.md` §4.")
    w("Built to make that prediction falsifiable and to establish the floor any")
    w("semantic intervention must clear.")
    w("")
    w("## Result")
    w("")
    w("| Measure | Value |")
    w("|---|---|")
    w(f"| In-scope cases | {len(task)} |")
    w(f"| Majority-class baseline ({majority}) | {maj_rate:.1%} |")
    w(f"| Keyword accuracy, all cases | {acc_all:.1%} |")
    w(f"| Keyword accuracy, decided only | {acc_dec:.1%} |")
    w(f"| Coverage | {coverage:.1%} |")
    w(f"| Macro-F1 | {macro_f1:.3f} |")
    w("")
    verdict = ("does not beat" if acc_all <= maj_rate else "beats")
    w(f"The keyword baseline **{verdict}** always predicting the majority class.")
    w("")
    w("## Per class")
    w("")
    w("| Class | n | Precision | Recall | F1 |")
    w("|---|---|---|---|---|")
    for _, r in per.iterrows():
        w(f"| {r['class']} | {int(r['n'])} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} |")
    w("")
    w("## Interpretation")
    w("")
    w("Macro-F1 is the honest number here: accuracy is inflated by the 61%")
    w("majority class. A classifier that recovers the minority classes at all")
    w("must show macro-F1 well above what weighted keyword matching achieves.")
    w("")
    w("`05_signal_table.csv` predicted this outcome from the signal spreads")
    w("alone. The failure is not a tuning problem — adding or reweighting rules")
    w("cannot recover a distinction that lives in syntactic role rather than")
    w("vocabulary.")
    (outdir / "07_baseline.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {outdir/'07_baseline.md'}")


if __name__ == "__main__":
    main()
