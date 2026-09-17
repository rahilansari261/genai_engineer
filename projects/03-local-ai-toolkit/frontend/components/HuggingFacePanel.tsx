/**
 * ============================================================================
 *  HUGGING FACE PANEL — engine 2: a task-specific model on HF's servers
 * ============================================================================
 * Unlike the Ollama panel (general chat) or the browser panel (also
 * sentiment), this one deliberately offers TWO different narrow tasks —
 * sentiment classification and summarization — to make the "Hugging Face
 * Tasks" idea concrete: it's not one general-purpose model, it's a hub of
 * many small models each built for one job. Switching the dropdown here
 * calls a completely different backend endpoint with a completely
 * different model.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import type { ClassifyResult, SummarizeResult } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Task = "classify" | "summarize";

const DEFAULT_MODEL: Record<Task, string> = {
  classify: "distilbert-base-uncased-finetuned-sst-2-english",
  summarize: "sshleifer/distilbart-cnn-12-6",
};

const DEFAULT_TEXT: Record<Task, string> = {
  classify: "I've been learning AI engineering and it's honestly a lot more fun than I expected.",
  summarize:
    "Retrieval-Augmented Generation, or RAG, is a technique that combines a language model with an external knowledge source. Instead of relying only on what the model learned during training, the system first searches a document collection for relevant passages, then feeds those passages into the model's prompt alongside the user's question. This lets the model answer using information it was never trained on, and lets you update its knowledge just by updating the documents, without retraining anything.",
};

export default function HuggingFacePanel() {
  const [task, setTask] = useState<Task>("classify");
  const [model, setModel] = useState(DEFAULT_MODEL.classify);
  const [text, setText] = useState(DEFAULT_TEXT.classify);
  const [result, setResult] = useState<ClassifyResult | SummarizeResult | null>(null);
  const [loading, setLoading] = useState(false);

  function handleTaskChange(next: Task) {
    setTask(next);
    setModel(DEFAULT_MODEL[next]);
    setText(DEFAULT_TEXT[next]);
    setResult(null);
  }

  async function run() {
    setLoading(true);
    setResult(null);
    const endpoint = task === "classify" ? "/hf/classify" : "/hf/summarize";
    try {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, model }),
      });
      setResult(await res.json());
    } catch {
      setResult({ error: `Couldn't reach the backend at ${API_URL}` } as ClassifyResult);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-black/10 dark:border-white/15 p-4">
      <div>
        <h2 className="font-medium">2. Hugging Face — runs on HF&apos;s servers</h2>
        <p className="text-xs opacity-60">Free tier, one task-specific model per job. Requires an HF_TOKEN.</p>
      </div>

      <div className="flex gap-2 text-xs">
        <button
          onClick={() => handleTaskChange("classify")}
          className={`rounded px-2 py-1 ${task === "classify" ? "bg-black text-white dark:bg-white dark:text-black" : "border border-black/10 dark:border-white/15"}`}
        >
          Sentiment classification
        </button>
        <button
          onClick={() => handleTaskChange("summarize")}
          className={`rounded px-2 py-1 ${task === "summarize" ? "bg-black text-white dark:bg-white dark:text-black" : "border border-black/10 dark:border-white/15"}`}
        >
          Summarization
        </button>
      </div>

      <input
        value={model}
        onChange={(e) => setModel(e.target.value)}
        className="rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
      />
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={4}
        className="rounded border border-black/10 dark:border-white/15 bg-transparent px-3 py-2 text-sm"
      />
      <button
        onClick={run}
        disabled={loading || !text.trim()}
        className="self-start rounded-lg bg-black px-4 py-1.5 text-xs font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
      >
        {loading ? "Running…" : "Run"}
      </button>

      {result?.error && <p className="text-xs text-red-600 dark:text-red-400">{result.error}</p>}
      {!result?.error && task === "classify" && (result as ClassifyResult)?.label && (
        <p className="text-sm">
          <span className="font-medium">{(result as ClassifyResult).label}</span>
          {" — confidence "}
          {((result as ClassifyResult).score! * 100).toFixed(1)}%
        </p>
      )}
      {!result?.error && task === "summarize" && (result as SummarizeResult)?.summary && (
        <p className="whitespace-pre-wrap text-sm">{(result as SummarizeResult).summary}</p>
      )}
    </div>
  );
}
