/**
 * ============================================================================
 *  ANOMALY PANEL — "anomaly detection", made concrete as "the odd ones out"
 * ============================================================================
 * Same embeddings, third job: instead of comparing to a query or to one
 * item, compare every item to the CENTROID (the average position of every
 * embedding in the index) and rank by distance from it. Notes that don't
 * closely match any of the dataset's topic clusters end up furthest away
 * — that's "anomaly detection" using nothing but the same distance math as
 * search and recommendations.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import type { EmbedderId, ScoredItem } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function AnomalyPanel({ embedder }: { embedder: EmbedderId }) {
  const [results, setResults] = useState<ScoredItem[] | null>(null);
  const [loading, setLoading] = useState(false);

  async function findOutliers() {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/anomalies?embedder=${embedder}&top_k=5`);
      const data = await res.json();
      setResults(data.results ?? []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <button
          onClick={findOutliers}
          disabled={loading}
          className="rounded-lg bg-black px-4 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
        >
          {loading ? "Computing…" : "Find the 5 most unusual notes"}
        </button>
        <p className="mt-2 text-xs opacity-50">
          Ranked by distance from the centroid — the &quot;average meaning&quot; of the whole dataset.
        </p>
      </div>

      {results && (
        <ul className="flex flex-col gap-2">
          {results.map((item, i) => (
            <li key={item.id} className="rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
              <div className="mb-1 flex items-center justify-between text-xs opacity-50">
                <span>
                  #{i + 1} · <span className="capitalize">{item.category}</span>
                </span>
                <span>distance from centroid {item.distance.toFixed(3)}</span>
              </div>
              {item.text}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
