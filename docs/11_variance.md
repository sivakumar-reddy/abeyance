# 11 — Run-to-run variance

Intervention 1 re-run 3 times against independent caches. Sonnet 5
does not accept a temperature parameter, so identical prompts can return
different labels. This quantifies how much.

## Per run

| Run | n | Accuracy | Macro-F1 | Coverage | Abstention precision |
|---|---|---|---|---|---|
| 1 | 83 | 51.8% | 0.549 | 74.7% | 23.8% |
| 2 | 83 | 54.2% | 0.571 | 78.3% | 16.7% |
| 3 | 83 | 49.4% | 0.525 | 73.5% | 22.7% |

## Spread

| Metric | Mean | Min | Max | Range | SD |
|---|---|---|---|---|---|
| `accuracy` | 0.518 | 0.494 | 0.542 | **0.048** | 0.024 |
| `accuracy_decided` | 0.686 | 0.672 | 0.694 | **0.021** | 0.012 |
| `coverage` | 0.755 | 0.735 | 0.783 | **0.048** | 0.025 |
| `macro_f1` | 0.548 | 0.525 | 0.571 | **0.046** | 0.023 |
| `f1_ACCURACY` | 0.644 | 0.629 | 0.652 | **0.023** | 0.013 |
| `f1_PERM` | 0.527 | 0.467 | 0.581 | **0.114** | 0.057 |
| `f1_INVEST` | 0.474 | 0.462 | 0.480 | **0.018** | 0.011 |
| `abstain_on_ambiguous` | 0.271 | 0.188 | 0.312 | **0.125** | 0.072 |
| `abstain_on_clear` | 0.239 | 0.224 | 0.254 | **0.030** | 0.015 |
| `abstention_precision` | 0.211 | 0.167 | 0.238 | **0.071** | 0.038 |

## How to read this

Where the range is comparable to the difference between systems reported in
`10_findings.md` §5, that difference is not established by a single run. The
keyword-to-LLM macro-F1 gap there is **0.078**; any metric whose range
approaches that magnitude should be quoted as an interval, and the
corresponding comparison re-stated as undetermined.

Note that this measures sampling variance only. It does not address the
statistical power problem in §6, which is a property of the golden set size
and is unaffected by re-running the model.