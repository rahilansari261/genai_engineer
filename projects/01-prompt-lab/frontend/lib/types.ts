/**
 * ============================================================================
 *  TYPES — hamare components ke beech share hone wale "shape contracts"
 * ============================================================================
 * TypeScript humein ek data ka exact shape describe karne deta hai (usme
 * kaunse fields hain, aur har ek ka type kya hai), aur phir editor/compiler
 * turant chilla deta hai agar hum usko galat use karne ki koshish karein —
 * jaise agar kisi field ka naam typo ho jaaye, ya kisi value ke `null` hone
 * wale case ko handle karna bhool jaayein.
 *
 * Yeh dono shapes backend ke main.py mein wale Python `ProviderRequest`/
 * `ProviderResult` models ko almost field-for-field mirror karte hain.
 * Frontend aur backend ke shapes ko is tarah sync mein rakhna ek bahut hi
 * normal (thoda manual zaroor) part hai bina shared schema tool ke
 * full-stack app banane ka — agar ek side par field ka naam badla, to
 * doosri side par bhi yaad rakh ke badalna padta hai.
 * ============================================================================
 */

// Teen AI providers jinko yeh app call karna jaanta hai. Isko exact
// strings ke union ke roop mein likhna (sirf `string` ki jagah) matlab
// TypeScript tumhe rok dega agar kabhi "opeani" jaisa typo kar diya.
export type Provider = "openai" | "anthropic" | "ollama";

// Ek row jo batata hai "kaunsa provider, kaunsa model, abhi on hai ya
// nahi" — yahi UI mein checkboxes + model text boxes ko drive karta hai.
export interface ProviderChoice {
  provider: Provider;
  model: string;
  enabled: boolean;
}

// Ek prompt run karne ke baad backend se ek provider ke liye jo WAPAS
// milta hai. Almost sab kuch `| null` hai kyunki cheezein fail ho sakti
// hain (missing API key, network error) — us case mein sirf `error` fill
// hota hai, aur UI ko pata hota hai ki blank response ki jagah wahi dikhana hai.
export interface ProviderResult {
  provider: Provider;
  model: string;
  text: string | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
  error: string | null;
}
