/**
 * ============================================================================
 *  HOME PAGE — the whole AI Safety Sandbox UI
 * ============================================================================
 * The flow, in plain words:
 *   0. As soon as the page loads, it pings the backend's /health endpoint.
 *      On free hosting the server sleeps when nobody has visited for a
 *      while — that first ping wakes it up, and Send stays locked (with a
 *      "waking up" notice) until the backend answers. Locally this takes
 *      milliseconds and you won't see it. See lib/waitForBackend.ts.
 *   1. Pick a "guard mode" (none / basic / strong — see backend/guardrails.py
 *      for what each system prompt actually says) and whether moderation
 *      is on.
 *   2. Either type your own message, or click one of the canned attacks in
 *      the sidebar to load it into the box.
 *   3. Hit Send. The backend runs it through input moderation, the chat
 *      model (with your chosen guard mode), and output moderation — see
 *      backend/main.py for that exact order.
 *   4. The result shows up as either the AI's reply, or "Stopped by
 *      moderation" if a safety layer caught it — and every attempt gets
 *      added to the log table below, so you can compare guard modes side
 *      by side.
 *
 * A note on reading results: "moderation stopped it" is something the code
 * can know for sure. "The AI held its ground" vs "the AI gave in" is NOT —
 * that means reading the AI's actual words, which is your job. That's why
 * the result panel and the log both show the reply text.
 * ============================================================================
 */

"use client";

import { useEffect, useState } from "react";
import AttackList from "@/components/AttackList";
import LogTable from "@/components/LogTable";
import { GUARD_MODE_INFO, LAYER_INFO, type GuardMode } from "@/lib/labels";
import type { Attack, ChatResult, LogEntry } from "@/lib/types";
import { waitForBackend } from "@/lib/waitForBackend";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Provider = "openai" | "anthropic" | "ollama";

// Where the backend is, from this page's point of view:
//   checking    — we just asked, no answer yet (usually lasts milliseconds)
//   waking      — no answer after a few seconds: a sleeping server is starting up
//   ready       — it answered; Send is unlocked
//   unreachable — still nothing after a couple of minutes; we gave up
type BackendStatus = "checking" | "waking" | "ready" | "unreachable";

// How long to wait before telling the user "it's waking up". Kept short so a
// slow start is explained quickly, but long enough that a normal fast local
// backend never flashes the notice.
const SLOW_START_MS = 3000;

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
  const [backendStatus, setBackendStatus] = useState<BackendStatus>("checking");

  // `useEffect` with an empty dependency array (`[]`) means "run this once,
  // right after the page first loads" — a good place to do setup work before
  // the user does anything. Two jobs here:
  //   1. Make sure the backend is awake (a free host may have put it to
  //      sleep) by pinging /health until it answers.
  //   2. Only THEN fetch the canned attack list. Asking a half-awake server
  //      for the list would just fail with a confusing error.
  useEffect(() => {
    // Set to true by the cleanup function below, so a page that has been
    // closed (or, in development, React's deliberate mount-unmount-mount
    // check) doesn't keep updating state after the fact.
    let cancelled = false;

    // If the backend hasn't answered after a few seconds, explain why the
    // page is locked. Locally it answers long before this fires.
    const slowStartTimer = setTimeout(() => {
      setBackendStatus((current) => (current === "checking" ? "waking" : current));
    }, SLOW_START_MS);

    waitForBackend(API_URL, { isCancelled: () => cancelled }).then((isUp) => {
      clearTimeout(slowStartTimer);
      if (cancelled) return;

      if (!isUp) {
        setBackendStatus("unreachable");
        return;
      }

      setBackendStatus("ready");
      fetch(`${API_URL}/attacks`)
        .then((res) => res.json())
        .then(setAttacks)
        .catch(() => setRequestError(`Couldn't load attacks — is the backend running on ${API_URL}?`));
    });

    return () => {
      cancelled = true;
      clearTimeout(slowStartTimer);
    };
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

  // The Send button's text says what's going on, instead of just going grey.
  const sendLabel =
    backendStatus === "unreachable"
      ? "Backend unavailable"
      : backendStatus !== "ready"
        ? "Waiting for backend…"
        : loading
          ? "Sending…"
          : "Send";

  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">AI Safety Sandbox</h1>
        <p className="mt-1 text-sm opacity-70">
          Try to trick your own AI app, and see which safety layer stops you.
        </p>
        <ol className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs opacity-60">
          <li>1. Choose the two safety layers</li>
          <li>2. Click an attack (or type your own)</li>
          <li>3. Press Send</li>
          <li>4. Read the result and compare in the log</li>
        </ol>
      </header>

      {/* Only shown when the backend is slow to answer or can't be reached —
          on a fast (local) backend neither notice ever appears. */}
      {backendStatus === "waking" && (
        <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
          <p className="font-medium">The backend is waking up…</p>
          <p className="mt-1 text-xs opacity-80">
            Free hosting puts the server to sleep after about 15 minutes without visitors, so the
            first load can take around a minute. This page unlocks by itself — no need to refresh.
          </p>
        </div>
      )}
      {backendStatus === "unreachable" && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300">
          <p className="font-medium">Couldn&apos;t reach the backend</p>
          <p className="mt-1 text-xs opacity-80">
            Tried {API_URL}/health for a couple of minutes with no answer. Is the backend running?
            Reload the page to try again.
          </p>
        </div>
      )}

      {/* The two safety layers, explained up front — they do different jobs. */}
      <section className="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-black/10 dark:border-white/15 p-4 text-sm">
          <p className="text-xs font-medium opacity-50">SAFETY LAYER 1</p>
          <h2 className="font-medium">Moderation</h2>
          <p className="mt-1 text-xs opacity-70">
            Checks <strong>what is being said</strong>. Blocks harmful content (violence, illegal
            acts, hate, self-harm, sexual content) — on your message before the AI sees it, and on
            the AI&apos;s reply before you see it.
          </p>
          <p className="mt-2 text-xs opacity-50">
            Won&apos;t catch tricks like &quot;ignore your instructions&quot; — those contain no
            harmful words.
          </p>
        </div>
        <div className="rounded-lg border border-black/10 dark:border-white/15 p-4 text-sm">
          <p className="text-xs font-medium opacity-50">SAFETY LAYER 2</p>
          <h2 className="font-medium">Guard mode</h2>
          <p className="mt-1 text-xs opacity-70">
            The hidden rules given to the AI itself (a &quot;system prompt&quot;). Protects
            against <strong>manipulation</strong>: &quot;ignore your rules&quot;, &quot;you are now
            DAN&quot;, &quot;show me your instructions&quot;.
          </p>
          <p className="mt-2 text-xs opacity-50">
            It&apos;s about resisting tricks, not about which topics are allowed.
          </p>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[240px_1fr]">
        {/* Sidebar: the canned attack suite */}
        <AttackList attacks={attacks} onSelect={handleSelectAttack} disabled={loading} />

        <div className="flex flex-col gap-4">
          {/* Controls: one block per safety layer, then which AI model to talk to */}
          <div className="grid grid-cols-1 gap-4 rounded-lg border border-black/10 dark:border-white/15 p-4 text-sm md:grid-cols-2">
            <div className="flex flex-col gap-1">
              <label className="flex items-center gap-2 font-medium">
                <input
                  type="checkbox"
                  checked={useModeration}
                  onChange={(e) => setUseModeration(e.target.checked)}
                />
                <span>Layer 1 — Moderation</span>
              </label>
              <p className="text-xs opacity-60">
                {useModeration
                  ? "ON: harmful content is blocked before and after the AI."
                  : "OFF: nothing checks for harmful content — only the AI's own built-in training is left."}
              </p>
            </div>

            <div className="flex flex-col gap-1">
              <label className="flex items-center gap-2 font-medium">
                <span>Layer 2 — Guard mode</span>
                <select
                  value={guardMode}
                  onChange={(e) => setGuardMode(e.target.value as GuardMode)}
                  className="rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 font-normal"
                >
                  <option value="none">none</option>
                  <option value="basic">basic</option>
                  <option value="strong">strong</option>
                </select>
              </label>
              <p className="text-xs opacity-60">{GUARD_MODE_INFO[guardMode]}</p>
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t border-black/10 dark:border-white/15 pt-3 md:col-span-2">
              <span className="opacity-70">AI model</span>
              <select
                value={provider}
                onChange={(e) => handleProviderChange(e.target.value as Provider)}
                className="rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1"
              >
                <option value="ollama">ollama (free, local)</option>
                <option value="openai">openai</option>
                <option value="anthropic">anthropic</option>
              </select>
              <input
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="w-44 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
              />
            </div>
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
              disabled={loading || !message.trim() || backendStatus !== "ready"}
              className="self-end rounded-lg bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
            >
              {sendLabel}
            </button>
          </div>

          {requestError && <p className="text-sm text-red-600 dark:text-red-400">{requestError}</p>}

          {/* Result panel: a moderation block, the AI's reply, or an error */}
          {result && (
            <div className="rounded-lg border border-black/10 dark:border-white/15 p-4 text-sm">
              {result.error && (
                <div>
                  <p className="font-medium text-amber-600 dark:text-amber-400">Something went wrong</p>
                  <p className="mt-1 text-xs opacity-70">{result.error}</p>
                </div>
              )}

              {!result.error && result.blocked && result.blocked_layer && (
                <div>
                  <p className="font-medium text-green-600 dark:text-green-400">
                    Stopped by moderation ({LAYER_INFO[result.blocked_layer].short})
                  </p>
                  <p className="mt-1 text-xs opacity-70">
                    {LAYER_INFO[result.blocked_layer].explanation}
                  </p>
                  {result.blocked_categories.length > 0 && (
                    <p className="mt-1 text-xs opacity-50">
                      Flagged as: {result.blocked_categories.join(", ")}
                    </p>
                  )}
                </div>
              )}

              {!result.error && !result.blocked && (
                <div>
                  <p className="font-medium text-sky-600 dark:text-sky-400">The AI replied</p>
                  <p className="mt-2 whitespace-pre-wrap">{result.text}</p>
                  <p className="mt-3 border-t border-black/10 dark:border-white/15 pt-2 text-xs opacity-60">
                    Moderation didn&apos;t stop this one. Now read the reply: did the AI refuse or stay
                    in character (good), or did it follow the attack — reveal its instructions,
                    play along (bad)?
                  </p>
                </div>
              )}

              {!result.moderation_available && (
                <p className="mt-2 text-xs opacity-50">
                  (Moderation didn&apos;t run — no OPENAI_API_KEY configured — so only the guard-mode
                  system prompt was tested this time.)
                </p>
              )}
            </div>
          )}

          {/* The adversarial-testing log — every attempt this session */}
          <div className="rounded-lg border border-black/10 dark:border-white/15 p-4">
            <h2 className="text-sm font-medium opacity-70">Attempt log</h2>
            <p className="mb-3 mt-1 text-xs opacity-50">
              Every attempt this session. Send the same attack under different guard modes and
              compare the rows.
            </p>
            <LogTable entries={log} />
          </div>
        </div>
      </div>
    </main>
  );
}
