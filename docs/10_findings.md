# 10 — Findings

**AI Feasibility and Evaluation Program: automated issue triage for consumer
credit-reporting complaints**

Sivakumar Reddy Yenna · August 2026

---

## Summary

CFPB publishes 16.9M consumer complaints, 3.8M of them with free-text
narratives, each tagged by the consumer at intake with a product and one of 89
issue categories. Those tags are the obvious training target for an automated
triage system.

This study asked whether they are good enough to be one.

They are not. Against 100 hand-labelled cases, the official issue tag matches
expert reading **46% of the time**. The disagreement is not diffuse: 38 of 54
issue disagreements fall inside a single three-category cycle, flowing in both
directions on every edge. Fourteen lexical features were tested against that
cycle and none separated it — the boundary is not recoverable from surface text.

Two AI interventions were then built and evaluated against a keyword baseline.
Neither reliably reproduced the ambiguity boundary a human identified by reading.
Two separate measurements explain why no conclusion can be drawn about which is
better. The study is **underpowered** — the observed abstention effect carries
p = 0.218 at 28% statistical power. And it is **noisy**: re-running the same
prompt three times moves the key abstention metric by 12.5 points, which is
larger than the effect being measured. The correct conclusion is undetermined,
not negative — and certainly not positive.

The deliverable is therefore not a triage system. It is a quantified account of
why one built on these labels would fail, and a specification of what a
conclusive evaluation would cost.

---

## 1. Data and scope

| | |
|---|---|
| Source | CFPB Consumer Complaint Database |
| Total complaints | 16,872,860 |
| With narratives | 3,830,206 (22.7%) |
| Taxonomy window | Locked at 2023-08-25, after the final rename chain |
| In-window narratives | 2,312,146 across 13 products and 89 issues |
| Golden set | 100 cases, seed 42, hand-labelled |

Three product rename chains were traced and the window set after the last of
them, so that no legacy category names enter the analysis. A defensive
normalisation step in the join script confirms this on every run; it has never
fired.

**Scope limitation, stated up front.** The golden set covers 14 of 89 issues and
7 of 13 products, with nine issue classes at n=1. It supports conclusions about
the dominant credit-reporting categories and nothing else. Evaluation was
narrowed to the three-class problem the data actually supports rather than
reporting 89-class metrics the sample cannot bear.

---

## 2. The label noise floor

Hand labels were joined against CFPB's own tags for the same 100 complaint IDs.

| Measure | Agreement |
|---|---|
| Product | 85.0% |
| Issue | **46.0%** |
| Issue, conditional on product agreeing (n=85) | 51.8% |
| Both | 44.0% |

Conditioning on the product barely moves the issue figure — 46.0% to 51.8% —
which rules out the obvious explanation. The disagreement is not downstream of
consumers picking the wrong product. It is intrinsic to the issue taxonomy.

Consumers can identify what kind of financial product they are complaining
about. The 89-option issue picker is close to a coin flip against expert reading.

**Consequence.** Any classifier scored against these labels has a ceiling near
50%, not because the model is weak but because the target is noisy. A reported
accuracy of 48% would be uninterpretable in both directions.

**Is the hand label the better one?** Marginally, and the margin is thin. Blind
re-labelling of 25 cases gives 70.6% self-agreement on the uncontaminated
stratum (95% CI [46.9%, 86.7%], kappa 0.555) against 46.0% agreement with the
intake tag. The confidence interval clears 46.0% by 0.9 points. The direction of
the finding holds; its precision does not. Section 8 records this in full.

### Where the disagreement lives

38 of 54 issue disagreements fall inside three categories:

| Edge | → | ← |
|---|---|---|
| Investigation ↔ Incorrect information | 9 | 7 |
| Incorrect information ↔ Improper use | 9 | 8 |
| Improper use ↔ Investigation | 3 | 2 |

Every edge runs in **both directions**. Had consumers simply been defaulting to a
catch-all, the flow would be one-way. It is not. Both parties move cases both
ways, which means these three categories are not reliably separable from the
narrative by either of them. That is a taxonomy defect, not a labelling failure.

---

## 3. The boundary is not lexical

Fourteen lexical signals were tested against the 38 boundary cases, each chosen
to map to a distinct FCRA theory rather than to surface wording. Presence rates
were grouped by the label the expert chose.

**Maximum separation across all fourteen: 0.33.** Two results in particular
rule out a keyword approach:

| Signal | ACCURACY | INVESTIGATION | PERM-PURPOSE | spread |
|---|---|---|---|---|
| `permission` | 0.18 | 0.10 | 0.36 | 0.26 |
| `inaccurate` | 0.65 | 0.40 | 0.36 | 0.29 |

`permission` — "permissible purpose", "without my consent", "unauthorized" — is
the *legal definition* of Improper use. It appears in only 36% of cases labelled
that way, and in 18% of cases labelled ACCURACY. The defining vocabulary of a
category does not identify membership in it.

`inaccurate` is the most common signal in the corpus and is **most** frequent in
cases that are not primarily accuracy complaints. Everyone says their information
is wrong.

The explanation is syntactic role. The same vocabulary appears in all three
classes, but in one it names the grievance and in another it names the remedy
being requested. Pattern matching cannot see role.

*Methodological note: a fifteenth signal returned zero matches and was flagged by
an automated guard as a regex defect rather than reported as a finding.*

---

## 4. Annotation guideline

The rule derived from case-by-case review is a counterfactual test. Remove the
alleged defect and ask whether the complainant still has a complaint.

| Remove | Complaint ends → | Label |
|---|---|---|
| The inaccuracy in the data | | ACCURACY |
| The absence of consent | | PERMISSIBLE-PURPOSE |
| The failure to act on a prior dispute | | INVESTIGATION |

INVESTIGATION carries a two-part condition — a prior dispute must exist **and**
the complaint must be about its handling. A prior dispute alone is insufficient;
nearly every credit-reporting complainant has disputed something.

**16 of 100 cases were judged unresolvable by any rule** and form the abstention
region. Three patterns:

- Two theories asserted as coordinate claims — *"inaccurate **and** unauthorized accounts"*
- Identity theft, which makes data wrong and furnishing unauthorised simultaneously
- Dispute failure alongside a substantive defect, neither subordinate to the other

Forcing a single label on these fabricates a distinction the text does not
contain.

---

## 5. Systems evaluated

All three scored against the same 83 in-scope cases.

| Measure | Keyword | LLM direct | Tournament | Majority class |
|---|---|---|---|---|
| Accuracy, all | 47.0% | 51.8% [49.4–54.2] | 44.6% | **61.4%** |
| Accuracy, decided only | 58.2% | 69.4% [67.2–69.4] | 62.7% | — |
| Coverage | 80.7% | 74.7% [73.5–78.3] | 71.1% | 100% |
| **Macro-F1** | 0.471 | **0.549 [0.525–0.571]** | 0.488 | — |
| Abstention precision | — | 23.8% [16.7–23.8] | 29.2% | — |

LLM figures are the run reported in `08_llm.md`, with the observed range across
three independent runs in brackets (`11_variance.md`). The keyword baseline is
deterministic. The tournament was run once and **has no variance estimate**;
its column should be read as a single draw, not a stable value.

Two consequences follow immediately.

**The macro-F1 advantage over keywords is real.** It holds at every run — worst
case +0.054, best case +0.100. This is the one comparison in the study that
survives its own error bars.

**The reported abstention precision of 23.8% was the maximum of three runs.**
The mean is 21.1%. A single cached run drew 2.7 points high by chance. This is
the ordinary mechanism by which single-run LLM evaluations are published
optimistic, and it occurred here.

**None beats always predicting the majority class on accuracy.** With a 61/19/19
split, accuracy is the wrong metric; macro-F1 is the honest one, and by that
measure the LLM recovers minority classes meaningfully better than keywords.

INVESTIGATION recall is the weakest class in every system — 0.250, 0.375, 0.312.
This was predicted by the guideline: it is the only class with a two-part
condition, and all three systems detect the first half and miss the second.

### 5.1 Keyword baseline — pre-registered failure

Built after §3 established that no lexical signal separates the classes, and
predicted to fail for that stated reason. It did: 47.0%, fourteen points below
the majority class.

It also reproduced the abstention boundary without being shown it:

| | Accuracy |
|---|---|
| On guideline-ABSTAIN cases (16) | **18.8%** |
| On clearly-separable cases (67) | 53.7% |

The 16 cases marked unresolvable by reading — before this classifier existed —
are the cases it gets most wrong, by nearly a factor of three.

### 5.2 Intervention 1 — LLM with abstention rule

Sonnet 5, prompt encoding the counterfactual test and the three abstention
categories as rules. No few-shot examples were drawn from the evaluation set; the
`abstain` column was never shown to the model.

Macro-F1 improved to 0.549. Abstention did not work:

| | Abstention rate |
|---|---|
| On guideline-ABSTAIN cases (16) | 31.2% |
| On clearly-separable cases (67) | 23.9% |

Roughly a quarter of everything, regardless. Three in four abstentions land on
cases judged perfectly separable. **Giving a model a written abstention rule
produced abstention behaviour without abstention judgment.**

That gap is 7.3 points. The run-to-run range of the ambiguous-case abstention
rate *by itself* is **12.5 points** (18.75%–31.25%, SD 0.072) — the widest
spread of any metric measured. The effect is 0.58x the noise in one of its own
terms, so it is not merely non-significant on the Fisher test in §6; it sits
inside sampling variance. A different draw would have reversed its sign.

Diagnosis: asking a model whether it is unsure elicits a self-report, and
self-reported uncertainty is not the same quantity as genuine indeterminacy.

### 5.2a Human confidence was calibrated; model confidence was not

The blind re-label carried a self-reported confidence rating on each of the 25
cases. It tracked reliability closely:

| | Mean confidence (1–3) |
|---|---|
| Cases reproduced from pass 1 (n=19) | **2.58** |
| Cases that flipped (n=6) | **1.83** |

The same quantity — a self-report of certainty — was elicited from the human and
from the model. For the human it predicted actual instability. For the model it
did not: abstention rates differed by 7.3 points between genuinely ambiguous and
clearly separable cases, against a run-to-run range of 12.5 points in one of
those terms alone.

This is the sharpest single contrast in the study. It does not show that models
cannot express calibrated uncertainty; it shows that *this* elicitation, on
*this* task, produced a number that looked like confidence and did not behave
like it. Any evaluation design that treats model-reported confidence as
interchangeable with human-reported confidence should test the assumption rather
than inherit it.

### 5.3 Intervention 2 — pairwise tournament

Designed to remove the self-report. Three forced head-to-head comparisons per
case, one per pair of theories; the model asked only which theory survives the
counterfactual, or whether neither dominates. Abstention derived structurally: a
cycle (A beats P beats I beats A) is a Condorcet paradox and was taken as the
operational definition of "genuinely two-headed."

**Zero cycles occurred in 83 cases.**

| Structure | n |
|---|---|
| clear | 34 |
| clear_with_ties | 25 |
| tied | 13 |
| no_majority | 11 |
| **cycle** | **0** |

The mechanism the intervention was built on does not exist in this data. The
model's pairwise judgments were **always transitive**, including on all 16 cases
a human judged genuinely two-headed. Ambiguity surfaces instead as explicit
NEITHER responses — 38 of 83 cases involved at least one tie.

This is a substantive negative result about LLM preference structure, obtained
from a test that pre-registered the opposite prediction.

---

## 6. The study was underpowered

Intervention 2 showed better abstention targeting: 43.8% on ambiguous cases
versus 25.4% on clear ones, odds ratio 2.29, against Intervention 1's 1.45.

Fisher's exact test on the concentration:

| Comparison | Odds ratio | p |
|---|---|---|
| Intervention 1 vs chance | 1.45 | 0.536 |
| Intervention 2 vs chance | 2.29 | 0.218 |
| Intervention 2 vs Intervention 1 | — | 0.716 |

**Neither result is significant, and the two interventions are not
distinguishable from each other.** The apparent +5.4% precision lift is seven
cases versus five.

Power to detect the observed effect, by simulation:

| Ambiguous cases | Total golden set | Power |
|---|---|---|
| **16** | **83** | **28%** |
| 30 | ~155 | 46% |
| 50 | ~259 | 70% |
| 75 | ~389 | 85% |
| 100 | ~518 | 94% |

A conclusive test needs roughly 75 ambiguous cases — a golden set near 400, or
about four times the labelling investment made here.

**The correct conclusion is that the comparison is undetermined.** Reporting
29.2% against 23.8% as evidence of improvement would have been the natural
mistake, and it would have been wrong.

---

## 7. What this means for a triage system

**Do not train against the intake labels.** They agree with expert reading 46% of
the time, and the disagreement concentrates in the three highest-volume
categories. A model that fits them learns the intake artefact.

**A three-category collapse is defensible; 89-way is not.** The three confusable
categories should either be merged or routed to human review as a group. This is
justified by the bidirectional confusion in §2, not by convenience.

**Budget for abstention, and do not trust the model to allocate it.** Roughly 16%
of credit-reporting complaints are genuinely two-headed. Neither intervention
identified them reliably. Until abstention can be validated, the region should be
defined by rule — the three patterns in §4 — rather than by model confidence.
Human reviewer confidence, by contrast, did track reliability (§5.2a) and is a
usable routing signal where a reviewer is already in the loop.

**Evaluation cost is a real line item.** Distinguishing these interventions
requires a golden set around 400 cases *and* repeated runs of each system. A
single-run comparison on 83 cases cannot separate them, and this study
demonstrates both failure modes rather than assuming them. That is the price of
an answer, and it should be budgeted before building, not after.

---

## 8. Limitations

- **Intra-rater reliability is 70.6%, and it only just clears the bar.** A blind
  re-label of 25 cases (labels withheld, order shuffled) gives 12/17 agreement on
  the uncontaminated stratum, 95% CI [46.9%, 86.7%], Cohen's kappa 0.555. The
  lower bound clears the 46.0% CFPB agreement rate by **0.9 percentage points**.
  ASM-1 is supported, but marginally, and a slightly different sample would have
  left it undetermined. See `14_reliability.md`.
- **The re-label protocol was compromised and the result is stratified
  accordingly.** The intended 48-hour gap became same-day, and 8 of the 25 cases
  had been re-read hours earlier with first-pass labels visible. Those 8 agree at
  87.5% against 70.6% for the clean stratum — an anchoring effect of **+16.9
  points**. The pooled figure of 76.0% is an overestimate and is not quoted.
- The `primary_grievance` review in §4 agreed with the first pass on 38 of 38
  cases, but the original labels were visible during that review. It is anchored
  and is **not** evidence of reliability. The +16.9 point anchoring effect
  measured in the re-label confirms the size of that distortion empirically.
- **Run-to-run variance was measured and it weakened a result.** Sonnet 5 does
  not accept a temperature parameter; three independent runs of Intervention 1
  (`11_variance.md`) show macro-F1 ranging 0.525–0.571 and the ambiguous-case
  abstention rate ranging 18.75%–31.25%. The macro-F1 advantage over keywords
  survives; the abstention concentration reported in §5.2 does not. The figure
  originally quoted for abstention precision was the maximum of the three runs.
- Intervention 2 was run once. It has no variance estimate, so the 29.2%
  abstention precision in §5 carries the same single-draw risk that the
  variance check exposed in Intervention 1. Its apparent advantage should not
  be relied on.
- Sampling variance and statistical power are independent problems. Re-running
  the model addresses the first and does nothing for the second.
- Class support is concentrated: 51 / 16 / 16. Minority-class metrics rest on 16
  cases each.
- Findings apply to credit-reporting complaints. The other 12 products are
  represented by 19 cases in total and no conclusions are drawn about them.

---

## Artifacts

| File | Contents |
|---|---|
| `01_corpus_profile.md` | Corpus census, narrative coverage |
| `02_taxonomy_drift.md` | Rename chains, window justification |
| `03_scoping_decision.md` | Window lock, class selection |
| `04_label_noise.md` | Agreement rates, confusion matrix |
| `05_boundary_cases.md` | 38 boundary narratives, signal table |
| `06_annotation_guideline.md` | Counterfactual test, abstention criterion |
| `07_baseline.md` | Keyword baseline |
| `08_llm.md` | Intervention 1, risk-coverage curve |
| `09_tournament.md` | Intervention 2, structural abstention |
| `11_variance.md` | Run-to-run variance across three independent runs |
| `14_reliability.md` | Intra-rater reliability, stratified by contamination |
| `golden_set_v2.csv` | 100 labelled cases with abstention flags |
