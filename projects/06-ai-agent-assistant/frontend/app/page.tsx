/**
 * ============================================================================
 *  HOME PAGE — ask the agent something that needs more than one tool
 * ============================================================================
 * Pick an engine, ask a question, watch the trace build up. Good test
 * questions genuinely need multiple tool calls — e.g. "Look up what RAG
 * is in the handbook, then look up HNSW on Wikipedia, and explain how the
 * two relate" needs both search_handbook AND wikipedia_search before the
 * model has enough to answer. See backend/tools.py for the full tool list.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import EnginePicker from "@/components/EnginePicker";
import RunLog from "@/components/RunLog";
import TraceView from "@/components/TraceView";
import type { AgentResult, Engine, LogEntry, ReactProvider } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DEFAULT_MODEL: Record<string, string> = {
  ollama: "llama3.2",
  openai: "gpt-4o-mini",
};

export default function Home() {
  const [engine, setEngine] = useState<Engine>("react");
  const [provider, setProvider] = useState<ReactProvider>("ollama");
  const [model, setModel] = useState(DEFAULT_MODEL.ollama);
  const [maxSteps, setMaxSteps] = useState(6);

  const [question, setQuestion] = useState(
    "Look up what RAG is in the handbook, then look up HNSW on Wikipedia, and explain how the two relate."
  );
  const [current, setCurrent] = useState<AgentResult | null>(null);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  function handleEngineChange(next: Engine) {
    setEngine(next);
    setModel(next === "react" ? DEFAULT_MODEL[provider] : DEFAULT_MODEL.openai);
  }

  function handleProviderChange(next: ReactProvider) {
    setProvider(next);
    setModel(DEFAULT_MODEL[next]);
  }

  async function ask() {
    if (!question.trim()) return;
    setLoading(true);
    setLoadError(null);
    setCurrent(null);

    const endpoint = `${API_URL}/agent/${engine}`;
    const body =
      engine === "react"
        ? { question, provider, model, max_steps: maxSteps }
        : { question, model, max_steps: maxSteps };

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const result: AgentResult = await res.json();
      setCurrent(result);
      setLog((prev) => [
        ...prev,
        {
          id: `${Date.now()}`,
          question,
          engine,
          provider: engine === "react" ? provider : null,
          model,
          maxSteps,
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
        <h1 className="text-2xl font-semibold">AI Agent Assistant</h1>
        <p className="mt-1 text-sm opacity-70">
          Three ways to build the same tool-using agent — watch its reasoning, not just its answer.
        </p>
      </header>

      {loadError && <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>}

      <EnginePicker
        engine={engine}
        provider={provider}
        model={model}
        onEngineChange={handleEngineChange}
        onProviderChange={handleProviderChange}
        onModelChange={setModel}
      />

      <div className="flex flex-col gap-2">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          rows={3}
          className="w-full resize-y rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-4 py-3 text-sm"
        />
        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-xs opacity-70">
            Max steps
            <input
              type="number"
              min={1}
              max={20}
              value={maxSteps}
              onChange={(e) => setMaxSteps(Number(e.target.value))}
              className="w-16 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1"
            />
          </label>
          <button
            onClick={ask}
            disabled={loading || !question.trim()}
            className="rounded-lg bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
          >
            {loading ? "Running…" : "Ask"}
          </button>
        </div>
      </div>

      {current && (
        <section>
          <h2 className="mb-3 text-sm font-medium opacity-70">Live trace</h2>
          <TraceView trace={current.trace} />
        </section>
      )}

      <section>
        <h2 className="mb-3 text-sm font-medium opacity-70">Run log</h2>
        <RunLog entries={log} />
      </section>
    </main>
  );
}
