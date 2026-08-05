# 15 — AI Opportunity Assessment

**Twelve candidate interventions for the consumer-complaint intake workflow**

| | |
|---|---|
| Author | Sivakumar Reddy Yenna |
| Date | August 2026 |
| Scoring model | `scoring_model.xlsx` (live, auditable) |
| Recommendation | `16_recommendation_memo.md` |

*Numbering note: this document belongs at Phase 2 of the programme but is numbered
15 because `01`–`03` were taken by the corpus and scoping work delivered in Phase 1.*

---

## 1. Method

Twelve candidate interventions were enumerated across the intake workflow —
classification, extraction, retrieval, generation, similarity and prediction —
and scored against seven dimensions, each 1–5 with written anchor definitions.

| Dimension | Weight | Direction |
|---|---|---|
| Data readiness | 20% | Higher better |
| Value at stake | 20% | Higher better |
| Failure cost | 20% | **Lower better** |
| Technical feasibility | 15% | Higher better |
| Reversibility | 10% | Higher better |
| Regulatory exposure | 10% | **Lower better** |
| Change management burden | 5% | **Lower better** |

Three dimensions are entered as *severity* and inverted in the formula, so every
contribution points the same direction. Weights live in the `Rubric` sheet and
drive the calculation — changing one recalculates all twelve scores, which makes
the model auditable rather than a static table.

**Data readiness scores are grounded in Phase 1 measurement, not estimated.**
The corpus study found the intake product tag agrees with expert reading 85% of
the time and the issue tag 46%. Those two numbers set the readiness scores for
candidates 1 and 2 directly. Candidates whose labels do not exist at all — UDAAP
risk, severity, dispute outcome — score 1.

---

## 2. Results

| # | Candidate | Type | Score | Value | Failure cost | Decision |
|---|---|---|---|---|---|---|
| 1 | Auto-classify Product (13 classes) | Classification | **4.15** | 4 | 2 | **BUILD** |
| 4 | Detect duplicate or related complaints | Similarity | 3.80 | 2 | 2 | Defer |
| 7 | Summarize narrative to 2-sentence abstract | Summarization | 3.80 | 2 | 2 | Defer |
| 3 | Extract structured entities | Extraction | 3.55 | 3 | 2 | Defer |
| 2 | Auto-classify Issue (89 classes) | Classification | 3.45 | **5** | 3 | **BUILD (reduced scope)** |
| 6 | Draft acknowledgment letter grounded in regulation | Generation + RAG | 3.20 | 4 | 4 | **BUILD** |
| 8 | Suggest applicable regulation section | Retrieval | 3.05 | 3 | 3 | Defer |
| 10 | Sentiment and consumer-distress flag | Classification | 2.90 | 2 | 3 | Defer |
| 5 | Severity and escalation scoring | Classification | 2.50 | 4 | 4 | Do not build |
| 12 | Predict likelihood of consumer dispute | Prediction | 2.30 | 3 | 4 | **DO NOT BUILD** |
| 9 | Detect UDAAP risk language | Classification | 2.05 | 4 | 5 | Do not build |
| 11 | Full autonomous resolution recommendation | Generation | **1.95** | 5 | 5 | **DO NOT BUILD** |

---

## 3. Rank order is not the build list

Candidates 4, 7 and 3 outrank candidate 2, and none of them is recommended.
Candidate 6 ranks sixth and is. That is not an inconsistency; it is the rubric
behaving as designed and needing human judgement on top.

**The rubric rewards safety, so low-value low-risk work floats up.** Duplicate
detection and narrative summarisation are cheap, reversible and carry almost no
regulatory surface. They score well because nothing about them is dangerous. They
also barely move the workflow — both score 2 on value at stake. Building the
safest thing available is not the same as building the useful thing.

Three judgements override the ranking:

**Candidate 2 is built despite a mid-table score because it carries the highest
value at stake of any candidate.** Issue routing determines which specialist
queue a complaint reaches. Its score is dragged down by a data readiness of 2,
which reflects the measured 46% label agreement — but that finding is an argument
for *changing the scope*, not for skipping the work. It is built as a reduced
three-category task with abstention, which is the only version the data supports.

**Candidate 6 is built despite a failure cost of 4 because it is fully
reversible.** A drafted acknowledgment letter is reviewed and approved by a human
before it reaches a consumer. Reversibility of 5 is what makes a high failure
cost tolerable — the error never leaves the building. This is the pairing the
rubric is designed to surface: high consequence, high catchability.

**Nothing is built on unmeasured labels.** Candidates 5, 9 and 12 all score 1–2
on data readiness because no ground truth exists for severity, UDAAP risk or
dispute outcome. Building any of them would mean inventing a target and then
reporting accuracy against it.

---

## 4. The do-not-build cases

These are recommendations, not omissions. Each is argued down for a stated
reason.

### Candidate 11 — Full autonomous resolution recommendation

**Highest value at stake of any candidate (5) and the lowest total score (1.95).**
That combination is the entire point of scoring failure cost separately from
value.

- **Irreversible.** Reversibility 1 — no human sees the output before it takes effect.
- **No reliable label.** There is no ground truth for "correct resolution" in the corpus.
- **Maximum regulatory exposure.** A wrong resolution on a regulated complaint is a compliance event, not a support ticket.
- **No catch point.** Every other candidate has a human between the model and the consumer. This one does not.

**Recommendation: do not build, at any confidence threshold.** The failure mode
is not a mislabelled complaint; it is a consumer receiving an incorrect
resolution to a financial dispute with no one having read it.

### Candidate 12 — Predict likelihood of consumer dispute

**Recommendation: do not build without a fair-lending and disparate-impact
review first.**

A model that scores consumers on how likely they are to escalate creates an
obvious mechanism for differential treatment, whether or not that is intended.
Complaint narratives correlate with geography, product mix and financial
circumstance, all of which correlate with protected characteristics. Before any
build, this needs disaggregated performance analysis and legal review — and that
review should be able to conclude "no."

### Candidate 9 — Detect UDAAP risk language

**Failure cost 5, regulatory exposure 5, data readiness 1.**

There is no labelled UDAAP corpus here. Building a detector would mean defining
the target ourselves and then reporting performance against our own definition
— which is precisely the circularity the Phase 1 label-noise study warns about.
A false negative means a genuine unfair-practice signal is suppressed by an
automated system, which is worse than not having the system.

### Candidate 5 — Severity and escalation scoring

Data readiness 1. Severity is not recorded in the corpus. The natural proxies —
narrative length, emotional register, capitalisation — measure how a person
writes, not how badly they were harmed. Defer until a severity label exists.

---

## 5. The frontier

Plotting value at stake against failure cost (see the `Frontier` sheet) puts
candidates **11, 9 and 5** in the top-right quadrant: high value *and* high
failure cost. That quadrant is the do-not-build region.

The single most important output of this assessment is that the
**highest-value candidate in the portfolio is also its worst recommendation.**
An assessment that ranked purely on value would have built candidate 11 first.

---

## 6. Build list

| # | Candidate | Why |
|---|---|---|
| 1 | Product classification | Highest score; labels measured at 85% agreement |
| 2 | Issue classification, reduced to 3 categories with abstention | Highest value at stake; scope narrowed to what the data supports |
| 6 | Grounded acknowledgment draft | High value, fully reversible, human approval enforced |

Between them these cover **classification, abstention, retrieval and generation**
— four distinct evaluation methodologies from one build, which is what makes the
evaluation programme worth running.

**Delivered so far:** candidate 2, built and evaluated across three systems
(`07`, `08`, `09`). Candidate 6 is specified and not yet built. Candidate 1 is
in scope and not yet built.
