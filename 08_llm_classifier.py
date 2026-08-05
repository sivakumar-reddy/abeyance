#!/usr/bin/env python3
"""
Project A — Step 8: LLM classifier (Intervention 1)
====================================================
Classifies credit-reporting complaint narratives into the three-class issue
taxonomy using the counterfactual test from `06_annotation_guideline.md`, with
explicit abstention and elicited confidence.

Design commitments
------------------
* The prompt encodes the *rule*, not examples from the golden set. Few-shot
  examples drawn from the evaluation set would leak the answer.
* The golden set's `abstain` column is never shown to the model. Whether the
  model abstains where the guideline says it should is the thing being measured.
* Every response is cached to JSONL on arrival. Sonnet 5 does not accept a
  temperature parameter, so run-to-run variation is possible; the cache is what
  makes the *scored* run reproducible. Delete the cache to re-sample.
* Confidence is elicited on a 0-1 scale and used only for the risk-coverage
  curve — it is not thresholded during classification.

Usage
-----
    setx ANTHROPIC_API_KEY "sk-ant-..."      # once, then reopen the shell
    python 08_llm_classifier.py --golden golden_set_v2.csv --outdir docs/

    # re-score from cache without calling the API
    python 08_llm_classifier.py --golden golden_set_v2.csv --outdir docs/ --offline
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

CLASSES = ["ACCURACY", "PERMISSIBLE-PURPOSE", "INVESTIGATION"]

ISSUE_TO_CLASS = {
    "Incorrect information on your report": "ACCURACY",
    "Improper use of your report": "PERMISSIBLE-PURPOSE",
    "Problem with a company's investigation into an existing problem": "INVESTIGATION",
}

SYSTEM = """You classify US consumer credit-reporting complaints by the primary grievance the complainant is asserting.

THE THREE CLASSES

ACCURACY — the grievance is the CONTENT of the credit report. Investigation, verification and deletion language often appears, but as the REMEDY being requested, not as the complaint. A prior dispute may be described as context for why they are writing now.

PERMISSIBLE-PURPOSE — the grievance is that the furnishing or the inquiry OCCURRED AT ALL, independent of whether the underlying data is correct. The theory is consent or authorisation.

INVESTIGATION — the grievance is the company's CONDUCT AFTER a dispute was filed. Two conditions must BOTH hold: (1) a prior dispute exists and is described, and (2) the complaint is about how that dispute was handled — non-response, refusal to act on submitted evidence, or a verification the complainant considers perfunctory. A prior dispute alone is NOT sufficient; nearly every complainant has disputed something.

THE DECIDING TEST

Remove the alleged defect and ask whether the complainant still has a complaint.
- Remove the inaccuracy in the data → complaint disappears → ACCURACY
- Remove the absence of consent → complaint disappears → PERMISSIBLE-PURPOSE
- Remove the company's failure to act on the prior dispute → complaint disappears → INVESTIGATION

WHEN TO ABSTAIN

Answer ABSTAIN when two or more theories survive the test INDEPENDENTLY — that is, when either would be a complete complaint standing alone. Specifically:
- The narrative asserts two defects as coordinate claims rather than one subordinate to the other (e.g. "inaccurate AND unauthorized accounts")
- Identity theft makes the data wrong AND the furnishing unauthorised at the same time, with neither subordinate
- A dispute failure is alleged ALONGSIDE a substantive defect, with neither presented as the reason for the other

Do not break ties. Abstaining on a genuinely two-headed complaint is correct; forcing a label on one is an error.

OUTPUT

Respond with JSON only. No preamble, no markdown fences.
{"label": "ACCURACY" | "PERMISSIBLE-PURPOSE" | "INVESTIGATION" | "ABSTAIN",
 "confidence": <float 0.0-1.0>,
 "counterfactual": "<one sentence: which defect, if removed, ends the complaint>",
 "competing": "<the strongest competing label, or empty string if none>"}"""


def build_client():
    try:
        import anthropic
    except ImportError:
        sys.exit("pip install anthropic")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=key)


def parse(raw):
    txt = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    obj = None
    attempts = [txt]
    # greedy and non-greedy brace spans, in case the model wrapped JSON in prose
    for pat in (r"\{.*\}", r"\{.*?\}"):
        m = re.search(pat, txt, re.DOTALL)
        if m:
            attempts.append(m.group(0))
    for cand in attempts:
        cand = re.sub(r",\s*([}\]])", r"\1", cand)          # trailing commas
        cand = cand.replace("\n", " ")
        try:
            obj = json.loads(cand)
            break
        except json.JSONDecodeError:
            continue
    if obj is None:
        # last resort: pull the label out of unstructured text
        m = re.search(r"\b(ACCURACY|PERMISSIBLE-PURPOSE|INVESTIGATION|ABSTAIN)\b", txt)
        if not m:
            return None
        c = re.search(r'"?confidence"?\s*[:=]\s*([0-9.]+)', txt)
        obj = {"label": m.group(1),
               "confidence": float(c.group(1)) if c else 0.5,
               "counterfactual": "RECOVERED_FROM_UNSTRUCTURED",
               "competing": ""}
    if not isinstance(obj, dict):
        return None
    label = str(obj.get("label", "")).strip().upper()
    if label not in CLASSES + ["ABSTAIN"]:
        return None
    try:
        conf = float(obj.get("confidence", 0.0))
    except (TypeError, ValueError):
        conf = 0.0
    return {
        "label": label,
        "confidence": max(0.0, min(1.0, conf)),
        "counterfactual": str(obj.get("counterfactual", ""))[:400],
        "competing": str(obj.get("competing", ""))[:60],
    }


class FatalAPIError(RuntimeError):
    """A malformed request. Retrying cannot help, so abort the whole run."""


def classify(client, model, narrative, retries=3, failure_log=None):
    last_raw = ""
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=1000,
                system=SYSTEM,
                messages=[{"role": "user", "content":
                           f"<complaint>\n{str(narrative)[:20000]}\n</complaint>"}],
            )
            raw = "".join(b.text for b in resp.content if b.type == "text")
            out = parse(raw)
            if out:
                return out
            last_raw = raw
            print(f"    unparseable response, retry {attempt + 1}")
        except Exception as e:
            status = getattr(e, "status_code", None)
            msg = str(e)
            # 400/401/403/404 are request or credential defects: retrying 83
            # times only burns the run. Surface the message and stop.
            if status in (400, 401, 403, 404):
                raise FatalAPIError(f"HTTP {status}: {msg}") from None
            wait = 2 ** attempt
            print(f"    {type(e).__name__} ({status}): {msg[:160]}")
            print(f"    retry in {wait}s")
            time.sleep(wait)
    if failure_log is not None and last_raw:
        failure_log.write(json.dumps({"raw": last_raw[:4000]}) + "\n")
        failure_log.flush()
        print(f"    raw response logged ({len(last_raw)} chars)")
    return None


def prf(y_true, y_pred, label):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1, tp + fn


def risk_coverage(df):
    """Accuracy as a function of coverage, sweeping the confidence threshold."""
    d = df[df["pred"] != "ABSTAIN"].sort_values("confidence", ascending=False)
    rows = []
    for k in range(1, len(d) + 1):
        head = d.head(k)
        rows.append({
            "k": k,
            "coverage": round(k / len(df), 4),
            "threshold": round(float(head["confidence"].iloc[-1]), 3),
            "accuracy": round(float((head["pred"] == head["gold"]).mean()), 4),
        })
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--cache", default="cache/08_llm_responses.jsonl")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--offline", action="store_true", help="score from cache only")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    cache_path = Path(args.cache); cache_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.golden, encoding="utf-8-sig")
    df["gold"] = df["my_issue"].map(ISSUE_TO_CLASS)
    task = df[df["gold"].notna()].copy()
    print(f"in-scope cases: {len(task)} of {len(df)}")

    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[int(r["case_no"])] = r
        print(f"cached: {len(cache)}")

    todo = [c for c in task["case_no"] if int(c) not in cache]
    if todo and not args.offline:
        client = build_client()
        print(f"calling API for {len(todo)} cases, model={args.model}")
        flog_path = cache_path.with_name("08_failures.jsonl")
        with cache_path.open("a", encoding="utf-8") as fh, \
             flog_path.open("a", encoding="utf-8") as flog:
            for i, case_no in enumerate(todo, 1):
                narrative = task.loc[task["case_no"] == case_no, "narrative"].iloc[0]
                print(f"  [{i}/{len(todo)}] case {case_no}")
                try:
                    out = classify(client, args.model, narrative,
                                   failure_log=flog)
                except FatalAPIError as e:
                    print(f"\nFATAL: {e}")
                    print("Aborting. No further calls made; the cache holds "
                          f"{len(cache)} good responses.")
                    sys.exit(1)
                if out is None:
                    print(f"    FAILED case {case_no}, skipping")
                    continue
                rec = {"case_no": int(case_no), **out}
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                cache[int(case_no)] = rec
    elif todo:
        print(f"WARNING: {len(todo)} cases missing from cache and --offline set")

    task = task[task["case_no"].astype(int).isin(cache)].copy()
    task["pred"] = [cache[int(c)]["label"] for c in task["case_no"]]
    task["confidence"] = [cache[int(c)]["confidence"] for c in task["case_no"]]
    task["counterfactual"] = [cache[int(c)]["counterfactual"] for c in task["case_no"]]

    # ---- headline ----
    decided = task[task["pred"] != "ABSTAIN"]
    acc_all = (task["pred"] == task["gold"]).mean()
    acc_dec = (decided["pred"] == decided["gold"]).mean() if len(decided) else float("nan")
    coverage = len(decided) / len(task)
    majority = task["gold"].value_counts().idxmax()
    maj_rate = (task["gold"] == majority).mean()

    print(f"\nmajority-class baseline ({majority}): {maj_rate:.1%}")
    print(f"LLM accuracy, all cases:          {acc_all:.1%}")
    print(f"LLM accuracy, decided only:       {acc_dec:.1%}  (coverage {coverage:.1%})")

    rows = [dict(zip(["class", "n", "precision", "recall", "f1"],
                     [c, prf(task["gold"], task["pred"], c)[3],
                      *[round(x, 3) for x in prf(task["gold"], task["pred"], c)[:3]]]))
            for c in CLASSES]
    per = pd.DataFrame(rows)[["class", "n", "precision", "recall", "f1"]]
    macro_f1 = per["f1"].mean()
    print(f"\nmacro-F1: {macro_f1:.3f}")
    print(per.to_string(index=False))

    # ---- does it abstain where the guideline says it should? ----
    amb = task[task["abstain"] == "ABSTAIN"]
    clear = task[task["abstain"] != "ABSTAIN"]
    ab_rate_amb = (amb["pred"] == "ABSTAIN").mean() if len(amb) else float("nan")
    ab_rate_clear = (clear["pred"] == "ABSTAIN").mean() if len(clear) else float("nan")
    print(f"\nabstains on guideline-ABSTAIN cases ({len(amb)}): {ab_rate_amb:.1%}")
    print(f"abstains on clearly-separable cases ({len(clear)}): {ab_rate_clear:.1%}")
    print(f"  -> abstention precision: "
          f"{(len(amb[amb['pred']=='ABSTAIN']) / max(1, len(task[task['pred']=='ABSTAIN']))):.1%}")

    conf = pd.crosstab(task["gold"], task["pred"])
    conf.to_csv(outdir / "08_llm_confusion.csv")
    print("\nconfusion (rows = gold, cols = predicted):")
    print(conf.to_string())

    rc = risk_coverage(task)
    rc.to_csv(outdir / "08_risk_coverage.csv", index=False)
    task[["case_no", "complaint_id", "gold", "pred", "confidence",
          "abstain", "counterfactual"]].to_csv(
        outdir / "08_llm_predictions.csv", index=False, encoding="utf-8")

    # ---- report ----
    L = []; w = L.append
    w("# 08 — LLM classifier (Intervention 1)")
    w("")
    w(f"Model `{args.model}`. Prompt encodes the counterfactual test")
    w("from `06_annotation_guideline.md`. No few-shot examples are drawn from the")
    w("evaluation set, and the `abstain` column is never shown to the model.")
    w("")
    w("## Result against the pre-registered floor")
    w("")
    w("| Measure | Keyword baseline | LLM | Majority class |")
    w("|---|---|---|---|")
    w(f"| Accuracy, all cases | 47.0% | {acc_all:.1%} | {maj_rate:.1%} |")
    w(f"| Accuracy, decided only | 58.2% | {acc_dec:.1%} | — |")
    w(f"| Coverage | 80.7% | {coverage:.1%} | 100% |")
    w(f"| Macro-F1 | 0.471 | {macro_f1:.3f} | — |")
    w("")
    w("## Per class")
    w("")
    w("| Class | n | Precision | Recall | F1 |")
    w("|---|---|---|---|---|")
    for _, r in per.iterrows():
        w(f"| {r['class']} | {int(r['n'])} | {r['precision']:.3f} | {r['recall']:.3f} | {r['f1']:.3f} |")
    w("")
    w("## Abstention behaviour")
    w("")
    w("The guideline identified 16 cases as unresolvable by any rule, by reading")
    w("narratives before any classifier existed. Whether the model abstains in the")
    w("same place is the central test of Intervention 1.")
    w("")
    w("| | Rate |")
    w("|---|---|")
    w(f"| Abstains on guideline-ABSTAIN cases (n={len(amb)}) | {ab_rate_amb:.1%} |")
    w(f"| Abstains on clearly-separable cases (n={len(clear)}) | {ab_rate_clear:.1%} |")
    w("")
    w("A model that abstains at similar rates in both groups is abstaining on")
    w("difficulty in general, not on the specific ambiguity the guideline defines.")
    w("")
    w("## Files")
    w("")
    w("- `08_llm_predictions.csv` — per-case label, confidence, and the model's counterfactual")
    w("- `08_risk_coverage.csv` — accuracy vs coverage, sweeping the confidence threshold")
    w("- `08_llm_confusion.csv` — confusion matrix")
    (outdir / "08_llm.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {outdir/'08_llm.md'}")
    print(f"wrote {outdir/'08_risk_coverage.csv'}  ({len(rc)} points)")


if __name__ == "__main__":
    main()
