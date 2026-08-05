"use client";

import { useEffect, useLayoutEffect, useRef, useState } from "react";
import Link from "next/link";
import { CLASS_LABEL, THEORY_NAME } from "../lib/triage";

const CASES = [
  { id: "01", hold: false, name: "Late payments reported that were never late",
    text: "There are two accounts on my credit report showing late payments from 2023 that were never late. I have bank statements showing every payment cleared on time. I want the payment history corrected to reflect what actually happened." },
  { id: "02", hold: false, name: "Four inquiries from lenders never contacted",
    text: "I pulled my credit report and found four hard inquiries from lenders I have never contacted and never applied to. I did not give written permission to any of them to access my file. I want to know how they obtained it." },
  { id: "03", hold: false, name: "Two disputes returned verified, nobody reviewed",
    text: "I mailed a dispute with supporting documentation in March, and again in May by certified mail. Both times the response came back that the item was verified. Nobody ever contacted me and nobody ever looked at what I sent. I am disputing how this investigation was handled." },
  { id: "04", hold: true, name: "Inaccurate and unauthorised, asserted together",
    text: "You have reported inaccurate and unauthorized accounts on my credit report. These accounts do not belong to me and I never gave written consent for any of them to be furnished. Both of these are violations of my rights as a consumer." },
  { id: "05", hold: true, name: "Identity theft spanning accuracy and consent",
    text: "I am a victim of identity theft. Someone opened accounts in my name that I never applied for, and those accounts are now being reported on my file with balances I never incurred. I have filed a police report. None of this should have been furnished at all and none of it is accurate." },
];

function Tick({ ok }) {
  return ok ? (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M2.5 7.3l3 3 6-6.6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  ) : (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
      <path d="M3.4 3.4l7.2 7.2M10.6 3.4l-7.2 7.2" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
    </svg>
  );
}

export default function Page() {
  const [text, setText] = useState("");
  const [picked, setPicked] = useState(null);
  const [phase, setPhase] = useState("idle");
  const [res, setRes] = useState(null);
  const [err, setErr] = useState("");
  const [copied, setCopied] = useState(false);

  // The pleading gutter is numbered to the height of the filing, so the numbers
  // end where the theories do rather than running on over the determination.
  const filingRef = useRef(null);
  const [lines, setLines] = useState(0);

  useLayoutEffect(() => {
    const el = filingRef.current;
    if (!el) {
      setLines(0);
      return;
    }
    const measure = () => setLines(Math.max(1, Math.floor((el.offsetHeight - 14) / 26)));
    measure();
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [res]);

  const ready = text.trim().length >= 40;

  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter" && ready && phase !== "working") analyse();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });

  async function analyse() {
    setPhase("working"); setErr(""); setRes(null); setCopied(false);
    try {
      const r = await fetch("/api/triage", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ narrative: text }),
      });
      const d = await r.json();
      if (!r.ok) { setErr(d.error || "Something went wrong."); setPhase("error"); return; }
      setRes(d); setPhase("done");
    } catch { setErr("Could not reach the adjudication service."); setPhase("error"); }
  }

  const held = res?.determination === "WITHHELD";
  const passed = res?.checks?.filter((c) => c.pass).length ?? 0;

  return (
    <>
      <nav className="topbar">
        <div className="in">
          <span className="mark">Abeyance<span> · decision console</span></span>
          <Link href="/" className="navlink" aria-current="page">Console</Link>
          <Link href="/evidence" className="navlink">Evidence</Link>
          <span className="grow" />
          <span className="ticker">
            {res ? <><b>{res.survivors}</b> of 3 surviving</> : "awaiting filing"}
          </span>
          <span className="chip build">Evaluation build</span>
        </div>
      </nav>

      <main className="console">
        <div className="context">
          <p className="line">
            Consumer credit reporting under the FCRA. Three competing legal theories,
            tested against every narrative.
          </p>
          <div className="figs">
            <span className="fig"><b>46%</b><span>intake labels agree with expert reading</span></span>
            <span className="fig"><b>1 in 6</b><span>complaints no rule resolves</span></span>
            <span className="fig"><b>0.33</b><span>best of fourteen lexical signals</span></span>
          </div>
        </div>

        <div className="panes">
          {/* intake */}
          <section className="card">
            <div className="head">
              <h2>Complaint</h2>
              <span className="aux">{text.length}</span>
            </div>
            <div className="scroll">
              <div className="pad">
                <textarea
                  value={text}
                  onChange={(e) => { setText(e.target.value); setPicked(null); }}
                  placeholder="Paste a consumer complaint narrative, or select one below."
                  aria-label="Complaint narrative"
                />
                <p className="libtitle">Sample cases</p>
                {CASES.map((c) => (
                  <button key={c.id} className="case" aria-pressed={picked === c.id}
                    onClick={() => { setText(c.text); setPicked(c.id); setPhase("idle"); setRes(null); }}>
                    <span className="num">{c.id}</span>
                    <span className="nm">{c.name}</span>
                    <span className={`dot${c.hold ? " hold" : ""}`} />
                  </button>
                ))}
              </div>
            </div>
            <div className="bar">
              <button className="primary" onClick={analyse} disabled={!ready || phase === "working"}>
                {phase === "working" ? "Adjudicating" : "Adjudicate"}
              </button>
              {ready ? <span className="kbd">⌘ ⏎</span> : <span className="hint">40 characters minimum</span>}
            </div>
          </section>

          {/* adjudication */}
          <section className="card">
            <div className="head">
              <h2>Adjudication</h2>
              {res && <span className="aux">{res.survivors} of 3 theories survive</span>}
            </div>

            <div className="scroll">
              {phase === "idle" && (
                <div className="pitch">
                  <p className="kicker">What this does</p>
                  <h1>Some complaints cannot be <em>decided</em>. It says which.</h1>
                  <p className="lede">
                    A complaint arrives as free text. The system states three competing
                    legal theories, removes each alleged defect in turn, and asks whether
                    a complaint still remains. <strong>When two theories survive, it
                    withholds the decision</strong>, because choosing between them would
                    invent a distinction the narrative does not contain.
                  </p>
                  <p className="fn">
                    The two cases carrying a <b>filled square</b> are ones the annotation
                    guideline records as unresolvable. Run either to watch the system
                    decline.
                  </p>
                </div>
              )}

              {phase === "working" && (
                <>
                  <div className="think">
                    {["01", "02", "03"].map((n) => (
                      <div className="row" key={n}><span className="ix">{n}</span><span className="sk" /></div>
                    ))}
                  </div>
                  <p className="thinklabel">Testing each theory against the narrative</p>
                </>
              )}

              {phase === "error" && (
                <div className="state err">
                  <p className="h">Adjudication failed</p>
                  <p className="p">{err}</p>
                </div>
              )}

              {phase === "done" && res && (
                <>
                  <div className="filing" ref={filingRef}>
                    <span className="gutter" aria-hidden="true">
                      {Array.from({ length: lines }, (_, i) => (
                        <span key={i}>{i + 1}</span>
                      ))}
                    </span>
                    {res.theories.map((t) => (
                      <div className={`thy${t.survives ? " live" : ""}`} key={t.id}>
                        <span>
                          <p className="nm">{THEORY_NAME[t.id]}</p>
                          <p className="test">{t.test || "No test returned."}</p>
                        </span>
                        <span className={`res${t.survives ? " survives" : ""}`}>
                          {t.survives ? "Survives" : "Falls away"}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className={`verdict${held ? " held" : ""}`}>
                    <p className="vlabel">{held ? "Determination withheld" : "Determination"}</p>
                    <p className="vmain">{CLASS_LABEL[res.determination]}</p>
                    {res.rationale && <p className="vsub">{res.rationale}</p>}
                    <div className="conf">
                      <span className="seg">
                        {Array.from({ length: 10 }, (_, i) => (
                          <i key={i} className={i < Math.round(res.confidence * 10) ? "on" : ""} />
                        ))}
                      </span>
                      <span className="n">{Math.round(res.confidence * 100)}% confidence</span>
                    </div>
                  </div>

                  {held ? (
                    <p className="note">
                      No acknowledgment letter is drafted for a withheld case. It goes to a
                      reviewer with the surviving theories above and the reason each one holds.
                    </p>
                  ) : (
                    <>
                      <div className="sec">
                        <h3>Draft controls</h3>
                        <span className="cnt">{passed} of {res.checks.length} passed</span>
                      </div>
                      {res.checks.map((c) => (
                        <div className={`chk${c.pass ? "" : " fail"}`} key={c.id}>
                          <span className="g" style={{ color: c.pass ? "var(--w-2)" : "var(--w-1)" }}><Tick ok={c.pass} /></span>
                          <span>
                            <span className="t">{c.label}</span>
                            <span className="d">{c.detail}</span>
                          </span>
                        </div>
                      ))}
                      {res.provisions?.length > 0 && (
                        <p className="prov">
                          Retrieved · {res.provisions.map((p) => `${p.sec} ${p.title}`).join("  ·  ")}
                        </p>
                      )}
                      {res.draft && (
                        <div className="lw">
                          <div className="lh">
                            <span>Draft acknowledgment · awaiting approval</span>
                            <button className="ghost" onClick={() => {
                              navigator.clipboard?.writeText(res.draft);
                              setCopied(true); setTimeout(() => setCopied(false), 1600);
                            }}>{copied ? "Copied" : "Copy"}</button>
                          </div>
                          <pre className="letter">{res.draft}</pre>
                        </div>
                      )}
                    </>
                  )}
                </>
              )}
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
