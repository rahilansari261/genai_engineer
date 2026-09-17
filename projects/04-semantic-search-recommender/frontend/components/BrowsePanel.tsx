/**
 * ============================================================================
 *  BROWSE PANEL — "recommendation systems", made concrete as "more like this"
 * ============================================================================
 * This is the exact same embedding index as the search panel, used for a
 * different job: given ONE item, find its nearest neighbors in the index.
 * That's genuinely all a lot of "recommended for you" / "similar items"
 * features are — the same distance calculation as search, just starting
 * from an existing item's embedding instead of typing a new query.
 * ============================================================================
 */

"use client";

import { useEffect, useState } from "react";
import type { EmbedderId, Item, ScoredItem } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function BrowsePanel({ embedder }: { embedder: EmbedderId }) {
  const [items, setItems] = useState<Item[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [similar, setSimilar] = useState<ScoredItem[] | null>(null);
  const [loading, setLoading] = useState(false);

  // Note: this component gets a `key={embedder}` from the parent page, so
  // React fully remounts it (resetting every piece of state to its
  // initial value) whenever the active index changes — a "similar" result
  // computed under one embedder wouldn't mean anything under another, so
  // we want a clean slate, not a manual reset here. See the React docs on
  // "resetting state with a key" for why this is preferred over calling
  // setState for a prop-change reset inside an effect.
  useEffect(() => {
    fetch(`${API_URL}/items?embedder=${embedder}`)
      .then((res) => res.json())
      .then((data) => setItems(data.items ?? []))
      .catch(() => setItems([]));
  }, [embedder]);

  async function findSimilar(id: string) {
    setSelectedId(id);
    setLoading(true);
    setSimilar(null);
    try {
      const res = await fetch(`${API_URL}/similar/${id}?embedder=${embedder}`);
      const data = await res.json();
      setSimilar(data.results ?? []);
    } catch {
      setSimilar([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      <div>
        <h3 className="mb-2 text-sm font-medium">All notes ({items.length})</h3>
        <ul className="flex max-h-[32rem] flex-col gap-2 overflow-y-auto pr-1">
          {items.map((item) => (
            <li
              key={item.id}
              className={`rounded-lg border p-3 text-sm ${
                selectedId === item.id
                  ? "border-black dark:border-white"
                  : "border-black/10 dark:border-white/15"
              }`}
            >
              <div className="mb-1 flex items-center justify-between text-xs opacity-50">
                <span className="capitalize">{item.category}</span>
                <button
                  onClick={() => findSimilar(item.id)}
                  className="rounded border border-black/10 px-2 py-0.5 hover:bg-black/5 dark:border-white/15 dark:hover:bg-white/10"
                >
                  Find similar
                </button>
              </div>
              {item.text}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h3 className="mb-2 text-sm font-medium">
          More like this{selectedId ? ` — ${selectedId}` : ""}
        </h3>
        {!selectedId && <p className="text-xs opacity-50">Click &quot;Find similar&quot; on any note.</p>}
        {loading && <p className="text-xs opacity-50">Loading…</p>}
        {similar && (
          <ul className="flex flex-col gap-2">
            {similar.map((item) => (
              <li key={item.id} className="rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
                <div className="mb-1 flex items-center justify-between text-xs opacity-50">
                  <span className="capitalize">{item.category}</span>
                  <span>distance {item.distance.toFixed(3)}</span>
                </div>
                {item.text}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
