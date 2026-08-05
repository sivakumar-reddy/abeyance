"""
Step 6 - Scoping decision memo.

Run from the project root:
    python src/scoping_decision.py

Why this exists:
    The drift analysis established that CFPB shipped a coordinated taxonomy
    release on 2023-08-25. This script computes the figures for that window
    and writes the scoping decision as a documented BRD constraint, with the
    evidence embedded rather than asserted.

Output:
    docs/03_scoping_decision.md
"""

from pathlib import Path
import sys
import duckdb

ROOT = Path(__file__).resolve().parent.parent
PARQUET = ROOT / "data" / "raw" / "complaints.parquet"
OUT_MD = ROOT / "docs" / "03_scoping_decision.md"

CUTOVER = "2023-08-25"
NARR = '"Consumer complaint narrative"'
HAS_NARR = f"{NARR} IS NOT NULL AND TRIM({NARR}) <> ''"

report = []


def emit(text=""):
    print(text)
    report.append(text)


def table(rows, headers):
    emit("| " + " | ".join(headers) + " |")
    emit("|" + "|".join(["---"] * len(headers)) + "|")
    for r in rows:
        emit("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    emit()


def main():
    if not PARQUET.exists():
        sys.exit(f"Cannot find {PARQUET}. Run profile_corpus.py first.")

    con = duckdb.connect()
    con.execute(f"""
        CREATE VIEW c AS
        SELECT *, TRY_CAST("Date received" AS DATE) AS dt
        FROM read_parquet('{PARQUET.as_posix()}')
    """)
    con.execute(f"""
        CREATE VIEW w AS
        SELECT * FROM c WHERE {HAS_NARR} AND dt >= DATE '{CUTOVER}'
    """)

    # ---- figures ---------------------------------------------------------
    full_n = con.execute(f"SELECT COUNT(*) FROM c WHERE {HAS_NARR}").fetchone()[0]
    win_n, win_prod, win_iss, win_sub, win_max = con.execute("""
        SELECT COUNT(*), COUNT(DISTINCT "Product"), COUNT(DISTINCT "Issue"),
               COUNT(DISTINCT "Sub-issue"), MAX(dt)
        FROM w
    """).fetchone()

    share = 100.0 * win_n / full_n

    rare = con.execute("""
        WITH t AS (SELECT "Issue" AS i, COUNT(*) AS n FROM w GROUP BY "Issue")
        SELECT COUNT(*) FILTER (WHERE n < 50),
               COUNT(*) FILTER (WHERE n < 200),
               COUNT(*) FILTER (WHERE n < 1000)
        FROM t
    """).fetchone()

    prods = con.execute("""
        SELECT "Product", COUNT(*) AS n,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)
        FROM w GROUP BY "Product" ORDER BY n DESC
    """).fetchall()

    dead = con.execute(f"""
        SELECT "Product", COUNT(*) AS n, MAX(dt)
        FROM c
        WHERE {HAS_NARR} AND "Product" NOT IN (SELECT DISTINCT "Product" FROM w)
        GROUP BY "Product" ORDER BY n DESC
    """).fetchall()

    top_iss = con.execute("""
        SELECT "Issue", COUNT(*) AS n,
               ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)
        FROM w GROUP BY "Issue" ORDER BY n DESC LIMIT 10
    """).fetchall()

    rare_iss = con.execute("""
        SELECT "Issue", COUNT(*) AS n
        FROM w GROUP BY "Issue" HAVING COUNT(*) < 50 ORDER BY n
    """).fetchall()

    monthly = con.execute("""
        SELECT STRFTIME(dt, '%Y-%m') AS m, COUNT(*)
        FROM w GROUP BY m ORDER BY m
    """).fetchall()
    recent = monthly[-6:] if len(monthly) >= 6 else monthly

    # ---- memo ------------------------------------------------------------
    emit("# Scoping Decision: Modelling Window")
    emit()
    emit("**Status:** Decided  ")
    emit(f"**Decision:** Restrict all modelling and evaluation to consumer "
         f"narratives received on or after **{CUTOVER}**.  ")
    emit("**Applies to:** golden set sampling, classifier training, evaluation, "
         "and all reported metrics.")
    emit()
    emit("---")
    emit()

    emit("## Decision")
    emit()
    emit(f"All work on this project uses complaints received on or after "
         f"{CUTOVER} that carry a consumer narrative. That is "
         f"**{win_n:,} narratives**, {share:.1f}% of the {full_n:,} narratives "
         f"in the full corpus, across **{win_prod} products** and "
         f"**{win_iss} issues**.")
    emit()

    emit("## Why this date")
    emit()
    emit(f"{CUTOVER} is not a round number chosen for convenience. It is the "
         "date CFPB shipped a coordinated taxonomy release. Four changes "
         "landed simultaneously:")
    emit()
    emit("1. `Credit reporting, credit repair services, or other personal consumer reports` "
         "was renamed to `Credit reporting or other personal consumer reports`")
    emit("2. `Payday loan, title loan, or personal loan` was renamed to "
         "`Payday loan, title loan, personal loan, or advance loan`")
    emit("3. `Credit card or prepaid card` was retired and split back into "
         "`Credit card` and `Prepaid card`")
    emit("4. `Debt or credit management` was introduced")
    emit()
    emit("The handoffs are exact. The retired credit reporting label's last "
         "narrative is dated 2023-08-25 and the replacement's first narrative "
         "is dated 2023-08-25. The payday loan handoff is one day. These are "
         "renames, not coexisting categories.")
    emit()
    emit("An earlier boundary would straddle a taxonomy change. A later one "
         "would discard usable data for no gain.")
    emit()

    emit("## What the full corpus would have cost us")
    emit()
    emit("The corpus spans 2011-12-01 to today and contains 21 distinct Product "
         "values. That figure is misleading. The following products have no "
         "narratives inside the modelling window at all:")
    emit()
    table(
        [(p, f"{n:,}", str(d)) for p, n, d in dead],
        ["Retired product", "Historic narratives", "Last seen"],
    )
    emit(f"**{len(dead)} of 21 products are dead label space.** Training on the "
         "full corpus would teach a model to predict categories that no longer "
         "exist, and evaluate it against a taxonomy that changed twice "
         "underneath the data. Neither failure is visible without this check.")
    emit()

    emit("## The window")
    emit()
    table(
        [
            ("Narratives", f"{win_n:,}"),
            ("Share of all narratives", f"{share:.1f}%"),
            ("Date range", f"{CUTOVER} to {win_max}"),
            ("Distinct products", win_prod),
            ("Distinct issues", win_iss),
            ("Distinct sub-issues", win_sub),
        ],
        ["Measure", "Value"],
    )

    emit("### Product distribution")
    emit()
    table([(p, f"{n:,}", f"{s}%") for p, n, s in prods],
          ["Product", "Narratives", "Share"])

    emit("### Top 10 issues")
    emit()
    table([(i, f"{n:,}", f"{s}%") for i, n, s in top_iss],
          ["Issue", "Narratives", "Share"])

    emit("### Recent monthly volume")
    emit()
    table([(m, f"{n:,}") for m, n in recent], ["Month", "Narratives"])

    emit("## Class imbalance")
    emit()
    table(
        [
            ("Issues with fewer than 50 narratives", rare[0]),
            ("Issues with fewer than 200 narratives", rare[1]),
            ("Issues with fewer than 1,000 narratives", rare[2]),
            ("Total distinct issues", win_iss),
        ],
        ["Measure", "Count"],
    )
    if rare_iss:
        emit("Issues below 50 narratives in the window:")
        emit()
        for i, n in rare_iss:
            emit(f"- {i} ({n})")
        emit()
    emit("Classes at this volume cannot be automated responsibly. They are "
         "candidates for permanent routing to the human queue regardless of "
         "model confidence, and that exclusion is a design decision rather "
         "than a modelling failure.")
    emit()

    emit("## What we give up")
    emit()
    emit("Roughly 13 years and the majority of historic narratives. This costs "
         "nothing that matters:")
    emit()
    emit("- The window still contains far more narratives than the project can "
         "use. The golden set is 250 cases and the held-out evaluation sample "
         "is 1,000.")
    emit("- Older narratives were written against a taxonomy no longer in use, "
         "so their labels are not valid targets.")
    emit("- Complaint language and subject matter shift over 13 years. Recent "
         "data is a better match for the deployment distribution.")
    emit()
    emit("The one genuine loss is the ability to study long-run trends. That is "
         "out of scope for this project.")
    emit()

    emit("## Risk")
    emit()
    emit("CFPB may revise the taxonomy again during the project. The precedent "
         "is roughly one major revision every six years, with the last in "
         "August 2023, so the near-term probability is low but not zero.")
    emit()
    emit("**Mitigation:** `src/taxonomy_drift.py` is re-runnable. Re-running it "
         "before the final evaluation will surface any new or retired labels. "
         "If a revision lands mid-project, the window is re-cut and the golden "
         "set is re-checked against the new labels rather than silently "
         "carrying stale ones.")
    emit()
    emit("This is the same monitoring problem a deployed system would face, and "
         "the detection mechanism is the same one that belongs in the model "
         "card's drift plan.")
    emit()

    emit("## Traceability")
    emit()
    emit("| Artifact | Reference |")
    emit("|---|---|")
    emit("| Corpus profile | `docs/01_corpus_profile.md` |")
    emit("| Drift evidence | `docs/02_taxonomy_drift.md` |")
    emit("| Generating script | `src/scoping_decision.py` |")
    emit()

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(report), encoding="utf-8")
    print(f"\nWritten to {OUT_MD}")


if __name__ == "__main__":
    main()
