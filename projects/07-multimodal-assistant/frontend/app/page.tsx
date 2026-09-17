/**
 * ============================================================================
 *  HOME PAGE — one assistant, four modalities
 * ============================================================================
 * Three tabs, each exercising a different modality pair from
 * backend/main.py: Vision (image + question -> text), Image Generation
 * (text -> image), and Voice (voice -> text -> reply -> voice, chaining
 * three modalities in one loop). See each panel component for the
 * specific engines it compares.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import ImageGenPanel from "@/components/ImageGenPanel";
import VisionPanel from "@/components/VisionPanel";
import VoicePanel from "@/components/VoicePanel";

type Tab = "vision" | "image-gen" | "voice";

const TAB_LABEL: Record<Tab, string> = {
  vision: "Vision",
  "image-gen": "Image Generation",
  voice: "Voice Assistant",
};

export default function Home() {
  const [tab, setTab] = useState<Tab>("vision");

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">Multimodal Assistant</h1>
        <p className="mt-1 text-sm opacity-70">
          Understand images, generate them, and hold a spoken conversation — one assistant, four modalities.
        </p>
      </header>

      <nav className="flex gap-2 border-b border-black/10 dark:border-white/15">
        {(["vision", "image-gen", "voice"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm ${
              tab === t ? "border-b-2 border-black font-medium dark:border-white" : "opacity-60"
            }`}
          >
            {TAB_LABEL[t]}
          </button>
        ))}
      </nav>

      {tab === "vision" && <VisionPanel />}
      {tab === "image-gen" && <ImageGenPanel />}
      {tab === "voice" && <VoicePanel />}
    </main>
  );
}
