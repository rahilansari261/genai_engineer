/**
 * ============================================================================
 *  TYPES — shapes shared between the frontend and backend/main.py
 * ============================================================================
 */

export type ChatProvider = "ollama" | "openai";
export type VisionProvider = "ollama" | "openai";
export type ImageGenProvider = "huggingface" | "openai";

export interface TraceStep {
  type: "thought" | "action" | "observation" | "final" | "error";
  tool?: string;
  content: string;
}

// The raw shape POST /chat returns.
export interface ChatApiResult {
  trace: TraceStep[];
  final_answer: string | null;
  blocked: boolean;
  blocked_layer: "input-moderation" | "output-moderation" | null;
  blocked_categories: string[];
  moderation_available: boolean;
  attachments: string[]; // base64 PNGs generated during this turn
  cost_usd: number;
  error: string | null;
}

// One entry in the on-screen conversation — a user turn or an assistant
// turn, with everything needed to render it (trace, attachments, cost).
export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  imagePreviewUrl?: string; // for a user message with an attached image
  result?: ChatApiResult; // for an assistant message
}
