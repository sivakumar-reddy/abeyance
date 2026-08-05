# 17 — Cost model and risk-coverage economics

Completes the Phase 1 exit criterion and the Phase 6 operating-point analysis.

## What this model does and does not claim

Internal handling costs for a regulated complaint workflow are not public. This
model does **not** claim a measured cost per case. It names every input, sources
or flags each one, and reports the conclusion that survives the uncertainty:
**break-even precision** — the accuracy an automated router must reach before it
stops destroying value. Break-even depends on the *ratio* of rework cost to
handling cost rather than their absolute levels, which is why it holds up across
wide swings in the wage and time inputs.

## Assumptions

| Input | Value | Unit | Basis |
|---|---|---|---|
| `wage_hourly` | 38.69 | USD/hour | Sourced — BLS OEWS May 2025, SOC 13-1031 Claims adjusters, examiners and investigators, national mean hourly wage (n=324,230). Closest published occupation to a regulated complaint handler. |
| `loading_factor` | 1.4 | multiplier | Sourced — Fully-loaded cost multiplier covering benefits, payroll tax, facilities and supervision. Conventional planning range 1.25-1.60. |
| `route_minutes` | 6.0 | minutes/complaint | **ASSUMPTION** — ASSUMPTION. Time to read a narrative and select a queue. Median narrative is 700 characters; corpus mean is 1,207. Not measured. |
| `rework_minutes` | 22.0 | minutes/misrouted complaint | **ASSUMPTION** — ASSUMPTION. Detection, re-reading, re-queueing and the handling time already spent in the wrong queue. Modelled at roughly 3.7x the routing task. |
| `review_minutes` | 7.5 | minutes/abstained complaint | **ASSUMPTION** — ASSUMPTION. Reviewing a withheld case with two candidate labels and a stated reason presented. Modelled at 1.25x unaided routing: the context helps, but the withheld cases are the hard ones. |
| `inference_cost` | 0.004 | USD/complaint | **ASSUMPTION** — ASSUMPTION. One LLM call over a ~700-character narrative with a ~600-token system prompt. Swept two orders of magnitude below to demonstrate it is not the driver. |
| `manual_error_rate` | 0.294 | fraction | **MEASURED** — MEASURED. 1 - 0.706 intra-rater agreement on the uncontaminated blind re-label stratum (14_reliability.md). Used as the human routing error rate. |

## Current state

| | USD per case |
|---|---|
| Routing labour (6 min) | 5.42 |
| Rework at 29.4% human error rate | 5.84 |
| **Total** | **11.26** |

Fully-loaded rate $54.17/hour. The human
error rate is the one input taken from measurement rather than assumption: it is
1 minus the 70.6% intra-rater agreement recorded in `14_reliability.md`.

## Break-even precision

### **43.3%**

Across the extremes of the two dominant inputs the break-even ranges from
**-49.4% to 63.9%** (a negative figure means the labour saved exceeds
the total cost of being wrong, so any precision pays). Measured against the
central estimate:

| System | Measured accuracy | vs break-even | Verdict |
|---|---|---|---|
| Keyword baseline | 47.0% | +3.7 pts | Clears |
| LLM direct | 51.8% | +8.5 pts | Clears |
| Pairwise tournament | 44.6% | +1.3 pts | Clears |
| Majority class | 61.4% | +18.1 pts | Clears |

## Sensitivity

| Parameter | Range tested | Break-even range | Swing |
|---|---|---|---|
| `rework_minutes` | 10.0 – 45.0 | 10.6% – 57.3% | **46.6%** |
| `route_minutes` | 3.0 – 12.0 | 57.0% – 16.1% | **40.9%** |
| `manual_error_rate` | 0.133 – 0.531 | 59.4% – 19.6% | **39.8%** |
| `inference_cost` | 0.001 – 0.04 | 43.3% – 43.5% | **0.2%** |
| `wage_hourly` | 30.0 – 50.0 | 43.4% – 43.3% | **0.0%** |
| `loading_factor` | 1.25 – 1.6 | 43.3% – 43.3% | **0.0%** |
| `review_minutes` | 4.0 – 14.0 | 43.3% – 43.3% | **0.0%** |

`inference_cost` was swept two orders of magnitude and barely moves the
break-even. The economics of this workflow are set by labour and rework, not by
model cost. Any business case resting on cheap inference is answering the wrong
question.

## Operating point

48 of 62 operating points produce a positive saving.
Best: **74.7% coverage** at confidence threshold 0.35, precision 69.3%, saving **$3.51 per case**.

![Risk-coverage curve](17_risk_coverage.png)

## Comparison against the human ceiling

The headline intra-rater figure of 70.6% spans the full label space. The model
performs a three-class task, so the like-for-like comparator is human
self-agreement restricted to those same three classes:

| Comparator | Agreement | 95% CI | n |
|---|---|---|---|
| All labels, clean stratum | 70.6% | [46.9%, 86.7%] | 17 |
| **Three classes only, clean stratum** | **75.0%** | [46.8%, 91.1%] | 12 |
| Three classes only, all 25 | 80.0% | [58.4%, 91.9%] | 20 |

**Why two different human figures appear in this document.** The cost model
prices human error at 29.4% (i.e. 70.6% accuracy) because a human router handles
the entire workload, not just the three credit-reporting categories. The chart
comparator is 75.0% because the model is only asked to do the three-class task.
Both are correct at their own scope; using either in the other's place would be an
error.

Quoting 70.6% against a three-class precision curve would understate the bar the
model has to clear. The correct comparator is **75.0%**, and at n=12 its
confidence interval is wide enough that no claim of parity or shortfall is
supportable in either direction.

## Conclusion — and why cost is the wrong criterion here

Current-state routing costs **$11.26 per case**: $5.42 of
reading labour plus $5.84 of rework driven by a 29.4%
human error rate.

Break-even precision is **43.3%** — and every system built clears it, including
the keyword baseline that was pre-registered as a failure.

**That result is arithmetically correct and operationally wrong, and the gap
between those two things is the finding.**

Break-even sits well below the 70.6% human accuracy because automation
removes 6 minutes of reading labour from every case. A system
can be substantially *worse* than a person and still be *cheaper*, because it
stops paying someone to read. Cost-optimal and quality-optimal are different
operating points, and a model that prices errors purely as rework minutes will
always recommend the cheaper one.

### The shadow price

| | USD per misroute |
|---|---|
| Modelled as rework time only | 19.86 |
| Required for break-even to equal human accuracy | 38.27 |
| Multiple | **1.9x** |

For automation to need human-level accuracy before it pays, a misrouted complaint
must cost **$38.27** rather than $19.86 — roughly
1.9 times the rework time. Everything above rework is the
consequence the rework model does not price: regulatory exposure, delayed
resolution for a consumer already in financial distress, and complaint-handling
timeliness obligations.

### Recommendation

**Do not select an operating point on cost.** The decision turns on what a
misrouted complaint is deemed to cost, and that is a policy judgement for
Compliance, not an output of this model. The analysis produces the question in a
form that can be answered:

> Is a misrouted consumer complaint worth more or less than $38.27 to this
> organisation?

If more, no system built clears the bar and the workflow stays manual. If less,
cost favours automation — and the Phase 2 assessment already flagged failure cost
and regulatory exposure as the dimensions that should override a favourable cost
case for exactly this reason.

This is why the assessment ran before the build. The measurement cost a fraction
of the system, and it converts an open-ended build decision into one bounded
question for the people entitled to answer it.