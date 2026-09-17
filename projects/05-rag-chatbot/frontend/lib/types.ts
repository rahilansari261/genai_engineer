/**
 * ============================================================================
 *  TYPES — shapes returned by the RAG backend
 * ============================================================================
 * Mirrors the Pydantic models in backend/main.py.
 * ============================================================================
 */

export type Pipeline = "raw" | "langchain";
export type VectorStoreBackend = "chroma" | "pinecone";
export type LlmProvider = "ollama" | "openai" | "anthropic";

export interface Source {
  source: string;
  snippet: string;
  distance: number;
}

export interface AskResult {
  answer: string | null;
  sources: Source[];
  error: string | null;
  pipeline: Pipeline;
  vector_store: VectorStoreBackend;
  latency_ms: number;
}

export interface IndexStatus {
  available: boolean;
  indexed: boolean;
  count: number;
}

export interface StatusResponse {
  raw_chroma: IndexStatus;
  raw_pinecone: IndexStatus;
  langchain_chroma: IndexStatus;
}

// One row in the on-page comparison log — lets you ask the same question
// under different pipeline/vector-store/provider combinations and see
// them stack up, the same idea as the attempt log in Project 2.
export interface LogEntry {
  id: string;
  question: string;
  pipeline: Pipeline;
  vectorStore: VectorStoreBackend;
  llmProvider: LlmProvider;
  llmModel: string;
  result: AskResult;
}
