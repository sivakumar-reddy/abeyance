# 14 — Intra-rater reliability

Establishes whether the hand labels are the more reliable side of the 46%
disagreement with CFPB intake tags. `10_findings.md` §8 and `12_brd.md`
ASM-1 both depend on this figure.

## Protocol deviation, disclosed

The intended design was a 48-hour gap between passes. **The re-label was
performed the same day.** In addition, 8 of the 25 cases had been re-read
hours earlier during the boundary worksheet with the first-pass labels
visible in the `my_issue` column.

The analysis is therefore stratified. The pooled figure across all 25 is
reported for completeness and **should not be quoted**.

## Issue agreement

| Stratum | n | Agree | Rate | 95% CI | Cohen's kappa |
|---|---|---|---|---|---|
| PRIMARY  — clean cases | 17 | 12 | 70.6% | [46.9%, 86.7%] | 0.555 |
| SECONDARY— worksheet-anchored | 8 | 7 | 87.5% | [52.9%, 97.8%] | 0.810 |
| POOLED   — all 25 (do not quote) | 25 | 19 | 76.0% | [56.6%, 88.5%] | 0.664 |

**Anchoring effect:** the worksheet-anchored stratum agrees +16.9% relative to the clean stratum.

## Product agreement

| Stratum | n | Agree | Rate | 95% CI |
|---|---|---|---|---|
| PRIMARY  — clean cases | 17 | 14 | 82.4% | [59.0%, 93.8%] |
| POOLED   — all 25 | 25 | 22 | 88.0% | [70.0%, 95.8%] |

## Verdict on ASM-1

Self-agreement on the primary stratum is **70.6%** (95% CI [46.9%, 86.7%], n=17), against **46.0%** agreement with CFPB intake tags.

**ASM-1: SUPPORTED**

## Limitations

- Primary stratum is n=17. The confidence interval is wide and no
  precise reliability figure should be claimed from it.
- Same-day re-labelling means even the primary stratum retains some recall
  advantage over a true 48-hour protocol. The figure is best read as an
  **upper bound** on self-consistency.
- Single rater. Inter-rater reliability with a second labeller would be a
  stronger test and was out of scope.