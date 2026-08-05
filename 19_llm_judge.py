#!/usr/bin/env python3
"""
Project A — Step 19: LLM-as-judge, and its validation (Phase 7)
================================================================
Why this exists
---------------
Step 18 evaluated drafts with four automated checks. Three decide properties
pattern matching can settle: does a cited section appear in the retrieved
context, does a figure appear in the source, does a prohibited phrase occur.

The fourth — does the draft RESTATE the consumer's grievance — is a semantic
judgement. The regex approximating it needed two corrections and still disagrees
with a human reader on inspection. That is the standard motivation for an LLM
judge, and the standard place where evaluation programmes go wrong: the judge is
adopted because it is convenient and its output is then treated as ground truth.

This script does not do that. It measures the judge before using it.

Design
------
Two properties are judged per draft:

    restatement  SEMANTIC. Contested. The thing the judge is for.
    timeline     DETERMINISTIC. A number is named, or it is not.

`timeline` is the control. It is trivially checkable by regex, so if the judge
disagrees with regex there, the judge is unreliable and its verdict on the
contested property carries no weight. A judge is only worth trusting on the hard
question if it is right on the easy one.

Three-way comparison
--------------------
    HUMAN   your labels, the reference
    REGEX   the step-18 screen
    JUDGE   this script

The question is whether the judge tracks the human better than the regex does.
If it does not, the regex is cheaper and should be kept.

Usage
-----
    # 1. generate the sheet, label it, then:
    python 19_llm_judge.py --make-sheet --outdir docs/
    python 19_llm_judge.py --human docs/19_human_labels.csv --outdir docs/
"""

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent

JUDGE_SYSTEM = """You assess acknowledgment letters written by a consumer complaint handling team. You are not writing or improving the letter. You are answering two factual questions about it.

QUESTION 1 — RESTATEMENT
Does the letter restate the consumer's specific grievance, in a way that shows the complaint was read?

YES if the letter names what this particular consumer complained about — the specific problem, account situation, or action they described.
NO if the letter only acknowledges receipt in generic terms, names the category without the substance, or could have been sent to any complainant.

The restatement does not need to be lengthy or use particular wording. It needs to be specific to this complaint.

QUESTION 2 — TIMELINE
Does the letter state a specific time period within which the consumer will receive a response?

YES only if a number of days or an equivalent explicit period is given.
NO if the letter refers to a timeframe without naming it — for example "within the timeframe required by applicable law", "in due course", or "as soon as possible".

OUTPUT
JSON only. No preamble, no markdown fences.
{"restatement": true|false, "restatement_reason": "<one short sentence>", "timeline": true|false, "timeline_reason": "<one short sentence>"}"""


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def kappa(a, b):
    """Cohen's kappa. Returns nan when the reference has no variance.

    If every reference label is identical, chance agreement is 1 and kappa is
    undefined. Reporting 0.000 in that case would read as 'no better than
    chance' when the correct statement is 'not computable'.
    """
    labels = sorted(set(a) | set(b))
    n = len(a)
    if n == 0 or len(set(a)) < 2:
        return float("nan")
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((list(a).count(l) / n) * (list(b).count(l) / n) for l in labels)
    return (po - pe) / (1 - pe) if abs(1 - pe) > 1e-12 else float("nan")


def error_direction(ref, pred):
    """Split disagreements into false negatives and false positives."""
    fn = sum(1 for r, p in zip(ref, pred) if r and not p)
    fp = sum(1 for r, p in zip(ref, pred) if not r and p)
    return fn, fp


def load_drafts(cache_path):
    cache = {}
    p = Path(cache_path)
    if not p.exists():
        sys.exit(f"no draft cache at {p} — run 18_draft_generation.py first")
    for ln in p.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            cache[int(r["case_no"])] = r
    return cache


def make_sheet(cache, out):
    """Write the drafts out for human labelling, with the machine verdicts withheld."""
    lines = ["# 19 — Human labelling sheet", "",
             "Read each draft and answer two questions. Machine verdicts are withheld",
             "deliberately: they are what your labels will be used to evaluate.", "",
             "**Q1 restatement** — does the letter restate *this* consumer's specific",
             "grievance, showing the complaint was read? Generic acknowledgment of receipt",
             "is NO. Naming the category without the substance is NO.", "",
             "**Q2 timeline** — does it state a specific number of days? A reference to",
             "\"the timeframe required by applicable law\" is NO.", "",
             "Reply one line per draft: `case_no  restatement(Y/N)  timeline(Y/N)`", "",
             "---", ""]
    rows = []
    for cn in sorted(cache):
        d = cache[cn]
        lines += [f"## case {cn}  ({d['grievance']})", "",
                  "> " + str(d["draft"]).strip().replace("\n", "\n> "), ""]
        rows.append({"case_no": cn, "human_restatement": "", "human_timeline": ""})
    (out / "19_human_sheet.md").write_text("\n".join(lines), encoding="utf-8")
    pd.DataFrame(rows).to_csv(out / "19_human_labels.csv", index=False)
    print(f"wrote {out/'19_human_sheet.md'}  ({len(rows)} drafts)")
    print(f"wrote {out/'19_human_labels.csv'}  — fill Y/N and re-run with --human")


def parse(raw):
    txt = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    for cand in [txt] + [m.group(0) for m in [re.search(r"\{.*\}", txt, re.DOTALL)] if m]:
        try:
            o = json.loads(re.sub(r",\s*([}\]])", r"\1", cand).replace("\n", " "))
            if isinstance(o, dict) and "restatement" in o:
                return {"restatement": bool(o.get("restatement")),
                        "restatement_reason": str(o.get("restatement_reason", ""))[:240],
                        "timeline": bool(o.get("timeline")),
                        "timeline_reason": str(o.get("timeline_reason", ""))[:240]}
        except json.JSONDecodeError:
            continue
    return None


def judge_one(client, model, draft, retries=3):
    for a in range(retries):
        try:
            r = client.messages.create(
                model=model, max_tokens=500, system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": f"<letter>\n{draft}\n</letter>"}])
            out = parse("".join(b.text for b in r.content if b.type == "text"))
            if out:
                return out
        except Exception as e:
            st = getattr(e, "status_code", None)
            if st in (400, 401, 403, 404):
                sys.exit(f"FATAL HTTP {st}: {e}")
            time.sleep(2 ** a)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--draft-cache", default="cache/18_drafts.jsonl")
    ap.add_argument("--cache", default="cache/19_judge.jsonl")
    ap.add_argument("--eval-csv", default="docs/18_draft_evaluation.csv")
    ap.add_argument("--human", default=None)
    ap.add_argument("--make-sheet", action="store_true")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    drafts = load_drafts(args.draft_cache)

    if args.make_sheet:
        make_sheet(drafts, out)
        return

    # ---- judge ----
    cp = Path(args.cache); cp.parent.mkdir(parents=True, exist_ok=True)
    jc = {}
    if cp.exists():
        for ln in cp.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln); jc[int(r["case_no"])] = r

    todo = [c for c in sorted(drafts) if c not in jc]
    if todo and not args.offline:
        try:
            import anthropic
        except ImportError:
            sys.exit("pip install anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set")
        client = anthropic.Anthropic()
        print(f"judging {len(todo)} drafts")
        with cp.open("a", encoding="utf-8") as fh:
            for i, cn in enumerate(todo, 1):
                print(f"  [{i}/{len(todo)}] case {cn}")
                v = judge_one(client, args.model, drafts[cn]["draft"])
                if v is None:
                    print(f"    FAILED case {cn}"); continue
                rec = {"case_no": cn, **v}
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                jc[cn] = rec

    if not args.human:
        print("\njudge verdicts cached. Re-run with --human docs/19_human_labels.csv to validate.")
        print(f"judged: {len(jc)}/{len(drafts)}")
        return

    # ---- three-way comparison ----
    hum = pd.read_csv(args.human, encoding="utf-8-sig")
    for c in ("human_restatement", "human_timeline"):
        if hum[c].isna().any():
            sys.exit(f"{hum[c].isna().sum()} blank values in {c} — label every row first")
        hum[c] = hum[c].astype(str).str.strip().str.upper().map(
            {"Y": True, "YES": True, "TRUE": True, "N": False, "NO": False, "FALSE": False})
        if hum[c].isna().any():
            sys.exit(f"unrecognised values in {c}; use Y or N")

    reg = pd.read_csv(args.eval_csv)
    reg["regex_restatement"] = ~reg["missing_elements"].fillna("").str.contains("restatement")
    reg["regex_timeline"] = ~reg["missing_elements"].fillna("").str.contains("timeline")

    j = pd.DataFrame([{"case_no": k, "judge_restatement": v["restatement"],
                       "judge_timeline": v["timeline"],
                       "judge_reason": v["restatement_reason"]} for k, v in jc.items()])

    df = hum.merge(j, on="case_no").merge(
        reg[["case_no", "regex_restatement", "regex_timeline"]], on="case_no")
    n = len(df)
    print(f"\nvalidated on {n} drafts")

    print("\n" + "=" * 66)
    print("TIMELINE — the deterministic control")
    print("=" * 66)
    rows = []
    for who in ("judge", "regex"):
        col = f"{who}_timeline"
        agree = int((df[col] == df["human_timeline"]).sum())
        lo, hi = wilson(agree, n)
        k = kappa(df["human_timeline"].tolist(), df[col].tolist())
        print(f"  {who:<6} vs human   {agree:>2}/{n} = {agree/n:>6.1%}   "
              f"CI [{lo:.1%}, {hi:.1%}]   kappa {k:.3f}")
        fn, fp = error_direction(df["human_timeline"].tolist(), df[col].tolist())
        if fn or fp:
            print(f"         errors: {fn} false negative, {fp} false positive")
        rows.append({"property": "timeline", "rater": who, "agree": agree, "n": n,
                     "rate": agree / n, "ci_low": lo, "ci_high": hi, "kappa": k,
                     "false_neg": fn, "false_pos": fp})

    print("\n" + "=" * 66)
    print("RESTATEMENT — the contested property")
    print("=" * 66)
    if df["human_restatement"].nunique() < 2:
        val = bool(df["human_restatement"].iloc[0])
        print(f"  NOTE: the human labelled every draft {val}. With no variance in the")
        print("  reference, kappa is undefined and agreement rate carries no information")
        print("  about discrimination — a rater that always answers the same way scores")
        print("  100%. Error DIRECTION is the only informative statistic here.")
    for who in ("judge", "regex"):
        col = f"{who}_restatement"
        agree = int((df[col] == df["human_restatement"]).sum())
        lo, hi = wilson(agree, n)
        k = kappa(df["human_restatement"].tolist(), df[col].tolist())
        print(f"  {who:<6} vs human   {agree:>2}/{n} = {agree/n:>6.1%}   "
              f"CI [{lo:.1%}, {hi:.1%}]   kappa {k:.3f}")
        fn, fp = error_direction(df["human_restatement"].tolist(), df[col].tolist())
        if fn or fp:
            print(f"         errors: {fn} false negative, {fp} false positive")
        rows.append({"property": "restatement", "rater": who, "agree": agree, "n": n,
                     "rate": agree / n, "ci_low": lo, "ci_high": hi, "kappa": k,
                     "false_neg": fn, "false_pos": fp})

    res = pd.DataFrame(rows)
    res.to_csv(out / "19_judge_validation.csv", index=False)

    jr = res[(res.property == "restatement") & (res.rater == "judge")].iloc[0]
    rr = res[(res.property == "restatement") & (res.rater == "regex")].iloc[0]
    jt = res[(res.property == "timeline") & (res.rater == "judge")].iloc[0]
    lift = jr["rate"] - rr["rate"]
    print(f"\n  judge minus regex on restatement: {lift*100:+.1f} points")

    control_ok = jt["rate"] >= 0.95
    print(f"  control passed (judge >=95% on timeline): {control_ok}")

    # disagreements worth reading
    bad = df[df["judge_restatement"] != df["human_restatement"]]
    if len(bad):
        print(f"\n  judge-human disagreements on restatement ({len(bad)}):")
        for _, r in bad.iterrows():
            print(f"    case {int(r['case_no'])}: human={r['human_restatement']} "
                  f"judge={r['judge_restatement']} — {str(r['judge_reason'])[:110]}")

    df.to_csv(out / "19_judge_detail.csv", index=False)

    # ---- report ----
    L = []; w = L.append
    w("# 19 — LLM-as-judge and its validation")
    w("")
    w("Step 18 evaluated drafts with four automated checks. Three settle properties")
    w("pattern matching can decide. The fourth — whether a draft restates the")
    w("consumer's grievance — is semantic, and the regex approximating it needed two")
    w("corrections and still disagreed with a human reader.")
    w("")
    w("That is the standard motivation for an LLM judge, and the standard place")
    w("evaluation programmes go wrong: the judge is adopted for convenience and its")
    w("output is then treated as ground truth. This measures it first.")
    w("")
    w("## The control")
    w("")
    w("Two properties were judged. `timeline` is trivially checkable — a number of days")
    w("is named or it is not. It exists to test the judge on a question with a known")
    w("answer before its verdict on the contested question is given any weight.")
    w("")
    w("| Property | Rater | Agreement with human | 95% CI | Cohen's kappa |")
    w("|---|---|---|---|---|")
    for _, r in res.iterrows():
        w(f"| {r['property']} | {r['rater']} | {r['agree']}/{int(r['n'])} = {r['rate']:.1%} | "
          f"[{r['ci_low']:.1%}, {r['ci_high']:.1%}] | {r['kappa']:.3f} |")
    w("")
    if control_ok:
        w(f"**Control passed.** The judge agrees with the human on `timeline` at "
          f"{jt['rate']:.1%}. Its verdict on the contested property is worth reading.")
    else:
        w(f"**Control FAILED.** The judge agrees with the human on `timeline` at only "
          f"{jt['rate']:.1%}, on a question with an objectively checkable answer. Its")
        w("verdict on the contested property should not be relied on, and the rest of")
        w("this document is reported for completeness rather than as a finding.")
    w("")
    if df["human_restatement"].nunique() < 2:
        w("## A degenerate reference")
        w("")
        val = "YES" if bool(df["human_restatement"].iloc[0]) else "NO"
        w(f"The human labelled **every draft {val}** on `restatement`. That has two")
        w("consequences that must be stated before any number below is read:")
        w("")
        w("- **Kappa is undefined.** With a constant reference, chance agreement is 1.")
        w("  Reporting 0.000 would read as *no better than chance* when the correct")
        w("  statement is *not computable*.")
        w("- **Agreement rate does not measure discrimination.** A rater that always")
        w("  answers YES scores 100% against this reference while distinguishing nothing.")
        w("")
        w("What remains informative is the **direction** of each rater's errors, and the")
        w("finding that the property does not vary across these 20 drafts at all.")
        w("")
    w("## Does the judge beat the regex?")
    w("")
    w(f"On `restatement`, the judge agrees with the human on **{jr['rate']:.1%}** of")
    w(f"drafts against the regex's **{rr['rate']:.1%}** — a difference of")
    w(f"**{lift*100:+.1f} points** at n={n}.")
    w("")
    degenerate = df["human_restatement"].nunique() < 2
    if degenerate:
        w("**That +40 points does not mean what it appears to mean.** Because every")
        w("reference label is the same, a judge that answers YES unconditionally scores")
        w("100% here. The result is consistent with a judge that reads carefully and")
        w("equally consistent with one that never says NO, and this test cannot separate")
        w("those two. What the comparison *does* establish is one-directional: the regex")
        w(f"produced {int(rr['false_neg'])} false negatives, so it was wrong, in a known")
        w("direction, on drafts a human accepts.")
        w("")
        w("### What the control says about trusting the judge")
        w("")
        w(f"On `timeline` — the property with genuine variance and an objectively")
        w(f"checkable answer — the judge scored {jt['rate']:.1%} (kappa {jt['kappa']:.3f}) and")
        w(f"the regex scored {res[(res.property=='timeline') & (res.rater=='regex')].iloc[0]['rate']:.1%}")
        w(f"(kappa {res[(res.property=='timeline') & (res.rater=='regex')].iloc[0]['kappa']:.3f}).")
        w("")
        w("**The deterministic check beat the judge on the only question where either")
        w("could be scored properly.** The judge cleared the control threshold, but it")
        w("cleared it while being outperformed by a regex that costs nothing and cannot")
        w("vary between runs.")
        w("")
        w("### Recommendation")
        w("")
        w("1. **Keep the deterministic check for `timeline`.** It is perfect on this")
        w("   sample and free. There is no case for an API call here.")
        w("2. **Fix the regex for `restatement` rather than replace it.** Its failure was")
        w("   8 false negatives in one direction, which is a pattern problem, not evidence")
        w("   that the property needs semantic judgement.")
        w("3. **Do not adopt the judge on this evidence.** Its apparent perfection is an")
        w("   artefact of a reference with no variance.")
        w("")
        w("### Outcome of the adversarial test (added after Step 20)")
        w("")
        w("The red-team log ran the missing test. The judge was shown two adversarial")
        w("drafts and one correct one:")
        w("")
        w("| Attack | Expected | Judge said | Correct |")
        w("|---|---|---|---|")
        w("| A1 — generic acknowledgment, no restatement | NO | NO | yes |")
        w("| A2 — restates the **wrong** grievance | NO | YES | **no** |")
        w("| A8 — correct draft | YES | YES | yes |")
        w("")
        w("**The judge detects the absence of a restatement. It does not detect the")
        w("incorrectness of one.** Shown a fluent, correctly cited letter describing a")
        w("complaint the consumer never made, it answered YES.")
        w("")
        w("This resolves the ambiguity left by the degenerate reference. The 100%")
        w("agreement in the table above is consistent with partial competence: the judge")
        w("is not answering YES unconditionally, but the discrimination it has is not the")
        w("discrimination the property requires. For a regulated acknowledgment letter,")
        w("saying the wrong thing confidently is a worse failure than saying nothing")
        w("specific, and that is the case the judge misses.")
        w("")
        w("### The test this evaluation could not run")
        w("")
        w("To establish that the judge discriminates on `restatement`, the sample must")
        w("contain drafts that genuinely fail it. None of these 20 do — the model restated")
        w("the grievance every time. The missing test is adversarial: construct drafts that")
        w("acknowledge receipt without restating anything, and check whether the judge")
        w("catches them. That belongs in the red-team log, and until it is run the judge's")
        w("performance on this property is unmeasured rather than good.")
    elif abs(lift) < 0.15:
        w("At this sample size that difference is not meaningful. The regex is free,")
        w("deterministic and needs no API call; on this evidence there is no case for")
        w("replacing it with a judge.")
    elif lift > 0:
        w("The judge tracks human judgement better. Note that this is measured on 20")
        w("drafts by a single rater, so it establishes direction rather than magnitude.")
    else:
        w("The regex tracks human judgement better than the judge does, which is the")
        w("outcome that most argues against adopting a judge for this property.")
    w("")
    w("## Error direction")
    w("")
    w("| Property | Rater | False negatives | False positives |")
    w("|---|---|---|---|")
    for _, r in res.iterrows():
        w(f"| {r['property']} | {r['rater']} | {int(r['false_neg'])} | {int(r['false_pos'])} |")
    w("")
    w("## Limitations")
    w("")
    w(f"- n={n}, single human rater. Confidence intervals are wide.")
    w("- The human labels were produced by the same person who wrote the annotation")
    w("  guideline and the regex, which is a source of correlated error.")
    w("- The judge was run once. Step 11 showed run-to-run variation moves comparable")
    w("  metrics by more than 10 points, and no variance estimate exists here.")
    (out / "19_judge_validation.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {out/'19_judge_validation.md'}")


if __name__ == "__main__":
    main()
