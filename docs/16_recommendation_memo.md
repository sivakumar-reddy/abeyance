# 16 — Recommendation Memo

**To:** Director, Complaint Operations
**From:** Sivakumar Reddy Yenna
**Date:** August 2026
**Subject:** AI intervention portfolio — build list, do-not-build list, and one finding that changes the scope

---

## Recommendation

Build three of twelve assessed interventions. Do not build four. Defer five.

The highest-value candidate in the portfolio is also the one I most strongly
recommend against, and the reason is the substance of this memo.

---

## What was assessed

Twelve candidate AI interventions across the complaint intake workflow, scored on
seven weighted dimensions with written anchors. The scoring model is live and
auditable — weights can be changed and every score recalculates.

Scores are grounded in measurement, not estimate. Before scoring anything, I
hand-labelled 100 complaint narratives and compared them against the labels
consumers select at intake.

---

## The finding that changes the scope

**The intake issue label agrees with expert reading 46% of the time.**

Product selection is sound at 85%. The failure is specific to the 89-option issue
picker, and it is concentrated: 38 of 54 disagreements fall among three
categories, flowing in both directions between them. Fourteen textual features
were tested to separate those three; the best achieved 0.33 separation, which is
inside noise.

**Operational consequence.** Any routing built on the intake issue tag is
selecting a queue on an unreliable signal, and it is doing so in the three
highest-volume categories. Any model trained against those tags learns the intake
artefact rather than the grievance.

**Scoping consequence.** Issue classification is still worth building — it has
the highest value at stake in the portfolio — but not as an 89-way task. It is
recommended as a three-category task with a mandatory abstention path. That is
the version the data supports.

---

## Build

| # | Intervention | Rationale |
|---|---|---|
| 1 | Product classification, 13 classes | Highest weighted score, 4.15. Labels measured at 85% agreement. Low failure cost, human-catchable. |
| 2 | Issue classification, 3 categories with abstention | Highest value at stake in the portfolio. Scope reduced from 89 classes in response to the label-noise finding. |
| 6 | Grounded acknowledgment draft | High value and high failure cost, but **fully reversible** — human approval is required before anything reaches a consumer. |

Together these cover classification, abstention, retrieval and generation, giving
four evaluation methodologies from one build programme.

---

## Do not build

| # | Intervention | Reason |
|---|---|---|
| 11 | Full autonomous resolution | Irreversible, no ground truth, maximum regulatory exposure, no human catch point |
| 12 | Consumer dispute prediction | Requires fair-lending and disparate-impact review before any build; that review must be free to conclude no |
| 9 | UDAAP risk detection | No labelled corpus. A false negative suppresses a genuine unfair-practice signal. |
| 5 | Severity and escalation scoring | No severity label exists. Available proxies measure how a person writes, not how badly they were harmed. |

**Candidate 11 deserves separate attention.** It scores 5 on value at stake — the
highest in the portfolio — and 1.95 overall, the lowest. An assessment that
ranked on value alone would have built it first. Its failure mode is not a
mislabelled complaint; it is a consumer receiving an incorrect resolution to a
financial dispute that no person read.

---

## Defer

Candidates 3, 4, 7, 8 and 10 — entity extraction, duplicate detection,
summarisation, regulation retrieval, distress flagging. All are low-risk and
several score well. None moves the workflow enough to justify going first. Three
of them outrank candidate 2 on the rubric and are still not recommended, because
the rubric rewards safety and the safest available work is not the useful work.

---

## What the build has shown so far

Candidate 2 has been built and evaluated across three systems: a keyword
baseline, a direct LLM classifier, and a pairwise tournament.

| | Keyword | LLM | Tournament | Always guess the largest class |
|---|---|---|---|---|
| Accuracy | 47.0% | 51.8% | 44.6% | **61.4%** |
| Macro-F1 | 0.471 | **0.549** | 0.488 | — |

**None beats always guessing the largest class on accuracy.** The LLM's advantage
on macro-F1 — the metric that credits the smaller categories — does survive
repeated runs. Nothing else does.

Two further results bear on how this programme should be run:

**Model-reported confidence did not behave like confidence.** Asked to abstain on
ambiguous complaints, the model abstained on roughly a quarter of everything
regardless. The gap between ambiguous and clear cases was 7.3 points, against a
run-to-run swing of 12.5 points in one of those terms alone.

**Human reviewer confidence did behave like confidence.** On a blind re-label,
mean self-rated confidence was 2.58 on cases reproduced and 1.83 on cases that
changed. Where a reviewer is already in the loop, their confidence is a usable
routing signal. The model's is not.

---

## What I am not claiming

The comparison between the two AI approaches **cannot be settled with the work
done so far**. The abstention effect carries p = 0.218 at 28% statistical power.
A conclusive comparison needs roughly 400 labelled cases and repeated runs of each
system.

I am reporting this rather than the more flattering version because the
alternative — quoting a 29.2% figure against 23.8% as an improvement — would not
have survived scrutiny, and the figure originally recorded turned out to be the
best of three runs rather than a typical one.

---

## Decision requested

1. **Approve** the three-item build list, with issue classification scoped to three categories.
2. **Approve** the do-not-build list, and note that candidate 12 requires legal review before it can be reconsidered.
3. **Fund the evaluation**, or accept that approach selection will remain undetermined. Roughly 400 labelled cases is the price of an answer.

Full assessment in `15_opportunity_assessment.md`. Scoring model in
`scoring_model.xlsx`. Evidence base in `10_findings.md`.
