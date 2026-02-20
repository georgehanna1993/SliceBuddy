"use client";

import React, { useEffect, useMemo, useRef, useState } from "react";
import Image from "next/image";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

type ChatMsg = {
  role: "user" | "bot";
  text?: string; // plain text (user messages)
  kind?: "text" | "plan" | "loading";
  planPayload?: any; // raw API response
};

type PlanItem = {
  id: string;
  title: string;
  createdAt: number;
};

function safeStr(v: any): string {
  if (v === null || v === undefined) return "";
  return String(v);
}

function titleFromUse(useText: string) {
  const t = useText.trim();
  if (!t) return "New Print Plan";
  return t.length > 32 ? t.slice(0, 32) + "…" : t;
}

function severityLabel(s: string) {
  const x = (s || "").toLowerCase();
  if (x === "high") return { tag: "HIGH", cls: "sb-sevHigh" };
  if (x === "medium") return { tag: "MED", cls: "sb-sevMed" };
  return { tag: "LOW", cls: "sb-sevLow" };
}

function bedContactLabel(stl: any) {
  if (!stl) return { label: "Unknown", tone: "muted" as const };
  const area = Number(stl.contact_area_mm2 || 0);
  const ratio = Number(stl.contact_ratio || 0);

  // same logic you used in CLI but hidden behind “labels”
  if (area > 0 && (area < 300 || ratio < 0.15)) return { label: "Very low", tone: "bad" as const };
  if (area > 0 && (area < 600 || ratio < 0.3)) return { label: "Low", tone: "warn" as const };
  return { label: "Good", tone: "good" as const };
}

function supportsLabel(payload: any) {
  const stl = payload?.stl_features;
  const slicer = payload?.plan?.slicer_settings?.settings || payload?.slicer_settings?.settings || {};
  const supports = safeStr(slicer.supports);

  if (stl?.likely_supports === true) return "Yes (likely needed)";
  if (supports) {
    const s = supports.toLowerCase();
    if (s.includes("on")) return "Yes";
    if (s.includes("auto")) return "Auto (only if needed)";
    if (s.includes("off")) return "No";
  }
  return "Auto (only if needed)";
}

function infillTypeOrSuggestion(payload: any) {
  const slicer = payload?.plan?.slicer_settings?.settings || payload?.slicer_settings?.settings || {};

  // Try a few common keys (you’ll probably standardize later)
  const t =
    slicer.infill_type ||
    slicer.infill_pattern ||
    slicer.infillPattern ||
    slicer.infill ||
    slicer["infill_type"];

  return t ? safeStr(t) : "Gyroid (good all-rounder)";
}

function fmtDims(payload: any) {
  const stl = payload?.stl_features;
  const bbox = stl?.bbox_mm;
  if (!bbox || !Array.isArray(bbox) || bbox.length !== 3) return null;
  const [x, y, z] = bbox.map((n: any) => Number(n));
  if (![x, y, z].every((n: number) => Number.isFinite(n))) return null;
  return `${x.toFixed(1)} × ${y.toFixed(1)} × ${z.toFixed(1)} mm`;
}

/**
 * Make a friendly, non-echoey overview based on keywords.
 * Goal: "Maybe it's a …" + practical print implications.
 * This is ONLY used if backend didn’t provide model_overview.
 */
function guessOverviewFromDescription(descRaw: string, supports: string, bedLabel: string, stl: any) {
  const desc = (descRaw || "").toLowerCase();

  let guess = "a general 3D model";
  let useCaseHint = "";
  let printHint = "";

  // Broad categories
  const isContainer = /box|tray|bin|case|organizer|container|holder/.test(desc);
  const isFidget = /fidget|twist|spinner|cube|worry|click/.test(desc);
  const isToy = /toy|ball|game|kid|kids|play/.test(desc);
  const isFunctional = /bracket|mount|clip|adapter|hinge|tool|stand|hook/.test(desc);
  const isDecor = /decor|ornament|statue|figurine|vase|art/.test(desc);

  if (isFidget) guess = "a fidget / tactile toy";
  else if (isContainer) guess = "a small container / organizer";
  else if (isFunctional) guess = "a functional part";
  else if (isDecor) guess = "a decorative print";
  else if (isToy) guess = "a toy or play object";

  if (isContainer) useCaseHint = "Likely meant to hold small items (screws, parts, desk stuff).";
  if (isFidget) useCaseHint = "Probably meant to be handled a lot, so smoothness matters.";
  if (isFunctional) useCaseHint = "Strength and layer adhesion matter more than looks here.";
  if (isDecor) useCaseHint = "Looks matter most; strength usually matters less.";

  // Mesh health note (beginner friendly)
  const meshNote =
    stl && stl.watertight === false
      ? "Mesh has openings/holes, so repairing the STL is recommended before printing."
      : "";

  // Practical hint based on supports + bed contact labels
  const supportsNeeded = supports.toLowerCase().includes("yes");
  if (supportsNeeded) {
    printHint = "Supports are likely needed due to overhangs—expect extra cleanup after printing.";
  } else {
    printHint = "Supports probably aren’t needed in this orientation, which keeps the print cleaner.";
  }

  if (bedLabel.toLowerCase().includes("very low")) {
    printHint += " Bed contact looks weak—consider a brim or re-orienting for better adhesion.";
  } else if (bedLabel.toLowerCase().includes("low")) {
    printHint += " Bed contact is a bit low—brim can help if you see lifting.";
  } else if (bedLabel.toLowerCase().includes("good")) {
    printHint += " Bed contact looks good—should be stable on the plate.";
  }

  const pieces = [
    `Maybe this is ${guess}.`,
    useCaseHint,
    printHint,
    meshNote,
  ].filter(Boolean);

  return pieces.join(" ");
}

export default function Page() {
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [activePlanId, setActivePlanId] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMsg[]>([
    { role: "bot", kind: "text", text: "Upload an STL + tell me what it’s used for, and I’ll generate a print plan." },
  ]);

  const [useText, setUseText] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isSending, setIsSending] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  const activePlan = useMemo(() => {
    if (!activePlanId) return null;
    return plans.find((p) => p.id === activePlanId) ?? null;
  }, [plans, activePlanId]);

  useEffect(() => {
    // Always scroll chat to bottom when messages change
    chatEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function newPlan() {
    const id = crypto.randomUUID();
    const item: PlanItem = { id, title: "New Print Plan", createdAt: Date.now() };

    setPlans((prev) => [item, ...prev]);
    setActivePlanId(id);

    setMessages([
      { role: "bot", kind: "text", text: "Upload an STL + tell me what it’s used for, and I’ll generate a print plan." },
    ]);
    setUseText("");
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function pickFile() {
    if (isSending) return;
    fileInputRef.current?.click();
  }

  function onFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null;
    setSelectedFile(f);
  }

  function clearComposer() {
    if (isSending) return;
    setUseText("");
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  function pushBotText(text: string) {
    setMessages((prev) => [...prev, { role: "bot", kind: "text", text }]);
  }

  function pushLoading() {
    setMessages((prev) => [...prev, { role: "bot", kind: "loading" }]);
  }

  function popLoading() {
    setMessages((prev) => prev.filter((m) => m.kind !== "loading"));
  }

  async function send() {
    const trimmed = useText.trim();
    if (!selectedFile) {
      pushBotText("Please choose an STL first (tap the +).");
      return;
    }
    if (!trimmed) {
      pushBotText("Add a short line about what the model is used for.");
      return;
    }
    if (isSending) return;

    // Add the user message ONCE
    setMessages((prev) => [...prev, { role: "user", kind: "text", text: trimmed }]);

    // Ensure we have a plan item + nice title
    if (!activePlanId) {
      const id = crypto.randomUUID();
      const item: PlanItem = { id, title: titleFromUse(trimmed), createdAt: Date.now() };
      setPlans((prev) => [item, ...prev]);
      setActivePlanId(id);
    } else {
      setPlans((prev) =>
        prev.map((p) =>
          p.id === activePlanId && (p.title === "New Print Plan" || p.title === "Print Plan")
            ? { ...p, title: titleFromUse(trimmed) }
            : p
        )
      );
    }

    setIsSending(true);
    pushLoading();

    try {
      const fd = new FormData();
      fd.append("use", trimmed);
      fd.append("stl", selectedFile);

      const resp = await fetch("http://127.0.0.1:8000/plan", {
        method: "POST",
        body: fd,
      });

      popLoading();

      if (!resp.ok) {
        let bodyText = "";
        try {
          bodyText = await resp.text();
        } catch {}
        pushBotText(`Server error (${resp.status}). ${bodyText ? bodyText.slice(0, 180) : "Check FastAPI logs."}`);
        return;
      }

      const data = await resp.json();

      // If backend ever returns a stop message
      if (data?.stop && data?.plan_explanation) {
        pushBotText(safeStr(data.plan_explanation));
        return;
      }

      // Instead of dumping markdown, render structured “plan cards”
      setMessages((prev) => [
        ...prev,
        { role: "bot", kind: "plan", planPayload: data },
      ]);

      setUseText("");
      // keep file selected
    } catch (e: any) {
      popLoading();
      pushBotText(`Something went wrong while generating the plan. ${safeStr(e?.message)}`);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <div className="sb-root">
      {/* Sidebar */}
      <aside className="sb-sidebar">
        <div className="sb-sidebarTop">
          <div className="sb-brand" aria-label="SliceBuddy">
            <div className="sb-brandBlock">
              <Image
                src="/logo.png"
                alt="SliceBuddy"
                width={220}
                height={120}
                priority
                className="sb-logo"
              />
              <div className="sb-subtitle">Beginner-friendly print plans</div>
            </div>
          </div>

          <button className="sb-newBtn" onClick={newPlan} disabled={isSending}>
            + New Print Plan
          </button>

          <div className="sb-sectionTitle">RECENT PLANS</div>

          <div className="sb-plans">
            {plans.length === 0 ? (
              <div className="sb-planEmpty">
                <div className="sb-planEmptyTitle">No plans yet.</div>
                <div className="sb-planEmptyHint">Upload an STL to create your first plan.</div>
              </div>
            ) : (
              plans.map((p) => (
                <button
                  key={p.id}
                  className={`sb-planItem ${p.id === activePlanId ? "active" : ""}`}
                  onClick={() => setActivePlanId(p.id)}
                  disabled={isSending}
                >
                  <div className="sb-planTitle">{p.title}</div>
                  <div className="sb-planMeta">{timeAgo(p.createdAt)}</div>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="sb-sidebarBottom">
          <div className="sb-userDot" />
        </div>
      </aside>

      {/* Main */}
      <main className="sb-main">
        <header className="sb-topbar">
          <div className="sb-topbarTitle">{activePlan?.title ?? "New Print Plan"}</div>
        </header>

        {/* Chat */}
        <section className="sb-chat">
          <div className="sb-chatInner">
            {messages.map((m, idx) => (
              <div key={idx} className={`sb-msg ${m.role === "user" ? "user" : "bot"}`}>
                <div className="sb-msgLabel">{m.role === "user" ? "You" : "SliceBuddy"}</div>

                <div className="sb-msgBubble">
                  {/* user text */}
                  {m.kind === "text" && m.role === "user" && <div>{m.text}</div>}

                  {/* bot text */}
                  {m.kind === "text" && m.role === "bot" && <div>{m.text}</div>}

                  {/* loading */}
                  {m.kind === "loading" && (
                    <div className="sb-loadingRow">
                      <div className="sb-spinner" aria-label="Loading" />
                      <div className="sb-loadingText">Generating your print plan…</div>
                    </div>
                  )}

                  {/* plan cards */}
                  {m.kind === "plan" && m.role === "bot" && <PlanCards payload={m.planPayload} />}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
        </section>

        {/* Composer */}
        <footer className="sb-composerBar">
          <input
            ref={fileInputRef}
            type="file"
            accept=".stl"
            onChange={onFilePicked}
            style={{ display: "none" }}
          />

          <div className="sb-composer">
            <button className="sb-plusBtn" onClick={pickFile} title="Choose STL" disabled={isSending}>
              +
            </button>

            <div className="sb-inputWrap">
              <input
                className="sb-input"
                placeholder="What is this model used for? (e.g., open-top box for screws)"
                value={useText}
                disabled={isSending}
                onChange={(e) => setUseText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") send();
                }}
              />
              <div className="sb-fileHint" aria-live="polite">
                {selectedFile ? `STL: ${selectedFile.name}` : "Tap + to choose an STL"}
              </div>
            </div>

            <button className="sb-clearBtn" onClick={clearComposer} disabled={isSending}>
              Clear
            </button>

            <button
              className={`sb-sendBtn ${selectedFile && useText.trim() && !isSending ? "ready" : ""}`}
              onClick={send}
              disabled={isSending}
            >
              {isSending ? "Sending…" : "Send"}
            </button>
          </div>

          <div className="sb-footnote">Requirement: upload an STL + describe what it’s used for.</div>
        </footer>
      </main>

      {/* Styles */}
      <style jsx global>{`
        :root{
          --sb-green: #3FAE58;
          --sb-bg: #F5F6F8;
          --sb-border: rgba(0,0,0,0.08);
          --sb-text: #111827;
          --sb-muted: rgba(17,24,39,0.65);
          --sb-card: #FFFFFF;
        }

        html, body {
          height: 100%;
          margin: 0;
          background: var(--sb-bg);
          color: var(--sb-text);
          font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
        }

        .sb-root{
          height: 100vh;
          display: grid;
          grid-template-columns: 320px 1fr;
          overflow: hidden;
        }

        /* Sidebar */
        .sb-sidebar{
          background: #fff;
          border-right: 1px solid var(--sb-border);
          display: flex;
          flex-direction: column;
          min-width: 0;
        }

        .sb-sidebarTop{ padding: 18px; }
        .sb-brand{
          width: 100%;
          display: flex;
          justify-content: flex-start;
          padding: 10px 6px 18px;
        }

        .sb-brandBlock{
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 10px;
        }

        .sb-logo{
          width: 220px;
          height: auto;
          object-fit: contain;
          display: block;
        }

        .sb-subtitle{
          font-size: 14px;
          color: var(--sb-muted);
          margin-left: 2px;
        }

        .sb-newBtn{
          width: 100%;
          padding: 12px 14px;
          border-radius: 10px;
          border: 1px solid var(--sb-border);
          background: #fff;
          color: var(--sb-text);
          font-weight: 700;
          cursor: pointer;
        }
        .sb-newBtn:disabled{ opacity: 0.7; cursor: not-allowed; }

        .sb-newBtn:hover{ border-color: rgba(0,0,0,0.16); }

        .sb-sectionTitle{
          margin-top: 18px;
          margin-bottom: 10px;
          font-size: 12px;
          font-weight: 800;
          letter-spacing: 0.08em;
          color: rgba(17,24,39,0.55);
        }

        .sb-plans{ display: flex; flex-direction: column; gap: 10px; }

        .sb-planEmpty{
          padding: 14px;
          border-radius: 12px;
          border: 1px solid var(--sb-border);
          background: rgba(0,0,0,0.02);
        }

        .sb-planEmptyTitle{ font-weight: 800; margin-bottom: 6px; }
        .sb-planEmptyHint{ font-size: 13px; color: var(--sb-muted); }

        .sb-planItem{
          text-align: left;
          padding: 12px 12px;
          border-radius: 12px;
          border: 1px solid var(--sb-border);
          background: #fff;
          cursor: pointer;
        }
        .sb-planItem:disabled{ opacity: 0.7; cursor: not-allowed; }

        .sb-planItem.active{
          border-color: rgba(63,174,88,0.65);
          box-shadow: 0 0 0 3px rgba(63,174,88,0.12);
        }

        .sb-planTitle{ font-weight: 800; }
        .sb-planMeta{ font-size: 12px; color: var(--sb-muted); margin-top: 4px; }

        .sb-sidebarBottom{ margin-top: auto; padding: 18px; }
        .sb-userDot{ width: 38px; height: 38px; border-radius: 999px; background: rgba(0,0,0,0.08); }

        /* Main */
        .sb-main{
          display: flex;
          flex-direction: column;
          min-width: 0;
          min-height: 0; /* IMPORTANT for scrolling */
        }

        .sb-topbar{
          background: var(--sb-green);
          height: 56px;
          display: flex;
          align-items: center;
          padding: 0 18px;
          color: #fff;
          font-weight: 900;
          border-bottom: 1px solid rgba(0,0,0,0.12);
          flex: 0 0 auto;
        }

        /* Chat must be scrollable */
        .sb-chat{
          flex: 1 1 auto;
          min-height: 0;         /* IMPORTANT */
          overflow-y: auto;      /* IMPORTANT */
          padding: 18px;
        }

        .sb-chatInner{
          max-width: 920px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 14px;
          padding-bottom: 14px;
        }

        .sb-msg{ display: flex; flex-direction: column; gap: 6px; }
        .sb-msgLabel{ font-size: 12px; font-weight: 900; color: rgba(17,24,39,0.7); }

        .sb-msgBubble{
          background: var(--sb-card);
          border: 1px solid var(--sb-border);
          border-radius: 14px;
          padding: 14px;
          color: var(--sb-text);
          line-height: 1.45;
          overflow-wrap: anywhere;
        }

        .sb-msg.user .sb-msgBubble{
          background: rgba(63,174,88,0.08);
          border-color: rgba(63,174,88,0.20);
        }

        /* Loading */
        .sb-loadingRow{
          display: flex;
          align-items: center;
          gap: 10px;
        }
        .sb-spinner{
          width: 18px;
          height: 18px;
          border-radius: 999px;
          border: 3px solid rgba(0,0,0,0.12);
          border-top-color: rgba(63,174,88,0.95);
          animation: sbspin 0.9s linear infinite;
        }
        @keyframes sbspin { to { transform: rotate(360deg); } }
        .sb-loadingText{ color: rgba(17,24,39,0.75); font-weight: 700; }

        /* Composer */
        .sb-composerBar{
          background: var(--sb-green);
          border-top: 1px solid rgba(0,0,0,0.12);
          padding: 8px 12px;
          flex: 0 0 auto;
        }

        .sb-composer{
          max-width: 920px;
          margin: 0 auto;
          display: grid;
          grid-template-columns: 64px 1fr 110px 140px;
          gap: 12px;
          align-items: stretch;
        }

        .sb-plusBtn, .sb-clearBtn, .sb-sendBtn, .sb-input{ height: 44px; }

        .sb-plusBtn{
          border: none;
          border-radius: 12px;
          background: #fff;
          color: #111827;
          font-size: 28px;
          font-weight: 900;
          cursor: pointer;
          box-shadow: 0 2px 0 rgba(0,0,0,0.12);
        }
        .sb-plusBtn:disabled{ opacity: 0.75; cursor: not-allowed; }

        .sb-inputWrap{
          display: flex;
          flex-direction: column;
          gap: 6px;
          min-width: 0;
        }

        .sb-input{
          width: 100%;
          border-radius: 12px;
          border: 2px solid rgba(0,0,0,0.20);
          padding: 0 16px;
          font-size: 15px;
          outline: none;
          background: #fff;
        }
        .sb-input:disabled{ opacity: 0.85; }

        .sb-fileHint{
          font-size: 13px;
          color: rgba(255,255,255,0.92);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          padding-left: 2px;
        }

        .sb-clearBtn{
          border: none;
          border-radius: 12px;
          background: #fff;
          font-weight: 900;
          cursor: pointer;
          box-shadow: 0 2px 0 rgba(0,0,0,0.12);
        }
        .sb-clearBtn:disabled{ opacity: 0.75; cursor: not-allowed; }

        .sb-sendBtn{
          border: none;
          border-radius: 12px;
          background: rgba(255,255,255,0.55);
          color: rgba(17,24,39,0.45);
          font-weight: 900;
          cursor: pointer;
          box-shadow: 0 2px 0 rgba(0,0,0,0.12);
        }

        .sb-sendBtn.ready{
          background: #BFF0C8;
          color: #0b3d1b;
        }

        .sb-sendBtn:disabled{ opacity: 0.8; cursor: not-allowed; }

        .sb-footnote{
          display: none;
        }
        @media (max-width: 760px){
          .sb-footnote{
            display: block;
            max-width: 920px;
            margin: 6px auto 0;
            font-size: 12px;
            color: rgba(255,255,255,0.95);
          }
        }

        @media (max-width: 980px){
          .sb-root{ grid-template-columns: 280px 1fr; }
          .sb-composer{ grid-template-columns: 56px 1fr 90px 120px; }
        }
        @media (max-width: 760px){
          .sb-root{ grid-template-columns: 1fr; }
          .sb-sidebar{ display:none; }
          .sb-composer{ grid-template-columns: 56px 1fr 120px; }
          .sb-clearBtn{ display:none; }
        }
      `}</style>
    </div>
  );
}

function PlanCards({ payload }: { payload: any }) {
  const plan = payload?.plan || {};
  const material = plan?.material || payload?.material || {};
  const orientation = plan?.orientation || payload?.orientation || {};
  const slicer = plan?.slicer_settings?.settings || payload?.slicer_settings?.settings || {};
  const risks = plan?.risks || payload?.risks || {};
  const stl = payload?.stl_features;

  const dims = fmtDims(payload);
  const bed = bedContactLabel(stl);
  const supports = supportsLabel(payload);

  // Prefer backend overview if available.
  // If not, generate a "Maybe it's..." overview WITHOUT echoing the user text.
  const backendOverview =
    safeStr(payload?.model_overview).trim() ||
    safeStr(plan?.model_overview).trim() ||
    "";

  // best-effort description source (doesn't have to be the user's raw text)
  const descSource =
    safeStr(payload?.input_norm?.description) ||
    safeStr(payload?.description) ||
    safeStr(plan?.summary) ||
    "";

  const overview =
    backendOverview ||
    guessOverviewFromDescription(descSource, supports, bed.label, stl);

  const warningsList: { severity: string; why: string }[] =
    risks?.items?.map((r: any) => ({ severity: safeStr(r.severity), why: safeStr(r.why) })) || [];

  const infillPct = slicer?.infill_percent ?? slicer?.["infill%"] ?? slicer?.infill ?? null;

  return (
    <div className="sb-planWrap">
      <Card title="🧠 Model Overview" subtitle="Short, human explanation (not just your input)">
        <div className="sb-overview">{overview}</div>

        <div className="sb-chipRow">
          {dims && <span className="sb-chip">📏 Size: {dims}</span>}
          {stl && (
            <span className={`sb-chip ${stl?.watertight ? "ok" : "bad"}`}>
              🩺 Mesh: {stl?.watertight ? "OK" : "Needs repair"}
            </span>
          )}
          <span className={`sb-chip ${bed.tone}`}>🧲 Bed contact: {bed.label}</span>
          <span className={`sb-chip ${supports.toLowerCase().includes("yes") ? "warn" : "ok"}`}>
            🧱 Supports: {supports}
          </span>
        </div>
      </Card>

      <div className="sb-cardGrid">
        <Card title="🧵 Material" subtitle="What to print with">
          <KV k="Recommended" v={safeStr(material?.recommended || "PLA")} />
          <KV k="Why" v={safeStr(material?.reason || "Easy to print and reliable for most models")} />
          {Array.isArray(material?.alternatives) && material.alternatives.length > 0 && (
            <KV k="Alternatives" v={material.alternatives.join(", ")} />
          )}
        </Card>

        <Card title="🧭 Orientation" subtitle="How to place it on the bed">
          <KV k="Recommended" v={safeStr(orientation?.recommended || "Lay flat on the largest face")} />
          <KV k="Why" v={safeStr(orientation?.reason || "More stability + better adhesion")} />
          {orientation?.tradeoffs && <KV k="Trade-offs" v={safeStr(orientation.tradeoffs)} />}
        </Card>

        <Card title="🧱 Supports" subtitle="Only if needed">
          <KV k="Setting" v={safeStr(slicer?.supports || supports)} />
          <KV
            k="What it means"
            v={
              supports.toLowerCase().includes("yes")
                ? "Some areas likely print in mid-air — supports help."
                : "Usually safe without supports in this orientation."
            }
          />
        </Card>

        <Card title="🧲 Bed Adhesion" subtitle="Stick it to the plate (peacefully)">
          <KV k="Bed contact" v={bed.label} />
          <KV k="Brim" v={`${Number(slicer?.brim_mm || 0)} mm`} />
          <div className="sb-hint">Tip: clean bed + slow first layer usually beats “praying harder”.</div>
        </Card>

        <Card title="💪 Strength" subtitle="Walls / top-bottom / infill">
          <KV k="Walls" v={safeStr(slicer?.walls ?? 3)} />
          <KV k="Top/Bottom" v={safeStr(slicer?.top_bottom_layers ?? slicer?.topBottom ?? 4)} />
          {infillPct !== null && <KV k="Infill" v={`${infillPct}%`} />}
          <KV k="Infill type" v={infillTypeOrSuggestion(payload)} />
        </Card>

        <Card title="⚙️ Quality" subtitle="General print quality defaults">
          <KV k="Layer height" v={`${Number(slicer?.layer_height_mm ?? 0.2)} mm`} />
          <KV
            k="Notes"
            v={Array.isArray(slicer?.notes) ? slicer.notes.join(" • ") : safeStr(slicer?.notes || "")}
          />
        </Card>
      </div>

      {warningsList.length > 0 && (
        <Card title="⚠️ Warnings" subtitle="Things that can ruin your day">
          <div className="sb-warnList">
            {warningsList.map((w, i) => {
              const sev = severityLabel(w.severity);
              return (
                <div key={i} className="sb-warnItem">
                  <span className={`sb-sev ${sev.cls}`}>{sev.tag}</span>
                  <span className="sb-warnText">{w.why}</span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Optional: raw markdown explanation (advanced) */}
      {(payload?.plan_explanation || plan?.explanation) && (
        <details className="sb-advanced">
          <summary>Advanced details (raw explanation)</summary>
          <div className="sb-advancedBody">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {safeStr(payload?.plan_explanation || plan?.explanation)}
            </ReactMarkdown>
          </div>
        </details>
      )}

      {/* plan styles */}
      <style jsx>{`
        .sb-planWrap{ display:flex; flex-direction:column; gap: 14px; }

        .sb-cardGrid{
          display:grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        .sb-overview{
          font-size: 15px;
          color: rgba(17,24,39,0.92);
          line-height: 1.45;
        }

        .sb-chipRow{
          display:flex;
          flex-wrap:wrap;
          gap: 8px;
          margin-top: 10px;
        }

        .sb-chip{
          font-size: 12px;
          font-weight: 800;
          padding: 7px 10px;
          border-radius: 999px;
          border: 1px solid rgba(0,0,0,0.10);
          background: rgba(0,0,0,0.03);
        }
        .sb-chip.ok{ background: rgba(63,174,88,0.12); border-color: rgba(63,174,88,0.20); }
        .sb-chip.warn{ background: rgba(255,170,0,0.12); border-color: rgba(255,170,0,0.20); }
        .sb-chip.bad{ background: rgba(255,60,60,0.10); border-color: rgba(255,60,60,0.20); }
        .sb-chip.good{ background: rgba(63,174,88,0.12); border-color: rgba(63,174,88,0.20); }
        .sb-chip.muted{ background: rgba(0,0,0,0.03); border-color: rgba(0,0,0,0.10); }

        .sb-hint{
          margin-top: 10px;
          font-size: 13px;
          color: rgba(17,24,39,0.65);
          font-weight: 700;
        }

        .sb-warnList{ display:flex; flex-direction:column; gap: 10px; }
        .sb-warnItem{ display:flex; gap: 10px; align-items:flex-start; }
        .sb-sev{
          font-size: 12px;
          font-weight: 900;
          padding: 4px 8px;
          border-radius: 10px;
          border: 1px solid rgba(0,0,0,0.10);
        }
        .sb-sevHigh{ background: rgba(255,60,60,0.12); border-color: rgba(255,60,60,0.20); }
        .sb-sevMed{ background: rgba(255,170,0,0.14); border-color: rgba(255,170,0,0.22); }
        .sb-sevLow{ background: rgba(63,174,88,0.14); border-color: rgba(63,174,88,0.22); }
        .sb-warnText{ font-weight: 700; color: rgba(17,24,39,0.85); }

        .sb-advanced{
          border: 1px solid rgba(0,0,0,0.10);
          border-radius: 14px;
          padding: 12px 12px;
          background: rgba(0,0,0,0.02);
        }
        .sb-advanced summary{
          cursor: pointer;
          font-weight: 900;
          color: rgba(17,24,39,0.85);
        }
        .sb-advancedBody{
          margin-top: 10px;
          font-size: 14px;
          line-height: 1.5;
        }

        @media (max-width: 760px){
          .sb-cardGrid{ grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
}

function Card({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div className="sb-card">
      <div className="sb-cardHead">
        <div className="sb-cardTitle">{title}</div>
        {subtitle && <div className="sb-cardSub">{subtitle}</div>}
      </div>
      <div className="sb-cardBody">{children}</div>

      <style jsx>{`
        .sb-card{
          border: 1px solid rgba(0,0,0,0.10);
          border-radius: 16px;
          background: #fff;
          box-shadow: 0 1px 0 rgba(0,0,0,0.04);
          overflow: hidden;
        }
        .sb-cardHead{
          padding: 12px 14px;
          border-bottom: 1px solid rgba(0,0,0,0.06);
          background: rgba(0,0,0,0.02);
        }
        .sb-cardTitle{
          font-weight: 950;
          font-size: 14px;
          letter-spacing: 0.2px;
        }
        .sb-cardSub{
          margin-top: 4px;
          font-size: 12px;
          color: rgba(17,24,39,0.62);
          font-weight: 700;
        }
        .sb-cardBody{ padding: 12px 14px; }
      `}</style>
    </div>
  );
}

function KV({ k, v }: { k: string; v: string }) {
  if (!v) return null;
  return (
    <div className="sb-kv">
      <div className="sb-k">{k}</div>
      <div className="sb-v">{v}</div>

      <style jsx>{`
        .sb-kv{
          display:grid;
          grid-template-columns: 140px 1fr;
          gap: 10px;
          padding: 8px 0;
          border-bottom: 1px dashed rgba(0,0,0,0.08);
        }
        .sb-k{
          font-size: 12px;
          color: rgba(17,24,39,0.55);
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }
        .sb-v{
          font-size: 14px;
          color: rgba(17,24,39,0.90);
          font-weight: 750;
        }
      `}</style>
    </div>
  );
}

function timeAgo(ts: number) {
  const sec = Math.floor((Date.now() - ts) / 1000);
  if (sec < 60) return `${sec}s ago`;
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min}m ago`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr}h ago`;
  const d = Math.floor(hr / 24);
  return `${d}d ago`;
}