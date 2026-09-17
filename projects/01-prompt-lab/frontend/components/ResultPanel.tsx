/**
 * ============================================================================
 *  RESULT PANEL — ek provider ka "answer card"
 * ============================================================================
 * Yeh ek chhota, reusable UI ka tukda hai (ek "component") jo EK box banata
 * hai: provider ka naam, uska jawab (ya error, ya loading state), aur uske
 * neeche stats ki ek row (tokens / latency / cost).
 *
 * Main page (app/page.tsx) inme se TEEN ko side by side render karta hai —
 * har provider ke liye ek — bas <ResultPanel .../> ko teen baar alag-alag
 * data ke saath call karke. Components ka yahi pura idea hai: "ek result
 * kaise draw karna hai" wala logic EK BAAR likho, phir usko reuse karo,
 * same JSX ko teen baar copy-paste karne ki jagah.
 * ============================================================================
 */

import type { ProviderResult } from "@/lib/types";

// Ek lookup table jo hamare internal provider id ("openai") ko screen par
// dikhane wale nicer label ("OpenAI") mein badalta hai. Wahi "ek string ko
// kisi aur cheez se map karo" wala trick jo backend ke main.py mein
// CALLERS karta hai.
const PROVIDER_LABEL: Record<string, string> = {
  openai: "OpenAI",
  anthropic: "Anthropic",
  ollama: "Ollama (local)",
};

export default function ResultPanel({
  result,
  loading,
}: {
  // `result` tab tak `null` rehta hai jab tak is provider ke liye asal mein
  // koi jawab nahi mil jaata (ya app abhi tak run hi nahi hua).
  result: ProviderResult | null;
  // `loading` sirf tab true hota hai jab ISI panel ki request abhi in-flight ho.
  loading: boolean;
}) {
  const label = result ? PROVIDER_LABEL[result.provider] ?? result.provider : "";

  return (
    <div className="flex flex-col rounded-lg border border-black/10 dark:border-white/15 min-h-64">
      {/* Header row: provider ka naam + kaunse model ne jawab diya */}
      <div className="flex items-center justify-between border-b border-black/10 dark:border-white/15 px-4 py-2">
        <span className="font-medium">{label}</span>
        {result && <span className="text-xs opacity-60">{result.model}</span>}
      </div>

      {/*
        Card ki main body. Yeh conditions ki ek chain hai jo decide karti
        hai KYA dikhana hai, isi order mein check hoti hain:
          1. Abhi bhi backend ka wait ho raha hai?     -> "Running…"
          2. Result mil gaya, lekin usmein error hai?  -> error ko red mein dikhao
          3. Result clean mila?                         -> asli answer text dikhao
          4. Abhi tak kuch hua hi nahi?                 -> "Not run yet"
        Inमें se kabhi ek hi baar true hota hai, isliye sirf ek hi render hota hai.
      */}
      <div className="flex-1 px-4 py-3 text-sm whitespace-pre-wrap overflow-y-auto">
        {loading && <span className="opacity-60">Running…</span>}
        {!loading && result?.error && (
          <span className="text-red-600 dark:text-red-400">{result.error}</span>
        )}
        {!loading && result && !result.error && result.text}
        {!loading && !result && <span className="opacity-40">Not run yet</span>}
      </div>

      {/*
        Stats footer tabhi dikhane ka sense banta hai jab humare paas ek
        successful (bina-error) result ho — jab kuch chala hi nahi, tab
        "0 tokens, $0" dikhane ka koi matlab nahi.
      */}
      {result && !result.error && (
        <div className="grid grid-cols-3 gap-2 border-t border-black/10 dark:border-white/15 px-4 py-2 text-xs opacity-70">
          <span>
            tokens: {result.total_tokens ?? "—"}
            {result.prompt_tokens != null && result.completion_tokens != null
              ? ` (${result.prompt_tokens} in / ${result.completion_tokens} out)`
              : ""}
          </span>
          <span>{result.latency_ms != null ? `${result.latency_ms} ms` : "—"}</span>
          <span>
            {result.cost_usd != null
              ? // Bahut chhote costs (cent ke fractions) 4 decimal places
                // par round ho kar $0.0000 ban jaate hain, isliye chhote
                // numbers ke liye zyada decimals dikhate hain aur bade,
                // zyada readable numbers ke liye kam.
                `$${result.cost_usd < 0.01 ? result.cost_usd.toFixed(6) : result.cost_usd.toFixed(4)}`
              : "free / unpriced"}
          </span>
        </div>
      )}
    </div>
  );
}
