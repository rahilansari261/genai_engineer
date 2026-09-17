/**
 * ============================================================================
 *  BROWSER CLASSIFIER — engine 3: no backend at all, runs in THIS tab
 * ============================================================================
 * This is the genuinely different one. Ollama runs on your computer but
 * through our Python backend; Hugging Face runs on their servers. This
 * component downloads a small AI model directly into your browser tab and
 * runs it right here, in JavaScript, using WebAssembly — there is no
 * `fetch()` to our FastAPI backend anywhere in this file. If you turned
 * the backend off entirely, this panel would still work.
 *
 * Transformers.js (`@huggingface/transformers`) is what makes this
 * possible: it's a JavaScript port of Hugging Face's Python `transformers`
 * library, running models that have been converted to the ONNX format
 * (a format designed to run efficiently outside of Python).
 *
 * We load the library and the model LAZILY (only once you click "Load
 * model"), for two reasons: it's a real, multi-megabyte download the
 * first time, and importing it during server-side rendering would try to
 * run browser-only code on the server, where it doesn't belong.
 * ============================================================================
 */

"use client";

import { useRef, useState } from "react";

// The exact shape of a Transformers.js "sentiment-analysis" pipeline
// function — described here by hand because the library's own types are
// generic over many different pipeline tasks, and pinning down this one
// specific shape keeps the rest of this component simple to read.
type Classifier = (text: string) => Promise<Array<{ label: string; score: number }>>;

type Status = "idle" | "loading-model" | "ready" | "running" | "error";

export default function BrowserClassifier() {
  const [status, setStatus] = useState<Status>("idle");
  const [text, setText] = useState("Learning to run AI models in the browser is surprisingly satisfying.");
  const [result, setResult] = useState<{ label: string; score: number } | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // A ref (not state) because the loaded pipeline function itself never
  // needs to trigger a re-render when it changes — we only care about the
  // `status` for that. Refs are React's way of holding onto a value across
  // renders without asking React to redraw the page when it changes.
  const classifierRef = useRef<Classifier | null>(null);

  async function loadModel() {
    setStatus("loading-model");
    setErrorMessage(null);
    try {
      // Dynamic import: this line is what keeps the (fairly large) ONNX
      // runtime out of the page's initial JavaScript bundle. It's only
      // fetched once this function actually runs — i.e. once you click
      // the button — not the moment the page loads.
      const { pipeline } = await import("@huggingface/transformers");

      // First call downloads the model's weights (cached by the browser
      // afterwards) and compiles it to run via WebAssembly. Everything
      // after this line runs entirely on your CPU, in this tab.
      const classifier = (await pipeline(
        "sentiment-analysis",
        "Xenova/distilbert-base-uncased-finetuned-sst-2-english"
      )) as unknown as Classifier;

      classifierRef.current = classifier;
      setStatus("ready");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Failed to load the model");
      setStatus("error");
    }
  }

  async function classify() {
    if (!classifierRef.current) return;
    setStatus("running");
    try {
      const output = await classifierRef.current(text);
      setResult(output[0]);
      setStatus("ready");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Classification failed");
      setStatus("error");
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-black/10 dark:border-white/15 p-4">
      <div>
        <h2 className="font-medium">3. Transformers.js — runs in this browser tab</h2>
        <p className="text-xs opacity-60">
          No backend call at all. First load downloads ~30-60MB of model weights, cached after that.
        </p>
      </div>

      {status === "idle" && (
        <button
          onClick={loadModel}
          className="self-start rounded-lg bg-black px-4 py-1.5 text-xs font-medium text-white dark:bg-white dark:text-black"
        >
          Load model into browser
        </button>
      )}

      {status === "loading-model" && (
        <p className="text-xs opacity-60">Downloading and compiling the model — first time only…</p>
      )}

      {(status === "ready" || status === "running") && (
        <>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={3}
            className="rounded border border-black/10 dark:border-white/15 bg-transparent px-3 py-2 text-sm"
          />
          <button
            onClick={classify}
            disabled={status === "running" || !text.trim()}
            className="self-start rounded-lg bg-black px-4 py-1.5 text-xs font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
          >
            {status === "running" ? "Classifying…" : "Classify"}
          </button>
          {result && (
            <p className="text-sm">
              <span className="font-medium">{result.label}</span>
              {" — confidence "}
              {(result.score * 100).toFixed(1)}%
            </p>
          )}
        </>
      )}

      {status === "error" && (
        <p className="text-xs text-red-600 dark:text-red-400">{errorMessage}</p>
      )}
    </div>
  );
}
