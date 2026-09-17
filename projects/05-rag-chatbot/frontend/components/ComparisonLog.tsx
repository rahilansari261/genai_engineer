/**
 * ============================================================================
 *  COMPARISON LOG — ask the same question under different settings, compare
 * ============================================================================
 * The real point of this project is visible here, not in any single
 * answer: ask the same question with "raw" selected, then again with
 * "langchain" selected (or swap the vector store, or the LLM), and this
 * log keeps every attempt visible at once so you can compare answers,
 * sources, and latency side by side instead of losing the previous
 * answer the moment you ask a new one.
 * ============================================================================
 */

import type { LogEntry } from "@/lib/types";

export default function ComparisonLog({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-xs opacity-50">No questions asked yet.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      {[...entries].reverse().map((entry) => (
        <div key={entry.id} className="rounded-lg border border-black/10 dark:border-white/15 p-4 text-sm">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs opacity-60">
            <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">{entry.pipeline}</span>
            {entry.pipeline === "raw" && (
              <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">{entry.vectorStore}</span>
            )}
            <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">
              {entry.llmProvider}/{entry.llmModel}
            </span>
            <span>{entry.result.latency_ms} ms</span>
          </div>

          <p className="mb-2 font-medium">{entry.question}</p>

          {entry.result.error && (
            <p className="text-red-600 dark:text-red-400">{entry.result.error}</p>
          )}
          {entry.result.answer && <p className="whitespace-pre-wrap">{entry.result.answer}</p>}

          {entry.result.sources.length > 0 && (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs opacity-60">
                {entry.result.sources.length} source{entry.result.sources.length > 1 ? "s" : ""}
              </summary>
              <ul className="mt-2 flex flex-col gap-2">
                {entry.result.sources.map((s, i) => (
                  <li key={i} className="rounded border border-black/10 dark:border-white/15 p-2 text-xs">
                    <div className="mb-1 flex items-center justify-between opacity-60">
                      <span>{s.source}</span>
                      <span>distance {s.distance.toFixed(3)}</span>
                    </div>
                    {s.snippet}…
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}
