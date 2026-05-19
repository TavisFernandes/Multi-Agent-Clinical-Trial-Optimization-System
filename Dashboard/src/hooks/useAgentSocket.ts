import { runMockPipeline } from "../mock/runMockPipeline";
import type { AgentWireEvent } from "../types/agentEvents";

function wsUrl(): string {
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  return `${proto}//${window.location.host}/ws/agents`;
}

/**
 * Runs analysis via WebSocket (proxied to FastAPI in dev) or local mock stream.
 */
export async function runAgentAnalysis(
  text: string,
  mock: boolean,
  onEvent: (ev: AgentWireEvent) => void,
): Promise<void> {
  if (mock) {
    await runMockPipeline(text, onEvent);
    return;
  }

  await new Promise<void>((resolve, reject) => {
    const ws = new WebSocket(wsUrl());
    let finished = false;

    const done = () => {
      if (finished) return;
      finished = true;
      resolve();
    };

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: "analyze", text }));
    };

    ws.onmessage = (m) => {
      let ev: AgentWireEvent;
      try {
        ev = JSON.parse(String(m.data)) as AgentWireEvent;
      } catch {
        onEvent({ type: "error", message: "Malformed WebSocket payload" });
        ws.close();
        done();
        return;
      }
      onEvent(ev);
      if (ev.type === "result" || ev.type === "final_output" || ev.type === "error") {
        ws.close();
        done();
      }
    };

    ws.onerror = () => {
      if (!finished) {
        onEvent({ type: "error", message: "WebSocket connection failed" });
        finished = true;
        reject(new Error("WebSocket error"));
      }
    };

    ws.onclose = () => {
      done();
    };
  });
}
