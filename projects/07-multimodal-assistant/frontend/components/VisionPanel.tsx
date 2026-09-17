/**
 * ============================================================================
 *  VISION PANEL — upload an image, ask about it
 * ============================================================================
 * The image is sent as a real file upload (multipart/form-data) to
 * POST /vision, alongside the question and which engine to use. See
 * backend/vision.py for how the SAME image gets attached to the request
 * differently depending on the provider.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import type { VisionProvider, VisionResult } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DEFAULT_MODEL: Record<VisionProvider, string> = {
  ollama: "moondream",
  openai: "gpt-4o-mini",
};

export default function VisionPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [question, setQuestion] = useState("What's in this image?");
  const [provider, setProvider] = useState<VisionProvider>("ollama");
  const [model, setModel] = useState(DEFAULT_MODEL.ollama);
  const [result, setResult] = useState<VisionResult | null>(null);
  const [loading, setLoading] = useState(false);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const selected = e.target.files?.[0] ?? null;
    setFile(selected);
    setResult(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
  }

  function handleProviderChange(next: VisionProvider) {
    setProvider(next);
    setModel(DEFAULT_MODEL[next]);
  }

  async function ask() {
    if (!file) return;
    setLoading(true);
    setResult(null);

    const formData = new FormData();
    formData.append("image", file);
    formData.append("question", question);
    formData.append("provider", provider);
    formData.append("model", model);

    try {
      const res = await fetch(`${API_URL}/vision`, { method: "POST", body: formData });
      setResult(await res.json());
    } catch {
      setResult({ answer: null, error: `Couldn't reach the backend at ${API_URL}` });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
        <span className="opacity-70">Engine</span>
        {(["ollama", "openai"] as VisionProvider[]).map((p) => (
          <button
            key={p}
            onClick={() => handleProviderChange(p)}
            className={`rounded-lg border px-3 py-1.5 text-xs ${
              provider === p ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
            }`}
          >
            {p === "ollama" ? "Ollama (free, local)" : "OpenAI"}
          </button>
        ))}
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="w-40 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
        />
      </div>

      <input type="file" accept="image/*" onChange={handleFileChange} className="text-sm" />

      {previewUrl && (
        // eslint-disable-next-line @next/next/no-img-element -- a locally picked file has no URL to optimize
        <img src={previewUrl} alt="Selected upload" className="max-h-64 rounded-lg border border-black/10 dark:border-white/15" />
      )}

      <div className="flex gap-2">
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          className="flex-1 rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-3 py-2 text-sm"
        />
        <button
          onClick={ask}
          disabled={loading || !file || !question.trim()}
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
        >
          {loading ? "Looking…" : "Ask"}
        </button>
      </div>

      {result?.error && <p className="text-sm text-red-600 dark:text-red-400">{result.error}</p>}
      {result?.answer && <p className="rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">{result.answer}</p>}
    </div>
  );
}
