// Shared logic between the API route and the UI.
// Ported directly from 08_llm_classifier.py, 18_draft_generation.py and the
// hardening applied after the red-team log in 20_red_team.py.

export const CLASSES = ["ACCURACY", "PERMISSIBLE-PURPOSE", "INVESTIGATION"];

export const CLASS_LABEL = {
  ACCURACY: "Incorrect information on your report",
  "PERMISSIBLE-PURPOSE": "Improper use of your report",
  INVESTIGATION: "Problem with a company's investigation",
  WITHHELD: "Withheld for human review",
};

export const THEORY_NAME = {
  ACCURACY: "Accuracy",
  "PERMISSIBLE-PURPOSE": "Permissible purpose",
  INVESTIGATION: "Investigation conduct",
};

export const ROUTE_SYSTEM = `You adjudicate US consumer credit-reporting complaints. You do not classify text. You test three competing legal theories against the narrative and report which survive.

THE THREE THEORIES

ACCURACY — the grievance is the CONTENT of the report. Investigation and deletion language often appears, but as the REMEDY requested, not the complaint.

PERMISSIBLE-PURPOSE — the grievance is that the furnishing or inquiry OCCURRED AT ALL, independent of whether the data is correct. The theory is consent.

INVESTIGATION — the grievance is the company's CONDUCT AFTER a dispute was filed. Two conditions must BOTH hold: a prior dispute is described, and the complaint is about how it was handled. A prior dispute alone is not sufficient.

THE COUNTERFACTUAL TEST

For EACH theory, remove the defect it names and ask whether the complainant still has a complaint.
- If removing that defect ends the complaint, the theory SURVIVES.
- If the complaint stands regardless, the theory FALLS AWAY.

DETERMINATION

Exactly one survivor  → that theory is the determination.
Two or more survivors → WITHHELD. Each would be a complete complaint standing alone, and choosing between them fabricates a distinction the narrative does not contain. Do not break the tie.
No survivors          → WITHHELD.

For each theory write the test in ONE clause naming the specific thing in this narrative. Not a definition. For example: "Remove the unauthorised inquiries and the complaint about incorrect balances remains."

WRITING CONSTRAINT
Never use a dash of any kind. No em dashes, no en dashes, no hyphens. Write compound words as separate words or choose a different word. Use commas, semicolons or separate sentences instead.

OUTPUT
JSON only. No preamble, no markdown fences.
{"theories":[{"id":"ACCURACY","survives":true|false,"test":"<one clause>"},{"id":"PERMISSIBLE-PURPOSE","survives":true|false,"test":"<one clause>"},{"id":"INVESTIGATION","survives":true|false,"test":"<one clause>"}],"determination":"ACCURACY"|"PERMISSIBLE-PURPOSE"|"INVESTIGATION"|"WITHHELD","confidence":<0.0-1.0>,"rationale":"<one sentence explaining the determination>"}`;

export const PROVISIONS = {
  "1681i": {
    title: "Procedure in case of disputed accuracy",
    summary:
      "A consumer reporting agency that receives a dispute about the completeness or accuracy of an item must conduct a reasonable reinvestigation, generally within 30 days, and must record the current status or delete the item.",
    appliesTo: ["INVESTIGATION", "ACCURACY"],
  },
  "1681e(b)": {
    title: "Accuracy of report",
    summary:
      "When preparing a consumer report, an agency must follow reasonable procedures to assure maximum possible accuracy of the information concerning the individual.",
    appliesTo: ["ACCURACY"],
  },
  "1681b": {
    title: "Permissible purposes of consumer reports",
    summary:
      "A consumer reporting agency may furnish a consumer report only for purposes the statute enumerates. Furnishing outside a permissible purpose is prohibited.",
    appliesTo: ["PERMISSIBLE-PURPOSE"],
  },
  "1681c-2": {
    title: "Block of information resulting from identity theft",
    summary:
      "An agency must block information a consumer identifies as resulting from an alleged identity theft, generally within four business days of receiving an identity theft report and proof of identity.",
    appliesTo: ["ACCURACY", "PERMISSIBLE-PURPOSE"],
  },
};

export function retrieve(grievance, k = 2) {
  const hits = Object.entries(PROVISIONS).filter(([, p]) =>
    p.appliesTo.includes(grievance)
  );
  return (hits.length ? hits : Object.entries(PROVISIONS)).slice(0, k);
}

export const DRAFT_SYSTEM = `You draft acknowledgment letters for a consumer financial complaint handling team.

WRITE a letter that:
1. References the complaint by its case number
2. Restates the consumer's grievance in one or two sentences, in your own words
3. Cites the applicable provision BY SECTION NUMBER, drawn only from the provisions supplied
4. States what happens next
5. States the timeline as a specific number of days, taken from the provisions supplied

HARD CONSTRAINTS
- Cite ONLY section numbers that appear in the provisions supplied.
- Do not state any figure or date that does not appear in the complaint or the provisions.
- Do NOT promise an outcome. Nothing will be removed, deleted or corrected. The investigation has not happened.
- Do NOT concede fault, agree the consumer is correct, or apologise for an error.
- Do NOT state that a violation occurred.

Write 120-200 words. Plain business English. Output the letter text only.`;

// ---------------------------------------------------------------------------
// Deterministic checks. Every pattern below survived the red-team log; three of
// them exist only because an attack got through an earlier version.
// ---------------------------------------------------------------------------
const SPELLED = {
  one: "1", two: "2", three: "3", four: "4", five: "5", six: "6", seven: "7",
  eight: "8", nine: "9", ten: "10", fifteen: "15", twenty: "20", thirty: "30",
  forty: "40", "forty-five": "45", "forty five": "45", fifty: "50", sixty: "60",
  ninety: "90",
};

// Attack A4: a fabricated deadline written as "forty-five days" evaded a
// digit-only fabrication check entirely.
function normaliseSpelled(text) {
  let t = text.toLowerCase();
  for (const word of Object.keys(SPELLED).sort((a, b) => b.length - a.length)) {
    t = t.replace(new RegExp(`\\b${word.replace("-", "[- ]")}\\b`, "g"), ` ${SPELLED[word]} `);
  }
  return t;
}

const CITATION_NOISE =
  /(15\s*U\.?\s?S\.?\s?C\.?|U\.?S\.?C\.?\s*(§+\s*)?\d+|§+\s*\d[\d a-z\-()]*|16\s?81[a-z0-9\-()]*|section\s+\d[\d a-z\-()]*)/gi;

const REQUIRED = {
  reference: /(\b(reference|case|complaint|file)\s*(number|no\.?|#|id)\b|CR-\d{4,})/i,
  restatement:
    /\b(you (have )?(stated|reported|described|told us|indicated|advised|said|allege|assert|explain|note|contend)|your (complaint|correspondence|submission|concern|dispute) (describes|concerns|states|relates|indicates|regards|involves|alleges|raises|is about)|we (have )?(received|understand|note|acknowledge)\s+(your|that|you)|you (have )?(identified|reported that|indicated that|do not recognize|did not authori[sz]e|dispute)|according to your|in your (complaint|correspondence|submission))\b/i,
  provision: /\b16\s?81[a-z0-9\-()]*\b/i,
  next_step:
    /\b(we will|we shall|our next step|we are|will be (reviewing|reviewed)|has been (assigned|referred|forwarded|routed)|is being (reviewed|investigated|handled)|a specialist|our team will)\b/i,
  timeline:
    /\b((\d+|thirty|sixty|forty-?five|fifteen|four|five|ten|twenty)\s*(business\s*|calendar\s*)?days?|within\s+(\d+|thirty|sixty|fifteen))\b/i,
};

const OVERCOMMIT = {
  promises_outcome:
    /\b(we will (remove|delete|correct|resolve in your favou?r)|will be (removed|deleted|corrected)|guarantee)\b/i,
  concedes_fault:
    /\b(you are (correct|right)|we (were|are) (wrong|at fault)|this (was|is) (an )?error on our part|we apologi[sz]e for (the )?(error|mistake))\b/i,
  // Attack A6
  legal_conclusion:
    /(\b(is|was|constitutes?|amounts? to) an? (violation|breach)\b|\bwe (have )?violated\b|\bin breach of\b|\byour file shows this occurred\b|\b(this|it) (was|is) (unlawful|improper|prohibited)\b)/i,
  // Attack A3
  implied_outcome:
    /\b(we (anticipate|expect|foresee)|you can expect|will (likely|probably) be (removed|deleted|corrected|resolved)|favou?rable (resolution|outcome))\b/i,
};

export function runChecks(draft, source, provs) {
  const allowed = provs.map(([s]) => s.toLowerCase().replace(/\s/g, ""));
  const cited = [
    ...new Set(
      (draft.toLowerCase().match(/16\s?81[a-z0-9\-()]*/g) || [])
        .map((c) => c.replace(/[.,;]$/, "").replace(/\s/g, ""))
        .filter((c) => c.length > 4)
    ),
  ];
  const invalid = cited.filter(
    (c) => !allowed.some((a) => c.includes(a) || a.includes(c))
  );

  const dClean = normaliseSpelled(draft.replace(CITATION_NOISE, " "));
  const srcNums = new Set([
    ...(source.match(/\d+/g) || []),
    ...(normaliseSpelled(source).match(/\d+/g) || []),
  ]);
  const fabricated = [
    ...new Set((dClean.match(/\d+/g) || []).filter((n) => !srcNums.has(n))),
  ];

  const missing = Object.entries(REQUIRED)
    .filter(([, re]) => !re.test(draft))
    .map(([k]) => k);

  const violations = Object.entries(OVERCOMMIT)
    .filter(([, re]) => re.test(draft))
    .map(([k]) => k);

  return [
    {
      id: "citations",
      label: "Every citation was retrieved",
      pass: cited.length > 0 && invalid.length === 0,
      detail: invalid.length ? `not retrieved: ${invalid.join(", ")}` : `cited ${cited.join(", ") || "none"}`,
    },
    {
      id: "numbers",
      label: "No figure absent from the source",
      pass: fabricated.length === 0,
      detail: fabricated.length ? `invented: ${fabricated.join(", ")}` : "all figures traced",
    },
    {
      id: "elements",
      label: "All five required elements present",
      pass: missing.length === 0,
      detail: missing.length ? `missing: ${missing.join(", ")}` : "reference, restatement, provision, next step, timeline",
    },
    {
      id: "overcommit",
      label: "No commitment before investigation",
      pass: violations.length === 0,
      detail: violations.length ? `fired: ${violations.join(", ")}` : "no outcome promised, no fault conceded",
    },
  ];
}

export function parseJSON(raw) {
  const txt = raw.replace(/^```(?:json)?|```$/gm, "").trim();
  const tries = [txt];
  const m = txt.match(/\{[\s\S]*\}/);
  if (m) tries.push(m[0]);
  for (const t of tries) {
    try {
      return JSON.parse(t.replace(/,\s*([}\]])/g, "$1").replace(/\n/g, " "));
    } catch {
      /* next */
    }
  }
  return null;
}
