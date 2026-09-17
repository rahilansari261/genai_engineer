/**
 * ============================================================================
 *  MESSAGE BUBBLE — one turn of the conversation, with everything visible
 * ============================================================================
 * A user turn shows the text and, if one was attached, the image. An
 * assistant turn shows the final answer OR a "blocked" notice (Project
 * 2's safety layer catching something), a collapsible reasoning trace
 * (Project 6), any images the agent generated (Project 7), and what this
 * one turn cost (Project 1) — every earlier project's contribution,
 * visible in one place instead of four separate tabs.
 * ============================================================================
 */

import TraceView from "@/components/TraceView";
import type { DisplayMessage } from "@/lib/types";

export default function MessageBubble({ message }: { message: DisplayMessage }) {
  const isUser = message.role === "user";
  const result = message.result;

  return (
    <div className={`flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 text-sm ${
          isUser ? "bg-black text-white dark:bg-white dark:text-black" : "border border-black/10 dark:border-white/15"
        }`}
      >
        {isUser ? (
          <>
            {message.imagePreviewUrl && (
              // eslint-disable-next-line @next/next/no-img-element -- a locally picked file has no URL to optimize
              <img src={message.imagePreviewUrl} alt="Attached" className="mb-2 max-h-48 rounded" />
            )}
            {message.content}
          </>
        ) : (
          <>
            {result?.error && <p className="text-amber-600 dark:text-amber-400">Error: {result.error}</p>}
            {result?.blocked && (
              <div>
                <p className="font-medium text-red-600 dark:text-red-400">Blocked at: {result.blocked_layer}</p>
                {result.blocked_categories.length > 0 && (
                  <p className="mt-1 text-xs opacity-70">Flagged categories: {result.blocked_categories.join(", ")}</p>
                )}
              </div>
            )}
            {!result?.error && !result?.blocked && <p className="whitespace-pre-wrap">{result?.final_answer}</p>}
            {result && !result.moderation_available && (
              <p className="mt-2 text-xs opacity-50">
                (Moderation unavailable — no OPENAI_API_KEY configured, only the guardrail system prompt was tested.)
              </p>
            )}
          </>
        )}
      </div>

      {!isUser && result?.attachments && result.attachments.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {result.attachments.map((b64, i) => (
            // eslint-disable-next-line @next/next/no-img-element -- a base64 data URL can't be optimized either
            <img key={i} src={`data:image/png;base64,${b64}`} alt="Generated" className="max-h-64 rounded-lg border border-black/10 dark:border-white/15" />
          ))}
        </div>
      )}

      {!isUser && result && result.trace.length > 0 && (
        <details className="w-full max-w-[85%]">
          <summary className="cursor-pointer text-xs opacity-60">
            {result.trace.filter((s) => s.type === "action").length} tool call(s) — show reasoning
          </summary>
          <div className="mt-2">
            <TraceView trace={result.trace} />
          </div>
        </details>
      )}

      {!isUser && result && result.cost_usd > 0 && (
        <span className="text-xs opacity-40">${result.cost_usd.toFixed(6)}</span>
      )}
    </div>
  );
}
