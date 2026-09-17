/**
 * ============================================================================
 *  TYPES — shapes returned by the agent backend
 * ============================================================================
 * Mirrors the Pydantic models in backend/main.py. One TraceStep shape is
 * shared by all three engines — see main.py's file comment for why that
 * matters: it's what lets one TraceView component render any engine's run.
 * ============================================================================
 */

export type Engine = "react" | "functions" | "responses";
export type ReactProvider = "ollama" | "openai";

export interface TraceStep {
  type: "thought" | "action" | "observation" | "final" | "error";
  tool?: string;
  content: string;
}

export interface AgentResult {
  trace: TraceStep[];
  final_answer: string | null;
  error: string | null;
}

// One row in the on-page comparison log — ask the same question with a
// different engine (or provider/model) and compare how each one got there.
export interface LogEntry {
  id: string;
  question: string;
  engine: Engine;
  provider: ReactProvider | null; // only meaningful for the "react" engine
  model: string;
  maxSteps: number;
  result: AgentResult;
}
