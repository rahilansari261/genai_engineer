/**
 * ============================================================================
 *  OLLAMA PANEL — engine 1: a model running on YOUR OWN computer
 * ============================================================================
 * Sends a prompt to our backend, which uses the official Ollama SDK
 * (backend/ollama_local.py) to talk to a model running locally. Nothing
 * about the AI itself leaves your machine — the backend is just relaying
 * your prompt to Ollama's local server and handing the reply back to the
 * browser.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import type { OllamaResult } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function OllamaPanel() {
  const [model, setModel] = useState("llama3.2");
  const [prompt, setPrompt] = useState("Explain what 'open source' means, in one sentence.");
  const [result, setResult] = useState<OllamaResult | null>(null);
  const [loading, setLoading] = useState(false);

  async function run() {
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${API_URL}/ollama/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model, prompt }),
      });
      setResult(await res.json());
    } catch {
      setResult({ text: null, error: `Couldn't reach the backend at ${API_URL}` });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-black/10 dark:border-white/15 p-4">
      <div>
        <h2 className="font-medium">1. Ollama — runs on your machine</h2>
        <p className="text-xs opacity-60">Free, private, offline. Requires `ollama serve` running locally.</p>
      </div>

      <input
        value={model}
        onChange={(e) => setModel(e.target.value)}
        className="rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
        placeholder="model name, e.g. llama3.2"
      />
      <textarea
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        rows={3}
        className="rounded border border-black/10 dark:border-white/15 bg-transparent px-3 py-2 text-sm"
      />
      <button
        onClick={run}
        disabled={loading || !prompt.trim()}
        className="self-start rounded-lg bg-black px-4 py-1.5 text-xs font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
      >
        {loading ? "Running…" : "Run"}
      </button>

      {result?.error && <p className="text-xs text-red-600 dark:text-red-400">{result.error}</p>}
      {result?.text && <p className="whitespace-pre-wrap text-sm">{result.text}</p>}
    </div>
  );
}
