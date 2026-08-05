# 21 — Governance Package

**Model card, failure taxonomy, monitoring plan and rollback triggers**

| | |
|---|---|
| System | Complaint issue triage and acknowledgment drafting |
| Version | v0.1 — evaluation build, **not approved for deployment** |
| Owner | Sivakumar Reddy Yenna |
| Date | August 2026 |
| Status | Assessment complete; build decision open (see `12_brd.md` §9) |

---

## 1. Model card

### 1.1 Intended use

**In scope.** Routing credit-reporting complaints that contain a free-text
narrative into three grievance categories, with mandatory abstention on
ambiguous cases; and drafting acknowledgment letters for human approval.

**Out of scope.** The other twelve product categories. The full 89-issue
taxonomy. Any output reaching a consumer without human approval. Severity
scoring, UDAAP detection, dispute prediction and autonomous resolution — all
four assessed and recommended against in `15_opportunity_assessment.md`.

**Never appropriate.** Deciding the outcome of a complaint. Communicating with a
consumer unreviewed. Training on the intake issue labels.

### 1.2 Performance

| Metric | Value | Source |
|---|---|---|
| Accuracy, 3-class routing | 51.8% [49.4–54.2] | `08`, `11` |
| Macro-F1 | 0.549 [0.525–0.571] | `08`, `11` |
| Majority-class baseline | 61.4% | `07` |
| Human ceiling, like-for-like 3-class | 75.0% [46.8–91.1], n=12 | `14`, `17` |
| Coverage at best operating point | 74.7% | `17` |
| Precision at that point | 69.3% | `17` |
| Draft groundedness — citations | 20/20 | `18` |
| Draft groundedness — no fabricated figures | 20/20 | `18` |
| Draft groundedness — no overcommitment | 20/20 | `18` |
| Draft required elements | 6/20 | `18` |

**The system does not beat always guessing the largest class on accuracy.** It
beats the keyword baseline on macro-F1, and that is the only system comparison
in this programme that survives its own error bars.

### 1.3 Disaggregation

| Class | n | Precision | Recall | F1 |
|---|---|---|---|---|
| ACCURACY | 51 | 0.763 | 0.569 | 0.652 |
| PERMISSIBLE-PURPOSE | 16 | 0.571 | 0.500 | 0.533 |
| INVESTIGATION | 16 | 0.600 | 0.375 | 0.462 |

INVESTIGATION is the weakest class in every system tested. It is the only class
with a two-part condition — a prior dispute must exist **and** the complaint must
be about its handling. All systems detect the first half and miss the second.

No disaggregation by consumer demographic is possible or attempted: the corpus
carries no protected-characteristic fields. **This is a limitation, not a
clearance.** A deployed system would require geographic and product-mix
disaggregation as a proxy check before any fair-lending assurance could be given.

### 1.4 Training and evaluation data

Evaluation is against 100 hand-labelled narratives drawn seeded from 2,312,146
in-window complaints. No model was trained; both interventions are prompted.
The intake labels are **not** used as a scoring target, because they agree with
expert reading only 46.0% of the time.

### 1.5 Known limitations

- Statistical power to detect the abstention effect: **28%**
- Run-to-run variation moves the key abstention metric by **12.5 points**
- Intra-rater reliability 70.6%, CI lower bound clears the comparison by 0.9 pts
- Single labeller throughout; correlated error is unquantified
- Sonnet 5 accepts no temperature parameter; determinism cannot be enforced

---

## 2. Failure taxonomy

Categorised from `07`, `08`, `09`, `18` and `20`. Counts are from the evaluation
sample and are indicative, not rates.

### Class R — Routing failures

| ID | Failure | Observed | Detectable pre-deployment? |
|---|---|---|---|
| R1 | Confuses the three credit-reporting categories | 24/83 | Yes — golden set |
| R2 | Misses INVESTIGATION's second condition | 10/16 | Yes — per-class recall |
| R3 | Abstains on a separable case | 16/67 | Yes — guideline labels |
| R4 | Routes a case the guideline marks unresolvable | 11/16 | Yes — guideline labels |

**R4 is the highest-severity routing failure.** A confident label on a genuinely
two-headed complaint is worse than an abstention, because it removes the human
who would have caught it.

### Class D — Drafting failures

| ID | Failure | Observed | Caught by harness? |
|---|---|---|---|
| D1 | Hedged timeline — "the timeframe required by applicable law" | 9/20 | Yes |
| D2 | Fabricated figure in digits | 0/20 | Yes |
| D3 | Fabricated figure spelled out | Red-team A4 | Yes, after fix |
| D4 | Citation not in retrieved context | 0/20 | Yes |
| D5 | Direct overcommitment | 0/20 | Yes |
| D6 | Indirect overcommitment — "we anticipate a favourable resolution" | Red-team A3 | Yes, after fix |
| D7 | Legal conclusion asserted | Red-team A6 | Yes, after fix |
| **D8** | **Restates the wrong grievance** | **Red-team A2** | **NO** |

**D8 is unmitigated.** A draft can be fluent, correctly cited, properly scoped,
free of fabricated figures, and about a complaint the consumer never made. Every
individual property it asserts is well-formed. The LLM judge was tested on it
and answered that the draft did restate the grievance.

D1 deserves separate note: it is a **hedging** failure, invisible to any check
that only looks for incorrect statements. It was caught only because the
required-elements check asks whether something is present, not whether what is
present is wrong.

### Class S — Security failures

| ID | Attack | Model behaviour | Output caught? |
|---|---|---|---|
| S1 | Direct instruction override | Resisted | n/a |
| S2 | Role-play framing with fake system note | **Complied** | Yes — overcommit check |
| S3 | Authority impersonation | Resisted | n/a |

S2 is the load-bearing result: one injection successfully steered generation, and
the downstream deterministic checks caught the output before it could reach a
human. **Injection resistance and output validation are separate defences.** The
second held when the first did not, which is the argument for keeping validation
downstream of the model rather than trusting the prompt.

---

## 3. Monitoring plan

If this system were deployed — which §5 does not recommend — the following would
be required from day one.

### 3.1 Continuous

| Signal | Frequency | Alert condition |
|---|---|---|
| Abstention rate | Daily | Outside 10–30% for 3 consecutive days |
| Class distribution of routed cases | Daily | Any class shifts >10 pts from a 30-day baseline |
| Draft check pass rate | Per draft | Any check below 95% over a rolling 100 |
| Human override rate on approved drafts | Weekly | Above 20% |
| Human reversal rate on routing | Weekly | Above 30% |

**Human override rate is the primary health signal**, not accuracy. Accuracy is
unmeasurable in production without re-labelling; override is observed for free
and rises before quality problems become visible elsewhere.

### 3.2 Periodic

| Activity | Frequency | Purpose |
|---|---|---|
| Re-label 50 production cases | Monthly | Detect drift against a fresh golden set |
| Re-run full evaluation, 3 runs | Quarterly | Variance and regression |
| Re-run red-team suite | Quarterly, and on any prompt change | Confirm known attacks stay caught |
| Taxonomy drift check | Quarterly | CFPB has renamed categories before; the window is locked at 2023-08-25 |
| Fair-lending disaggregation | Quarterly | Geographic and product-mix proxy analysis |

**Any prompt change invalidates the evaluation.** The red-team suite and a
three-run variance check must both re-pass before a changed prompt reaches
production. This is not optional: `11_variance.md` shows the same prompt moves
metrics by 12.5 points between runs, so an unmeasured prompt change is
indistinguishable from noise.

---

## 4. Rollback triggers

Rollback means reverting to full manual routing. These are **automatic**, not
discretionary. No approval is needed to pull the system; approval is needed to
put it back.

| # | Trigger | Threshold | Action |
|---|---|---|---|
| T1 | Consumer receives an unapproved draft | Any single instance | **Immediate full stop** |
| T2 | Draft check failure reaches a consumer | Any single instance | **Immediate full stop** |
| T3 | Human reversal rate on routing | >40% over 100 cases | Suspend routing, keep drafting |
| T4 | Human override rate on drafts | >35% over 100 drafts | Suspend drafting, keep routing |
| T5 | Any check pass rate | <90% over a rolling 100 | Suspend the affected component |
| T6 | Abstention rate | <5% or >50% for 5 days | Suspend and investigate |
| T7 | Red-team regression | Any previously caught attack passes | Suspend until closed |
| T8 | Regulatory inquiry naming an automated decision | Any | Suspend pending legal review |

T1 and T2 are absolute and have no rate threshold. A single consumer receiving
unreviewed automated correspondence in a regulated complaint process is a
compliance event, not a quality metric.

---

## 5. Deployment recommendation

**Do not deploy v0.1.**

Three conditions from `12_brd.md` §9 remain unmet or only marginally met:

1. **Intra-rater reliability** — met marginally. 70.6%, CI lower bound clears the
   comparison by 0.9 percentage points, n=17.
2. **Statistical power** — not met. 28% power; ~400 labelled cases needed.
3. **Repeated runs per system** — partially met. Intervention 1 only.

And one failure is unmitigated: **D8, restating the wrong grievance**, which no
deterministic check can catch and which the LLM judge does not detect.

Separately, the economic case does not decide the question. `17_cost_model.md`
shows break-even precision at 43.3%, which every system clears — but only
because automation removes reading labour, so a system can be worse than a person
and still be cheaper. The decision turns on whether a misrouted complaint costs
more or less than **$38.27**, and that is a policy judgement for Compliance
rather than an output of this analysis.

**What would change the recommendation:** an expanded golden set at ~400 cases
with repeated runs, a defensible answer to the $38.27 question, and either a
detection method for D8 or an accepted control that compensates for it — for
example, requiring the reviewing human to confirm the restatement against the
narrative as an explicit approval step rather than a general read.
