/**
 * ============================================================================
 *  TYPES — shapes shared between the frontend and the FastAPI backend
 * ============================================================================
 * These mirror the Pydantic models in backend/guardrails.py and
 * backend/main.py. See Project 1's lib/types.ts for the fuller explanation
 * of why we keep a hand-written copy of these shapes on both sides.
 * ============================================================================
 */

// One canned red-team prompt, as returned by GET /attacks.
export interface Attack {
  id: string;
  label: string;
  category: string;
  prompt: string;
}

// What POST /chat sends back for a single message.
export interface ChatResult {
  text: string | null;
  blocked: boolean;
  // Which safety layer stopped it, if any — matches backend/main.py exactly.
  blocked_layer: "input-moderation" | "output-moderation" | null;
  blocked_categories: string[];
  moderation_available: boolean;
  guard_mode: string;
  provider: string;
  model: string;
  error: string | null;
}

// One row in the on-page "attempt log". This type only exists on the
// frontend (the backend doesn't remember past requests) — it's just how we
// keep a running history of what you've tried in THIS browser session, so
// you can compare results across different guard modes without them
// disappearing the moment you send the next message.
export interface LogEntry {
  id: string;
  timestamp: number;
  messagePreview: string;
  attackLabel: string | null; // null if it was a message you typed yourself
  guardMode: string;
  moderationOn: boolean;
  result: ChatResult;
}
