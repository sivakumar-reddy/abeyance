#!/usr/bin/env python3
"""
Project A — Step 22: Few-shot, class prior, and self-consistency
=================================================================
`10_findings.md` §5 records three systems, none of which beat the 61.4%
majority-class baseline. Before concluding that the task is unlearnable at this
label quality, the three cheapest and most commonly recommended prompt
interventions are tested, stacked, so that each one's contribution is separable.

    A  baseline          rule-only prompt, zero-shot        (reuses 08 cache)
    B  + few-shot        k-fold examples, no leakage
    C  + class prior     empirical prior from training folds only
    D  + self-consistency  three samples of C, majority vote

Design commitments
------------------
* Few-shot examples are drawn ONLY from training folds. A case is never shown an
  example of itself, and the fold's prior is computed from training folds too.
  Without this the result is leakage dressed as improvement.
* Condition A is not re-run. The 08 cache is a valid sample of that condition and
  re-calling it would spend money to obtain a second one.
* Condition D reuses C as its first vote for the same reason. Only votes 2 and 3
  are new calls.
* `abstain` labels ARE shown in few-shot examples, which 08 deliberately withheld.
  That is the intervention: the question is whether demonstrating abstention
  teaches it. Abstention metrics on held-out folds remain honest because the test
  fold is never in the prompt, but this is a different measurement from 08 and is
  reported as such.
* Every comparison against the baseline is an exact binomial test, and every
  comparison between conditions is an exact McNemar test on the same cases. The
  §6 power problem is not solved by any of this and is restated in the output.

Cost
----
Roughly 332 calls at default settings: 83 for B, 83 for C, 166 for D's two extra
votes. Condition A is free.

Usage
-----
    python 22_fewshot.py --golden golden_set_v2.csv --outdir docs/
    python 22_fewshot.py --golden golden_set_v2.csv --outdir docs/ --offline
    python 22_fewshot.py --golden golden_set_v2.csv --outdir docs/ --folds 5 --shots 8
"""

import argparse
import importlib.util
import json
import math
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SEED = 42


# --------------------------------------------------------------------------
# reuse the step 08 harness rather than copying it
# --------------------------------------------------------------------------

def load_classifier():
    """Import 08_llm_classifier.py despite the leading digit in its name."""
    path = HERE / "08_llm_classifier.py"
    if not path.exists():
        sys.exit(f"cannot find {path}")
    spec = importlib.util.spec_from_file_location("llm_clf", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# folds
# --------------------------------------------------------------------------

def stratified_folds(task, k, seed=SEED):
    """Assign each case to one of k folds, stratified on gold label.

    Stratification matters here: with 51/16/16 support, an unstratified split
    can leave a fold with two cases of a minority class, and the per-class F1
    for that fold becomes noise.
    """
    rng = random.Random(seed)
    fold_of = {}
    for label in sorted(task["gold"].unique()):
        cases = sorted(int(c) for c in task.loc[task["gold"] == label, "case_no"])
        rng.shuffle(cases)
        for i, c in enumerate(cases):
            fold_of[c] = i % k
    return fold_of


# --------------------------------------------------------------------------
# prompt construction
# --------------------------------------------------------------------------

def pick_examples(train, n_shots, seed=SEED):
    """Stratified example selection from the training folds.

    Aims for an even spread across the three classes plus abstention, because
    an example set that mirrors the 61/19/19 prior would simply demonstrate
    the majority class and reinforce the failure mode being tested.
    """
    rng = random.Random(seed)
    per_bucket = max(1, n_shots // 4)
    picked = []

    for label in ["ACCURACY", "PERMISSIBLE-PURPOSE", "INVESTIGATION"]:
        pool = train[(train["gold"] == label) & (train["abstain"] != "ABSTAIN")]
        pool = pool.to_dict("records")
        rng.shuffle(pool)
        picked.extend(pool[:per_bucket])

    abstain_pool = train[train["abstain"] == "ABSTAIN"].to_dict("records")
    rng.shuffle(abstain_pool)
    picked.extend(abstain_pool[:per_bucket])

    rng.shuffle(picked)
    return picked[:n_shots]


def example_messages(examples, max_chars=800):
    """Few-shot examples as alternating user/assistant turns.

    Turns rather than a system-prompt block: the model is being shown the shape
    of the exchange it is about to be asked for, not told about it.
    """
    msgs = []
    for ex in examples:
        narrative = str(ex["narrative"])[:max_chars]
        label = "ABSTAIN" if ex["abstain"] == "ABSTAIN" else ex["gold"]
        answer = {
            "label": label,
            "confidence": 0.9 if label != "ABSTAIN" else 0.5,
            "counterfactual": str(ex.get("decisive_signal") or "")[:200],
            "competing": "" if label != "ABSTAIN" else "two theories survive independently",
        }
        msgs.append({"role": "user", "content": f"<complaint>\n{narrative}\n</complaint>"})
        msgs.append({"role": "assistant", "content": json.dumps(answer)})
    return msgs


def prior_block(train):
    """Empirical class prior, computed from training folds only."""
    counts = Counter(train["gold"])
    total = sum(counts.values())
    lines = ["", "BASE RATES IN THIS CORPUS", ""]
    for label in ["ACCURACY", "PERMISSIBLE-PURPOSE", "INVESTIGATION"]:
        lines.append(f"{label}: {counts.get(label, 0) / total:.0%}")
    lines.append("")
    lines.append(
        "These are the observed frequencies, not a licence to guess the largest "
        "class. Depart from the prior whenever the counterfactual test points "
        "elsewhere, and abstain when two theories survive it."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# API call, structured like clf.classify but accepting few-shot turns
# --------------------------------------------------------------------------

def call(client, model, system, shots, narrative, clf, retries=3, failure_log=None):
    last_raw = ""
    messages = list(shots) + [
        {"role": "user", "content": f"<complaint>\n{str(narrative)[:20000]}\n</complaint>"}
    ]
    for attempt in range(retries):
        try:
            resp = client.messages.create(
                model=model, max_tokens=1000, system=system, messages=messages,
            )
            raw = "".join(b.text for b in resp.content if b.type == "text")
            out = clf.parse(raw)
            if out:
                return out
            last_raw = raw
            print(f"    unparseable response, retry {attempt + 1}")
        except Exception as e:
            status = getattr(e, "status_code", None)
            if status in (400, 401, 403, 404):
                raise clf.FatalAPIError(f"HTTP {status}: {e}") from None
            wait = 2 ** attempt
            print(f"    {type(e).__name__} ({status}): {str(e)[:160]}")
            print(f"    retry in {wait}s")
            time.sleep(wait)
    if failure_log is not None and last_raw:
        failure_log.write(json.dumps({"raw": last_raw[:4000]}) + "\n")
        failure_log.flush()
    return None


def run_condition(task, fold_of, clf, args, name, cache_path,
                  use_shots, use_prior, client_holder):
    """Score one condition across all folds, caching per case."""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = {}
    if cache_path.exists():
        for line in cache_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                cache[int(r["case_no"])] = r

    todo = [int(c) for c in task["case_no"] if int(c) not in cache]
    if todo and args.offline:
        print(f"{name}: {len(todo)} cases missing and --offline set; scoring partial")
    elif todo:
        if client_holder[0] is None:
            try:
                import anthropic
            except ImportError:
                sys.exit("pip install anthropic")
            if not os.environ.get("ANTHROPIC_API_KEY"):
                sys.exit("ANTHROPIC_API_KEY is not set")
            client_holder[0] = anthropic.Anthropic()
        client = client_holder[0]

        print(f"\n{name}: calling API for {len(todo)} cases -> {cache_path.name}")
        flog = cache_path.with_name(cache_path.stem + "_failures.jsonl")
        with cache_path.open("a", encoding="utf-8") as fh, \
             flog.open("a", encoding="utf-8") as flogf:
            for i, case_no in enumerate(todo, 1):
                fold = fold_of[case_no]
                train = task[task["case_no"].astype(int).map(fold_of) != fold]

                system = clf.SYSTEM
                if use_prior:
                    system = system + "\n" + prior_block(train)

                shots = []
                if use_shots:
                    # seed varies by fold so folds do not share an example set,
                    # but is deterministic so the run is reproducible
                    ex = pick_examples(train, args.shots, seed=SEED + fold)
                    shots = example_messages(ex)

                narrative = task.loc[task["case_no"] == case_no, "narrative"].iloc[0]
                if i % 10 == 1 or i == len(todo):
                    print(f"    [{i}/{len(todo)}] case {case_no} (fold {fold})")
                try:
                    out = call(client, args.model, system, shots, narrative, clf,
                               failure_log=flogf)
                except clf.FatalAPIError as e:
                    print(f"\nFATAL: {e}")
                    print(f"Aborting. Cache holds {len(cache)} good responses.")
                    sys.exit(1)
                if out is None:
                    print(f"    FAILED case {case_no}, skipping")
                    continue
                rec = {"case_no": int(case_no), "fold": fold, **out}
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                cache[int(case_no)] = rec
    return cache


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------

def binom_sf(k, n, p):
    """P(X >= k) for X ~ Binomial(n, p). Exact, no scipy dependency."""
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def mcnemar_exact(a_correct, b_correct):
    """Two-sided exact McNemar on paired correctness vectors."""
    b = sum(1 for x, y in zip(a_correct, b_correct) if x and not y)
    c = sum(1 for x, y in zip(a_correct, b_correct) if y and not x)
    n = b + c
    if n == 0:
        return b, c, 1.0
    k = min(b, c)
    p = 2 * sum(math.comb(n, i) * 0.5 ** n for i in range(0, k + 1))
    return b, c, min(1.0, p)


def bootstrap_ci(correct, reps=10000, seed=SEED):
    rng = random.Random(seed)
    n = len(correct)
    means = []
    for _ in range(reps):
        means.append(sum(rng.choice(correct) for _ in range(n)) / n)
    means.sort()
    return means[int(0.025 * reps)], means[int(0.975 * reps)]


def score(task, preds, clf):
    have = task[task["case_no"].astype(int).isin(preds)].copy()
    if len(have) == 0:
        return None
    have["pred"] = [preds[int(c)] for c in have["case_no"]]

    decided = have[have["pred"] != "ABSTAIN"]
    amb = have[have["abstain"] == "ABSTAIN"]
    clear = have[have["abstain"] != "ABSTAIN"]
    n_abst = max(1, len(have[have["pred"] == "ABSTAIN"]))
    f1s = [clf.prf(have["gold"], have["pred"], c)[2] for c in clf.CLASSES]

    return {
        "n": len(have),
        "accuracy": (have["pred"] == have["gold"]).mean(),
        "accuracy_decided": (decided["pred"] == decided["gold"]).mean() if len(decided) else float("nan"),
        "coverage": len(decided) / len(have),
        "macro_f1": sum(f1s) / len(f1s),
        "f1_ACCURACY": f1s[0],
        "f1_PERM": f1s[1],
        "f1_INVEST": f1s[2],
        "abstain_on_ambiguous": (amb["pred"] == "ABSTAIN").mean() if len(amb) else float("nan"),
        "abstain_on_clear": (clear["pred"] == "ABSTAIN").mean() if len(clear) else float("nan"),
        "abstention_precision": len(amb[amb["pred"] == "ABSTAIN"]) / n_abst,
        "_correct": list((have["pred"] == have["gold"]).astype(int)),
        "_cases": [int(c) for c in have["case_no"]],
    }


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--shots", type=int, default=8)
    ap.add_argument("--votes", type=int, default=3)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    clf = load_classifier()

    df = pd.read_csv(args.golden, encoding="utf-8-sig")
    df["gold"] = df["my_issue"].map(clf.ISSUE_TO_CLASS)
    task = df[df["gold"].notna()].copy()
    task["case_no"] = task["case_no"].astype(int)

    majority = task["gold"].value_counts().idxmax()
    maj_rate = (task["gold"] == majority).mean()
    print(f"in-scope cases: {len(task)}   folds: {args.folds}   shots: {args.shots}")
    print(f"majority class {majority}: {maj_rate:.1%}")

    fold_of = stratified_folds(task, args.folds)
    sizes = Counter(fold_of.values())
    print(f"fold sizes: {[sizes[i] for i in range(args.folds)]}")

    client_holder = [None]

    # ---- A: baseline, from the existing 08 cache ----
    base_cache = {}
    p = Path("cache/08_llm_responses.jsonl")
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                base_cache[int(r["case_no"])] = r
    else:
        sys.exit("cache/08_llm_responses.jsonl not found; run 08 first")
    print(f"A baseline: {len(base_cache)} cached responses reused, 0 new calls")

    conditions = {}
    conditions["A_baseline"] = {int(k): v["label"] for k, v in base_cache.items()}

    # ---- B: few-shot ----
    cb = run_condition(task, fold_of, clf, args, "B_fewshot",
                       Path("cache/22_B_fewshot.jsonl"), True, False, client_holder)
    conditions["B_fewshot"] = {int(k): v["label"] for k, v in cb.items()}

    # ---- C: few-shot + prior ----
    cc = run_condition(task, fold_of, clf, args, "C_fewshot_prior",
                       Path("cache/22_C_prior.jsonl"), True, True, client_holder)
    conditions["C_fewshot_prior"] = {int(k): v["label"] for k, v in cc.items()}

    # ---- D: self-consistency over C ----
    votes = [cc]
    for v in range(2, args.votes + 1):
        cv = run_condition(task, fold_of, clf, args, f"D_vote{v}",
                           Path(f"cache/22_D_vote{v}.jsonl"), True, True, client_holder)
        votes.append(cv)

    d_pred = {}
    d_split = 0
    for c in task["case_no"]:
        c = int(c)
        labels = [v[c]["label"] for v in votes if c in v]
        if not labels:
            continue
        tally = Counter(labels).most_common()
        if len(tally) > 1 and tally[0][1] == tally[1][1]:
            d_split += 1
            d_pred[c] = votes[0][c]["label"] if c in votes[0] else tally[0][0]
        else:
            d_pred[c] = tally[0][0]
    conditions["D_selfconsistency"] = d_pred
    print(f"\nD: {d_split} cases had no majority across {len(votes)} votes "
          f"(broke toward vote 1)")

    # ---- score ----
    scored = {}
    for name, preds in conditions.items():
        m = score(task, preds, clf)
        if m is None:
            print(f"skipping {name}: no cached responses")
            continue
        scored[name] = m
    if not scored:
        sys.exit("no condition has any responses; nothing to score")

    rows = []
    for name, m in scored.items():
        lo, hi = bootstrap_ci(m["_correct"])
        k = sum(m["_correct"])
        rows.append({
            "condition": name,
            "n": m["n"],
            "accuracy": round(m["accuracy"], 4),
            "ci_lo": round(lo, 4),
            "ci_hi": round(hi, 4),
            "vs_majority_p": round(binom_sf(k, m["n"], maj_rate), 4),
            "beats_majority": bool(m["accuracy"] > maj_rate),
            "macro_f1": round(m["macro_f1"], 4),
            "coverage": round(m["coverage"], 4),
            "abstention_precision": round(m["abstention_precision"], 4),
            "abstain_on_ambiguous": round(m["abstain_on_ambiguous"], 4),
            "abstain_on_clear": round(m["abstain_on_clear"], 4),
        })
    res = pd.DataFrame(rows)

    print("\n" + "=" * 78)
    print(f"ablation against the {maj_rate:.1%} majority-class baseline")
    print("=" * 78)
    print(res.to_string(index=False))

    # ---- paired tests between adjacent conditions ----
    order = [c for c in ["A_baseline", "B_fewshot", "C_fewshot_prior",
                         "D_selfconsistency"] if c in scored]
    pairs = []
    for i in range(len(order) - 1):
        a, b = order[i], order[i + 1]
        common = sorted(set(scored[a]["_cases"]) & set(scored[b]["_cases"]))
        av = [scored[a]["_correct"][scored[a]["_cases"].index(c)] for c in common]
        bv = [scored[b]["_correct"][scored[b]["_cases"].index(c)] for c in common]
        nb, nc, pv = mcnemar_exact(av, bv)
        pairs.append({"comparison": f"{a} -> {b}", "n_paired": len(common),
                      "a_only_correct": nb, "b_only_correct": nc,
                      "mcnemar_p": round(pv, 4)})
    # A vs D as well, since that is the headline question
    if "A_baseline" in scored and "D_selfconsistency" in scored:
        common = sorted(set(scored["A_baseline"]["_cases"]) & set(scored["D_selfconsistency"]["_cases"]))
        av = [scored["A_baseline"]["_correct"][scored["A_baseline"]["_cases"].index(c)] for c in common]
        bv = [scored["D_selfconsistency"]["_correct"][scored["D_selfconsistency"]["_cases"].index(c)] for c in common]
        nb, nc, pv = mcnemar_exact(av, bv)
        pairs.append({"comparison": "A_baseline -> D_selfconsistency", "n_paired": len(common),
                      "a_only_correct": nb, "b_only_correct": nc, "mcnemar_p": round(pv, 4)})

    pair_df = pd.DataFrame(pairs) if pairs else pd.DataFrame(
        columns=["comparison", "n_paired", "a_only_correct", "b_only_correct", "mcnemar_p"])

    print("\npaired comparisons (exact McNemar)")
    print(pair_df.to_string(index=False) if len(pair_df) else "  (only one condition scored)")

    res.to_csv(outdir / "22_ablation.csv", index=False)
    pair_df.to_csv(outdir / "22_paired_tests.csv", index=False)

    per_case = pd.DataFrame({"case_no": task["case_no"], "gold": task["gold"],
                             "abstain": task["abstain"],
                             "fold": [fold_of[int(c)] for c in task["case_no"]]})
    for name in scored:
        preds = conditions[name]
        per_case[name] = [preds.get(int(c), "") for c in task["case_no"]]
    per_case.to_csv(outdir / "22_predictions.csv", index=False, encoding="utf-8")

    # ---- report ----
    L = []; w = L.append
    w("# 22 — Few-shot, class prior, and self-consistency")
    w("")
    w(f"Three prompt interventions stacked and tested against the {maj_rate:.1%} "
      "majority-class")
    w("baseline recorded in `10_findings.md` §5. Examples and priors are drawn from")
    w(f"training folds only across {args.folds} stratified folds, so no case "
      "contributes to its own")
    w("prompt.")
    w("")
    w("## Conditions")
    w("")
    w("| | Prompt | New calls |")
    w("|---|---|---|")
    w("| A | rule only, zero-shot | 0, reuses the step 08 cache |")
    w(f"| B | rule + {args.shots} few-shot examples | {len(task)} |")
    w("| C | rule + few-shot + empirical class prior | " + str(len(task)) + " |")
    w(f"| D | C sampled {args.votes} times, majority vote | "
      f"{len(task) * (args.votes - 1)} |")
    w("")
    w("## Result")
    w("")
    w("| Condition | n | Accuracy | 95% CI | p vs majority | Macro-F1 | Coverage | Abstention precision |")
    w("|---|---|---|---|---|---|---|---|")
    for _, r in res.iterrows():
        w(f"| {r['condition']} | {int(r['n'])} | {r['accuracy']:.1%} | "
          f"{r['ci_lo']:.1%} to {r['ci_hi']:.1%} | {r['vs_majority_p']:.3f} | "
          f"{r['macro_f1']:.3f} | {r['coverage']:.1%} | {r['abstention_precision']:.1%} |")
    w("")
    w(f"Majority-class baseline: **{maj_rate:.1%}** ({majority}).")
    w("")
    w("## Did any single change do the work")
    w("")
    w("| Comparison | Paired n | Only first correct | Only second correct | McNemar p |")
    w("|---|---|---|---|---|")
    for _, r in pair_df.iterrows():
        w(f"| {r['comparison']} | {int(r['n_paired'])} | {int(r['a_only_correct'])} | "
          f"{int(r['b_only_correct'])} | {r['mcnemar_p']:.3f} |")
    w("")
    w("## Abstention")
    w("")
    w("Step 08 withheld the `abstain` column from the model entirely. Here it is")
    w("demonstrated in the few-shot examples drawn from training folds, which makes")
    w("this a different measurement rather than a continuation of the same one. The")
    w("held-out fold is never in the prompt, so the metric is honest, but it answers")
    w("a narrower question: whether abstention can be taught by demonstration, not")
    w("whether it emerges from the rule alone.")
    w("")
    w("| Condition | Abstains on guideline-ABSTAIN | Abstains on clear | Precision |")
    w("|---|---|---|---|")
    for _, r in res.iterrows():
        w(f"| {r['condition']} | {r['abstain_on_ambiguous']:.1%} | "
          f"{r['abstain_on_clear']:.1%} | {r['abstention_precision']:.1%} |")
    w("")
    w("## What this does not settle")
    w("")
    w("The power problem in `10_findings.md` §6 is a property of the golden set")
    w(f"size, not of the prompt. With {len(task)} cases and roughly 16 genuinely")
    w("ambiguous ones, a real difference in abstention behaviour would still be")
    w("undetectable at conventional power. A condition that appears to improve here")
    w("and carries a McNemar p above 0.05 is undetermined, not better.")
    w("")
    w("## Files")
    w("")
    w("- `22_ablation.csv` — headline metrics per condition with bootstrap intervals")
    w("- `22_paired_tests.csv` — exact McNemar between adjacent conditions")
    w("- `22_predictions.csv` — per-case predictions under all four conditions")
    (outdir / "22_fewshot.md").write_text("\n".join(L), encoding="utf-8")

    print(f"\nwrote {outdir/'22_fewshot.md'}")
    print(f"wrote {outdir/'22_ablation.csv'}")
    print(f"wrote {outdir/'22_paired_tests.csv'}")
    print(f"wrote {outdir/'22_predictions.csv'}")


if __name__ == "__main__":
    main()
