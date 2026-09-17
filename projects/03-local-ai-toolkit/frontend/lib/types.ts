/**
 * ============================================================================
 *  TYPES — shapes returned by the backend's three endpoints
 * ============================================================================
 * Mirrors the Pydantic response models in backend/main.py. There's no type
 * here for the browser (Transformers.js) result — that one never leaves
 * the browser, so it doesn't need a "shared with the backend" shape; its
 * type lives directly in BrowserClassifier.tsx instead.
 * ============================================================================
 */

export interface OllamaResult {
  text: string | null;
  error: string | null;
}

export interface ClassifyResult {
  label: string | null;
  score: number | null;
  error: string | null;
}

export interface SummarizeResult {
  summary: string | null;
  error: string | null;
}
