/**
 * ============================================================================
 *  LOG TABLE — the "adversarial testing" record
 * ============================================================================
 * This is what turns "I tried a few attacks and it seemed fine" (a vague
 * impression) into "here are 6 attacks x 3 guard modes = 18 attempts, and
 * here's exactly what happened to each one" (evidence). That's the actual
 * point of the "Conducting adversarial testing" roadmap node — a
 * repeatable log you can compare across changes to your guardrails, not a
 * one-off vibe check.
 *
 * Each attempt ends in one of three ways:
 *   - Blocked by moderation (green) — a safety layer stopped it. The code
 *     knows this for certain.
 *   - The AI replied (blue) — moderation did NOT stop it, so it reached the
 *     model. Whether the model refused or gave in is something only you can
 *     tell by reading its words, so we show a preview of the reply right
 *     here instead of guessing. (An older version of this table labelled
 *     every such row "Got through" in red — which was wrong whenever the
 *     model had politely refused.)
 *   - Error (amber) — something failed, e.g. Ollama isn't running.
 * ============================================================================
 */

import { LAYER_INFO } from "@/lib/labels";
import type { LogEntry } from "@/lib/types";

const REPLY_PREVIEW_LENGTH = 90;

function outcomeLabel(entry: LogEntry): { text: string; detail: string | null; className: string } {
  const { result } = entry;

  if (result.error) {
    return { text: "Error", detail: result.error, className: "text-amber-600 dark:text-amber-400" };
  }

  if (result.blocked && result.blocked_layer) {
    return {
      text: "Blocked by moderation",
      detail: LAYER_INFO[result.blocked_layer].short,
      className: "text-green-600 dark:text-green-400",
    };
  }

  // Not blocked: show the start of the AI's reply so you can judge it.
  const reply = (result.text ?? "").replace(/\s+/g, " ").trim();
  const preview = reply.length > REPLY_PREVIEW_LENGTH ? `${reply.slice(0, REPLY_PREVIEW_LENGTH)}…` : reply;
  return {
    text: "The AI replied",
    detail: preview ? `"${preview}"` : null,
    className: "text-sky-600 dark:text-sky-400",
  };
}

export default function LogTable({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-xs opacity-50">No attempts yet — send a message or fire an attack above.</p>;
  }

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-black/10 dark:border-white/15 opacity-60">
              <th className="py-2 pr-4 font-medium">Attempt</th>
              <th className="py-2 pr-4 font-medium">Guard mode</th>
              <th className="py-2 pr-4 font-medium">Moderation</th>
              <th className="py-2 pr-4 font-medium">What happened</th>
            </tr>
          </thead>
          <tbody>
            {/* Newest attempt on top, so the log reads like a running history */}
            {[...entries].reverse().map((entry) => {
              const outcome = outcomeLabel(entry);
              return (
                <tr key={entry.id} className="border-b border-black/5 dark:border-white/5 align-top">
                  <td className="py-2 pr-4">
                    <div className="font-medium">{entry.attackLabel ?? "(custom message)"}</div>
                    <div className="opacity-50">{entry.messagePreview}</div>
                  </td>
                  <td className="py-2 pr-4 capitalize">{entry.guardMode}</td>
                  <td className="py-2 pr-4">{entry.moderationOn ? "on" : "off"}</td>
                  <td className="py-2 pr-4">
                    <div className={`font-medium ${outcome.className}`}>{outcome.text}</div>
                    {outcome.detail && <div className="opacity-60">{outcome.detail}</div>}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-xs opacity-50">
        <span className="text-green-600 dark:text-green-400">Green</span> = moderation stopped it.{" "}
        <span className="text-sky-600 dark:text-sky-400">Blue</span> = it reached the AI and got a
        reply — read the reply to see whether the AI held its ground or gave in. The log can&apos;t
        judge that for you.
      </p>
    </div>
  );
}
