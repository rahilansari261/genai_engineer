/**
 * ============================================================================
 *  TYPES — shapes returned by the multimodal backend
 * ============================================================================
 * Mirrors the Pydantic models in backend/main.py.
 * ============================================================================
 */

export type VisionProvider = "ollama" | "openai";
export type ImageGenProvider = "huggingface" | "openai";
export type SpeechProvider = "local" | "openai";
export type TtsProvider = "browser" | "openai";
export type ChatProvider = "ollama" | "openai";

export interface VisionResult {
  answer: string | null;
  error: string | null;
}

export interface ImageGenResult {
  image_base64: string | null;
  error: string | null;
}

export interface TranscribeResult {
  text: string | null;
  error: string | null;
}

export interface ChatResult {
  reply: string | null;
  error: string | null;
}
