# Abeyance — triage console

A review interface for the evaluation programme in the parent repository. Paste a
consumer credit-reporting complaint; the system routes it to one of three
grievance categories, or declines.

**The refusal is the product.** Two of the five loaded examples are cases the
annotation guideline marks unresolvable — they assert two legal theories, neither
subordinate to the other. Those return a file stamp rather than a label, and no
acknowledgment letter is drafted for them.

---

## What it does

**Stage 1 — route.** Applies the counterfactual test from
`docs/06_annotation_guideline.md`: remove the alleged defect and ask whether the
complainant still has a complaint. Returns a category, a confidence, and the
sentence naming which defect ends the complaint. Or returns ABSTAIN.

**Stage 2 — draft.** For routed cases only, retrieves the applicable FCRA
provisions and drafts an acknowledgment letter, then runs four deterministic
checks over it:

| Check | Prevents |
|---|---|
| Every citation was retrieved | Citing a provision from training data rather than context |
| No figure absent from the source | Inventing a deadline that sounds plausible |
| All five required elements present | An acknowledgment missing the case reference or timeline |
| No commitment before investigation | Promising removal, conceding fault, asserting a violation |

The checks are ported from `18_draft_generation.py` **including the three
patterns that exist only because a red-team attack got through an earlier
version** — indirect overcommitment, spelled-out fabricated numbers, and asserted
legal conclusions. The JavaScript port was verified against the same fixtures as
the Python original.

Checks run **downstream of generation**. During red-teaming one prompt injection
successfully steered the model, and the output was still caught before it could
reach a person. Injection resistance and output validation are separate defences.

---

## Run locally

```bash
npm install
cp .env.example .env.local     # add your key
npm run dev
```

Open http://localhost:3000.

## Deploy to Vercel

```bash
vercel
```

Then set `ANTHROPIC_API_KEY` in Project Settings → Environment Variables.

**The key is server-side only.** It is read in `app/api/triage/route.js` and
never sent to the browser. Do not prefix it with `NEXT_PUBLIC_`.

---

## Files

```
app/
  layout.js               fonts and document shell
  page.js                 the console
  globals.css             docket palette, stamp signature
  api/triage/route.js     server-side Anthropic calls
lib/
  triage.js               prompts, provisions, deterministic checks
```

---

## What this is not

This is an evaluation build and is **not approved for deployment**. Measured
accuracy on the three-class task is 51.8%, below the 61.4% you get by always
guessing the largest class. The system's macro-F1 advantage over a keyword
baseline is the only comparison in the programme that survives its own error
bars.

One failure remains unmitigated: a draft can restate the *wrong* grievance —
fluent, correctly cited, and about a complaint the consumer never made. No
deterministic check catches it, and the LLM judge tested on it did not either.
See `docs/21_governance.md` §2, failure D8.
