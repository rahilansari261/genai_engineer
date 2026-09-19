/**
 * ============================================================================
 *  WAIT FOR BACKEND — wake a sleeping free-hosted server, and know when it's up
 * ============================================================================
 * Why this exists: free hosting (e.g. Render's free tier) puts a server to
 * sleep after about 15 minutes with no visitors. The next request wakes it
 * up, but that takes around a minute — and during that minute requests can
 * hang, time out, or come back as errors like 502/503. If the page just fires
 * its normal requests into that, it looks broken for a minute.
 *
 * What this does: it knocks on the backend's cheap `GET /health` door (see
 * backend/main.py — it does no work, it only answers `{"status":"ok"}`). If
 * there's no good answer, it waits a few seconds and knocks again, until the
 * backend says OK or we give up. The very first knock is the one that wakes
 * the sleeping server; the rest just wait for it to finish starting.
 *
 * Two details that matter:
 *   - Every knock has its OWN timeout. A request to a half-awake server can
 *     hang forever, and without a timeout that one hanging request would
 *     freeze the whole loop.
 *   - It returns true/false instead of throwing, so the page can simply show
 *     "ready" or "couldn't reach the backend" without any try/catch of its own.
 *
 * On your own laptop the backend answers in a few milliseconds, so this
 * returns true on the first knock and you never notice it.
 * ============================================================================
 */

export interface WaitForBackendOptions {
  attemptTimeoutMs?: number; // how long ONE knock may take before we abandon it
  retryDelayMs?: number; // pause between knocks
  giveUpAfterMs?: number; // stop trying after this long in total
  isCancelled?: () => boolean; // lets the page stop the loop (e.g. it was closed)
}

export async function waitForBackend(
  baseUrl: string,
  options: WaitForBackendOptions = {}
): Promise<boolean> {
  const {
    attemptTimeoutMs = 10_000,
    retryDelayMs = 3_000,
    giveUpAfterMs = 120_000, // a cold start is ~1 minute, so 2 minutes leaves plenty of margin
    isCancelled = () => false,
  } = options;

  const deadline = Date.now() + giveUpAfterMs;

  while (!isCancelled() && Date.now() < deadline) {
    try {
      const response = await fetch(`${baseUrl}/health`, {
        signal: AbortSignal.timeout(attemptTimeoutMs),
      });
      if (response.ok) return true;
      // Not OK (e.g. the host's proxy answering 503 while the server boots) — retry below.
    } catch {
      // Network error or our own timeout — the server isn't up yet. Retry below.
    }
    await new Promise((resolve) => setTimeout(resolve, retryDelayMs));
  }

  return false;
}
