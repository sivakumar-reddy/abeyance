# 08 — LLM classifier (Intervention 1)

Model `claude-sonnet-5`. Prompt encodes the counterfactual test
from `06_annotation_guideline.md`. No few-shot examples are drawn from the
evaluation set, and the `abstain` column is never shown to the model.

## Result against the pre-registered floor

| Measure | Keyword baseline | LLM | Majority class |
|---|---|---|---|
| Accuracy, all cases | 47.0% | 51.8% | 61.4% |
| Accuracy, decided only | 58.2% | 69.4% | — |
| Coverage | 80.7% | 74.7% | 100% |
| Macro-F1 | 0.471 | 0.549 | — |

## Per class

| Class | n | Precision | Recall | F1 |
|---|---|---|---|---|
| ACCURACY | 51 | 0.763 | 0.569 | 0.652 |
| PERMISSIBLE-PURPOSE | 16 | 0.571 | 0.500 | 0.533 |
| INVESTIGATION | 16 | 0.600 | 0.375 | 0.462 |

## Abstention behaviour

The guideline identified 16 cases as unresolvable by any rule, by reading
narratives before any classifier existed. Whether the model abstains in the
same place is the central test of Intervention 1.

| | Rate |
|---|---|
| Abstains on guideline-ABSTAIN cases (n=16) | 31.2% |
| Abstains on clearly-separable cases (n=67) | 23.9% |

A model that abstains at similar rates in both groups is abstaining on
difficulty in general, not on the specific ambiguity the guideline defines.

## Files

- `08_llm_predictions.csv` — per-case label, confidence, and the model's counterfactual
- `08_risk_coverage.csv` — accuracy vs coverage, sweeping the confidence threshold
- `08_llm_confusion.csv` — confusion matrix