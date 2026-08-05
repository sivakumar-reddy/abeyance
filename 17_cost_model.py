#!/usr/bin/env python3
"""
Project A — Step 17: Cost model and risk-coverage economics
============================================================
Completes the Phase 1 exit criterion (current-state cost per case, stated
defensibly) and Phase 6 (risk-coverage curve with a dollar axis and a
recommended operating point).

Approach
--------
Internal handling costs for a regulated complaint workflow are not public, so
this does not claim a measured cost. It builds a transparent parametric model
where every input is named and sourced, then reports the conclusion that is
ROBUST to the uncertainty: the break-even precision.

Break-even precision is the accuracy an automated router must reach before it
stops destroying value. It depends on the RATIO of rework cost to handling
cost, not on their absolute levels, which makes it stable across wide swings in
the wage and time assumptions. That is the number to defend in a room.

Usage
-----
    python 17_cost_model.py --outdir docs/
    python 17_cost_model.py --outdir docs/ --coverage docs/08_risk_coverage.csv
"""

import argparse
import json
from pathlib import Path

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAVE_PLT = True
except ImportError:
    HAVE_PLT = False


# ---------------------------------------------------------------------------
# Assumptions. Every one is named, sourced, and swept in the sensitivity table.
# ---------------------------------------------------------------------------
ASSUMPTIONS = {
    "wage_hourly": {
        "value": 38.69,
        "unit": "USD/hour",
        "source": "BLS OEWS May 2025, SOC 13-1031 Claims adjusters, examiners and "
                  "investigators, national mean hourly wage (n=324,230). Closest "
                  "published occupation to a regulated complaint handler.",
        "low": 30.00, "high": 50.00,
    },
    "loading_factor": {
        "value": 1.40,
        "unit": "multiplier",
        "source": "Fully-loaded cost multiplier covering benefits, payroll tax, "
                  "facilities and supervision. Conventional planning range 1.25-1.60.",
        "low": 1.25, "high": 1.60,
    },
    "route_minutes": {
        "value": 6.0,
        "unit": "minutes/complaint",
        "source": "ASSUMPTION. Time to read a narrative and select a queue. Median "
                  "narrative is 700 characters; corpus mean is 1,207. Not measured.",
        "low": 3.0, "high": 12.0,
    },
    "rework_minutes": {
        "value": 22.0,
        "unit": "minutes/misrouted complaint",
        "source": "ASSUMPTION. Detection, re-reading, re-queueing and the handling "
                  "time already spent in the wrong queue. Modelled at roughly 3.7x "
                  "the routing task.",
        "low": 10.0, "high": 45.0,
    },
    "review_minutes": {
        "value": 7.5,
        "unit": "minutes/abstained complaint",
        "source": "ASSUMPTION. Reviewing a withheld case with two candidate labels "
                  "and a stated reason presented. Modelled at 1.25x unaided routing: "
                  "the context helps, but the withheld cases are the hard ones.",
        "low": 4.0, "high": 14.0,
    },
    "inference_cost": {
        "value": 0.004,
        "unit": "USD/complaint",
        "source": "ASSUMPTION. One LLM call over a ~700-character narrative with a "
                  "~600-token system prompt. Swept two orders of magnitude below to "
                  "demonstrate it is not the driver.",
        "low": 0.001, "high": 0.040,
    },
    "manual_error_rate": {
        "value": 0.294,
        "unit": "fraction",
        "source": "MEASURED. 1 - 0.706 intra-rater agreement on the uncontaminated "
                  "blind re-label stratum (14_reliability.md). Used as the human "
                  "routing error rate.",
        "low": 0.133, "high": 0.531,
    },
}


def loaded_rate(a):
    return a["wage_hourly"] * a["loading_factor"] / 60.0        # USD per minute


def current_state(a):
    m = loaded_rate(a)
    handling = a["route_minutes"] * m
    rework = a["manual_error_rate"] * a["rework_minutes"] * m
    return {"handling": handling, "rework": rework, "total": handling + rework}


def automated(a, coverage, precision):
    """Cost per case when `coverage` of volume is routed automatically at `precision`."""
    m = loaded_rate(a)
    manual_total = current_state(a)["total"]
    auto = a["inference_cost"] + (1 - precision) * a["rework_minutes"] * m
    abstained = a["inference_cost"] + a["review_minutes"] * m + \
        a["manual_error_rate"] * a["rework_minutes"] * m
    return coverage * auto + (1 - coverage) * abstained, manual_total


def breakeven_precision(a):
    """Precision at which fully-covered automation equals the manual cost per case."""
    m = loaded_rate(a)
    manual_total = current_state(a)["total"]
    # inference + (1-p)*rework_min*m = manual_total
    return 1 - (manual_total - a["inference_cost"]) / (a["rework_minutes"] * m)


def flat(d):
    return {k: v["value"] for k, v in d.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--coverage", default="docs/08_risk_coverage.csv")
    args = ap.parse_args()
    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)

    a = flat(ASSUMPTIONS)
    cs = current_state(a)
    be = breakeven_precision(a)

    print("CURRENT STATE")
    print(f"  fully-loaded rate      ${a['wage_hourly'] * a['loading_factor']:.2f}/hour "
          f"(${loaded_rate(a):.4f}/minute)")
    print(f"  routing labour         ${cs['handling']:.2f}/case")
    print(f"  rework at {a['manual_error_rate']:.1%} error  ${cs['rework']:.2f}/case")
    print(f"  TOTAL                  ${cs['total']:.2f}/case")
    print(f"\nBREAK-EVEN PRECISION     {be:.1%}")

    # measured precision of each system, from 07/08/09
    systems = {
        "Keyword baseline": 0.470,
        "LLM direct": 0.518,
        "Pairwise tournament": 0.446,
        "Majority class": 0.614,
    }
    print("\nMEASURED ACCURACY vs BREAK-EVEN")
    verdicts = {}
    for name, p in systems.items():
        gap = p - be
        verdicts[name] = gap
        print(f"  {name:<22} {p:.1%}   {gap*100:+.1f} pts   "
              f"{'clears' if gap > 0 else 'DESTROYS VALUE'}")

    # ---- sensitivity on break-even ----
    print("\nSENSITIVITY — break-even precision")
    sens = []
    for k, spec in ASSUMPTIONS.items():
        lo_a, hi_a = dict(a), dict(a)
        lo_a[k], hi_a[k] = spec["low"], spec["high"]
        lo, hi = breakeven_precision(lo_a), breakeven_precision(hi_a)
        sens.append({"parameter": k, "low_input": spec["low"], "high_input": spec["high"],
                     "breakeven_at_low": lo, "breakeven_at_high": hi,
                     "swing": abs(hi - lo)})
    sens = pd.DataFrame(sens).sort_values("swing", ascending=False)
    for _, r in sens.iterrows():
        print(f"  {r['parameter']:<20} {r['breakeven_at_low']:>7.1%} .. "
              f"{r['breakeven_at_high']:>7.1%}   swing {r['swing']:.1%}")
    sens.to_csv(out / "17_sensitivity.csv", index=False)

    worst = breakeven_precision({**a, "rework_minutes": ASSUMPTIONS["rework_minutes"]["high"],
                                 "route_minutes": ASSUMPTIONS["route_minutes"]["low"]})
    best = breakeven_precision({**a, "rework_minutes": ASSUMPTIONS["rework_minutes"]["low"],
                                "route_minutes": ASSUMPTIONS["route_minutes"]["high"]})
    lo_be, hi_be = min(worst, best), max(worst, best)
    print(f"\n  break-even range across the extremes: {lo_be:.1%} .. {hi_be:.1%}")
    if lo_be < 0:
        print("    (a negative break-even means that under those inputs the labour saved")
        print("     exceeds the total cost of being wrong, so any precision pays)")
    lo_plot, hi_plot = max(0.0, lo_be), min(1.0, hi_be)

    # shadow price: what a misroute must cost for break-even to equal human accuracy
    m_ = loaded_rate(a)
    human_acc = 1 - a["manual_error_rate"]
    implied = (cs["total"] - a["inference_cost"]) / (1 - human_acc)
    modelled = a["rework_minutes"] * m_
    print(f"\nSHADOW PRICE OF A MISROUTE")
    print(f"  modelled as rework time only:            ${modelled:.2f}")
    print(f"  required for break-even = human {human_acc:.1%}:  ${implied:.2f}")
    print(f"  multiple: {implied/modelled:.1f}x")

    # ---- risk-coverage economics ----
    rc_path = Path(args.coverage)
    rc = None
    if rc_path.exists():
        rc = pd.read_csv(rc_path)
        rows = []
        for _, r in rc.iterrows():
            cost, manual = automated(a, r["coverage"], r["accuracy"])
            rows.append({"coverage": r["coverage"], "threshold": r["threshold"],
                         "precision": r["accuracy"], "cost_per_case": cost,
                         "manual_cost": manual, "saving": manual - cost})
        econ = pd.DataFrame(rows)
        econ.to_csv(out / "17_risk_coverage_economics.csv", index=False)
        pos = econ[econ["saving"] > 0]
        print(f"\nRISK-COVERAGE ECONOMICS  ({len(econ)} operating points)")
        if len(pos):
            bestop = pos.loc[pos["saving"].idxmax()]
            print(f"  operating points with positive saving: {len(pos)}/{len(econ)}")
            print(f"  best: coverage {bestop['coverage']:.1%} at threshold "
                  f"{bestop['threshold']:.2f}, precision {bestop['precision']:.1%}, "
                  f"saving ${bestop['saving']:.2f}/case")
        else:
            print("  NO operating point produces a positive saving.")
            print(f"  best available: ${econ['saving'].max():.2f}/case "
                  f"at coverage {econ.loc[econ['saving'].idxmax(), 'coverage']:.1%}")
    else:
        print(f"\n(no risk-coverage file at {rc_path}; skipping economics)")

    # ---- chart ----
    if HAVE_PLT and rc is not None:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax.plot(econ["coverage"] * 100, econ["precision"] * 100,
                lw=2, color="#1F3864", label="Achieved precision")
        ax.axhline(be * 100, ls="--", lw=1.8, color="#C00000",
                   label=f"Break-even precision ({be:.1%})")
        ax.axhspan(lo_plot * 100, hi_plot * 100, color="#C00000", alpha=0.10,
                   label=f"Break-even range ({lo_plot:.0%}–{hi_plot:.0%})")
        # Like-for-like comparator: human self-agreement restricted to the SAME
        # three-class task the model performs. The headline 70.6% figure spans the
        # full label space and is not comparable to a three-class precision curve.
        ax.axhline(75.0, ls=":", lw=1.8, color="#548235",
                   label="Human ceiling, 3-class (75.0%, n=12)")
        ax.axhspan(46.8, 91.1, color="#548235", alpha=0.07,
                   label="Human ceiling 95% CI")
        ax.set_xlabel("Coverage — share of volume routed automatically (%)")
        ax.set_ylabel("Precision (%)")
        ax.set_title("Risk-coverage curve against the break-even line", loc="left",
                     fontsize=13, weight="bold", color="#1F3864")
        ax.set_ylim(0, 100)
        ax.grid(alpha=.25)
        ax.legend(loc="lower left", fontsize=9, framealpha=.95)
        fig.tight_layout()
        fig.savefig(out / "17_risk_coverage.png", dpi=160)
        print(f"\nwrote {out/'17_risk_coverage.png'}")

    # ---- report ----
    L = []; w = L.append
    w("# 17 — Cost model and risk-coverage economics")
    w("")
    w("Completes the Phase 1 exit criterion and the Phase 6 operating-point analysis.")
    w("")
    w("## What this model does and does not claim")
    w("")
    w("Internal handling costs for a regulated complaint workflow are not public. This")
    w("model does **not** claim a measured cost per case. It names every input, sources")
    w("or flags each one, and reports the conclusion that survives the uncertainty:")
    w("**break-even precision** — the accuracy an automated router must reach before it")
    w("stops destroying value. Break-even depends on the *ratio* of rework cost to")
    w("handling cost rather than their absolute levels, which is why it holds up across")
    w("wide swings in the wage and time inputs.")
    w("")
    w("## Assumptions")
    w("")
    w("| Input | Value | Unit | Basis |")
    w("|---|---|---|---|")
    for k, s in ASSUMPTIONS.items():
        tag = "**MEASURED**" if s["source"].startswith("MEASURED") else (
            "**ASSUMPTION**" if s["source"].startswith("ASSUMPTION") else "Sourced")
        w(f"| `{k}` | {s['value']} | {s['unit']} | {tag} — {s['source']} |")
    w("")
    w("## Current state")
    w("")
    w("| | USD per case |")
    w("|---|---|")
    w(f"| Routing labour ({a['route_minutes']:.0f} min) | {cs['handling']:.2f} |")
    w(f"| Rework at {a['manual_error_rate']:.1%} human error rate | {cs['rework']:.2f} |")
    w(f"| **Total** | **{cs['total']:.2f}** |")
    w("")
    w(f"Fully-loaded rate ${a['wage_hourly'] * a['loading_factor']:.2f}/hour. The human")
    w("error rate is the one input taken from measurement rather than assumption: it is")
    w("1 minus the 70.6% intra-rater agreement recorded in `14_reliability.md`.")
    w("")
    w("## Break-even precision")
    w("")
    w(f"### **{be:.1%}**")
    w("")
    w(f"Across the extremes of the two dominant inputs the break-even ranges from")
    w(f"**{lo_be:.1%} to {hi_be:.1%}** (a negative figure means the labour saved exceeds")
    w("the total cost of being wrong, so any precision pays). Measured against the")
    w("central estimate:")
    w("")
    w("| System | Measured accuracy | vs break-even | Verdict |")
    w("|---|---|---|---|")
    for name, p in systems.items():
        g = verdicts[name]
        w(f"| {name} | {p:.1%} | {g*100:+.1f} pts | "
          f"{'Clears' if g > 0 else '**Destroys value**'} |")
    w("")
    w("## Sensitivity")
    w("")
    w("| Parameter | Range tested | Break-even range | Swing |")
    w("|---|---|---|---|")
    for _, r in sens.iterrows():
        w(f"| `{r['parameter']}` | {r['low_input']} – {r['high_input']} | "
          f"{r['breakeven_at_low']:.1%} – {r['breakeven_at_high']:.1%} | "
          f"**{r['swing']:.1%}** |")
    w("")
    w("`inference_cost` was swept two orders of magnitude and barely moves the")
    w("break-even. The economics of this workflow are set by labour and rework, not by")
    w("model cost. Any business case resting on cheap inference is answering the wrong")
    w("question.")
    w("")
    if rc is not None:
        w("## Operating point")
        w("")
        if len(pos):
            w(f"{len(pos)} of {len(econ)} operating points produce a positive saving.")
            w(f"Best: **{bestop['coverage']:.1%} coverage** at confidence threshold "
              f"{bestop['threshold']:.2f}, precision {bestop['precision']:.1%}, saving "
              f"**${bestop['saving']:.2f} per case**.")
        else:
            w("**No operating point produces a positive saving.** Sweeping the confidence")
            w("threshold across the full range never lifts precision above break-even at")
            w("any level of coverage. The recommendation is not a threshold; it is that")
            w("this workflow should not be automated on the evidence available.")
        w("")
        w("![Risk-coverage curve](17_risk_coverage.png)")
        w("")
    w("## Comparison against the human ceiling")
    w("")
    w("The headline intra-rater figure of 70.6% spans the full label space. The model")
    w("performs a three-class task, so the like-for-like comparator is human")
    w("self-agreement restricted to those same three classes:")
    w("")
    w("| Comparator | Agreement | 95% CI | n |")
    w("|---|---|---|---|")
    w("| All labels, clean stratum | 70.6% | [46.9%, 86.7%] | 17 |")
    w("| **Three classes only, clean stratum** | **75.0%** | [46.8%, 91.1%] | 12 |")
    w("| Three classes only, all 25 | 80.0% | [58.4%, 91.9%] | 20 |")
    w("")
    w("**Why two different human figures appear in this document.** The cost model")
    w("prices human error at 29.4% (i.e. 70.6% accuracy) because a human router handles")
    w("the entire workload, not just the three credit-reporting categories. The chart")
    w("comparator is 75.0% because the model is only asked to do the three-class task.")
    w("Both are correct at their own scope; using either in the other's place would be an")
    w("error.")
    w("")
    w("Quoting 70.6% against a three-class precision curve would understate the bar the")
    w("model has to clear. The correct comparator is **75.0%**, and at n=12 its")
    w("confidence interval is wide enough that no claim of parity or shortfall is")
    w("supportable in either direction.")
    w("")
    w("## Conclusion — and why cost is the wrong criterion here")
    w("")
    w(f"Current-state routing costs **${cs['total']:.2f} per case**: ${cs['handling']:.2f} of")
    w(f"reading labour plus ${cs['rework']:.2f} of rework driven by a {a['manual_error_rate']:.1%}")
    w("human error rate.")
    w("")
    w(f"Break-even precision is **{be:.1%}** — and every system built clears it, including")
    w("the keyword baseline that was pre-registered as a failure.")
    w("")
    w("**That result is arithmetically correct and operationally wrong, and the gap")
    w("between those two things is the finding.**")
    w("")
    w(f"Break-even sits well below the {human_acc:.1%} human accuracy because automation")
    w(f"removes {a['route_minutes']:.0f} minutes of reading labour from every case. A system")
    w("can be substantially *worse* than a person and still be *cheaper*, because it")
    w("stops paying someone to read. Cost-optimal and quality-optimal are different")
    w("operating points, and a model that prices errors purely as rework minutes will")
    w("always recommend the cheaper one.")
    w("")
    w("### The shadow price")
    w("")
    w("| | USD per misroute |")
    w("|---|---|")
    w(f"| Modelled as rework time only | {modelled:.2f} |")
    w(f"| Required for break-even to equal human accuracy | {implied:.2f} |")
    w(f"| Multiple | **{implied/modelled:.1f}x** |")
    w("")
    w(f"For automation to need human-level accuracy before it pays, a misrouted complaint")
    w(f"must cost **${implied:.2f}** rather than ${modelled:.2f} — roughly")
    w(f"{implied/modelled:.1f} times the rework time. Everything above rework is the")
    w("consequence the rework model does not price: regulatory exposure, delayed")
    w("resolution for a consumer already in financial distress, and complaint-handling")
    w("timeliness obligations.")
    w("")
    w("### Recommendation")
    w("")
    w("**Do not select an operating point on cost.** The decision turns on what a")
    w("misrouted complaint is deemed to cost, and that is a policy judgement for")
    w("Compliance, not an output of this model. The analysis produces the question in a")
    w("form that can be answered:")
    w("")
    w(f"> Is a misrouted consumer complaint worth more or less than ${implied:.2f} to this")
    w("> organisation?")
    w("")
    w(f"If more, no system built clears the bar and the workflow stays manual. If less,")
    w("cost favours automation — and the Phase 2 assessment already flagged failure cost")
    w("and regulatory exposure as the dimensions that should override a favourable cost")
    w("case for exactly this reason.")
    w("")
    w("This is why the assessment ran before the build. The measurement cost a fraction")
    w("of the system, and it converts an open-ended build decision into one bounded")
    w("question for the people entitled to answer it.")
    (out / "17_cost_model.md").write_text("\n".join(L), encoding="utf-8")
    (out / "17_assumptions.json").write_text(json.dumps(ASSUMPTIONS, indent=2))
    print(f"wrote {out/'17_cost_model.md'}")


if __name__ == "__main__":
    main()
