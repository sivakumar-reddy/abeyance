import Anthropic from "@anthropic-ai/sdk";
import {
  ROUTE_SYSTEM,
  DRAFT_SYSTEM,
  retrieve,
  runChecks,
  parseJSON,
  CLASSES,
} from "../../../lib/triage";

export const runtime = "nodejs";
export const maxDuration = 60;

const MODEL = process.env.TRIAGE_MODEL || "claude-sonnet-5";
const MAX_NARRATIVE = 20000;

function client() {
  const key = process.env.ANTHROPIC_API_KEY;
  if (!key) {
    throw new Error(
      "ANTHROPIC_API_KEY is not set. Create .env.local with your key and restart the dev server."
    );
  }
  return new Anthropic({ apiKey: key });
}

// The interface is set without dashes of any kind, so model prose is normalised
// before it reaches the client. Statutory section identifiers are left alone:
// the character in 1681c-2 is part of a citation, not punctuation.
function undash(str) {
  return String(str)
    .replace(/\s*[\u2014\u2013]\s*/g, ", ")
    .replace(/([A-Za-z])-([A-Za-z])/g, "$1 $2")
    .replace(/\s+-\s+/g, ", ")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function text(msg) {
  return msg.content.filter((b) => b.type === "text").map((b) => b.text).join("");
}

export async function POST(req) {
  let body;
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "Request body was not valid JSON." }, { status: 400 });
  }

  const narrative = String(body.narrative || "").slice(0, MAX_NARRATIVE).trim();
  if (narrative.length < 40) {
    return Response.json(
      { error: "Paste a complaint of at least 40 characters to route it." },
      { status: 400 }
    );
  }

  let anthropic;
  try {
    anthropic = client();
  } catch (e) {
    return Response.json({ error: e.message }, { status: 500 });
  }

  try {
    // --- stage 1: adjudicate the three theories ---
    const routeMsg = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 900,
      system: ROUTE_SYSTEM,
      messages: [{ role: "user", content: `<complaint>\n${narrative}\n</complaint>` }],
    });
    const adj = parseJSON(text(routeMsg));

    const VALID = ["WITHHELD", ...CLASSES];
    const determination = String(adj?.determination || "").toUpperCase();
    if (!adj || !VALID.includes(determination) || !Array.isArray(adj.theories)) {
      return Response.json(
        { error: "The adjudicator returned an unreadable response. Try again." },
        { status: 502 }
      );
    }

    // Normalise the ledger and enforce the ordering the UI expects, so a
    // reordered or partial response still renders coherently.
    const byId = Object.fromEntries(
      adj.theories
        .filter((t) => t && CLASSES.includes(String(t.id).toUpperCase()))
        .map((t) => [String(t.id).toUpperCase(), t])
    );
    const theories = CLASSES.map((id) => ({
      id,
      survives: Boolean(byId[id]?.survives),
      test: undash(byId[id]?.test || "").slice(0, 260),
    }));

    const survivors = theories.filter((t) => t.survives).length;
    const confidence = Math.max(0, Math.min(1, Number(adj.confidence) || 0));

    const result = {
      theories,
      survivors,
      determination,
      confidence,
      rationale: undash(adj.rationale || "").slice(0, 400),
      provisions: [],
      draft: null,
      checks: [],
    };

    // Withholding terminates the pipeline by design. A held case goes to a
    // person with the surviving theories, not to a drafting step.
    if (determination === "WITHHELD") return Response.json(result);

    // --- stage 2: draft ---
    const label = determination;
    const provs = retrieve(label);
    result.provisions = provs.map(([sec, p]) => ({ sec, title: p.title }));

    const caseNo = "CR-" + String(Math.floor(Math.random() * 90000) + 10000);
    const context = [
      `CASE NUMBER: ${caseNo}`,
      `ROUTED GRIEVANCE: ${label}`,
      "",
      "COMPLAINT NARRATIVE:",
      narrative,
      "",
      "RETRIEVED PROVISIONS:",
      ...provs.map(([sec, p]) => `  [${sec}] ${p.title} — ${p.summary}`),
    ].join("\n");

    const draftMsg = await anthropic.messages.create({
      model: MODEL,
      max_tokens: 900,
      system: DRAFT_SYSTEM,
      messages: [{ role: "user", content: context }],
    });
    const draft = text(draftMsg).trim();

    result.caseNo = caseNo;
    result.draft = draft;
    result.checks = runChecks(draft, context, provs);
    return Response.json(result);
  } catch (e) {
    // Always log the real cause server-side. A generic message in the browser
    // is fine for users; hiding it from the developer is not.
    console.error("[triage] request failed:", e?.status, e?.message, e);

    const status = e?.status;
    const detail = e?.error?.error?.message || e?.message || String(e);

    if (status === 401 || status === 403) {
      return Response.json(
        { error: "The server's API key was rejected. Check ANTHROPIC_API_KEY." },
        { status: 500 }
      );
    }
    if (status === 429) {
      return Response.json({ error: "Rate limited. Wait a moment and try again." }, { status: 429 });
    }
    if (status === 400 || status === 404) {
      return Response.json({ error: `Request rejected: ${detail}` }, { status: 400 });
    }
    return Response.json(
      {
        error:
          process.env.NODE_ENV === "production"
            ? "The routing service did not respond. Try again."
            : `Routing failed: ${detail}`,
      },
      { status: 502 }
    );
  }
}
