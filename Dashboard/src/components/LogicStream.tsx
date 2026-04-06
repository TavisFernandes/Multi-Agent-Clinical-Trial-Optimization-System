import { useEffect, useRef } from "react";
import type { LogicLine } from "../types/agentEvents";

type CurrentAgent = "idle" | "architect" | "critic";

const variantClass: Record<LogicLine["variant"], string> = {
  default: "text-white/80",
  architect: "text-teal-neon drop-shadow-[0_0_8px_rgba(45,212,191,0.35)]",
  critic: "text-rose-300",
  system: "text-white/50",
  error: "text-rose-400 font-semibold",
};

export function LogicStream({ lines, currentAgent = "idle" }: { lines: LogicLine[]; currentAgent?: CurrentAgent }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const borderColorClass = currentAgent === "architect" 
    ? "border-teal-neon/50" 
    : currentAgent === "critic" 
      ? "border-red-500/50" 
      : "border-white/10";
  const headerColorClass = currentAgent === "architect"
    ? "text-teal-neon"
    : currentAgent === "critic"
    ? "text-red-400"
    : "text-white/60";

  return (
    <section className={`flex h-full min-h-[320px] max-h-[min(100vh,800px)] flex-col rounded-2xl border ${borderColorClass} bg-white/[0.08] p-4 shadow-glass backdrop-blur-2xl transition-all duration-500`}>
      <header className={`mb-3 flex items-center justify-between border-b transition-all duration-500 ${borderColorClass} pb-2`}>
        <h2 className={`text-sm font-semibold uppercase tracking-[0.2em] transition-all duration-500 ${headerColorClass}`}>
          Agent Terminal
        </h2>
        <span className={`rounded-full border ${borderColorClass} px-2 py-1 text-xs transition-all duration-500 ${headerColorClass}`}>
          /ws/agents
        </span>
      </header>
      <div
        id="agentTerminal"
        className="logic-scroll flex-1 space-y-3 overflow-y-auto pr-1 font-mono text-sm leading-relaxed"
      >
        {lines.length === 0 && (
          <p className="text-white/40 text-sm leading-relaxed">
            Awaiting run. Toggle Mock Mode to simulate the full cyber-medical flow
            without trained weights.
          </p>
        )}
        {lines.map((line) => (
          <div
            key={line.id}
            className={`border-l transition-all duration-300 ${borderColorClass} pl-2 ${variantClass[line.variant]}`}
          >
            {line.text}
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </section>
  );
}
