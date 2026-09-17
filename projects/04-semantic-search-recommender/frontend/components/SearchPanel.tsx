/**
 * ============================================================================
 *  SEARCH PANEL — semantic search vs. plain keyword search, side by side
 * ============================================================================
 * This is the whole "problem this solves" pitch from the project README,
 * made visible: the SAME query is run two ways at once —
 *   - keyword: does this note share actual words with your query?
 *   - semantic: is this note's MEANING close to your query's meaning,
 *     according to the embedding model, regardless of shared words?
 * Try the default query below, "raising a well-mannered canine companion"
 * — note n01 (about raising a puppy) never uses the words "canine",
 * "mannered", or "companion" in that sense, so keyword search scores it 0
 * and instead surfaces an unrelated gardening note that happens to
 * contain the literal word "companion" (as in companion planting), while
 * semantic search ranks the actual puppy note first by meaning.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import type { EmbedderId, SearchResponse } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function SearchPanel({ embedder }: { embedder: EmbedderId }) {
  const [query, setQuery] = useState("raising a well-mannered canine companion");
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);

  async function search() {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, embedder, top_k: 5 }),
      });
      setResult(await res.json());
    } catch {
      setResult({ semantic: [], keyword: [], error: `Couldn't reach the backend at ${API_URL}` });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          className="flex-1 rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-3 py-2 text-sm"
          placeholder="Search your notes…"
        />
        <button
          onClick={search}
          disabled={loading || !query.trim()}
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {result?.error && <p className="text-sm text-red-600 dark:text-red-400">{result.error}</p>}

      {result && !result.error && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <h3 className="mb-2 text-sm font-medium">
              Semantic search <span className="opacity-50">(by meaning)</span>
            </h3>
            <ul className="flex flex-col gap-2">
              {result.semantic.map((item) => (
                <li key={item.id} className="rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
                  <div className="mb-1 flex items-center justify-between text-xs opacity-50">
                    <span className="capitalize">{item.category}</span>
                    <span>distance {item.distance.toFixed(3)}</span>
                  </div>
                  {item.text}
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium">
              Keyword search <span className="opacity-50">(shared words)</span>
            </h3>
            <ul className="flex flex-col gap-2">
              {result.keyword.map((item) => (
                <li key={item.id} className="rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
                  <div className="mb-1 flex items-center justify-between text-xs opacity-50">
                    <span className="capitalize">{item.category}</span>
                    <span>{item.score === 0 ? "no shared words" : `${item.score} shared word(s)`}</span>
                  </div>
                  {item.text}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
