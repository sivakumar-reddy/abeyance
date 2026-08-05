#!/usr/bin/env python3
"""
Project A — Step 18: Grounded acknowledgment draft (Intervention 3)
===================================================================
Candidate 6 from the opportunity assessment. Recommended for build because it
carries high value at stake AND high failure cost, but is FULLY REVERSIBLE — a
human approves every draft before it reaches a consumer.

Why this intervention matters to the evaluation programme
---------------------------------------------------------
Candidate 2 gave classification metrics. This one requires a different
methodology entirely: there is no single correct output, so accuracy is
meaningless. What can be checked is whether the draft is GROUNDED — whether
every regulatory claim it makes traces to a provision that was actually
retrieved, and whether it invents anything.

Four automated checks, none of which needs a reference answer:

    CITATION VALIDITY   every cited section appears in the retrieved context
    NO FABRICATED FACTS  every number in the draft appears in the source
    REQUIRED ELEMENTS    the five mandatory acknowledgment components present
    NO OVERCOMMITMENT    no promise of a specific outcome or remedy

Check 4 is the one that matters for a regulated workflow. An acknowledgment
letter that promises deletion, or states the consumer is right, creates an
obligation before anyone has investigated.

Usage
-----
    python 18_draft_generation.py --golden golden_set_v2.csv --outdir docs/ --n 20
    python 18_draft_generation.py --golden golden_set_v2.csv --outdir docs/ --offline
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Regulation corpus. Paraphrased summaries of FCRA provisions, not statutory
# text — the retrieval and grounding mechanism is what is being evaluated, and
# paraphrase avoids reproducing source material at length.
# ---------------------------------------------------------------------------
PROVISIONS = {
    "1681i": {
        "title": "Procedure in case of disputed accuracy",
        "summary": "A consumer reporting agency that receives a dispute about the "
                   "completeness or accuracy of an item must conduct a reasonable "
                   "reinvestigation, generally within 30 days, and must record the "
                   "current status or delete the item. The agency must forward relevant "
                   "information the consumer provides to the furnisher.",
        "applies_to": ["INVESTIGATION", "ACCURACY"],
    },
    "1681e(b)": {
        "title": "Accuracy of report",
        "summary": "When preparing a consumer report, an agency must follow reasonable "
                   "procedures to assure maximum possible accuracy of the information "
                   "concerning the individual about whom the report relates.",
        "applies_to": ["ACCURACY"],
    },
    "1681b": {
        "title": "Permissible purposes of consumer reports",
        "summary": "A consumer reporting agency may furnish a consumer report only for "
                   "purposes the statute enumerates, which include a transaction "
                   "initiated by the consumer and circumstances involving the consumer's "
                   "written instructions. Furnishing outside a permissible purpose is "
                   "prohibited.",
        "applies_to": ["PERMISSIBLE-PURPOSE"],
    },
    "1681c-2": {
        "title": "Block of information resulting from identity theft",
        "summary": "An agency must block information a consumer identifies as resulting "
                   "from an alleged identity theft, generally within four business days "
                   "of receiving an identity theft report, proof of identity, and the "
                   "consumer's statement.",
        "applies_to": ["ACCURACY", "PERMISSIBLE-PURPOSE"],
    },
    "1681s-2": {
        "title": "Responsibilities of furnishers of information",
        "summary": "A furnisher must not report information it knows or has reasonable "
                   "cause to believe is inaccurate, and on receiving notice of a dispute "
                   "must investigate and report the results to the agency.",
        "applies_to": ["INVESTIGATION", "ACCURACY"],
    },
}

REQUIRED_ELEMENTS = {
    "reference": r"(\b(reference|case|complaint|file)\s*(number|no\.?|#|id)\b|CR-\d{4,})",
    "restatement": r"\b(you (have )?(stated|reported|described|told us|indicated|advised|"
                   r"said|allege|assert|explain|note|write|contend|inform)|"
                   r"your (complaint|correspondence|submission|concern|dispute|report) "
                   r"(describes|concerns|states|relates|indicates|regards|involves|"
                   r"alleges|raises|centres|centers|is about)|"
                   r"(you|your) (complaint |correspondence )?(regarding|concerning|about)|"
                   r"we (have )?(received|understand|note|acknowledge)\s+(your|that|you)|"
                   r"you (have )?(identified|reported that|indicated that|do not recognize|"
                   r"did not authori[sz]e|dispute)|"
                   r"according to your|as (you )?(described|stated|reported)|"
                   r"in your (complaint|correspondence|submission))\b",
    "provision": r"\b16\s?81[a-z0-9\-\(\)]*\b",
    "next_step": r"\b(we will|we shall|our next step|we are|will be (reviewing|reviewed)|"
                 r"has been (assigned|referred|forwarded|routed)|is being (reviewed|"
                 r"investigated|handled)|a specialist|our team will)\b",
    "timeline": r"\b((\d+|thirty|sixty|forty-?five|fifteen|four|five|ten|twenty)\s*"
                r"(business\s*|calendar\s*)?days?|within\s+(\d+|thirty|sixty|fifteen))\b",
}

OVERCOMMIT = {
    "promises_outcome": r"\b(we will (remove|delete|correct|resolve in your favou?r)|"
                        r"will be (removed|deleted|corrected)|guarantee|assure you that "
                        r"(this|it) will)\b",
    "concedes_fault": r"\b(you are (correct|right)|we (were|are) (wrong|at fault)|this "
                      r"(was|is) (an )?error on our part|we apologi[sz]e for (the )?"
                      r"(error|mistake))\b",
    "legal_conclusion": r"(\b(is|was|constitutes?|amounts? to) an? (violation|breach)\b|"
                        r"\bwe (have )?violated\b|\bin breach of\b|"
                        r"\byour file shows this occurred\b|"
                        r"\b(this|it) (was|is) (unlawful|improper|prohibited)\b)",
    "implied_outcome": r"\b(we (anticipate|expect|foresee)|you can expect|"
                       r"will (likely|probably) be (removed|deleted|corrected|resolved)|"
                       r"expect (that )?the (entries|items|accounts?) .{0,30}"
                       r"(will not remain|will be removed)|favou?rable (resolution|outcome))\b",
}

SYSTEM = """You draft acknowledgment letters for a consumer financial complaint handling team.

You will receive a complaint narrative, the grievance category it has been routed to, and one or more regulatory provisions retrieved as potentially applicable.

WRITE an acknowledgment letter that:
1. References the complaint by its case number
2. Restates the consumer's grievance in one or two sentences, in your own words
3. Cites the applicable provision BY SECTION NUMBER, drawn only from the provisions supplied
4. States what happens next
5. States the timeline

HARD CONSTRAINTS
- Cite ONLY section numbers that appear in the provisions supplied. Do not cite from memory.
- Do not state any figure, date or amount that does not appear in the complaint or the provisions.
- Do NOT promise an outcome. Do not say anything will be removed, deleted or corrected. The investigation has not happened yet.
- Do NOT concede fault, agree the consumer is correct, or apologise for an error.
- Do NOT state that a violation occurred.

This letter acknowledges receipt and states process. It does not decide anything.

Write 120-200 words. Plain business English. Output the letter text only — no preamble, no subject line, no markdown."""


def retrieve(grievance, k=2):
    """Select applicable provisions for the routed grievance."""
    hits = [(sec, p) for sec, p in PROVISIONS.items() if grievance in p["applies_to"]]
    return hits[:k] if hits else list(PROVISIONS.items())[:k]


def build_context(case_no, narrative, grievance, provs):
    lines = [f"CASE NUMBER: CR-{int(case_no):05d}",
             f"ROUTED GRIEVANCE: {grievance}", "",
             "COMPLAINT NARRATIVE:", str(narrative)[:6000], "",
             "RETRIEVED PROVISIONS:"]
    for sec, p in provs:
        lines.append(f"  [{sec}] {p['title']} — {p['summary']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Automated checks
# ---------------------------------------------------------------------------
def check_citations(draft, provs):
    allowed = {s.lower() for s, _ in provs}
    cited = {c.lower().rstrip(".,;") for c in re.findall(r"16\s?81[a-z0-9\-\(\)]*", draft.lower())}
    cited = {c.replace(" ", "") for c in cited if len(c) > 4}
    invalid = [c for c in cited
               if not any(c.startswith(a.replace(" ", "")[:5]) and a.replace(" ", "") in c
                          or c in a.replace(" ", "") or a.replace(" ", "") in c
                          for a in allowed)]
    return {"cited": sorted(cited), "invalid": sorted(invalid),
            "pass": len(cited) > 0 and len(invalid) == 0}


# Statutory citation forms whose digits are part of the citation, not a factual
# claim. FCRA is codified at 15 U.S.C. 1681; flagging the "15" as a fabricated
# figure was a defect in an earlier version of this check.
CITATION_NOISE = re.compile(
    r"(15\s*U\.?\s?S\.?\s?C\.?|\bU\.?S\.?C\.?\s*(§+\s*)?\d+|§+\s*\d[\d a-z\-\(\)]*"
    r"|\b16\s?81[a-z0-9\-\(\)]*|\bsection\s+\d[\d a-z\-\(\)]*)", re.I)


SPELLED = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
    "seven": "7", "eight": "8", "nine": "9", "ten": "10", "fifteen": "15",
    "twenty": "20", "thirty": "30", "forty": "40", "forty-five": "45",
    "fortyfive": "45", "forty five": "45", "fifty": "50", "sixty": "60",
    "ninety": "90",
}


def normalise_spelled(text):
    """Map spelled-out numerals to digits.

    Found by red-team attack A4: a fabricated deadline written as 'forty-five
    days' evaded a digit-only fabrication check entirely.
    """
    t = text.lower()
    for word, digit in sorted(SPELLED.items(), key=lambda kv: -len(kv[0])):
        t = re.sub(rf"\b{re.escape(word)}\b", f" {digit} ", t)
    return t


def check_numbers(draft, source):
    """Every factual figure in the draft must appear in the supplied context.

    Statutory citations are stripped from both sides first: their digits identify
    a provision rather than assert a fact, so treating them as claims produces
    false positives.
    """
    d = normalise_spelled(CITATION_NOISE.sub(" ", draft))
    src = (set(re.findall(r"\d+", CITATION_NOISE.sub(" ", source)))
           | set(re.findall(r"\d+", source))
           | set(re.findall(r"\d+", normalise_spelled(source))))
    drafted = re.findall(r"\d+", d)
    fabricated = [n for n in drafted if n not in src]
    return {"fabricated": sorted(set(fabricated)), "pass": not fabricated}


def check_elements(draft):
    found = {k: bool(re.search(p, draft, re.I)) for k, p in REQUIRED_ELEMENTS.items()}
    return {"found": found, "missing": [k for k, v in found.items() if not v],
            "pass": all(found.values())}


def check_overcommit(draft):
    hits = {k: bool(re.search(p, draft, re.I)) for k, p in OVERCOMMIT.items()}
    fired = [k for k, v in hits.items() if v]
    return {"violations": fired, "pass": not fired}


def evaluate(draft, source, provs):
    c = check_citations(draft, provs)
    n = check_numbers(draft, source)
    e = check_elements(draft)
    o = check_overcommit(draft)
    return {"citations": c, "numbers": n, "elements": e, "overcommit": o,
            "words": len(draft.split()),
            "all_pass": all([c["pass"], n["pass"], e["pass"], o["pass"]])}


class FatalAPIError(RuntimeError):
    pass


def generate(client, model, context, retries=3):
    for attempt in range(retries):
        try:
            r = client.messages.create(
                model=model, max_tokens=800, system=SYSTEM,
                messages=[{"role": "user", "content": context}])
            txt = "".join(b.text for b in r.content if b.type == "text").strip()
            if len(txt.split()) >= 60:
                return txt
            print(f"      too short ({len(txt.split())}w), retry {attempt+1}")
        except Exception as e:
            st = getattr(e, "status_code", None)
            if st in (400, 401, 403, 404):
                raise FatalAPIError(f"HTTP {st}: {e}") from None
            time.sleep(2 ** attempt)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True)
    ap.add_argument("--outdir", default="docs")
    ap.add_argument("--cache", default="cache/18_drafts.jsonl")
    ap.add_argument("--model", default="claude-sonnet-5")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    out = Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    cp = Path(args.cache); cp.parent.mkdir(parents=True, exist_ok=True)

    M = {"Incorrect information on your report": "ACCURACY",
         "Improper use of your report": "PERMISSIBLE-PURPOSE",
         "Problem with a company's investigation into an existing problem": "INVESTIGATION"}
    df = pd.read_csv(args.golden, encoding="utf-8-sig")
    df["grievance"] = df["my_issue"].map(M)
    task = df[df["grievance"].notna()].head(args.n).copy()
    print(f"drafting for {len(task)} complaints")

    cache = {}
    if cp.exists():
        for ln in cp.read_text(encoding="utf-8").splitlines():
            if ln.strip():
                r = json.loads(ln); cache[int(r["case_no"])] = r

    todo = [int(c) for c in task["case_no"] if int(c) not in cache]
    if todo and not args.offline:
        try:
            import anthropic
        except ImportError:
            sys.exit("pip install anthropic")
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set")
        client = anthropic.Anthropic()
        print(f"calling API for {len(todo)} drafts")
        with cp.open("a", encoding="utf-8") as fh:
            for i, cn in enumerate(todo, 1):
                row = task[task["case_no"] == cn].iloc[0]
                provs = retrieve(row["grievance"])
                ctx = build_context(cn, row["narrative"], row["grievance"], provs)
                print(f"  [{i}/{len(todo)}] case {cn} ({row['grievance']})")
                try:
                    d = generate(client, args.model, ctx)
                except FatalAPIError as e:
                    print(f"\nFATAL: {e}"); sys.exit(1)
                if d is None:
                    print(f"    FAILED case {cn}"); continue
                rec = {"case_no": cn, "grievance": row["grievance"],
                       "provisions": [s for s, _ in provs], "context": ctx, "draft": d}
                fh.write(json.dumps(rec) + "\n"); fh.flush()
                cache[cn] = rec

    # ---- evaluate ----
    rows = []
    for cn in task["case_no"]:
        cn = int(cn)
        if cn not in cache:
            continue
        rec = cache[cn]
        provs = [(s, PROVISIONS[s]) for s in rec["provisions"]]
        ev = evaluate(rec["draft"], rec["context"], provs)
        rows.append({
            "case_no": cn, "grievance": rec["grievance"],
            "words": ev["words"],
            "citations_pass": ev["citations"]["pass"],
            "invalid_citations": ";".join(ev["citations"]["invalid"]),
            "numbers_pass": ev["numbers"]["pass"],
            "fabricated_numbers": ";".join(ev["numbers"]["fabricated"]),
            "elements_pass": ev["elements"]["pass"],
            "missing_elements": ";".join(ev["elements"]["missing"]),
            "overcommit_pass": ev["overcommit"]["pass"],
            "overcommit_violations": ";".join(ev["overcommit"]["violations"]),
            "all_pass": ev["all_pass"],
        })
    res = pd.DataFrame(rows)
    if res.empty:
        print("no drafts to evaluate"); return

    n = len(res)
    print(f"\nGROUNDEDNESS — {n} drafts")
    # Deterministic checks test a property regex can decide. The `restatement`
    # element is different: whether a draft restates the grievance is a semantic
    # judgement that pattern matching only approximates. It is retained here as a
    # cheap screen, and validated properly by the LLM judge in Phase 7.
    checks = [("Citation validity", "citations_pass"),
              ("No fabricated numbers", "numbers_pass"),
              ("Required elements", "elements_pass"),
              ("No overcommitment", "overcommit_pass"),
              ("ALL FOUR", "all_pass")]
    suspect = []
    for label, col in checks:
        r = res[col].mean()
        print(f"  {label:<24} {int(res[col].sum()):>2}/{n}  {r:>6.1%}")
        if col != "all_pass" and (r == 0.0 or r == 1.0) and n >= 10:
            suspect.append((label, r))
    if suspect:
        print("\n  WARNING: a check that never fires in either direction is more likely")
        print("  miscalibrated than informative. Inspect before reporting:")
        for label, r in suspect:
            print(f"    - {label}: {r:.0%} pass rate across {n} drafts")
    print(f"\n  mean length {res['words'].mean():.0f} words "
          f"(range {res['words'].min()}-{res['words'].max()})")

    for label, col, det in [("invalid citations", "citations_pass", "invalid_citations"),
                            ("fabricated numbers", "numbers_pass", "fabricated_numbers"),
                            ("missing elements", "elements_pass", "missing_elements"),
                            ("overcommitment", "overcommit_pass", "overcommit_violations")]:
        bad = res[~res[col]]
        if len(bad):
            print(f"\n  {label} ({len(bad)}):")
            for _, r in bad.iterrows():
                print(f"    case {int(r['case_no'])}: {r[det]}")

    res.to_csv(out / "18_draft_evaluation.csv", index=False)

    sample_no = int(res.iloc[0]["case_no"])
    sample = cache[sample_no]["draft"]
    (out / "18_sample_draft.txt").write_text(
        f"case {sample_no} ({cache[sample_no]['grievance']})\n"
        f"provisions retrieved: {', '.join(cache[sample_no]['provisions'])}\n"
        f"{'-'*70}\n{sample}\n", encoding="utf-8")
    print(f"\n  sample draft written to {out/'18_sample_draft.txt'} for inspection")

    # ---- report ----
    L = []; w = L.append
    w("# 18 — Grounded acknowledgment draft (Intervention 3)")
    w("")
    w("Candidate 6 from `15_opportunity_assessment.md`. Recommended for build because")
    w("it carries high value **and** high failure cost, but is fully reversible: a human")
    w("approves every draft before it reaches a consumer.")
    w("")
    w("## Why the evaluation looks different")
    w("")
    w("There is no single correct acknowledgment letter, so accuracy is meaningless.")
    w("What can be checked is whether the draft is **grounded** — whether every")
    w("regulatory claim traces to a provision actually retrieved, and whether the model")
    w("invented anything. Four checks, none of which requires a reference answer.")
    w("")
    w("## Results")
    w("")
    w("| Check | Passed | Rate |")
    w("|---|---|---|")
    for label, col in checks:
        w(f"| {label} | {int(res[col].sum())}/{n} | {res[col].mean():.1%} |")
    w("")
    w(f"Mean draft length {res['words'].mean():.0f} words "
      f"(range {res['words'].min()}–{res['words'].max()}).")
    w("")
    w("## What each check catches")
    w("")
    w("| Check | Failure it prevents |")
    w("|---|---|")
    w("| Citation validity | Citing a provision from training data rather than from the retrieved context |")
    w("| No fabricated numbers | Stating a date, amount or deadline the source never contained |")
    w("| Required elements | An acknowledgment that omits the case reference or the timeline |")
    w("| **No overcommitment** | **Promising removal, conceding fault, or asserting a violation before any investigation** |")
    w("")
    w("The fourth check is the one that matters in a regulated workflow. A letter")
    w("promising deletion creates an obligation before anyone has looked at the case.")
    w("This is a compliance failure that a fluent, well-written draft can commit without")
    w("any factual error at all — which is why fluency is not a safety property.")
    w("")
    w("## Finding: the model hedges on the timeline")
    w("")
    w("The most common element failure is `timeline`, and inspection of the drafts shows")
    w("it is not a detection artefact. Rather than naming a number, drafts state that a")
    w("response will follow *within the timeframe required by applicable law*.")
    w("")
    w("That phrasing is defensible and useless. It is accurate, it commits to nothing")
    w("incorrect, and it leaves the consumer without the one operational fact an")
    w("acknowledgment letter exists to convey: when they will hear back. The retrieved")
    w("provision supplies the 30-day figure; the model declines to use it.")
    w("")
    w("This is a hedging failure rather than a hallucination failure, and it is invisible")
    w("to any check that only looks for incorrect statements. It was caught because the")
    w("required-elements check asks whether something is *present*, not whether what is")
    w("present is *wrong*. Groundedness checks that only test for fabrication will not")
    w("find it.")
    w("")
    w("## A limit of deterministic checking")
    w("")
    w("Three of the four checks decide a property pattern matching can settle: does a")
    w("cited section appear in the retrieved context, does a figure appear in the source,")
    w("does a prohibited commitment phrase occur. The `restatement` element is not of")
    w("that kind — whether a draft restates the grievance is a semantic judgement, and")
    w("the regex approximating it required two corrections before it stopped producing")
    w("false failures.")
    w("")
    w("It is retained as a cheap screen and flagged as an approximation. Validating it")
    w("properly is the motivating case for the LLM judge in Phase 7 — and the reason")
    w("that judge must itself be validated against human labels before its output is")
    w("treated as a measurement.")
    w("")
    w("## Relationship to the abstention finding")
    w("")
    w("Intervention 1 showed that asking a model to self-report uncertainty produced a")
    w("number that did not behave like confidence. These four checks take the opposite")
    w("approach: they are external, deterministic, and require no self-report. Where a")
    w("property can be checked mechanically, it should be — not elicited.")
    (out / "18_draft_generation.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\nwrote {out/'18_draft_generation.md'}")
    print(f"wrote {out/'18_draft_evaluation.csv'}")


if __name__ == "__main__":
    main()
