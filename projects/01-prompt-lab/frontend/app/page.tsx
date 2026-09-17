/**
 * ============================================================================
 *  HOME PAGE — poora Prompt Lab UI
 * ============================================================================
 * Yeh app ka EKMATRA page hai. Yeh ek "client component" hai (neeche wali
 * "use client" line dekho), jiska Next.js mein matlab hai: yeh code user ke
 * asli browser mein chalta hai, state rakh sakta hai (aisi cheezein jo page
 * use karte waqt badalti rehti hain, jaise textbox mein kya type kiya), aur
 * clicks par react kar sakta hai.
 *
 * Flow, seedhi bhasha mein:
 *   1. Tum ek prompt type karte ho aur jo providers try karne hain unko tick karte ho.
 *   2. Tum "Run" click karte ho.
 *   3. Yeh page hamare FastAPI backend (backend/main.py wala code) ko EK
 *      request bhejta hai, saath mein prompt + kaunse providers select kiye.
 *   4. Backend un sab providers ko EK SAATH call karta hai aur results ka
 *      ek array wapas bhejta hai.
 *   5. Hum har result ko uske apne <ResultPanel> box mein dikhate hain.
 * ============================================================================
 */

"use client";

import { useState } from "react";
import ResultPanel from "@/components/ResultPanel";
import type { ProviderChoice, ProviderResult } from "@/lib/types";

// Backend kahan chal raha hai. Agar environment variable set kiya hai
// (dekho .env.local.example) to wahan se padhta hai, warna maan leta hai
// ki `uvicorn main:app --port 8000` wale default port par locally chal
// raha hai.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Page pehli baar khulte hi kya tick aur fill hota hai. Yeh models
// bindaas apni marzi se badal do, jo tumhare paas actually available hain.
const DEFAULT_CHOICES: ProviderChoice[] = [
  { provider: "openai", model: "gpt-4o-mini", enabled: true },
  { provider: "anthropic", model: "claude-3-5-haiku-20241022", enabled: true },
  { provider: "ollama", model: "llama3.2", enabled: true },
];

export default function Home() {
  // ------------------------------------------------------------------
  // REACT STATE: har `useState` tumhe data ka ek tukda deta hai jo page
  // renders ke beech "yaad" rakhta hai, saath mein usko update karne wala
  // function bhi. Jab bhi neeche wale `set...` functions mein se koi call
  // hota hai, React is component ko dobara chalata hai aur naye values ke
  // saath page ko redraw karta hai — bas yahi hai React ka poora mental
  // model, ek line mein.
  // ------------------------------------------------------------------
  const [prompt, setPrompt] = useState("Explain what an API is, in two sentences.");
  const [system, setSystem] = useState("");
  const [choices, setChoices] = useState<ProviderChoice[]>(DEFAULT_CHOICES);
  // `results` ek provider ke naam ("openai") ko uske ProviderResult se map
  // karta hai, jab mil jaaye.
  const [results, setResults] = useState<Record<string, ProviderResult>>({});
  const [loading, setLoading] = useState(false);
  // Sirf REQUEST-level failure ke liye (jaise backend chal hi nahi raha) —
  // ek provider ka fail hona (galat key) uske apne panel ke andar dikhta hai.
  const [requestError, setRequestError] = useState<string | null>(null);

  // Sirf jin providers ka checkbox tick hai, wahi backend ko bheje jaate hain.
  const enabledChoices = choices.filter((c) => c.enabled);

  // Ek provider ka checkbox on/off karta hai. `.map()` yahan ek bilkul
  // NAYA array banata hai, purane ko edit nahi karta — React chahta hai
  // ki tum state ko replace karo, jagah par edit mat karo, taaki usko
  // pata chale ki kuch badla hai.
  function toggleProvider(provider: string) {
    setChoices((prev) =>
      prev.map((c) => (c.provider === provider ? { ...c, enabled: !c.enabled } : c))
    );
  }

  // Ek provider row ke model naam wale text box ko update karta hai.
  function updateModel(provider: string, model: string) {
    setChoices((prev) => prev.map((c) => (c.provider === provider ? { ...c, model } : c)));
  }

  // Yeh wahi function hai jise "Run" button call karta hai. Yeh `async`
  // isliye hai kyunki `fetch` (backend se network par baat karna) time
  // leta hai, aur humein uska result aane se pehle use karne ki jagah
  // `await` karna padta hai.
  async function runPrompt() {
    if (enabledChoices.length === 0 || !prompt.trim()) return;

    setLoading(true);
    setRequestError(null);
    setResults({}); // purane answers clear karo taaki re-run par stale data na dikhe

    try {
      // Hamare backend ke POST /complete/stream endpoint ko call karta hai
      // (dekho main.py). Yeh `/complete` jaisa hi request body leta hai,
      // bas response ek saath nahi, ek-ek karke (NDJSON stream) aata hai —
      // isliye jo provider pehle ready ho jaaye, uska panel turant update
      // ho jaata hai, baaki slow providers ka wait nahi karna padta.
      const response = await fetch(`${API_URL}/complete/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          system: system.trim() || undefined,
          providers: enabledChoices.map(({ provider, model }) => ({ provider, model })),
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error(`Backend returned ${response.status}`);
      }

      // Stream ko chunk-by-chunk padhते hain. Har chunk mein ek ya zyada
      // NDJSON lines aa sakti hain, aur ek line beech mein bhi kat sakti
      // hai — isliye hum ek `buffer` mein sab jama karte hain, sirf poori
      // (newline-terminated) lines ko parse karte hain, aur adhuri line
      // ko agle chunk ke liye buffer mein hi chhod dete hain.
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? ""; // aakhri, shayad adhuri line agli baar ke liye rakh lo

        for (const line of lines) {
          if (!line.trim()) continue;
          // Jaise hi ek provider ka result line aata hai, sirf USI
          // provider ki entry ko results mein update karte hain — baaki
          // providers jo abhi tak nahi aaye, unke purane (ya khaali)
          // state ko chhedte nahi.
          const result: ProviderResult = JSON.parse(line);
          setResults((prev) => ({ ...prev, [result.provider]: result }));
        }
      }
    } catch (err) {
      // Yeh sirf REQUEST mein hi problem hone par fire hota hai — jaise
      // backend bilkul chal hi nahi raha, isliye `fetch` connect bhi nahi
      // kar paaya.
      setRequestError(
        err instanceof Error
          ? `${err.message} — is the backend running on ${API_URL}?`
          : "Something went wrong"
      );
    } finally {
      // `finally` hamesha chalta hai, chahe try succeed ho ya catch fire
      // ho — isse guarantee milta hai ki "Running…" wala state hamesha
      // off ho jaayega.
      setLoading(false);
    }
  }

  // ------------------------------------------------------------------
  // Page ka asli markup (JSX — HTML jaisa syntax, curly braces mein JS
  // values ke saath mixed). Roughly: title -> prompt form -> teen result panels.
  // ------------------------------------------------------------------
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-semibold">Prompt Lab & Token Inspector</h1>
        <p className="mt-1 text-sm opacity-70">
          One prompt, three providers, side by side — response, tokens, latency, and cost.
        </p>
      </header>

      <section className="flex flex-col gap-3">
        {/* Main prompt box — iski value upar wale `prompt` state se juli hui
            hai, aur har keystroke us state ko update karta hai (React ki
            zabaan mein ek "controlled input"). */}
        <textarea
          className="w-full resize-y rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-4 py-3 text-sm"
          rows={4}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Type a prompt…"
        />
        <input
          className="w-full rounded-lg border border-black/10 dark:border-white/15 bg-transparent px-4 py-2 text-sm"
          value={system}
          onChange={(e) => setSystem(e.target.value)}
          placeholder="Optional system prompt…"
        />

        {/* Har provider ke liye ek row: use enable/disable karne ke liye
            checkbox, aur uska model change karne ke liye text box. */}
        <div className="flex flex-wrap items-center gap-4">
          {choices.map((choice) => (
            <label key={choice.provider} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={choice.enabled}
                onChange={() => toggleProvider(choice.provider)}
              />
              <span className="capitalize">{choice.provider}</span>
              <input
                className="w-44 rounded border border-black/10 dark:border-white/15 bg-transparent px-2 py-1 text-xs"
                value={choice.model}
                onChange={(e) => updateModel(choice.provider, e.target.value)}
              />
            </label>
          ))}

          {/* Loading ke dauraan disabled (double-submit se bachne ke liye),
              ya koi provider tick nahi hai, ya prompt box khaali hai to bhi
              disabled. */}
          <button
            onClick={runPrompt}
            disabled={loading || enabledChoices.length === 0 || !prompt.trim()}
            className="ml-auto rounded-lg bg-black px-5 py-2 text-sm font-medium text-white disabled:opacity-40 dark:bg-white dark:text-black"
          >
            {loading ? "Running…" : "Run"}
          </button>
        </div>

        {requestError && <p className="text-sm text-red-600 dark:text-red-400">{requestError}</p>}
      </section>

      {/* Teen result cards, har provider ke liye ek — har ek ko bas
          `results` ka apna slice diya jaata hai (ya null agar abhi tak
          nahi mila). */}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {choices.map((choice) => (
          <ResultPanel
            key={choice.provider}
            result={results[choice.provider] ?? null}
            // Poori request abhi bhi "loading" ho sakti hai (kyunki koi
            // aur, slower provider abhi bhi chal raha hai), lekin ISI
            // provider ka result agar stream se mil chuka hai, to panel
            // ko "Running…" dikhaana band kar do — uska apna result turant
            // dikha do, baaki panels ka intezaar na karo.
            loading={loading && choice.enabled && !results[choice.provider]}
          />
        ))}
      </section>
    </main>
  );
}
