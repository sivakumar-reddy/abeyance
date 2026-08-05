#!/usr/bin/env python3
"""
Project A — Step 9: Pairwise tournament (Intervention 2)
=========================================================
Intervention 1 failed a specific test: given a written abstention rule, the model
abstained at 31.2% on guideline-ambiguous cases and 23.9% on clearly separable
ones — a 7-point gap at n=16, which is one case. Abstention precision was 23.8%.
It produced abstention *behaviour* without abstention *judgment*.

The diagnosis: asking a model "are you unsure?" elicits a self-report, and
self-reported uncertainty is not the same quantity as genuine indeterminacy.

This intervention removes the self-report. Each narrative is put through three
head-to-head comparisons — one per pair of competing legal theories — with the
model asked only which theory survives the counterfactual test, or whether
neither dominates. Abstention is then DERIVED from the structure of the results:

    * one theory wins both its matches            -> label it
    * the three results form a cycle (A>P>I>A)    -> ABSTAIN
    * ties prevent any theory reaching two wins   -> ABSTAIN

A cycle is a Condorcet paradox: the narrative supports mutually inconsistent
orderings, which is what "genuinely two-headed" means operationally. The model is
never asked whether it is uncertain. Uncertainty is measured by disagreement
among its own forced choices.

Usage
-----
    python 09_pairwise_tournament.py --golden golden_set_v2.csv --outdir docs/
    python 09_pairwise_tournament.py --golden golden_set_v2.csv --outdir docs/ --offline
"""

import argparse
import itertools
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

CLASSES = ["ACCURACY", "PERMISSIBLE-PURPOSE", "INVESTIGATION"]
PAIRS = list(itertools.combinations(CLASSES, 2))

ISSUE_TO_CLASS = {
    "Incorrect information on your report": "ACCURACY",
    "Improper use of your report": "PERMISSIBLE-PURPOSE",
    "Problem with a company's investigation into an existing problem": "INVESTIGATION",
}

THEORY = {
    "ACCURACY":
        "ACCURACY — the grievance is the CONTENT of the credit report. Remove the "
        "inaccuracy in the reported data and the complaint disappears. Investigation "
        "and deletion language may appear, but as the REMEDY requested, not the complaint.",
    "PERMISSIBLE-PURPOSE":
        "PERMISSIBLE-PURPOSE — the grievance is that the furnishing or the inquiry "
        "OCCURRED AT ALL, independent of whether the data is correct. Remove the absence "
        "of consent or authorisation and the complaint disappears.",
    "INVESTIGATION":
        "INVESTIGATION — the grievance is the company's CONDUCT AFTER a dispute was "
        "filed. Remove the company's failure to act on that prior dispute and the "
        "complaint disappears. A prior dispute alone is NOT sufficient; nearly every "
        "complainant has disputed something.",
}


def system_for(a, b):
    return f"""You compare two competing legal theories for a US consumer credit-reporting complaint and decide which one, if any, better explains why the complainant is aggrieved.

THEORY A
{THEORY[a]}

THEORY B
{THEORY[b]}

THE TEST
For each theory, remove the defect it names and ask whether the complainant still has a complaint. The theory whose removal ends the complaint is the better explanation.

Answer "{a}" if only theory A's removal ends the complaint.
Answer "{b}" if only theory B's removal ends the complaint.
Answer "NEITHER" if BOTH would independently end the complaint, or if NEITHER would — that is, if the two theories are not ordered by this narrative.

Do not break a genuine tie. "NEITHER" is a substantive answer, not a failure to decide.

OUTPUT
JSON only. No preamble, no markdown fences.
{{"winner": "{a}" | "{b}" | "NEITHER", "reason": "<one sentence>"}}"""


def parse(raw, a, b):
    txt = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    obj = None
    cands = [txt]
    for pat in (r"\{.*\}", r"\{.*?\}"):
        m = re.search(pat, txt, re.DOTALL)
        if m:
            cands.append(m.group(0))
    for c in cands:
        c = re.sub(r",\s*([}\]])", r"\1", c).replace("\n", " ")
        try:
            obj = json.loads(c)
            break
        except json.JSONDecodeError:
            continue
    if isinstance(obj, dict):
        w = str(obj.get("winner", "")).strip().upper()
        if w in (a, b, "NEITHER"):
            return {"winner": w, "reason": str(obj.get("reason", ""))[:300]}
    for cand in (a, b, "NEITHER"):
        if re.search(rf"\b{re.escape(cand)}\b", txt.upper()):
            return {"winner": cand, "reason": "RECOVERED_FROM_UNSTRUCTURED"}
    return None


class FatalAPIError(RuntimeError):
    pass


def compare(client, model, narrative, a, b, retries=3):
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=500,
                system=system_for(a, b),
                messages=[{"role": "user",
                           "content": f"<complaint>\n{str(narrative)[:20000]}\n</complaint>"}],
            )
            raw = "".join(bl.text for bl in resp.content if bl.type == "text")
            out = parse(raw, a, b)
            if out:
                return out
            print(f"      unparseable, retry {attempt + 1}")
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in (400, 401, 403, 404):
                raise FatalAPIError(f"HTTP {status}: {e}") from None
            wait = 2 ** attempt
            print(f"      {type(e).__name__} ({status}), retry in {wait}s")
            time.sleep(wait)
    return None


def aggregate(results):
    """results: {(a,b): winner}. Returns (label, structure, margin)."""
    wins = {c: 0.0 for c in CLASSES}
    ties = 0
    for (a, b), w in results.items():
        if w == "NEITHER":
            ties += 1
            wins[a] += 0.5
            wins[b] += 0.5
        else:
            wins[w] += 1.0

    ranked = sorted(wins.items(), key=lambda kv: -kv[1])
    top, second = ranked[0], ranked[1]
    margin = top[1] - second[1]

    if top[1] >= 2.0 and margin > 0:
        return top[0], ("clear" if ties == 0 else "clear_with_ties"), margin
    if ties == 0 and all(abs(v - 1.0) < 1e-9 for v in wins.values()):
        return "ABSTAIN", "cycle", 0.0          # Condorcet paradox
    if margin == 0:
        return "ABSTAIN", "tied", 0.0
    return "ABSTAIN", "no_majority", margin


def prf(y_true, y_pred, label):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * pr * rc / (pr + rc) if pr + rc else 0.0
    return pr, rc, f1, tp + fn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--cache", default="cache/09_pairwise.jsonl")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    cache_path = Path(args.cache); cache_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.golden, encoding="utf-8-sig")
    df["gold"] = df["my_issue"].map(ISSUE_TO_CLASS)
    task = df[df["gold"].notna()].copy()
    print(f"in-scope cases: {len(task)}   comparisons needed: {len(task) * len(PAIRS)}")

    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[(int(r["case_no"]), r["a"], r["b"])] = r
        print(f"cached comparisons: {len(cache)}")

    todo = [(int(c), a, b) for c in task["case_no"] for a, b in PAIRS
            if (int(c), a, b) not in cache]

    if todo and not args.offline:
        try:
            import anthropic
        except ImportError:
            sys.exit("pip install anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set")
        client = anthropic.Anthropic()
        print(f"calling API for {len(todo)} comparisons")
        with cache_path.open("a", encoding="utf-8") as fh:
            last_case = None
            for i, (case_no, a, b) in enumerate(todo, 1):
                if case_no != last_case:
                    print(f"  case {case_no}  [{i}/{len(todo)}]")
                    last_case = case_no
                narrative = task.loc[task["case_no"] == case_no, "narrative"].iloc[0]
                try:
                    out = compare(client, args.model, narrative, a, b)
                except FatalAPIError as e:
                    print(f"\nFATAL: {e}\nAborting; cache holds {len(cache)} comparisons.")
                    sys.exit(1)
                if out is None:
                    print(f"    FAILED {case_no} {a} vs {b}")
                    continue
                rec = {"case_no": case_no, "a": a, "b": b, **out}
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                cache[(case_no, a, b)] = rec

    # ---- aggregate ----
    rows = []
    for c in task["case_no"]:
        c = int(c)
        res = {(a, b): cache[(c, a, b)]["winner"] for a, b in PAIRS if (c, a, b) in cache}
        if len(res) < len(PAIRS):
            continue
        label, structure, margin = aggregate(res)
        rows.append({"case_no": c, "pred": label, "structure": structure, "margin": margin,
                     **{f"{a[:4]}_v_{b[:4]}": res[(a, b)] for a, b in PAIRS}})
    agg = pd.DataFrame(rows)
    task = task.merge(agg, on="case_no", how="inner")
    print(f"\ncomplete tournaments: {len(task)}")

    # ---- headline ----
    decided = task[task["pred"] != "ABSTAIN"]
    acc_all = (task["pred"] == task["gold"]).mean()
    acc_dec = (decided["pred"] == decided["gold"]).mean() if len(decided) else float("nan")
    coverage = len(decided) / len(task)
    majority = task["gold"].value_counts().idxmax()
    maj_rate = (task["gold"] == majority).mean()

    print(f"\nmajority-class baseline ({majority}): {maj_rate:.1%}")
    print(f"tournament accuracy, all cases:   {acc_all:.1%}")
    print(f"tournament accuracy, decided:     {acc_dec:.1%}  (coverage {coverage:.1%})")

    per = pd.DataFrame([
        {"class": c, "n": prf(task["gold"], task["pred"], c)[3],
         "precision": round(prf(task["gold"], task["pred"], c)[0], 3),
         "recall": round(prf(task["gold"], task["pred"], c)[1], 3),
         "f1": round(prf(task["gold"], task["pred"], c)[2], 3)}
        for c in CLASSES])
    macro_f1 = per["f1"].mean()
    print(f"\nmacro-F1: {macro_f1:.3f}")
    print(per.to_string(index=False))

    print("\nabstention structure:")
    print(task["structure"].value_counts().to_string())

    amb = task[task["abstain"] == "ABSTAIN"]
    clear = task[task["abstain"] != "ABSTAIN"]
    r_amb = (amb["pred"] == "ABSTAIN").mean() if len(amb) else float("nan")
    r_clear = (clear["pred"] == "ABSTAIN").mean() if len(clear) else float("nan")
    n_abst = max(1, len(task[task["pred"] == "ABSTAIN"]))
    prec_abst = len(amb[amb["pred"] == "ABSTAIN"]) / n_abst

    print(f"\nabstains on guideline-ABSTAIN cases ({len(amb)}): {r_amb:.1%}")
    print(f"abstains on clearly-separable cases ({len(clear)}): {r_clear:.1%}")
    print(f"  -> abstention precision: {prec_abst:.1%}")
    print(f"  -> lift over Intervention 1 (23.8%): {prec_abst - 0.238:+.1%}")

    conf = pd.crosstab(task["gold"], task["pred"])
    conf.to_csv(outdir / "09_tournament_confusion.csv")
    print("\nconfusion (rows = gold, cols = predicted):")
    print(conf.to_string())

    keep = ["case_no", "complaint_id", "gold", "pred", "structure", "margin", "abstain"] + \
           [c for c in task.columns if "_v_" in c]
    task[keep].to_csv(outdir / "09_tournament_predictions.csv", index=False, encoding="utf-8")

    # ---- report ----
    L = []; w = L.append
    w("# 09 — Pairwise tournament (Intervention 2)")
    w("")
    w("Intervention 1 abstained at 31.2% on guideline-ambiguous cases and 23.9% on")
    w("clearly separable ones — abstention precision 23.8%, barely above the base")
    w("rate. It produced abstention behaviour without abstention judgment.")
    w("")
    w("This intervention never asks the model whether it is uncertain. Each case is")
    w("decided by three forced head-to-head comparisons, and abstention is derived")
    w("from the structure of the results: a cycle (A beats P beats I beats A) is a")
    w("Condorcet paradox and is what 'genuinely two-headed' means operationally.")
    w("")
    w("## Comparison across all three systems")
    w("")
    w("| Measure | Keyword | LLM direct | Tournament | Majority |")
    w("|---|---|---|---|---|")
    w(f"| Accuracy, all | 47.0% | 51.8% | {acc_all:.1%} | {maj_rate:.1%} |")
    w(f"| Accuracy, decided | 58.2% | 69.4% | {acc_dec:.1%} | — |")
    w(f"| Coverage | 80.7% | 74.7% | {coverage:.1%} | 100% |")
    w(f"| Macro-F1 | 0.471 | 0.549 | {macro_f1:.3f} | — |")
    w(f"| Abstention precision | — | 23.8% | {prec_abst:.1%} | — |")
    w("")
    w("## Per class")
    w("")
    w("| Class | n | Precision | Recall | F1 |")
    w("|---|---|---|---|---|")
    for _, r in per.iterrows():
        w(f"| {r['class']} | {int(r['n'])} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} |")
    w("")
    w("## Where abstentions come from")
    w("")
    w("| Structure | n |")
    w("|---|---|")
    for k, v in task["structure"].value_counts().items():
        w(f"| {k} | {v} |")
    w("")
    w(f"Abstains on guideline-ABSTAIN cases (n={len(amb)}): **{r_amb:.1%}**")
    w(f"Abstains on clearly-separable cases (n={len(clear)}): **{r_clear:.1%}**")
    w("")
    w("If these two rates are close, structural abstention has the same defect as")
    w("self-reported abstention and the negative result generalises: the boundary")
    w("the guideline identifies is not recoverable by either method.")
    (outdir / "09_tournament.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {outdir/'09_tournament.md'}")


if __name__ == "__main__":
    main()
