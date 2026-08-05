# 19 — LLM-as-judge and its validation

Step 18 evaluated drafts with four automated checks. Three settle properties
pattern matching can decide. The fourth — whether a draft restates the
consumer's grievance — is semantic, and the regex approximating it needed two
corrections and still disagreed with a human reader.

That is the standard motivation for an LLM judge, and the standard place
evaluation programmes go wrong: the judge is adopted for convenience and its
output is then treated as ground truth. This measures it first.

## The control

Two properties were judged. `timeline` is trivially checkable — a number of days
is named or it is not. It exists to test the judge on a question with a known
answer before its verdict on the contested question is given any weight.

| Property | Rater | Agreement with human | 95% CI | Cohen's kappa |
|---|---|---|---|---|
| timeline | judge | 19/20 = 95.0% | [76.4%, 99.1%] | 0.900 |
| timeline | regex | 20/20 = 100.0% | [83.9%, 100.0%] | 1.000 |
| restatement | judge | 20/20 = 100.0% | [83.9%, 100.0%] | nan |
| restatement | regex | 12/20 = 60.0% | [38.7%, 78.1%] | nan |

**Control passed.** The judge agrees with the human on `timeline` at 95.0%. Its verdict on the contested property is worth reading.

## A degenerate reference

The human labelled **every draft YES** on `restatement`. That has two
consequences that must be stated before any number below is read:

- **Kappa is undefined.** With a constant reference, chance agreement is 1.
  Reporting 0.000 would read as *no better than chance* when the correct
  statement is *not computable*.
- **Agreement rate does not measure discrimination.** A rater that always
  answers YES scores 100% against this reference while distinguishing nothing.

What remains informative is the **direction** of each rater's errors, and the
finding that the property does not vary across these 20 drafts at all.

## Does the judge beat the regex?

On `restatement`, the judge agrees with the human on **100.0%** of
drafts against the regex's **60.0%** — a difference of
**+40.0 points** at n=20.

**That +40 points does not mean what it appears to mean.** Because every
reference label is the same, a judge that answers YES unconditionally scores
100% here. The result is consistent with a judge that reads carefully and
equally consistent with one that never says NO, and this test cannot separate
those two. What the comparison *does* establish is one-directional: the regex
produced 8 false negatives, so it was wrong, in a known
direction, on drafts a human accepts.

### What the control says about trusting the judge

On `timeline` — the property with genuine variance and an objectively
checkable answer — the judge scored 95.0% (kappa 0.900) and
the regex scored 100.0%
(kappa 1.000).

**The deterministic check beat the judge on the only question where either
could be scored properly.** The judge cleared the control threshold, but it
cleared it while being outperformed by a regex that costs nothing and cannot
vary between runs.

### Recommendation

1. **Keep the deterministic check for `timeline`.** It is perfect on this
   sample and free. There is no case for an API call here.
2. **Fix the regex for `restatement` rather than replace it.** Its failure was
   8 false negatives in one direction, which is a pattern problem, not evidence
   that the property needs semantic judgement.
3. **Do not adopt the judge on this evidence.** Its apparent perfection is an
   artefact of a reference with no variance.

### Outcome of the adversarial test (added after Step 20)

The red-team log ran the missing test. The judge was shown two adversarial
drafts and one correct one:

| Attack | Expected | Judge said | Correct |
|---|---|---|---|
| A1 — generic acknowledgment, no restatement | NO | NO | yes |
| A2 — restates the **wrong** grievance | NO | YES | **no** |
| A8 — correct draft | YES | YES | yes |

**The judge detects the absence of a restatement. It does not detect the
incorrectness of one.** Shown a fluent, correctly cited letter describing a
complaint the consumer never made, it answered YES.

This resolves the ambiguity left by the degenerate reference. The 100%
agreement in the table above is consistent with partial competence: the judge
is not answering YES unconditionally, but the discrimination it has is not the
discrimination the property requires. For a regulated acknowledgment letter,
saying the wrong thing confidently is a worse failure than saying nothing
specific, and that is the case the judge misses.

### The test this evaluation could not run

To establish that the judge discriminates on `restatement`, the sample must
contain drafts that genuinely fail it. None of these 20 do — the model restated
the grievance every time. The missing test is adversarial: construct drafts that
acknowledge receipt without restating anything, and check whether the judge
catches them. That belongs in the red-team log, and until it is run the judge's
performance on this property is unmeasured rather than good.

## Error direction

| Property | Rater | False negatives | False positives |
|---|---|---|---|
| timeline | judge | 1 | 0 |
| timeline | regex | 0 | 0 |
| restatement | judge | 0 | 0 |
| restatement | regex | 8 | 0 |

## Limitations

- n=20, single human rater. Confidence intervals are wide.
- The human labels were produced by the same person who wrote the annotation
  guideline and the regex, which is a source of correlated error.
- The judge was run once. Step 11 showed run-to-run variation moves comparable
  metrics by more than 10 points, and no variance estimate exists here.