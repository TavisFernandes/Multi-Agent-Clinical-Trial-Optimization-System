import type { AgentWireEvent } from "../types/agentEvents";

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms));

let _id = 0;
const nid = () => `mock-${++_id}`;

/**
 * Simulates: Upload → classify → NER graph → Architect draft → Critic reject → Architect final → graph steady.
 * Event shapes mirror the real `/ws/agents` stream for drop-in replacement.
 */
export async function runMockPipeline(
  text: string,
  onEvent: (ev: AgentWireEvent) => void,
): Promise<void> {
  const sample = text.trim() || "Phase II oncology trial with dose escalation.";

  onEvent({ type: "status", message: "Ingesting clinical payload (mock)…", id: nid() });
  await delay(500);

  onEvent({
    type: "ner_graph",
    route: "text",
    entities: [
      { text: "Phase II", label: "PHASE" },
      { text: "Drug X", label: "DRUG" },
      { text: "150 mg", label: "DOSAGE" },
      { text: "N=90", label: "ENROLLMENT" },
      { text: "Primary endpoint", label: "ENDPOINT" },
    ],
  });
  await delay(450);

  onEvent({
    type: "reasoning",
    agent: "Orchestrator",
    message: "Task classified as TEXT → NER + RNN path (mock).",
    iteration: 0,
    step: 0,
  });
  await delay(400);

  onEvent({
    type: "reasoning",
    agent: "Retriever",
    message: "Vector search: 4 protocol chunks matched entities.",
    effect: undefined,
  });
  await delay(500);

  onEvent({
    type: "reasoning",
    agent: "Architect",
    message: "Drafting Medical Report v1 (sections: Overview, Evidence).",
    effect: "architect_pulse",
  });
  await delay(700);

  onEvent({
    type: "reasoning",
    agent: "Critic",
    message:
      "Missing or weak fields: Dosage, Phase, Patient Count — returning to Architect.",
    effect: "critic_glitch",
    feedback: "Dosage Mismatch Detected — structured dose line absent from draft.",
  });
  await delay(900);

  onEvent({
    type: "reasoning",
    agent: "Architect",
    message: "Revising report: injecting Dosage, Phase, Enrollment blocks.",
    effect: "architect_pulse",
  });
  await delay(750);

  onEvent({
    type: "reasoning",
    agent: "Critic",
    message: "Report passes structural checks (Dosage, Phase, Patient Count signals present).",
    effect: "critic_ok",
  });
  await delay(400);

  onEvent({
    type: "loop_complete",
    session_id: "mock-session",
    approved: true,
    critic_approved: true,
    iterations_used: 2,
  });

  const final_report = `# Mock final report\n\nSource excerpt: ${sample.slice(0, 200)}…\n\n## Dosage\n150 mg QD (mock)\n\n## Phase\nPhase II\n\n## Enrollment\nN=90`;

  const mockPayload = {
    session_id: "mock-session",
    report: final_report,
    final_report,
    critic_approved: true,
    input_type: "text",
    entities: [],
    analysis: "",
    retrieved_trials: [],
    agent_iterations: ["Iteration 1: mock", "Iteration 2: mock approved"],
    pipeline: { route: "text", warnings: ["Mock mode — models not loaded."] },
  };

  onEvent({
    type: "result",
    data: mockPayload,
  });

  onEvent({
    type: "final_output",
    data: mockPayload,
  });
}
