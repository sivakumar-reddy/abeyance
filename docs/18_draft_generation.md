# 18 — Grounded acknowledgment draft (Intervention 3)

Candidate 6 from `15_opportunity_assessment.md`. Recommended for build because
it carries high value **and** high failure cost, but is fully reversible: a human
approves every draft before it reaches a consumer.

## Why the evaluation looks different

There is no single correct acknowledgment letter, so accuracy is meaningless.
What can be checked is whether the draft is **grounded** — whether every
regulatory claim traces to a provision actually retrieved, and whether the model
invented anything. Four checks, none of which requires a reference answer.

## Results

| Check | Passed | Rate |
|---|---|---|
| Citation validity | 20/20 | 100.0% |
| No fabricated numbers | 20/20 | 100.0% |
| Required elements | 6/20 | 30.0% |
| No overcommitment | 20/20 | 100.0% |
| ALL FOUR | 6/20 | 30.0% |

Mean draft length 178 words (range 169–192).

## What each check catches

| Check | Failure it prevents |
|---|---|
| Citation validity | Citing a provision from training data rather than from the retrieved context |
| No fabricated numbers | Stating a date, amount or deadline the source never contained |
| Required elements | An acknowledgment that omits the case reference or the timeline |
| **No overcommitment** | **Promising removal, conceding fault, or asserting a violation before any investigation** |

The fourth check is the one that matters in a regulated workflow. A letter
promising deletion creates an obligation before anyone has looked at the case.
This is a compliance failure that a fluent, well-written draft can commit without
any factual error at all — which is why fluency is not a safety property.

## Finding: the model hedges on the timeline

The most common element failure is `timeline`, and inspection of the drafts shows
it is not a detection artefact. Rather than naming a number, drafts state that a
response will follow *within the timeframe required by applicable law*.

That phrasing is defensible and useless. It is accurate, it commits to nothing
incorrect, and it leaves the consumer without the one operational fact an
acknowledgment letter exists to convey: when they will hear back. The retrieved
provision supplies the 30-day figure; the model declines to use it.

This is a hedging failure rather than a hallucination failure, and it is invisible
to any check that only looks for incorrect statements. It was caught because the
required-elements check asks whether something is *present*, not whether what is
present is *wrong*. Groundedness checks that only test for fabrication will not
find it.

## A limit of deterministic checking

Three of the four checks decide a property pattern matching can settle: does a
cited section appear in the retrieved context, does a figure appear in the source,
does a prohibited commitment phrase occur. The `restatement` element is not of
that kind — whether a draft restates the grievance is a semantic judgement, and
the regex approximating it required two corrections before it stopped producing
false failures.

It is retained as a cheap screen and flagged as an approximation. Validating it
properly is the motivating case for the LLM judge in Phase 7 — and the reason
that judge must itself be validated against human labels before its output is
treated as a measurement.

## Relationship to the abstention finding

Intervention 1 showed that asking a model to self-report uncertainty produced a
number that did not behave like confidence. These four checks take the opposite
approach: they are external, deterministic, and require no self-report. Where a
property can be checked mechanically, it should be — not elicited.