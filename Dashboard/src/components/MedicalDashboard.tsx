import { motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";
import { runAgentAnalysis } from "../hooks/useAgentSocket";
import type {
  AgentWireEvent,
  LogicLine,
  LogicLineVariant,
  UiPhase,
} from "../types/agentEvents";
import { LogicStream } from "./LogicStream";
import { Scene3D } from "./Scene3D";
import { ScanBeamOverlay } from "./ScanBeamOverlay";
import { SplineBackground } from "./SplineBackground";

let lineSeq = 0;
const nextLineId = () => `l-${++lineSeq}`;

function extractFinalReport(ev: AgentWireEvent): string {
  const raw = ev as Record<string, unknown>;
  const top = raw.final_report;
  if (typeof top === "string" && top.trim()) return top;
  const data = ev.data;
  if (data && typeof data === "object" && !Array.isArray(data)) {
    const d = data as Record<string, unknown>;
    const fr = d.final_report;
    const rep = d.report;
    if (typeof fr === "string" && fr.trim()) return fr;
    if (typeof rep === "string" && rep.trim()) return rep;
  }
  return "";
}

function labelsFromNer(ev: AgentWireEvent): string[] {
  const raw = ev.entities;
  if (!Array.isArray(raw)) return [];
  return raw.map((e) => {
    if (e && typeof e === "object") {
      const o = e as { text?: string; label?: string };
      return (o.text || o.label || "entity").trim();
    }
    return "entity";
  });
}

type CurrentAgent = "idle" | "architect" | "critic";

export function MedicalDashboard() {
  const [phase, setPhase] = useState<UiPhase>("idle");
  const [mockMode, setMockMode] = useState(true);
  const [text, setText] = useState(
    "Phase II dose-escalation of Drug X at 150 mg QD; planned enrollment N=90.",
  );
  const [lines, setLines] = useState<LogicLine[]>([]);
  const [graphLabels, setGraphLabels] = useState<string[]>([
    "NER",
    "PHASE",
    "DRUG",
    "COHORT",
  ]);
  const [pulse, setPulse] = useState(0);
  const [glitch, setGlitch] = useState(false);
  const [scanActive, setScanActive] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<CurrentAgent>("idle");
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [taskClassified, setTaskClassified] = useState<string | null>(null);
  const [finalReport, setFinalReport] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const pushLine = useCallback((t: string, variant: LogicLineVariant = "default") => {
    setLines((prev) => [...prev, { id: nextLineId(), text: t, variant }]);
  }, []);

  const triggerArchitectPulse = useCallback(() => {
    setPulse(1);
    window.setTimeout(() => setPulse(0.35), 180);
    window.setTimeout(() => setPulse(0), 950);
  }, []);

  const triggerCriticGlitch = useCallback(() => {
    setGlitch(true);
    window.setTimeout(() => setGlitch(false), 1100);
  }, []);

  const handleWireEvent = useCallback(
    (ev: AgentWireEvent) => {
      const t = String(ev.type || "");

      if (t === "status" && typeof ev.message === "string") {
        pushLine(`System: ${ev.message}`, "system");
        setCurrentAgent("idle");
        return;
      }

      if (t === "ner_graph") {
        const lbs = labelsFromNer(ev);
        if (lbs.length) setGraphLabels(lbs);
        pushLine(
          `Pipeline: NER graph updated (${String(ev.route || "unknown")} route, ${lbs.length} nodes).`,
          "system",
        );
        setTaskClassified(`NER: ${lbs.join(", ")}`);
        setCurrentAgent("idle");
        return;
      }

      if (t === "reasoning") {
        const agent = String(ev.agent || "Agent");
        const msg = String(ev.message || "");
        const variant: LogicLineVariant =
          agent === "Architect"
            ? "architect"
            : agent === "Critic"
              ? "critic"
              : "default";
        
        if (agent === "Architect") {
          setCurrentAgent("architect");
        } else if (agent === "Critic") {
          setCurrentAgent("critic");
        }
        
        pushLine(`${agent}: ${msg}`, variant);

        if (ev.effect === "architect_pulse") triggerArchitectPulse();
        if (ev.effect === "critic_glitch") {
          triggerCriticGlitch();
          const fb = typeof ev.feedback === "string" ? ev.feedback : "";
          if (fb && fb !== msg) {
            pushLine(`Critic feedback ▸ ${fb}`, "error");
          }
        }
        return;
      }

      if (t === "loop_complete") {
        const ok =
          typeof ev.critic_approved === "boolean"
            ? ev.critic_approved
            : typeof ev.approved === "boolean"
              ? ev.approved
              : true;
        pushLine(`Orchestrator: loop complete (approved=${String(ok)}).`, "system");
        setCurrentAgent("idle");
        return;
      }

      if (t === "final_output") {
        const reportText = extractFinalReport(ev);
        if (reportText) setFinalReport(reportText);
        pushLine("System: Final clinical report received.", "system");
        setCurrentAgent("idle");
        return;
      }

      if (t === "result") {
        const reportText = extractFinalReport(ev);
        if (reportText) setFinalReport(reportText);
        pushLine("System: Final payload received.", "system");
        setCurrentAgent("idle");
        return;
      }

      if (t === "error") {
        const detail =
          typeof ev.detail === "string"
            ? ev.detail
            : typeof ev.message === "string"
              ? ev.message
              : JSON.stringify(ev.detail ?? ev.message ?? ev);
        pushLine(`Error: ${detail}`, "error");
        setCurrentAgent("idle");
      }
    },
    [pushLine, triggerArchitectPulse, triggerCriticGlitch],
  );

  const runPipeline = useCallback(
    async (overrideText?: string) => {
      const payload = (overrideText ?? text).trim();
      if (!payload) {
        pushLine("System: Add clinical text or upload a file first.", "error");
        return;
      }
      setPhase("processing");
      setScanActive(true);
      setFinalReport("");
      pushLine(
        mockMode
          ? "System: Mock Mode — simulating classification, agents, and graph."
          : "System: Live WebSocket stream to FastAPI `/ws/agents`…",
        "system",
      );
      try {
        await runAgentAnalysis(payload, mockMode, handleWireEvent);
      } catch (e) {
        pushLine(`System: ${String(e)}`, "error");
      } finally {
        setScanActive(false);
        setPhase("done");
      }
    },
    [handleWireEvent, mockMode, pushLine, text],
  );

  const onFile = async (f: File | null) => {
    if (!f) return;
    const clipped = (await f.text()).slice(0, 120_000);
    setText(clipped);    setUploadedFileName(f.name);    pushLine(`System: Loaded file “${f.name}” (${f.size} bytes).`, "system");
    await runPipeline(clipped);
  };

  // Dynamic color scheme based on current agent
  const borderColorClass = currentAgent === "architect" 
    ? "border-teal-neon/50" 
    : currentAgent === "critic" 
      ? "border-red-500/50" 
      : "border-white/10";

  return (
    <div className="relative min-h-screen w-full overflow-x-hidden overflow-y-auto bg-navy text-white">
      {/* Phase 1: Spline Background Layer - behind 3D + UI */}
      <div className="fixed inset-0 z-0">
        <SplineBackground />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-navy/35 via-transparent to-navy/50 opacity-70" />
      </div>

      {/* 3D Scene and Effects — above Spline, below cards */}
      <motion.div
        className="fixed inset-0 z-[3] pointer-events-none"
        animate={
          glitch
            ? {
                x: [0, -5, 6, -4, 0],
                y: [0, 2, -3, 1, 0],
                filter: [
                  "hue-rotate(0deg) contrast(1.05)",
                  "hue-rotate(90deg) contrast(1.2)",
                  "hue-rotate(200deg) contrast(1.15)",
                  "hue-rotate(0deg) contrast(1.05)",
                ],
              }
            : { x: 0, y: 0, filter: "hue-rotate(0deg) contrast(1)" }
        }
        transition={{ duration: 0.45, ease: "easeInOut" }}
      >
        <div className="absolute inset-0 opacity-85">
          <Scene3D labels={graphLabels} pulse={pulse} scanActive={scanActive} />
        </div>
      </motion.div>

      {/* Scanning Overlay - Phase 3 */}
      <ScanBeamOverlay active={phase === "processing" && scanActive} />

      {/* Radial Gradient Vignette — lighter center so 3D / Spline read through */}
      <div className="pointer-events-none fixed inset-0 z-[4] bg-[radial-gradient(ellipse_at_center,transparent_0%,#0a0a0c_55%)] opacity-60" />

      {/* Main Layout Container */}
      <div className="relative z-[20] min-h-screen w-full flex flex-col lg:flex-row items-stretch">
        {/* LEFT SIDEBAR - File Upload & Task Classifier */}
        <div className="pointer-events-auto w-full lg:w-80 min-h-0 lg:min-h-screen border-b lg:border-b-0 lg:border-r border-white/10 bg-white/[0.06] backdrop-blur-xl overflow-y-auto">
          <div className="p-6 space-y-6 text-[15px] leading-relaxed">
            {/* File Upload Card */}
            <div className={`rounded-2xl border ${borderColorClass} bg-white/[0.08] p-5 shadow-glass backdrop-blur-2xl transition-all duration-500`}>
              <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/65 mb-4">
                📁 File Upload
              </h3>
              <input
                ref={fileRef}
                type="file"
                accept=".txt,.csv,.md,.json,text/*"
                className="hidden"
                onChange={(e) => void onFile(e.target.files?.[0] ?? null)}
              />
              <button
                type="button"
                onClick={() => fileRef.current?.click()}
                className={`w-full rounded-lg border ${currentAgent === "architect" ? "border-teal-neon/40 hover:border-teal-neon/60" : currentAgent === "critic" ? "border-red-500/40 hover:border-red-500/60" : "border-white/20 hover:border-white/40"} bg-white/[0.05] px-4 py-3 text-sm text-white/80 transition hover:bg-white/[0.08] font-semibold`}
              >
                Choose file
              </button>
              {uploadedFileName && (
                <div className="mt-3 p-2 rounded-lg bg-white/[0.05] border border-white/10">
                  <p className="text-sm text-white/75">
                    <span className="text-teal-neon/90">✓</span> {uploadedFileName}
                  </p>
                </div>
              )}
            </div>

            {/* Task Classifier Status */}
            <div className={`rounded-2xl border ${borderColorClass} bg-white/[0.08] p-5 shadow-glass backdrop-blur-2xl transition-all duration-500`}>
              <h3 className="text-sm font-semibold uppercase tracking-[0.2em] text-white/65 mb-4">
                🏷️ Task Classifier
              </h3>
              <div className="space-y-3">
                <div className={`p-3 rounded-lg border transition-all duration-300 ${
                  phase === "processing" 
                    ? currentAgent === "architect"
                      ? "border-teal-neon/40 bg-teal-neon/5"
                      : currentAgent === "critic"
                      ? "border-red-500/40 bg-red-500/5"
                      : "border-white/10 bg-white/[0.02]"
                    : "border-white/10 bg-white/[0.02]"
                }`}>
                  <p className="text-sm font-mono text-white/75 truncate">
                    <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                      phase === "processing" 
                        ? currentAgent === "architect"
                          ? "bg-teal-neon"
                          : currentAgent === "critic"
                          ? "bg-red-500"
                          : "bg-white/50"
                        : "bg-white/30"
                    }`}></span>
                    Status: <span className={currentAgent === "architect" ? "text-teal-neon" : currentAgent === "critic" ? "text-red-400" : "text-white/60"}>{phase}</span>
                  </p>
                </div>
                {taskClassified && (
                  <div className="p-3 rounded-lg border border-teal-neon/30 bg-teal-neon/5">
                    <p className="text-sm text-teal-neon/90 font-semibold">Labels:</p>
                    <p className="text-sm text-teal-neon/85 mt-2 break-words leading-relaxed">{taskClassified}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Current Agent Badge */}
            {currentAgent !== "idle" && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`rounded-lg border p-3 text-center ${
                  currentAgent === "architect"
                    ? "border-teal-neon/50 bg-teal-neon/10"
                    : "border-red-500/50 bg-red-500/10"
                }`}
              >
                <p className={`text-sm font-bold uppercase tracking-wider ${
                  currentAgent === "architect" ? "text-teal-neon" : "text-red-400"
                }`}>
                  {currentAgent === "architect" ? "🏗️ Architect" : "🔍 Critic"} Active
                </p>
              </motion.div>
            )}
          </div>
        </div>

        {/* CENTER CONTENT */}
        <div className="pointer-events-auto flex-1 min-h-0 flex justify-center items-start py-8 lg:py-12 px-4 lg:px-8">
          <div className="w-full max-w-xl flex flex-col gap-5">
            <header className={`rounded-2xl border ${borderColorClass} bg-white/[0.08] p-6 shadow-glass backdrop-blur-2xl transition-all duration-500`}>
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <p className={`text-xs font-semibold uppercase tracking-[0.35em] ${currentAgent === "architect" ? "text-teal-neon/90" : currentAgent === "critic" ? "text-red-400/90" : "text-teal-neon/80"}`}>
                    🤖 Clinical Intelligence System
                  </p>
                  <h2 className="text-2xl font-semibold tracking-tight text-white mt-2 leading-snug">
                    Multi-Agent Trial Optimization
                  </h2>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3 text-sm leading-snug">
                <div className="p-3 rounded-lg bg-white/[0.06] border border-teal-neon/20">
                  <p className="text-white/65">🏗️ Architect Agent</p>
                  <p className="text-teal-neon/90 font-semibold mt-1">Reasoning</p>
                </div>
                <div className="p-3 rounded-lg bg-white/[0.06] border border-white/10">
                  <p className="text-white/65">🔍 Critic Agent</p>
                  <p className="text-white/80 font-semibold mt-1">Validation</p>
                </div>
                <div className="p-3 rounded-lg bg-white/[0.06] border border-teal-neon/20">
                  <p className="text-white/65">📊 NER Pipeline</p>
                  <p className="text-teal-neon/90 font-semibold mt-1">Classification</p>
                </div>
                <div className="p-3 rounded-lg bg-white/[0.06] border border-white/10">
                  <p className="text-white/65">🌐 WebSocket</p>
                  <p className="text-white/80 font-semibold mt-1">Real-time Sync</p>
                </div>
              </div>
            </header>

            <div className={`rounded-2xl border ${borderColorClass} bg-white/[0.08] p-6 shadow-glass backdrop-blur-2xl transition-all duration-500`}>
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-white/50 block mb-3">
                📋 Clinical Payload
              </label>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={5}
                className={`w-full resize-y min-h-[120px] rounded-xl border transition bg-black/35 px-3 py-3 font-mono text-sm text-white/90 leading-relaxed outline-none focus:ring-2 ${
                  currentAgent === "architect"
                    ? "border-teal-neon/25 focus:border-teal-neon/45 focus:ring-teal-neon/20"
                    : currentAgent === "critic"
                    ? "border-red-500/25 focus:border-red-500/45 focus:ring-red-500/20"
                    : "border-white/10 focus:border-teal-neon/40 focus:ring-teal-neon/20"
                }`}
              />
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => void runPipeline()}
                  disabled={phase === "processing"}
                  className={`rounded-full border px-5 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${
                    currentAgent === "architect"
                      ? "border-teal-neon/50 bg-teal-neon/90 text-navy shadow-[0_0_24px_rgba(45,212,191,0.35)] hover:bg-teal-neon"
                      : currentAgent === "critic"
                      ? "border-red-500/50 bg-red-500/90 text-white shadow-[0_0_24px_rgba(248,113,113,0.35)] hover:bg-red-500"
                      : "border-white/10 bg-teal-neon/90 text-navy shadow-[0_0_24px_rgba(45,212,191,0.25)] hover:bg-teal-neon"
                  }`}
                >
                  {phase === "processing" ? "Processing…" : "Run"}
                </button>
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  className="rounded-full border border-white/20 bg-white/5 px-4 py-2 text-sm text-white/80 transition hover:border-teal-neon/30 hover:bg-white/[0.08]"
                >
                  Upload
                </button>
                <label className="ml-auto flex cursor-pointer items-center gap-2 text-sm text-white/60">
                  <input
                    type="checkbox"
                    checked={mockMode}
                    onChange={(e) => setMockMode(e.target.checked)}
                    className="accent-teal-neon"
                  />
                  Mock
                </label>
              </div>
              <p className="mt-3 text-sm text-white/45">
                State: <span className={currentAgent === "architect" ? "text-teal-neon/90" : currentAgent === "critic" ? "text-red-400/90" : "text-teal-neon/90"}>{phase}</span>
              </p>
            </div>

            <div
              id="finalReportBox"
              className="rounded-2xl border border-teal-neon/25 bg-black/50 p-6 shadow-glass backdrop-blur-xl"
            >
              <h2 className="text-xl font-semibold text-teal-neon/95 tracking-tight m-0 mb-4">
                📄 Final Clinical Report
              </h2>
              <pre
                id="finalReport"
                className="m-0 font-mono text-sm leading-relaxed text-teal-neon/90 whitespace-pre-wrap break-words max-h-[480px] overflow-y-auto"
              >
                {finalReport}
              </pre>
            </div>
          </div>
        </div>

        {/* RIGHT SIDEBAR - Agent Terminal Logs */}
        <div className="pointer-events-auto w-full lg:w-96 min-h-[280px] lg:min-h-screen border-t lg:border-t-0 lg:border-l border-white/10 bg-white/[0.06] backdrop-blur-xl flex flex-col">
          <div className="flex-1 overflow-y-auto p-4 lg:p-5">
            <LogicStream lines={lines} currentAgent={currentAgent} />
          </div>
        </div>
      </div>
    </div>
  );
}
