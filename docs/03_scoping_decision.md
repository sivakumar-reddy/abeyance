# Scoping Decision: Modelling Window

**Status:** Decided  
**Decision:** Restrict all modelling and evaluation to consumer narratives received on or after **2023-08-25**.  
**Applies to:** golden set sampling, classifier training, evaluation, and all reported metrics.

---

## Decision

All work on this project uses complaints received on or after 2023-08-25 that carry a consumer narrative. That is **2,312,146 narratives**, 60.4% of the 3,830,206 narratives in the full corpus, across **13 products** and **89 issues**.

## Why this date

2023-08-25 is not a round number chosen for convenience. It is the date CFPB shipped a coordinated taxonomy release. Four changes landed simultaneously:

1. `Credit reporting, credit repair services, or other personal consumer reports` was renamed to `Credit reporting or other personal consumer reports`
2. `Payday loan, title loan, or personal loan` was renamed to `Payday loan, title loan, personal loan, or advance loan`
3. `Credit card or prepaid card` was retired and split back into `Credit card` and `Prepaid card`
4. `Debt or credit management` was introduced

The handoffs are exact. The retired credit reporting label's last narrative is dated 2023-08-25 and the replacement's first narrative is dated 2023-08-25. The payday loan handoff is one day. These are renames, not coexisting categories.

An earlier boundary would straddle a taxonomy change. A later one would discard usable data for no gain.

## What the full corpus would have cost us

The corpus spans 2011-12-01 to today and contains 21 distinct Product values. That figure is misleading. The following products have no narratives inside the modelling window at all:

| Retired product | Historic narratives | Last seen |
|---|---|---|
| Credit reporting | 31,587 | 2017-04-22 |
| Payday loan, title loan, or personal loan | 17,219 | 2023-08-24 |
| Bank account or service | 14,883 | 2017-04-22 |
| Consumer Loan | 9,458 | 2017-04-21 |
| Payday loan | 1,745 | 2017-04-21 |
| Money transfers | 1,497 | 2017-04-21 |
| Other financial service | 292 | 2017-04-20 |
| Virtual currency | 16 | 2017-04-03 |

**8 of 21 products are dead label space.** Training on the full corpus would teach a model to predict categories that no longer exist, and evaluate it against a taxonomy that changed twice underneath the data. Neither failure is visible without this check.

## The window

| Measure | Value |
|---|---|
| Narratives | 2,312,146 |
| Share of all narratives | 60.4% |
| Date range | 2023-08-25 to 2026-07-27 |
| Distinct products | 13 |
| Distinct issues | 89 |
| Distinct sub-issues | 209 |

### Product distribution

| Product | Narratives | Share |
|---|---|---|
| Credit reporting or other personal consumer reports | 1,671,566 | 72.3% |
| Debt collection | 217,097 | 9.39% |
| Checking or savings account | 107,630 | 4.65% |
| Credit card | 106,871 | 4.62% |
| Money transfer, virtual currency, or money service | 86,168 | 3.73% |
| Mortgage | 36,811 | 1.59% |
| Vehicle loan or lease | 26,543 | 1.15% |
| Student loan | 26,121 | 1.13% |
| Payday loan, title loan, personal loan, or advance loan | 17,895 | 0.77% |
| Prepaid card | 10,045 | 0.43% |
| Debt or credit management | 5,383 | 0.23% |
| Credit reporting, credit repair services, or other personal consumer reports | 15 | 0.0% |
| Credit card or prepaid card | 1 | 0.0% |

### Top 10 issues

| Issue | Narratives | Share |
|---|---|---|
| Incorrect information on your report | 842,867 | 36.45% |
| Improper use of your report | 478,963 | 20.72% |
| Problem with a company's investigation into an existing problem | 349,112 | 15.1% |
| Attempts to collect debt not owed | 100,935 | 4.37% |
| Managing an account | 57,866 | 2.5% |
| Written notification about debt | 54,239 | 2.35% |
| Other transaction problem | 49,035 | 2.12% |
| Problem with a purchase shown on your statement | 27,968 | 1.21% |
| False statements or representation | 26,060 | 1.13% |
| Trouble during payment process | 19,826 | 0.86% |

### Recent monthly volume

| Month | Narratives |
|---|---|
| 2026-02 | 12,096 |
| 2026-03 | 21,594 |
| 2026-04 | 20,933 |
| 2026-05 | 16,402 |
| 2026-06 | 5,490 |
| 2026-07 | 1,463 |

## Class imbalance

| Measure | Count |
|---|---|
| Issues with fewer than 50 narratives | 7 |
| Issues with fewer than 200 narratives | 17 |
| Issues with fewer than 1,000 narratives | 31 |
| Total distinct issues | 89 |

Issues below 50 narratives in the window:

- Property was damaged or destroyed property (3)
- Lost or stolen refund (7)
- Property was sold (11)
- Was approved for a loan, but didn't receive money (37)
- Problem with overdraft (39)
- Incorrect exchange rate (45)
- Credit limit changed (48)

Classes at this volume cannot be automated responsibly. They are candidates for permanent routing to the human queue regardless of model confidence, and that exclusion is a design decision rather than a modelling failure.

## What we give up

Roughly 13 years and the majority of historic narratives. This costs nothing that matters:

- The window still contains far more narratives than the project can use. The golden set is 250 cases and the held-out evaluation sample is 1,000.
- Older narratives were written against a taxonomy no longer in use, so their labels are not valid targets.
- Complaint language and subject matter shift over 13 years. Recent data is a better match for the deployment distribution.

The one genuine loss is the ability to study long-run trends. That is out of scope for this project.

## Risk

CFPB may revise the taxonomy again during the project. The precedent is roughly one major revision every six years, with the last in August 2023, so the near-term probability is low but not zero.

**Mitigation:** `src/taxonomy_drift.py` is re-runnable. Re-running it before the final evaluation will surface any new or retired labels. If a revision lands mid-project, the window is re-cut and the golden set is re-checked against the new labels rather than silently carrying stale ones.

This is the same monitoring problem a deployed system would face, and the detection mechanism is the same one that belongs in the model card's drift plan.

## Traceability

| Artifact | Reference |
|---|---|
| Corpus profile | `docs/01_corpus_profile.md` |
| Drift evidence | `docs/02_taxonomy_drift.md` |
| Generating script | `src/scoping_decision.py` |
