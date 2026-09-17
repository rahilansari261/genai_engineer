/**
 * ============================================================================
 *  ENGINE PICKER — three ways of building the same agent
 * ============================================================================
 * See backend/main.py and the three agent_*.py files for what each engine
 * actually does differently. "react" is the only one that works with
 * Ollama (free, local) — "functions" and "responses" both require OpenAI,
 * since they use OpenAI-specific APIs, not a provider-agnostic technique.
 * ============================================================================
 */

import type { Engine, ReactProvider } from "@/lib/types";

const ENGINE_LABEL: Record<Engine, string> = {
  react: "Manual: ReAct (text-based)",
  functions: "Manual: OpenAI function calling",
  responses: "OpenAI Responses API",
};

export default function EnginePicker({
  engine,
  provider,
  model,
  onEngineChange,
  onProviderChange,
  onModelChange,
}: {
  engine: Engine;
  provider: ReactProvider;
  model: string;
  onEngineChange: (e: Engine) => void;
  onProviderChange: (p: ReactProvider) => void;
  onModelChange: (m: string) => void;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className="opacity-70">Engine</span>
        {(["react", "functions", "responses"] as Engine[]).map((e) => (
          <button
            key={e}
            onClick={() => onEngineChange(e)}
            className={`rounded-lg border px-3 py-1.5 text-xs ${
              engine === e ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
            }`}
          >
            {ENGINE_LABEL[e]}
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {engine === "react" && (
          <>
            <span className="opacity-70">Provider</span>
            {(["ollama", "openai"] as ReactProvider[]).map((p) => (
              <button
                key={p}
                onClick={() => onProviderChange(p)}
                className={`rounded-lg border px-3 py-1.5 text-xs ${
                  provider === p ? "border-black bg-black text-white dark:border-white dark:bg-white dark:text-black" : "border-black/10 dark:border-white/15"
                }`}
              >
                {p}
              </button>
            ))}
          </>
        )}
        {engine !== "react" && <span className="text-xs opacity-50">Requires OPENAI_API_KEY</span>}
        <input
          value={model}
          onChange={(e) => onModelChange(e.target.value)}
          className="w-48 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
        />
      </div>
    </div>
  );
}
