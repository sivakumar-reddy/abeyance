# 07 — Keyword baseline

Pre-registered as a predicted failure in `06_annotation_guideline.md` §4.
Built to make that prediction falsifiable and to establish the floor any
semantic intervention must clear.

## Result

| Measure | Value |
|---|---|
| In-scope cases | 83 |
| Majority-class baseline (ACCURACY) | 61.4% |
| Keyword accuracy, all cases | 47.0% |
| Keyword accuracy, decided only | 58.2% |
| Coverage | 80.7% |
| Macro-F1 | 0.471 |

The keyword baseline **does not beat** always predicting the majority class.

## Per class

| Class | n | Precision | Recall | F1 |
|---|---|---|---|---|
| ACCURACY | 51 | 0.714 | 0.490 | 0.581 |
| PERMISSIBLE-PURPOSE | 16 | 0.417 | 0.625 | 0.500 |
| INVESTIGATION | 16 | 0.500 | 0.250 | 0.333 |

## Interpretation

Macro-F1 is the honest number here: accuracy is inflated by the 61%
majority class. A classifier that recovers the minority classes at all
must show macro-F1 well above what weighted keyword matching achieves.

`05_signal_table.csv` predicted this outcome from the signal spreads
alone. The failure is not a tuning problem — adding or reweighting rules
cannot recover a distinction that lives in syntactic role rather than
vocabulary.