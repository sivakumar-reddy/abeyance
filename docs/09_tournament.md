# 09 — Pairwise tournament (Intervention 2)

Intervention 1 abstained at 31.2% on guideline-ambiguous cases and 23.9% on
clearly separable ones — abstention precision 23.8%, barely above the base
rate. It produced abstention behaviour without abstention judgment.

This intervention never asks the model whether it is uncertain. Each case is
decided by three forced head-to-head comparisons, and abstention is derived
from the structure of the results: a cycle (A beats P beats I beats A) is a
Condorcet paradox and is what 'genuinely two-headed' means operationally.

## Comparison across all three systems

| Measure | Keyword | LLM direct | Tournament | Majority |
|---|---|---|---|---|
| Accuracy, all | 47.0% | 51.8% | 44.6% | 61.4% |
| Accuracy, decided | 58.2% | 69.4% | 62.7% | — |
| Coverage | 80.7% | 74.7% | 71.1% | 100% |
| Macro-F1 | 0.471 | 0.549 | 0.488 | — |
| Abstention precision | — | 23.8% | 29.2% | — |

## Per class

| Class | n | Precision | Recall | F1 |
|---|---|---|---|---|
| ACCURACY | 51 | 0.727 | 0.471 | 0.571 |
| PERMISSIBLE-PURPOSE | 16 | 0.421 | 0.500 | 0.457 |
| INVESTIGATION | 16 | 0.714 | 0.312 | 0.435 |

## Where abstentions come from

| Structure | n |
|---|---|
| clear | 34 |
| clear_with_ties | 25 |
| tied | 13 |
| no_majority | 11 |

Abstains on guideline-ABSTAIN cases (n=16): **43.8%**
Abstains on clearly-separable cases (n=67): **25.4%**

If these two rates are close, structural abstention has the same defect as
self-reported abstention and the negative result generalises: the boundary
the guideline identifies is not recoverable by either method.