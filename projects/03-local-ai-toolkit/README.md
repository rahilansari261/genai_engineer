# 03 — Local AI Toolkit

Run open-source models entirely on your own machine — from the terminal, from a Python backend, and directly in the browser — and compare them to the hosted APIs from Project 1.

## What problem does this solve?

It's easy to assume "using AI" means "having an OpenAI API key and a credit card" — and that assumption quietly blocks a lot of experimentation (rate limits, cost anxiety, no offline access, data leaving your machine). Most beginners have never actually run a model themselves and don't know it's even an option, let alone how "open source model" differs from "open weights," or why a model running in Ollama behaves differently from the same-sized model behind an API. This project makes local, free, private inference a real, working alternative you've used with your own hands — not just a line item on the roadmap.

## What you'll learn

- **Open vs Closed Source Models** — you'll feel the tradeoffs directly: setup cost and hardware limits vs. zero API cost and full control
- **Hugging Face Hub / Hugging Face Tasks / Finding Open Source Models** — browse the Hub, pick models by task (text-generation, summarization, sentiment-analysis), not just by name
- **Using Open Source Models — Inference SDK** — call a hosted open-source model via Hugging Face's Inference API from Python
- **Ollama / Ollama Models / Ollama SDK** — pull and run a local model, then call it programmatically instead of via the CLI
- **Transformers.js** — run a small model *in the browser*, client-side, with no backend call at all — a genuinely different execution model worth seeing firsthand

## Builds on

[01 — Prompt Lab](../01-prompt-lab/README.md) for the overall pattern (FastAPI backend + Next.js frontend), but this project is standalone — it doesn't share code with Project 1.

## Tech stack

Python (official `ollama` SDK, Hugging Face's `huggingface_hub` `InferenceClient`), Next.js/TypeScript frontend with `@huggingface/transformers` running entirely client-side (WASM) for the third panel.

## How it works, in one picture

```
  Browser (Next.js) — three independent panels, each a different "engine":

  1. Ollama panel        --POST /ollama/generate-->  FastAPI  --Ollama SDK-->  Ollama, on YOUR machine
  2. Hugging Face panel  --POST /hf/classify--------> FastAPI  --HF SDK------>  Hugging Face's servers
                          --POST /hf/summarize------->    (a different task-specific model per endpoint)
  3. Browser panel       -- no backend call at all --> a model downloaded straight into THIS tab,
                                                        run with WebAssembly, right here
```

Every code file has big comments explaining what it does and why. Read `backend/ollama_local.py` next to Project 1's `backend/providers.py` — same job (call Ollama), done with an official SDK instead of hand-rolled HTTP, which is the point of that file. Then read `backend/hf_tasks.py` and `frontend/components/BrowserClassifier.tsx` for the other two engines.

## What you'll build

- **Engine 1 — Ollama**: a chat-style prompt box backed by the official Ollama Python SDK (not raw HTTP like Projects 1-2), running whatever model you've pulled locally
- **Engine 2 — Hugging Face**: a panel that switches between two genuinely different task-specific models — sentiment classification and summarization — both running on Hugging Face's own hosted Inference API
- **Engine 3 — Transformers.js**: a sentiment classifier that downloads its model straight into your browser tab and runs entirely client-side — no backend call at all, provably so (open the browser's network tab and watch)

## Stretch goals

- Try a second local model with `ollama pull` and compare output quality/speed against the first
- Point the Hugging Face panel at a different task-specific model from the [Hub](https://huggingface.co/models) (translation, NER, zero-shot classification) — you just need its model ID
- Compare the *feel* of latency across all three: Ollama (local hardware-bound), Hugging Face (network + their server), Transformers.js (one-time download, then instant on every future run)

## A note on a dependency advisory

Installing `@huggingface/transformers` pulls in `onnxruntime-node` and `sharp` as optional dependencies for running models in *Node.js* — `npm audit` will flag known high-severity issues in both, with no fix currently available. This project never uses that Node-side code path (`BrowserClassifier.tsx` only imports the library inside a browser component, and the production build in this README's setup steps confirms Turbopack doesn't bundle those native Node modules into the client bundle) — but it's worth knowing the advisory is there and unresolved upstream, rather than being surprised by `npm audit` output later.

## Setup & run

Three moving parts this time: backend, frontend, and (optionally) Ollama itself.

### 1. Run the backend (Terminal 1)

```bash
cd projects/03-local-ai-toolkit/backend

python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# HF_TOKEN: free, from https://huggingface.co/settings/tokens (read access is enough)
# — only needed for the Hugging Face panel. Ollama needs no key at all.
cp .env.example .env

uvicorn main:app --reload --port 8000
```

Check it worked: [http://localhost:8000/health](http://localhost:8000/health) should show `{"status":"ok"}`.

### 2. Run the frontend (Terminal 2)

```bash
cd projects/03-local-ai-toolkit/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### 3. Get Ollama working (for engine 1)

```bash
ollama pull llama3.2
ollama serve
```

### 4. Try engine 3 with zero setup at all

The browser panel needs no backend, no API key, and no Ollama — click "Load model into browser" and it just works (after a one-time model download). Good first thing to try if you haven't set anything else up yet.

### 5. To stop everything

`Ctrl+C` in both terminals.

Note: this project's backend also defaults to port 8000. Don't run it at the same time as another project's backend without changing one of their ports (`uvicorn main:app --port 8020`, and update that project's frontend `.env.local` to match).
