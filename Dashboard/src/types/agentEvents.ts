export type UiPhase = "idle" | "processing" | "done";

export type LogicLineVariant = "default" | "architect" | "critic" | "system" | "error";

export interface LogicLine {
  id: string;
  text: string;
  variant: LogicLineVariant;
}

export interface NerEntity {
  text?: string;
  label?: string;
}

/** Server / mock payloads the dashboard understands */
export type AgentWireEvent = Record<string, unknown> & {
  type?: string;
  agent?: string;
  message?: string;
  effect?: string;
  feedback?: string;
  entities?: NerEntity[];
  route?: string;
  detail?: unknown;
  data?: unknown;
};
