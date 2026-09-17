/**
 * ============================================================================
 *  HOME PAGE — the whole AI Safety Sandbox UI
 * ============================================================================
 * The flow, in plain words:
 *   1. Pick a "guard mode" (none / basic / strong — see backend/guardrails.py
 *      for what each system prompt actually says) and whether moderation
 *      is on.
 *   2. Either type your own message, or click one of the canned attacks in
 *      the sidebar to load it into the box.
 *   3. Hit Send. The backend runs it through input moderation, the chat
 *      model (with your chosen guard mode), and output moderation — see
 *      backend/main.py for that exact order.
 *   4. The result shows up as either the AI's reply, or "BLOCKED at <layer>"
 *      if a safety layer caught it — and every attempt gets added to the
 *      log table below, so you can compare guard modes side by side.
 * ============================================================================
 */

"use client";

import { useEffect, useState } from "react";
import AttackList from "@/components/AttackList";
import LogTable from "@/components/LogTable";
import type { Attack, ChatResult, LogEntry } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Provider = "openai" | "anthropic" | "ollama";
type GuardMode = "none" | "basic" | "strong";

// Suggested default model per provider — swapped in automatically when you
// change the provider dropdown, but you can still type over it by hand.
const DEFAULT_MODEL: Record<Provider, string> = {
  openai: "gpt-4o-mini",
  anthropic: "claude-3-5-haiku-20241022",
  ollama: "llama3.2",
};

export default function Home() {
  const [message, setMessage] = useState("");
  const [provider, setProvider] = useState<Provider>("ollama");
  const [model, setModel] = useState(DEFAULT_MODEL.ollama);
  const [guardMode, setGuardMode] = useState<GuardMode>("strong");
  const [useModeration, setUseModeration] = useState(true);

  const [attacks, setAttacks] = useState<Attack[]>([]);
  const [result, setResult] = useState<ChatResult | null>(null);
  const [log, setLog] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  // `useEffect` with an empty dependency array (`[]`) means "run this once,
  // right after the page first loads" — a good place to fetch data the
  // page needs before the user does anything. Here: the canned attack list.
  useEffect(() => {
    fetch(`${API_URL}/attacks`)
      .then((res) => res.json())
      .then(setAttacks)
      .catch(() => setRequestError(`Couldn't load attacks — is the backend running on ${API_URL}?`));
  }, []);

  function handleProviderChange(next: Provider) {
    setProvider(next);
    setModel(DEFAULT_MODEL[next]); // reset to that provider's sensible default
  }

  function handleSelectAttack(attack: Attack) {
    setMessage(attack.prompt);
  }

  async function sendMessage() {
    if (!message.trim()) return;

    setLoading(true);
    setRequestError(null);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          provider,
          model,
          guard_mode: guardMode,
          use_moderation: useModeration,
        }),
      });

      if (!response.ok) throw new Error(`Backend returned ${response.status}`);

      const data: ChatResult = await response.json();
      setResult(data);

      // If the message currently in the box is EXACTLY one of the canned
      // attack prompts, label the log entry with that attack's name —
      // otherwise it was something you typed yourself.
      const matchedAttack = attacks.find((a) => a.prompt === message);

      const entry: LogEntry = {
        id: `${Date.now()}`,
        timestamp: Date.now(),
        messagePreview: message.length > 60 ? `${message.slice(0, 60)}…` : message,
        attackLabel: matchedAttack?.label ?? null,
        guardMode,
        moderationOn: useModeration,
        result: data,
      };
      setLog((prev) => [...prev, entry]);
    } catch (err) {
      setRequestError(
        err instanceof Error
          ? `${err.message} — is the backend running on ${API_URL}?`
          : "Something went wrong"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">AI Safety Sandbox</h1>
        <p className="mt-1 text-sm opacity-70">
          Try to break your own guardrails, and watch moderation + defenses catch (or miss) it.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[240px_1fr]">
        {/* Sidebar: the canned attack suite */}
        <AttackList attacks={attacks} onSelect={handleSelectAttack} disabled={loading} />

        <div className="flex flex-col gap-4">
          {/* Controls: guard mode, moderation toggle, provider/model */}
          <div className="flex flex-wrap items-center gap-4 rounded-lg border border-black/10 dark:border-white/15 p-3 text-sm">
            <label className="flex items-center gap-2">
              <span className="opacity-70">Guard mode</span>
              <select
                value={guardMode}
                onChange={(e) => setGuardMode(e.target.value as GuardMode)}
                className="rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1"
              >
                <option value="none">none (no system prompt)</option>
                <option value="basic">basic</option>
                <option value="strong">strong</option>
              </select>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={useModeration}
                onChange={(e) => setUseModeration(e.target.checked)}
              />
              <span>Moderation API (input + output)</span>
            </label>

            <label className="flex items-center gap-2">
              <span className="opacity-70">Provider</span>
              <select
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value as Provider)}
                className="rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1"
              >
                <option value="ollama">ollama (free, local)</option>
                <option value="openai">openai</option>
                <option value="anthropic">anthropic</option>
              </select>
            </label>

            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-44 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
            />
          </div>

          {/* Message box + send */}
          <div className="flex flex-col gap-2">
            <textarea
              className="w-full resize-y rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-4 py-3 text-sm"
              rows={4}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Type a message, or pick an attack from the sidebar…"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !message.trim()}
              className="self-end rounded-lg bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
            >
              {loading ? "Sending…" : "Send"}
            </button>
          </div>

          {requestError && <p className="text-sm text-red-600 dark:text-red-400">{requestError}</p>}

          {/* Result panel: either the reply, a BLOCKED notice, or an error */}
          {result && (
            <div className="rounded-lg border border-black/10 dark:border-white/15 p-4 text-sm">
              {result.error && (
                <p className="text-amber-600 dark:text-amber-400">Error: {result.error}</p>
              )}
              {!result.error && result.blocked && (
                <div>
                  <p className="font-medium text-green-600 dark:text-green-400">
                    Blocked at: {result.blocked_layer}
                  </p>
                  {result.blocked_categories.length > 0 && (
                    <p className="mt-1 text-xs opacity-70">
                      Flagged categories: {result.blocked_categories.join(", ")}
                    </p>
                  )}
                </div>
              )}
              {!result.error && !result.blocked && (
                <p className="whitespace-pre-wrap">{result.text}</p>
              )}
              {!result.moderation_available && (
                <p className="mt-2 text-xs opacity-50">
                  (Moderation unavailable — no OPENAI_API_KEY configured, so only the guard-mode
                  system prompt was tested this time.)
                </p>
              )}
            </div>
          )}

          {/* The adversarial-testing log — every attempt this session */}
          <div className="rounded-lg border border-black/10 dark:border-white/15 p-4">
            <h2 className="mb-3 text-sm font-medium opacity-70">Attempt log</h2>
            <LogTable entries={log} />
          </div>
        </div>
      </div>
    </main>
  );
}
