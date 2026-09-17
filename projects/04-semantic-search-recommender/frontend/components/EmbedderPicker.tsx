/**
 * ============================================================================
 *  EMBEDDER PICKER — choosing which embedding index to search against
 * ============================================================================
 * This project can hold TWO separate indexes over the exact same 50 notes:
 * one embedded with a free local model (Sentence Transformers), one
 * embedded with OpenAI's paid Embeddings API — see backend/ingest.py. This
 * component just shows which of those actually got built (you have to run
 * `python ingest.py` first — see the README) and lets you switch between
 * them, so you can compare search quality between a free and a paid
 * embedding model on the identical dataset.
 * ============================================================================
 */

import type { EmbedderId, EmbedderInfo } from "@/lib/types";

export default function EmbedderPicker({
  embedders,
  active,
  onChange,
}: {
  embedders: EmbedderInfo[];
  active: EmbedderId;
  onChange: (id: EmbedderId) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
      <span className="opacity-70">Embedding index:</span>
      {embedders.map((e) => {
        const disabled = !e.indexed;
        return (
          <button
            key={e.id}
            disabled={disabled}
            onClick={() => onChange(e.id)}
            title={
              !e.available
                ? "Not available — missing OPENAI_API_KEY"
                : !e.indexed
                  ? "Run `python ingest.py` in the backend first"
                  : `${e.count} items indexed`
            }
            className={`rounded-lg border px-3 py-1.5 text-xs disabled:opacity-40 ${
              active === e.id
                ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black"
                : "border-black/10 dark:border-white/15"
            }`}
          >
            {e.label} {e.indexed ? `(${e.count})` : "— not indexed"}
          </button>
        );
      })}
    </div>
  );
}
