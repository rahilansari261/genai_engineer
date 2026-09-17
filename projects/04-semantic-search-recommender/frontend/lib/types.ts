/**
 * ============================================================================
 *  TYPES — shapes returned by the backend's search/recommend/anomaly API
 * ============================================================================
 * Mirrors the Pydantic response models in backend/main.py.
 * ============================================================================
 */

export type EmbedderId = "local" | "openai";

export interface EmbedderInfo {
  id: EmbedderId;
  label: string;
  available: boolean; // can this embedder even be used right now (key present, etc.)
  indexed: boolean; // has `python ingest.py` actually built this collection yet
  count: number; // how many items are indexed under it
}

export interface Item {
  id: string;
  text: string;
  category: string;
}

// A search/similar/anomaly result: an Item plus how it was ranked.
export interface ScoredItem extends Item {
  distance: number; // lower = more similar (semantic search, similar-items, and anomaly all reuse this same shape)
}

export interface KeywordMatch extends Item {
  score: number; // higher = more overlapping words with the query
}

export interface SearchResponse {
  semantic: ScoredItem[];
  keyword: KeywordMatch[];
  error: string | null;
}
