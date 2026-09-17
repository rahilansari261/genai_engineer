/**
 * ============================================================================
 *  SETTINGS BAR — safety toggle, provider choices, running cost
 * ============================================================================
 * The safety toggle is deliberately the most prominent control here — see
 * backend/guardrails.py and agent.py's file comment for what turning it
 * off actually removes (the defensive system prompt AND moderation), the
 * same before/after comparison Project 2 was built around. The running
 * cost total is Project 1's contribution: a live, visible number instead
 * of an abstract idea that AI calls cost money.
 * ============================================================================
 */

import type { ChatProvider, ImageGenProvider, VisionProvider } from "@/lib/types";

export default function SettingsBar({
  safety,
  onSafetyChange,
  chatProvider,
  onChatProviderChange,
  visionProvider,
  onVisionProviderChange,
  imageGenProvider,
  onImageGenProviderChange,
  totalCost,
}: {
  safety: boolean;
  onSafetyChange: (v: boolean) => void;
  chatProvider: ChatProvider;
  onChatProviderChange: (v: ChatProvider) => void;
  visionProvider: VisionProvider;
  onVisionProviderChange: (v: VisionProvider) => void;
  imageGenProvider: ImageGenProvider;
  onImageGenProviderChange: (v: ImageGenProvider) => void;
  totalCost: number;
}) {
  return (
    <div className="flex flex-wrap items-center gap-4 rounded-lg border border-black/10 dark:border-white/15 p-3 text-xs">
      <button
        onClick={() => onSafetyChange(!safety)}
        className={`rounded-lg border px-3 py-1.5 font-medium ${
          safety
            ? "border-green-600 text-green-700 dark:border-green-400 dark:text-green-400"
            : "border-red-600 text-red-700 dark:border-red-400 dark:text-red-400"
        }`}
        title="Toggles the guardrail system prompt AND content moderation — see guardrails.py"
      >
        Safety: {safety ? "ON" : "OFF"}
      </button>

      <label className="flex items-center gap-1 opacity-70">
        Reasoning
        <select
          value={chatProvider}
          onChange={(e) => onChatProviderChange(e.target.value as ChatProvider)}
          className="rounded border border-black/10 dark:border-white/15 bg-transparent px-1 py-0.5"
        >
          <option value="ollama">ollama (free)</option>
          <option value="openai">openai</option>
        </select>
      </label>

      <label className="flex items-center gap-1 opacity-70">
        Vision
        <select
          value={visionProvider}
          onChange={(e) => onVisionProviderChange(e.target.value as VisionProvider)}
          className="rounded border border-black/10 dark:border-white/15 bg-transparent px-1 py-0.5"
        >
          <option value="ollama">ollama (free)</option>
          <option value="openai">openai</option>
        </select>
      </label>

      <label className="flex items-center gap-1 opacity-70">
        Image gen
        <select
          value={imageGenProvider}
          onChange={(e) => onImageGenProviderChange(e.target.value as ImageGenProvider)}
          className="rounded border border-black/10 dark:border-white/15 bg-transparent px-1 py-0.5"
        >
          <option value="huggingface">hugging face (free)</option>
          <option value="openai">openai</option>
        </select>
      </label>

      <span className="ml-auto font-medium opacity-70">Session cost: ${totalCost.toFixed(6)}</span>
    </div>
  );
}
