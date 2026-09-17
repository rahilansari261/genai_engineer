/**
 * ============================================================================
 *  HOME PAGE — one embedding index, three features
 * ============================================================================
 * The whole point of this project in one page: Search, Recommendations
 * ("more like this"), and Anomaly detection are NOT three different
 * technologies — they're the same embedding index, queried three
 * different ways. Switching tabs below doesn't change what data is
 * loaded, only what question you're asking of it.
 * ============================================================================
 */

"use client";

import { useEffect, useState } from "react";
import AnomalyPanel from "@/components/AnomalyPanel";
import BrowsePanel from "@/components/BrowsePanel";
import EmbedderPicker from "@/components/EmbedderPicker";
import SearchPanel from "@/components/SearchPanel";
import type { EmbedderId, EmbedderInfo } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Tab = "search" | "browse" | "anomalies";

export default function Home() {
  const [embedders, setEmbedders] = useState<EmbedderInfo[]>([]);
  const [activeEmbedder, setActiveEmbedder] = useState<EmbedderId>("local");
  const [tab, setTab] = useState<Tab>("search");
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/embedders`)
      .then((res) => res.json())
      .then((data: EmbedderInfo[]) => {
        setEmbedders(data);
        // Prefer whichever embedder is actually indexed already.
        const firstIndexed = data.find((e) => e.indexed);
        if (firstIndexed) setActiveEmbedder(firstIndexed.id);
      })
      .catch(() => setLoadError(`Couldn't reach the backend at ${API_URL}`));
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">Semantic Search & Recommender</h1>
        <p className="mt-1 text-sm opacity-70">
          One embedding index over 50 personal notes — search by meaning, find similar notes, spot the odd ones out.
        </p>
      </header>

      {loadError && <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>}

      <EmbedderPicker embedders={embedders} active={activeEmbedder} onChange={setActiveEmbedder} />

      <nav className="flex gap-2 border-b border-black/10 dark:border-white/15">
        {(["search", "browse", "anomalies"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm capitalize ${
              tab === t ? "border-b-2 border-black font-medium dark:border-white" : "opacity-60"
            }`}
          >
            {t === "browse" ? "Browse & Similar" : t}
          </button>
        ))}
      </nav>

      {tab === "search" && <SearchPanel key={activeEmbedder} embedder={activeEmbedder} />}
      {tab === "browse" && <BrowsePanel key={activeEmbedder} embedder={activeEmbedder} />}
      {tab === "anomalies" && <AnomalyPanel key={activeEmbedder} embedder={activeEmbedder} />}
    </main>
  );
}
