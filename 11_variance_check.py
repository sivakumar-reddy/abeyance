#!/usr/bin/env python3
"""
Project A — Step 11: Run-to-run variance
=========================================
`10_findings.md` §8 records an unmet limitation: Sonnet 5 does not accept a
temperature parameter, so run-to-run variation is possible, and the single
cached run in `08_llm.md` cannot support a confidence interval.

This script runs Intervention 1 three independent times against separate caches
and reports the spread on every headline metric. Where the spread is wide, the
corresponding number in §5 should be quoted as a range rather than a point.

It reuses the prompt and parser from `08_llm_classifier.py` by import, so there
is no second copy of the classification logic to drift out of sync.

Usage
-----
    python 11_variance_check.py --golden golden_set_v2.csv --outdir docs/
    python 11_variance_check.py --golden golden_set_v2.csv --outdir docs/ --runs 3
    python 11_variance_check.py --golden golden_set_v2.csv --outdir docs/ --offline
"""

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def load_classifier():
    """Import 08_llm_classifier.py despite the leading digit in its name."""
    path = HERE / "08_llm_classifier.py"
    if not path.exists():
        sys.exit(f"cannot find {path}")
    spec = importlib.util.spec_from_file_location("llm_clf", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def score_run(task, cache, clf):
    """Returns the headline metrics for one cached run."""
    have = task[task["case_no"].astype(int).isin(cache)].copy()
    have["pred"] = [cache[int(c)]["label"] for c in have["case_no"]]

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
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    clf = load_classifier()

    df = pd.read_csv(args.golden, encoding="utf-8-sig")
    df["gold"] = df["my_issue"].map(clf.ISSUE_TO_CLASS)
    task = df[df["gold"].notna()].copy()
    print(f"in-scope cases: {len(task)}   runs: {args.runs}")

    # Run 1 reuses the existing cache from step 08 — it is a valid independent
    # sample and re-calling it would only spend money to get another one.
    cache_paths = [Path("cache/08_llm_responses.jsonl")] + [
        Path(f"cache/11_run{i}.jsonl") for i in range(2, args.runs + 1)
    ]

    client = None
    results = []

    for run_idx, cpath in enumerate(cache_paths, 1):
        cpath.parent.mkdir(parents=True, exist_ok=True)
        cache = {}
        if cpath.exists():
            for line in cpath.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    r = json.loads(line)
                    cache[int(r["case_no"])] = r

        todo = [int(c) for c in task["case_no"] if int(c) not in cache]
        if todo and not args.offline:
            if client is None:
                try:
                    import anthropic
                except ImportError:
                    sys.exit("pip install anthropic")
                if not os.environ.get("ANTHROPIC_API_KEY"):
                    sys.exit("ANTHROPIC_API_KEY is not set")
                client = anthropic.Anthropic()
            print(f"\nrun {run_idx}: calling API for {len(todo)} cases -> {cpath.name}")
            with cpath.open("a", encoding="utf-8") as fh, \
                 cpath.with_name(f"11_run{run_idx}_failures.jsonl").open("a", encoding="utf-8") as flog:
                for i, case_no in enumerate(todo, 1):
                    narrative = task.loc[task["case_no"] == case_no, "narrative"].iloc[0]
                    if i % 10 == 1 or i == len(todo):
                        print(f"    [{i}/{len(todo)}] case {case_no}")
                    try:
                        out = clf.classify(client, args.model, narrative, failure_log=flog)
                    except clf.FatalAPIError as e:
                        print(f"\nFATAL: {e}")
                        sys.exit(1)
                    if out is None:
                        print(f"    FAILED case {case_no}")
                        continue
                    rec = {"case_no": int(case_no), **out}
                    fh.write(json.dumps(rec) + "\n"); fh.flush()
                    cache[int(case_no)] = rec
        elif todo:
            print(f"run {run_idx}: {len(todo)} cases missing and --offline set; scoring partial")

        m = score_run(task, cache, clf)
        m["run"] = run_idx
        m["cache"] = cpath.name
        results.append(m)
        print(f"run {run_idx}: n={m['n']}  acc={m['accuracy']:.1%}  "
              f"macroF1={m['macro_f1']:.3f}  abst_prec={m['abstention_precision']:.1%}")

    res = pd.DataFrame(results).set_index("run")
    metrics = ["accuracy", "accuracy_decided", "coverage", "macro_f1",
               "f1_ACCURACY", "f1_PERM", "f1_INVEST",
               "abstain_on_ambiguous", "abstain_on_clear", "abstention_precision"]

    summary = pd.DataFrame({
        "mean": res[metrics].mean(),
        "min": res[metrics].min(),
        "max": res[metrics].max(),
        "range": res[metrics].max() - res[metrics].min(),
        "sd": res[metrics].std(ddof=1),
    }).round(4)

    print("\n" + "=" * 62)
    print("variance across runs")
    print("=" * 62)
    print(summary.to_string())

    res.to_csv(outdir / "11_variance_runs.csv")
    summary.to_csv(outdir / "11_variance_summary.csv")

    # ---- report ----
    L = []; w = L.append
    w("# 11 — Run-to-run variance")
    w("")
    w(f"Intervention 1 re-run {args.runs} times against independent caches. Sonnet 5")
    w("does not accept a temperature parameter, so identical prompts can return")
    w("different labels. This quantifies how much.")
    w("")
    w("## Per run")
    w("")
    w("| Run | n | Accuracy | Macro-F1 | Coverage | Abstention precision |")
    w("|---|---|---|---|---|---|")
    for r, row in res.iterrows():
        w(f"| {r} | {int(row['n'])} | {row['accuracy']:.1%} | {row['macro_f1']:.3f} | "
          f"{row['coverage']:.1%} | {row['abstention_precision']:.1%} |")
    w("")
    w("## Spread")
    w("")
    w("| Metric | Mean | Min | Max | Range | SD |")
    w("|---|---|---|---|---|---|")
    for mname, row in summary.iterrows():
        w(f"| `{mname}` | {row['mean']:.3f} | {row['min']:.3f} | {row['max']:.3f} | "
          f"**{row['range']:.3f}** | {row['sd']:.3f} |")
    w("")
    w("## How to read this")
    w("")
    w("Where the range is comparable to the difference between systems reported in")
    w("`10_findings.md` §5, that difference is not established by a single run. The")
    w("keyword-to-LLM macro-F1 gap there is **0.078**; any metric whose range")
    w("approaches that magnitude should be quoted as an interval, and the")
    w("corresponding comparison re-stated as undetermined.")
    w("")
    w("Note that this measures sampling variance only. It does not address the")
    w("statistical power problem in §6, which is a property of the golden set size")
    w("and is unaffected by re-running the model.")
    (outdir / "11_variance.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {outdir/'11_variance.md'}")
    print(f"wrote {outdir/'11_variance_runs.csv'}")
    print(f"wrote {outdir/'11_variance_summary.csv'}")


if __name__ == "__main__":
    main()
