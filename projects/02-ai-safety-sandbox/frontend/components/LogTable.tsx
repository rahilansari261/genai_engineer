/**
 * ============================================================================
 *  LOG TABLE — the "adversarial testing" record
 * ============================================================================
 * This is what turns "I tried a few attacks and it seemed fine" (a vague
 * impression) into "here are 6 attacks x 3 guard modes = 18 attempts, and
 * here's exactly which ones got through" (evidence). That's the actual
 * point of the "Conducting adversarial testing" roadmap node — a
 * repeatable log you can compare across changes to your guardrails, not a
 * one-off vibe check.
 * ============================================================================
 */

import type { LogEntry } from "@/lib/types";

function outcomeLabel(entry: LogEntry): { text: string; className: string } {
  if (entry.result.error) {
    return { text: `Error: ${entry.result.error}`, className: "text-amber-600 dark:text-amber-400" };
  }
  if (entry.result.blocked) {
    return {
      text: `Blocked (${entry.result.blocked_layer})`,
      className: "text-green-600 dark:text-green-400",
    };
  }
  return { text: "Got through", className: "text-red-600 dark:text-red-400" };
}

export default function LogTable({ entries }: { entries: LogEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-xs opacity-50">No attempts yet — send a message or fire an attack above.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-black/10 dark:border-white/15 opacity-60">
            <th className="py-2 pr-4 font-medium">Attempt</th>
            <th className="py-2 pr-4 font-medium">Guard mode</th>
            <th className="py-2 pr-4 font-medium">Moderation</th>
            <th className="py-2 pr-4 font-medium">Outcome</th>
          </tr>
        </thead>
        <tbody>
          {/* Newest attempt on top, so the log reads like a running history */}
          {[...entries].reverse().map((entry) => {
            const outcome = outcomeLabel(entry);
            return (
              <tr key={entry.id} className="border-b border-black/5 dark:border-white/5">
                <td className="py-2 pr-4">
                  <div className="font-medium">{entry.attackLabel ?? "(custom message)"}</div>
                  <div className="opacity-50">{entry.messagePreview}</div>
                </td>
                <td className="py-2 pr-4 capitalize">{entry.guardMode}</td>
                <td className="py-2 pr-4">{entry.moderationOn ? "on" : "off"}</td>
                <td className={`py-2 pr-4 font-medium ${outcome.className}`}>{outcome.text}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
