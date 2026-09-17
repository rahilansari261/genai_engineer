/**
 * ============================================================================
 *  RUN LOG — every question you've asked, with its full trace, kept visible
 * ============================================================================
 * Same idea as Project 5's comparison log: ask the same question with a
 * different engine and this keeps every attempt on screen at once, so you
 * can compare not just the final answers but the whole reasoning path
 * that got each engine there.
 * ============================================================================
 */

import TraceView from "@/components/TraceView";
import type { LogEntry } from "@/lib/types";

const ENGINE_LABEL: Record<LogEntry["engine"], string> = {
  react: "react",
  functions: "functions",
  responses: "responses",
};

export default function RunLog({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-xs opacity-50">No questions asked yet.</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      {[...entries].reverse().map((entry) => (
        <div key={entry.id} className="rounded-lg border border-black/10 dark:border-white/15 p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs opacity-60">
            <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">{ENGINE_LABEL[entry.engine]}</span>
            {entry.provider && (
              <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">{entry.provider}</span>
            )}
            <span className="rounded bg-black/5 px-2 py-0.5 dark:bg-white/10">{entry.model}</span>
            <span>max {entry.maxSteps} steps</span>
            <span>{entry.result.trace.filter((s) => s.type === "action").length} tool call(s)</span>
          </div>

          <p className="mb-3 text-sm font-medium">{entry.question}</p>

          <TraceView trace={entry.result.trace} />
        </div>
      ))}
    </div>
  );
}
