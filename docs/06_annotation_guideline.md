# 06 — Annotation guideline and abstention criterion

Derived from case-by-case review of the 38 boundary disagreements identified in
`04_label_noise.md` and characterised in `05_boundary_cases.md`.

---

## 1. Why a semantic rule was required

`05_signal_table.csv` tested fourteen lexical signals across three FCRA theories.
The best separated the three classes by **0.33** presence rate at n=38 — inside
noise. Two results in particular rule out a keyword approach:

| Signal | chose ACCURACY | chose INVESTIGATION | chose PERM-PURPOSE | spread |
|---|---|---|---|---|
| `permission` | 0.18 | 0.10 | 0.36 | 0.26 |
| `inaccurate` | 0.65 | 0.40 | 0.36 | 0.29 |

`permission` matches the *legal definition* of Improper use, yet appears in only
36% of cases labelled that way and in 18% of cases labelled ACCURACY.
`inaccurate` is the most common signal overall and is **most** frequent in cases
that are not primarily accuracy complaints.

The vocabulary is shared across all three classes. What differs is the
**syntactic role** the vocabulary plays: whether a term names the grievance or
names the remedy the consumer is requesting. That is not recoverable by pattern
matching, which is why the task requires reading for intent.

---

## 2. The decision rule

### The counterfactual test

For each narrative, remove the alleged defect and ask whether the consumer still
has a complaint.

| Remove this | If the complaint disappears | Label |
|---|---|---|
| The inaccuracy in the reported data | → | **ACCURACY** |
| The absence of consent or permissible purpose | → | **PERMISSIBLE-PURPOSE** |
| The company's failure to act on a prior dispute | → | **INVESTIGATION** |

### Class definitions

**ACCURACY — Incorrect information on your report**

The grievance is the *content* of the report. Investigation, verification and
deletion language routinely appears, but as the **requested remedy**, not the
complaint. Prior disputes may be described; they supply context for why the
consumer is now writing.

> "I request a full investigation into the negative items reported on my credit
> report." — the investigation is what they want done, not what went wrong.

**PERMISSIBLE-PURPOSE — Improper use of your report**

The grievance is that the furnishing or the inquiry **occurred at all**,
independent of whether the underlying data is correct. The theory is consent or
authorisation. Note that a consumer can assert this while also believing the
data is wrong; what makes it permissible-purpose is that the absence of consent
would be a complete complaint on its own.

> "I never gave any written consent to report anything on my consumer reports."

**INVESTIGATION — Problem with a company's investigation into an existing problem**

The grievance is the company's **conduct after a dispute was filed**. Two
conditions must both hold:

1. A prior dispute exists and is described
2. The complaint is about how that dispute was handled — non-response, refusal
   to act on submitted evidence, or a verification the consumer considers
   perfunctory

A prior dispute alone is not sufficient. Almost every credit-reporting
complainant has disputed something.

> "I have submitted multiple formal dispute letters… I have exhausted all
> attempts to resolve this matter directly."

### Ordering when more than one applies

If exactly one theory would survive the counterfactual test, label it. If two or
more survive independently, see §3 — do not break the tie.

---

## 3. Abstention criterion

**16 of 38 boundary cases (42%) were judged not separable by any rule.** These
are not labelling failures; they are narratives that assert two independent
legal theories, either of which would stand alone. Forcing a single label on
them fabricates a distinction the text does not contain.

Abstain when any of the following holds:

**A. Conjunctive assertion of two theories.** The narrative states both defects
as coordinate claims rather than one subordinate to the other.

> "You have reported inaccurate **and unauthorized** accounts on my credit
> report." (case 17)
> "unauthorized inquiries **and** charged off accounts on my profile." (case 11)

**B. Identity theft spanning both accuracy and consent.** Fraud makes the data
wrong *and* makes the furnishing unauthorised simultaneously. Neither is
subordinate.

> "I am a victim of identity theft and did not make the charge." (case 75)

**C. Dispute failure alongside a substantive defect.** The consumer alleges both
that the information is wrong and that the company failed to investigate, with
neither presented as the reason for the other.

> "I have mailed off letters to the credit bureaus continuously and thus far I
> have not gotten a response." — where errors are also alleged. (case 2)

Distribution of the abstention set:

| Primary reading | Abstain | Separable |
|---|---|---|
| ACCURACY | 6 | 11 |
| INVESTIGATION | 6 | 4 |
| PERMISSIBLE-PURPOSE | 4 | 7 |

INVESTIGATION is the least separable class (6 of 10 abstain), consistent with it
requiring a two-part condition that is frequently only half-satisfied.

---

## 4. Implications for evaluation

- **Abstention is expected on ~16% of the full corpus** (16 of 100 golden cases),
  concentrated entirely within credit-reporting complaints. This is the floor for
  the risk-coverage curve, established before any model was run.
- A system that produces a confident single label on category-A/B/C cases is
  **wrong even when it matches the official label**, because the official label
  is itself an arbitrary resolution of a genuine ambiguity.
- The keyword baseline is predicted to fail. `05_signal_table.csv` is the
  pre-registered reason.

---

## 5. Caveat on self-consistency

`primary_grievance` matched the first-pass label on **38 of 38** cases. This is
**not** evidence of labelling reliability: the `my_issue` column was visible in
the worksheet, so the second reading was anchored to the first.

Reliability is measured only by `blind_relabel_25.csv`, where the first-pass
labels are withheld and row order is shuffled. That result — not this one — is
what supports any claim that the hand labels are the more reliable side of the
46% disagreement with CFPB.
