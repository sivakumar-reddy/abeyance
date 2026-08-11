# 22 — Few-shot, class prior, and self-consistency

Three prompt interventions stacked and tested against the 61.4% majority-class
baseline recorded in `10_findings.md` §5. Examples and priors are drawn from
training folds only across 5 stratified folds, so no case contributes to its own
prompt.

## Conditions

| | Prompt | New calls |
|---|---|---|
| A | rule only, zero-shot | 0, reuses the step 08 cache |
| B | rule + 8 few-shot examples | 83 |
| C | rule + few-shot + empirical class prior | 83 |
| D | C sampled 3 times, majority vote | 166 |

## Result

| Condition | n | Accuracy | 95% CI | p vs majority | Macro-F1 | Coverage | Abstention precision |
|---|---|---|---|---|---|---|---|
| A_baseline | 83 | 51.8% | 41.0% to 62.6% | 0.971 | 0.549 | 74.7% | 23.8% |
| B_fewshot | 83 | 43.4% | 32.5% to 54.2% | 1.000 | 0.494 | 67.5% | 29.6% |
| C_fewshot_prior | 83 | 50.6% | 39.8% to 61.5% | 0.983 | 0.540 | 77.1% | 31.6% |
| D_selfconsistency | 83 | 50.6% | 39.8% to 61.5% | 0.983 | 0.558 | 73.5% | 27.3% |

Majority-class baseline: **61.4%** (ACCURACY).

## Did any single change do the work

| Comparison | Paired n | Only first correct | Only second correct | McNemar p |
|---|---|---|---|---|
| A_baseline -> B_fewshot | 83 | 7 | 0 | 0.016 |
| B_fewshot -> C_fewshot_prior | 83 | 0 | 6 | 0.031 |
| C_fewshot_prior -> D_selfconsistency | 83 | 1 | 1 | 1.000 |
| A_baseline -> D_selfconsistency | 83 | 4 | 3 | 1.000 |

## Abstention

Step 08 withheld the `abstain` column from the model entirely. Here it is
demonstrated in the few-shot examples drawn from training folds, which makes
this a different measurement rather than a continuation of the same one. The
held-out fold is never in the prompt, so the metric is honest, but it answers
a narrower question: whether abstention can be taught by demonstration, not
whether it emerges from the rule alone.

| Condition | Abstains on guideline-ABSTAIN | Abstains on clear | Precision |
|---|---|---|---|
| A_baseline | 31.2% | 23.9% | 23.8% |
| B_fewshot | 50.0% | 28.4% | 29.6% |
| C_fewshot_prior | 37.5% | 19.4% | 31.6% |
| D_selfconsistency | 37.5% | 23.9% | 27.3% |

## What this does not settle

The power problem in `10_findings.md` §6 is a property of the golden set
size, not of the prompt. With 83 cases and roughly 16 genuinely
ambiguous ones, a real difference in abstention behaviour would still be
undetectable at conventional power. A condition that appears to improve here
and carries a McNemar p above 0.05 is undetermined, not better.

## Files

- `22_ablation.csv` — headline metrics per condition with bootstrap intervals
- `22_paired_tests.csv` — exact McNemar between adjacent conditions
- `22_predictions.csv` — per-case predictions under all four conditions