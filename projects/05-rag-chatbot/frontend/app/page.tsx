/**
 * ============================================================================
 *  HOME PAGE — chat with the AI engineering handbook in backend/docs/
 * ============================================================================
 * The flow: pick a pipeline (raw or langchain) and, for the raw pipeline,
 * a vector store (local Chroma or cloud Pinecone). Ask a question. The
 * backend embeds it, retrieves the closest chunks from backend/docs/*.md,
 * and generates an answer grounded in them — see backend/main.py's
 * POST /ask for the exact routing. Every answer is added to the
 * comparison log below, so asking the same question again under
 * different settings builds up a real side-by-side comparison.
 * ============================================================================
 */

"use client";

import { useEffect, useState } from "react";
import ComparisonLog from "@/components/ComparisonLog";
import PipelinePicker from "@/components/PipelinePicker";
import type { AskResult, LlmProvider, LogEntry, Pipeline, StatusResponse, VectorStoreBackend } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DEFAULT_MODEL: Record<LlmProvider, string> = {
  ollama: "llama3.2",
  openai: "gpt-4o-mini",
  anthropic: "claude-3-5-haiku-20241022",
};

export default function Home() {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [docs, setDocs] = useState<string[]>([]);

  const [pipeline, setPipeline] = useState<Pipeline>("raw");
  const [vectorStore, setVectorStore] = useState<VectorStoreBackend>("chroma");
  const [llmProvider, setLlmProvider] = useState<LlmProvider>("ollama");
  const [llmModel, setLlmModel] = useState(DEFAULT_MODEL.ollama);

  const [question, setQuestion] = useState("What's the difference between fine-tuning and RAG?");
  const [log, setLog] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/status`)
      .then((res) => res.json())
      .then(setStatus)
      .catch(() => setLoadError(`Couldn't reach the backend at ${API_URL}`));
    fetch(`${API_URL}/corpus`)
      .then((res) => res.json())
      .then((data) => setDocs(data.docs ?? []))
      .catch(() => {});
  }, []);

  function handleProviderChange(next: LlmProvider) {
    setLlmProvider(next);
    setLlmModel(DEFAULT_MODEL[next]);
  }

  async function ask() {
    if (!question.trim()) return;
    setLoading(true);
    setLoadError(null);

    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          pipeline,
          vector_store: vectorStore,
          llm_provider: llmProvider,
          llm_model: llmModel,
          top_k: 4,
        }),
      });
      const result: AskResult = await res.json();

      setLog((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          question,
          pipeline,
          vectorStore,
          llmProvider,
          llmModel,
          result,
        },
      ]);
    } catch {
      setLoadError(`Couldn't reach the backend at ${API_URL}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">RAG Chatbot</h1>
        <p className="mt-1 text-sm opacity-70">
          Chat with a small AI engineering handbook, built two ways: by hand, and with LangChain.
        </p>
        {docs.length > 0 && (
          <p className="mt-2 text-xs opacity-50">Indexed docs: {docs.join(", ")}</p>
        )}
      </header>

      {loadError && <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>}

      <PipelinePicker
        status={status}
        pipeline={pipeline}
        vectorStore={vectorStore}
        onPipelineChange={setPipeline}
        onVectorStoreChange={setVectorStore}
      />

      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
        <span className="opacity-70">LLM</span>
        {(["ollama", "openai", "anthropic"] as LlmProvider[]).map((p) => (
          <button
            key={p}
            onClick={() => handleProviderChange(p)}
            className={`rounded-lg border px-3 py-1.5 text-xs ${
              llmProvider === p ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
            }`}
          >
            {p}
          </button>
        ))}
        <input
          value={llmModel}
          onChange={(e) => setLlmModel(e.target.value)}
          className="w-48 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
        />
      </div>

      <div className="flex flex-col gap-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          className="w-full resize-y rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-4 py-3 text-sm"
          placeholder="Ask something about RAG, embeddings, agents, safety, or fine-tuning…"
        />
        <button
          onClick={ask}
          disabled={loading || !question.trim()}
          className="self-end rounded-lg bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-medium opacity-70">Comparison log</h2>
        <ComparisonLog entries={log} />
      </section>
    </main>
  );
}
