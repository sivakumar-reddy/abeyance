# 04 — Label noise analysis

Golden set: **100 hand-labelled cases**. Matched in parquet: **100**.

## Headline

| Measure | Agreement |
|---|---|
| Product | 85.0% |
| Issue | 46.0% |
| Issue, conditional on product agreeing (n=85) | 51.8% |
| Both | 44.0% |

CFPB product and issue labels are selected by the consumer at intake, not
assigned by a reviewer. Divergence from expert reading is therefore expected
and is a property of the data, not an error in either party. The size of the
divergence bounds what any classifier trained on these labels can achieve:
a model scored against the official labels cannot exceed this agreement rate
without learning the intake artefact rather than the underlying grievance.

## Most frequent issue confusions

| Official (consumer-selected) | Hand label | n |
|---|---|---|
| Problem with a company's investigation into an existing problem | Incorrect information on your report | 9 |
| Incorrect information on your report | Improper use of your report | 9 |
| Improper use of your report | Incorrect information on your report | 8 |
| Incorrect information on your report | Problem with a company's investigation into an existing problem | 7 |
| Improper use of your report | Problem with a company's investigation into an existing problem | 3 |
| Problem with a company's investigation into an existing problem | Improper use of your report | 2 |
| Attempts to collect debt not owed | Incorrect information on your report | 2 |
| Took or threatened to take negative or legal action | False statements or representation | 1 |
| Other transaction problem | Other service problem | 1 |
| Getting a credit card | Incorrect information on your report | 1 |
| Advertising and marketing, including promotional offers | Incorrect information on your report | 1 |
| Attempts to collect debt not owed | False statements or representation | 1 |

## Files

- `04_disagreements.csv` — every disagreeing case with truncated narrative
- `04_issue_confusion.csv` — full confusion matrix, official rows x hand-label columns

## Caveats

- Support is concentrated: the golden set covers 14 of 89 issues and 7 of 13 products.
- Nine issue classes have n=1; no per-class rate should be quoted for them.
- Single labeller, single pass. Intra-rater reliability is measured separately
  by the blind re-label subset and is required before any human ceiling is claimed.