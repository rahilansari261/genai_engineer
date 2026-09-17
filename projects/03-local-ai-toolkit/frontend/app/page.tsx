/**
 * ============================================================================
 *  HOME PAGE — three engines, side by side
 * ============================================================================
 * This page doesn't hold much logic of its own — it just lays out three
 * independent panels, one per "way of running an open-source model":
 *
 *   1. OllamaPanel          -> your own machine, via our backend
 *   2. HuggingFacePanel     -> Hugging Face's servers, via our backend
 *   3. BrowserClassifier    -> this browser tab, no backend involved
 *
 * Each panel manages its own state and makes its own calls — unlike
 * Project 1, where one "Run" button fired all three at once, here you run
 * each engine independently, since they're not really comparable side by
 * side (different tasks, different latencies, one doesn't even involve
 * the network to our backend at all).
 * ============================================================================
 */

import BrowserClassifier from "@/components/BrowserClassifier";
import HuggingFacePanel from "@/components/HuggingFacePanel";
import OllamaPanel from "@/components/OllamaPanel";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">Local AI Toolkit</h1>
        <p className="mt-1 text-sm opacity-70">
          Three ways to run open-source AI: your own machine, Hugging Face&apos;s servers, and right here in this tab.
        </p>
      </header>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <OllamaPanel />
        <HuggingFacePanel />
        <BrowserClassifier />
      </section>
    </main>
  );
}
