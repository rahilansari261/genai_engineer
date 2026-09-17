/**
 * ============================================================================
 *  HOME PAGE — the whole capstone, as one conversation
 * ============================================================================
 * Every message you send becomes one call to POST /chat, carrying the
 * full prior conversation (so the agent has real memory across turns —
 * new in this project, none of the earlier ones needed it), any attached
 * image, and every provider/safety setting from the bar above. See
 * backend/agent.py for what happens to all of that in one guarded,
 * tool-using, cost-tracked loop.
 * ============================================================================
 */

"use client";

import { useEffect, useState } from "react";
import Composer from "@/components/Composer";
import MessageBubble from "@/components/MessageBubble";
import SettingsBar from "@/components/SettingsBar";
import type { ChatApiResult, ChatProvider, DisplayMessage, ImageGenProvider, VisionProvider } from "@/lib/types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function Home() {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCost, setTotalCost] = useState(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [docs, setDocs] = useState<string[]>([]);

  const [safety, setSafety] = useState(true);
  const [chatProvider, setChatProvider] = useState<ChatProvider>("ollama");
  const [visionProvider, setVisionProvider] = useState<VisionProvider>("ollama");
  const [imageGenProvider, setImageGenProvider] = useState<ImageGenProvider>("huggingface");

  useEffect(() => {
    fetch(`${API_URL}/status`)
      .then((res) => res.json())
      .then((data) => setDocs(data.docs ?? []))
      .catch(() => setLoadError(`Couldn't reach the backend at ${API_URL}`));
  }, []);

  async function handleSend(text: string, image: File | null) {
    const userMessage: DisplayMessage = {
      id: `${Date.now()}-user`,
      role: "user",
      content: text,
      imagePreviewUrl: image ? URL.createObjectURL(image) : undefined,
    };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setLoadError(null);

    // The backend only needs plain {role, content} pairs for memory — an
    // assistant turn's content is its final answer, or a short stand-in
    // if that turn was blocked or errored, so the model still sees SOME
    // trace of what happened rather than a confusing gap in the history.
    const history = messages.map((m) => ({
      role: m.role,
      content:
        m.role === "user"
          ? m.content
          : m.result?.final_answer ?? (m.result?.blocked ? "[response blocked by safety]" : "[no response]"),
    }));

    const formData = new FormData();
    formData.append("message", text);
    formData.append("history", JSON.stringify(history));
    formData.append("provider", chatProvider);
    formData.append("model", chatProvider === "ollama" ? "llama3.2" : "gpt-4o-mini");
    formData.append("vision_provider", visionProvider);
    formData.append("vision_model", visionProvider === "ollama" ? "moondream" : "gpt-4o-mini");
    formData.append("image_gen_provider", imageGenProvider);
    formData.append("image_gen_model", imageGenProvider === "openai" ? "dall-e-3" : "black-forest-labs/FLUX.1-schnell");
    formData.append("safety", String(safety));
    if (image) formData.append("image", image);

    try {
      const res = await fetch(`${API_URL}/chat`, { method: "POST", body: formData });
      const result: ChatApiResult = await res.json();
      setMessages((prev) => [...prev, { id: `${Date.now()}-assistant`, role: "assistant", content: "", result }]);
      setTotalCost((prev) => prev + (result.cost_usd ?? 0));
    } catch {
      setLoadError(`Couldn't reach the backend at ${API_URL}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex h-screen w-full max-w-3xl flex-col gap-4 px-6 py-6">
      <header>
        <h1 className="text-2xl font-semibold">AI Copilot</h1>
        <p className="mt-1 text-sm opacity-70">
          RAG, tool use, vision, image generation, and safety guardrails — one assistant.
        </p>
        {docs.length > 0 && <p className="mt-1 text-xs opacity-50">Knowledge base: {docs.join(", ")}</p>}
      </header>

      <SettingsBar
        safety={safety}
        onSafetyChange={setSafety}
        chatProvider={chatProvider}
        onChatProviderChange={setChatProvider}
        visionProvider={visionProvider}
        onVisionProviderChange={setVisionProvider}
        imageGenProvider={imageGenProvider}
        onImageGenProviderChange={setImageGenProvider}
        totalCost={totalCost}
      />

      {loadError && <p className="text-sm text-red-600 dark:text-red-400">{loadError}</p>}

      <div className="flex flex-1 flex-col gap-4 overflow-y-auto py-2">
        {messages.length === 0 && (
          <p className="text-sm opacity-50">
            Try: &quot;What&apos;s the difference between RAG and fine-tuning, and what&apos;s 12% of 850?&quot; — or attach an
            image and ask about it, or try a prompt injection with Safety off vs. on.
          </p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
      </div>

      <Composer onSend={handleSend} disabled={loading} />
    </main>
  );
}
