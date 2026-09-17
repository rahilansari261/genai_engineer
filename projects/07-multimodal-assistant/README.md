# 07 — Multimodal Assistant

Upload an image and ask about it, generate an image from text, and hold a full spoken conversation with it — one assistant, four modalities, each with a free/local option and a paid/hosted one.

## What problem does this solve?

Most learning material treats "chat with text," "understand an image," "generate an image," and "speech in/out" as four separate topics you'd learn from four separate tutorials — so it never clicks that they're just different endpoints you can wire into the *same* assistant. This project builds one assistant that does all four, which is the more realistic shape of what you'll actually be asked to build as an AI engineer: not "a vision demo" and "a TTS demo" separately, but one product a user talks to, shows things to, and hears back from.

## What you'll learn

- **Multimodal AI Usecases / Multimodal AI Tasks** — image understanding, image generation, and audio in/out as genuinely different API shapes, not variations of chat completions
- **Image Understanding — OpenAI Vision API** — a real image attached to a chat request as a content part, compared directly against a free local vision model (Ollama's `moondream`)
- **Image Generation — DALL-E API** — text-to-image via OpenAI, compared against a free Hugging Face-hosted model
- **Audio Processing — Speech-to-Text (Whisper API) / Text-to-Speech** — a full voice loop: record → transcribe → reply → speak, with a free local option at *every* step
- **Hugging Face Models for Multimodal** — a hosted open-source image-generation model, used the same way Project 3 used HF's Inference SDK for other tasks
- A genuinely free way to do TTS that isn't a Hugging Face model at all: the **browser's own `speechSynthesis` API** — see the note below

## A note on scope: no LangChain/LlamaIndex here

The roadmap also lists "LangChain / LlamaIndex for Multimodal Apps." This project skips wrapping these four integrations in a framework — Project 5 already did a thorough, honest raw-vs-framework comparison (chunking and retrieval), and repeating that comparison here across four different modalities would mostly add abstraction, not a new lesson. Wiring one of these panels through LangChain's multimodal message types is a genuine, well-scoped stretch goal below if you want that specific comparison.

## Builds on

Nothing structurally required, but reuses the provider-comparison mindset from Project 1 and the graceful-degradation pattern (missing key → clear message, not a crash) from every project before it. Backend + Ollama run in Docker, same pattern as Projects 5 and 6.

## How it works, in one picture

```
  Vision:        image + question --> vision.py --> Ollama moondream (free, local)  |  OpenAI gpt-4o-mini (paid)
  Image gen:     text prompt      --> image_gen.py --> Hugging Face (free, needs HF_TOKEN) | OpenAI DALL-E (paid)
  Voice loop:    mic recording -> POST /transcribe -> POST /chat -> POST /speak (or browser speechSynthesis)
                     |                  |                  |                |
                 MediaRecorder    faster-whisper       Ollama/OpenAI    OpenAI TTS, or
                 (browser API)    (free, local) or      (plain reply)   window.speechSynthesis
                                  OpenAI Whisper                        (free, client-side, no backend call)
```

Every code file has big comments explaining what it does and why. `backend/vision.py` is the best starting point — it shows the same image attached to a request two completely different ways depending on the provider. `frontend/components/VoicePanel.tsx` is worth reading end to end: it's the one place in this repo where three backend calls (and one *not*-backend call, for browser TTS) get chained into a single user-facing action.

## What you'll build

- A **Vision** tab: upload any image, ask a question about it, compare Ollama's free local `moondream` against OpenAI's vision-capable chat model on the same image
- An **Image Generation** tab: type a prompt, generate with a free Hugging Face-hosted model or paid DALL-E, see the result inline
- A **Voice Assistant** tab: record your voice with the browser's own microphone API, get it transcribed (locally and free, or via OpenAI), get a reply from an LLM, and hear that reply spoken back — either through the browser's built-in TTS (genuinely free, zero backend calls) or OpenAI's TTS API

## What actually happened when this was tested

Real, unstaged results from live testing, not assumed:

- **A real public speech sample**, run through the local `faster-whisper` "tiny" model, came back as *"The birds can use lid on the smooth planks"* for source audio that actually said *"The birch canoe slid on the smooth planks"* — close but genuinely imperfect, which is the honest tradeoff of using the smallest, fastest local model size rather than a staged perfect transcript.
- **A hand-drawn test image** (sun, sky, grass, a triangle) sent to `moondream` came back correctly identifying the sun, sky, and grass, but calling a brown triangle "red" — small vision models make small, real mistakes, and seeing one directly is more useful than reading that they can.
- **A packaging gap**: `faster-whisper` imports `requests` internally but doesn't declare it as a dependency, so the container built and started fine but failed the moment transcription was actually used. Added `requests` to `requirements.txt` explicitly and rebuilt — worth knowing this class of bug exists (a library's declared dependencies aren't always complete) rather than assuming a clean `pip install` guarantees every import will work.

## Stretch goals

- Chain vision + generation: describe an uploaded image, then generate a variation of it from that description
- Add video understanding on a short clip (sample a few frames, describe what's happening across them)
- Wire one panel (e.g. Vision) through LangChain's multimodal message format and compare against this project's raw approach — see the scope note above
- Swap `faster-whisper`'s model size from `"tiny"` to `"base"` or `"small"` in `speech_to_text.py` and compare transcription accuracy against the honest "tiny" result above

## Setup & run

Same Docker-based pattern as Projects 5 and 6: backend + Ollama in containers, frontend runs natively.

### 1. Start the backend + Ollama

```bash
cd projects/07-multimodal-assistant
cp backend/.env.example backend/.env   # all keys optional — see below for what each unlocks
docker compose up --build
```

Check it worked: [http://localhost:8000/health](http://localhost:8000/health).

### 2. Pull the free vision model (one-time)

```bash
docker compose exec ollama ollama pull moondream
```

For the Voice Assistant tab's free reply step, also pull a text model if you haven't in another project's Ollama volume (each project has its own): `docker compose exec ollama ollama pull llama3.2`.

### 3. Run the frontend

```bash
cd projects/07-multimodal-assistant/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

### What works with zero API keys

- **Vision** tab with the Ollama engine selected (`moondream`)
- **Voice Assistant** tab with speech-to-text set to "local", reply set to "ollama", and text-to-speech set to "browser" — a complete voice loop, no key required at all

### What needs keys

- `OPENAI_API_KEY` — OpenAI vision, DALL-E image generation, OpenAI Whisper, and OpenAI TTS
- `HF_TOKEN` (free) — the Hugging Face image-generation option; get one at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

### To stop everything

`Ctrl+C` the frontend, then `docker compose down` from `projects/07-multimodal-assistant/`.

Note: like every other project's backend, this one publishes port 8000 (and 11434 for Ollama) — don't run another project's backend at the same time without changing ports. This project's `docker-compose.yml` also pins public DNS servers (`8.8.8.8`, `1.1.1.1`) for the same Docker Desktop DNS quirk documented in Project 6's README.
