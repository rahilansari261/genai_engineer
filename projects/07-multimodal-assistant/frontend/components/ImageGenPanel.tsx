/**
 * ============================================================================
 *  IMAGE GEN PANEL — text prompt in, generated image out
 * ============================================================================
 * See backend/image_gen.py — both engines return a base64 PNG, which this
 * component just drops straight into an <img src="data:image/png;base64,...">,
 * no separate file hosting or URL needed.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import type { ImageGenProvider, ImageGenResult } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const DEFAULT_MODEL: Record<ImageGenProvider, string> = {
  huggingface: "black-forest-labs/FLUX.1-schnell",
  openai: "dall-e-3",
};

export default function ImageGenPanel() {
  const [prompt, setPrompt] = useState("A cozy reading nook with a cat asleep on a stack of programming books, watercolor style");
  const [provider, setProvider] = useState<ImageGenProvider>("huggingface");
  const [model, setModel] = useState(DEFAULT_MODEL.huggingface);
  const [result, setResult] = useState<ImageGenResult | null>(null);
  const [loading, setLoading] = useState(false);

  function handleProviderChange(next: ImageGenProvider) {
    setProvider(next);
    setModel(DEFAULT_MODEL[next]);
  }

  async function generate() {
    if (!prompt.trim()) return;
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(`${API_URL}/image-gen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, provider, model }),
      });
      setResult(await res.json());
    } catch {
      setResult({ image_base64: null, error: `Couldn't reach the backend at ${API_URL}` });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
        <span className="opacity-70">Engine</span>
        {(["huggingface", "openai"] as ImageGenProvider[]).map((p) => (
          <button
            key={p}
            onClick={() => handleProviderChange(p)}
            className={`rounded-lg border px-3 py-1.5 text-xs ${
              provider === p ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
            }`}
          >
            {p === "huggingface" ? "Hugging Face (free, needs HF_TOKEN)" : "OpenAI DALL-E"}
          </button>
        ))}
        <input
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="w-56 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
        />
      </div>

      <div className="flex gap-2">
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="flex-1 rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-3 py-2 text-sm"
        />
        <button
          onClick={generate}
          disabled={loading || !prompt.trim()}
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
        >
          {loading ? "Generating…" : "Generate"}
        </button>
      </div>

      {result?.error && <p className="text-sm text-red-600 dark:text-red-400">{result.error}</p>}
      {result?.image_base64 && (
        // eslint-disable-next-line @next/next/no-img-element -- a base64 data URL can't be optimized either
        <img
          src={`data:image/png;base64,${result.image_base64}`}
          alt={prompt}
          className="max-h-96 rounded-lg border border-black/10 dark:border-white/15"
        />
      )}
    </div>
  );
}
