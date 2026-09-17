/**
 * Reused from Project 6, unchanged — the agent's reasoning made visible
 * step by step. See Project 6's README for why this exists at all.
 */

import type { TraceStep } from "@/lib/types";

const STEP_STYLE: Record<TraceStep["type"], string> = {
  thought: "opacity-60 italic",
  action: "text-blue-600 dark:text-blue-400",
  observation: "text-green-700 dark:text-green-400 font-mono text-xs whitespace-pre-wrap",
  final: "font-medium",
  error: "text-red-600 dark:text-red-400",
};

const STEP_LABEL: Record<TraceStep["type"], string> = {
  thought: "Thought",
  action: "Action",
  observation: "Observation",
  final: "Final Answer",
  error: "Error",
};

export default function TraceView({ trace }: { trace: TraceStep[] }) {
  if (trace.length === 0) return null;

  return (
    <ol className="flex flex-col gap-2 text-sm">
      {trace.map((step, i) => (
        <li key={i} className="rounded-lg border border-black/10 dark:border-white/15 p-3">
          <div className="mb-1 flex items-center gap-2 text-xs font-medium opacity-70">
            <span>
              {i + 1}. {STEP_LABEL[step.type]}
            </span>
            {step.tool && <span className="rounded bg-black/5 px-1.5 py-0.5 dark:bg-white/10">{step.tool}</span>}
          </div>
          <div className={STEP_STYLE[step.type]}>{step.content}</div>
        </li>
      ))}
    </ol>
  );
}
