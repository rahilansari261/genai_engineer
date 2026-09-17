/**
 * ============================================================================
 *  PIPELINE PICKER — raw vs. LangChain, and (for raw) which vector store
 * ============================================================================
 * This is the control surface for the project's central comparison: the
 * SAME question, answered by two differently-built pipelines, optionally
 * against two different vector stores. Options are disabled — not
 * hidden — when they haven't been indexed yet (or, for Pinecone, aren't
 * configured at all), so it's clear WHY something can't be picked yet
 * rather than it just silently not being there.
 * ============================================================================
 */

import type { Pipeline, StatusResponse, VectorStoreBackend } from "@/lib/types";

export default function PipelinePicker({
  status,
  pipeline,
  vectorStore,
  onPipelineChange,
  onVectorStoreChange,
}: {
  status: StatusResponse | null;
  pipeline: Pipeline;
  vectorStore: VectorStoreBackend;
  onPipelineChange: (p: Pipeline) => void;
  onVectorStoreChange: (v: VectorStoreBackend) => void;
}) {
  const rawReady = status?.raw_chroma.indexed ?? false;
  const langchainReady = status?.langchain_chroma.indexed ?? false;
  const pineconeReady = status?.raw_pinecone.indexed ?? false;
  const pineconeConfigured = status?.raw_pinecone.available ?? false;

  return (
    <div className="flex flex-wrap items-center gap-4 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
      <div className="flex items-center gap-2">
        <span className="opacity-70">Pipeline</span>
        <button
          disabled={!rawReady}
          onClick={() => onPipelineChange("raw")}
          title={!rawReady ? "Run `python ingest.py` in the backend first" : `${status?.raw_chroma.count} chunks indexed`}
          className={`rounded-lg border px-3 py-1.5 text-xs disabled:opacity-40 ${
            pipeline === "raw" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
          }`}
        >
          raw (hand-rolled)
        </button>
        <button
          disabled={!langchainReady}
          onClick={() => onPipelineChange("langchain")}
          title={!langchainReady ? "Run `python ingest.py` in the backend first" : `${status?.langchain_chroma.count} chunks indexed`}
          className={`rounded-lg border px-3 py-1.5 text-xs disabled:opacity-40 ${
            pipeline === "langchain" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
          }`}
        >
          langchain
        </button>
      </div>

      {pipeline === "raw" && (
        <div className="flex items-center gap-2">
          <span className="opacity-70">Vector store</span>
          <button
            onClick={() => onVectorStoreChange("chroma")}
            className={`rounded-lg border px-3 py-1.5 text-xs ${
              vectorStore === "chroma" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
            }`}
          >
            Chroma (local)
          </button>
          <button
            disabled={!pineconeReady}
            onClick={() => onVectorStoreChange("pinecone")}
            title={
              !pineconeConfigured
                ? "Not available — missing PINECONE_API_KEY"
                : !pineconeReady
                  ? "Run `python ingest.py` in the backend first"
                  : `${status?.raw_pinecone.count} vectors indexed`
            }
            className={`rounded-lg border px-3 py-1.5 text-xs disabled:opacity-40 ${
              vectorStore === "pinecone" ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
            }`}
          >
            Pinecone (cloud)
          </button>
        </div>
      )}
    </div>
  );
}
