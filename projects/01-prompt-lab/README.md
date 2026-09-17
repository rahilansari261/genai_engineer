# 01 — Prompt Lab & Token Inspector

Send one prompt to OpenAI, Anthropic, and a local Ollama model at the same time, and see the response, token count, latency, and cost side by side.

## What problem does this solve?

When you start working with AI APIs, a bunch of things that experienced AI engineers take for granted are actually invisible to a newcomer:

- "Which model should I use?" — you can't answer that until you've seen more than one model answer the *same* question
- "Why is my bill so high?" — tokens and pricing feel abstract until you watch a token counter tick up in real time and see a dollar amount attached to it
- "Is this provider slow, or is it just me?" — latency differences between providers are easy to *feel* but hard to *see* without measuring
- "What happens if I don't have an API key?" — real apps have to handle missing config gracefully, not just crash

This project makes all four of those things visible on one screen, so instead of reading about "context windows" or "pricing" in the abstract, you're looking at real numbers from a real request you just sent.

## What you'll learn

This is the foundation project — it exists to make the invisible parts of "calling an LLM" visible, before any framework hides them from you.

- **What is an AI Engineer? / AI Engineer vs ML Engineer** — you're building the "plumbing" layer an AI engineer owns (API integration, cost/latency tradeoffs), not training models
- **LLMs / Inference / AI vs AGI** — inference is just an API call with a prompt in, tokens out; seeing three different LLMs answer the same prompt makes "they're not all the same model" concrete
- **Pre-trained Models — Capabilities / Context Length / Cut-off Dates** — you'll hit real context-length limits and see real knowledge cut-offs when you compare outputs
- **OpenAI Platform — Chat Completions API, Writing Prompts** — direct SDK usage, no abstraction
- **Managing Tokens — Maximum Tokens, Token Counting** — using `tiktoken` to count tokens before you send them, and reading real `usage` fields back from each provider
- **Pricing Considerations** — turning token counts into actual dollar estimates using each provider's published rates

## Builds on

Nothing — this is project 1.

## Tech stack

- **Backend**: Python, FastAPI, `openai`, `anthropic`, `httpx` (for Ollama's local HTTP API), `tiktoken`
- **Frontend**: Next.js (TypeScript, App Router), Tailwind CSS

## How it works, in one picture

```
  Browser (Next.js)                FastAPI backend                  AI providers
  ------------------               -----------------                 ------------
  You type a prompt   --POST-->    POST /complete        --fires all three at once-->  OpenAI
  and tick providers   /complete   (main.py)                                            Anthropic
                                        |                                                Ollama (local)
                                   waits for all of them,
                                   counts tokens & cost
                                        |
  Three result cards  <--JSON--    one JSON array back
```

Every code file has big comments at the top and throughout explaining what it does and why — start with `backend/main.py`, then `backend/providers.py`, then `frontend/app/page.tsx`. Reading those three, in that order, tells the whole story of this project.

## What you'll build

- A backend endpoint (`POST /complete`) that fans a single prompt out to whichever providers you select, and returns each provider's response plus token count, latency, and estimated cost — all in one JSON payload
- A one-page frontend: a textarea, checkboxes for OpenAI / Anthropic / Ollama, and three response panels rendered side by side once you hit "Run"
- Graceful degradation: no `OPENAI_API_KEY`? That panel shows "no API key configured" instead of crashing the whole request. Ollama not running? Same idea.

## Stretch goals

- Add a streaming mode (SSE or chunked response) instead of waiting for the full completion
- Add a system-prompt field and see how differently each provider treats it
- Log every run to a local JSON file and build a tiny "cost so far" running total

## Setup & run

You need the backend and frontend running **at the same time**, in two separate terminals — the frontend is just the UI, all the actual AI-calling logic lives in the backend.

### 1. Run the backend (Terminal 1)

```bash
cd projects/01-prompt-lab/backend

# Create an isolated Python environment just for this project, so its
# dependencies don't clash with any other Python project on your machine.
python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate

# Install the packages listed in requirements.txt
pip install -r requirements.txt

# Copy the example env file and fill in whichever API keys you have.
# Every key is optional — leave any of them blank and that provider's
# panel will just show "no API key configured" instead of erroring out.
cp .env.example .env

# Start the API server with auto-reload (restarts itself when you edit code)
uvicorn main:app --reload --port 8000
```

Leave this terminal running. Check it worked: open [http://localhost:8000/health](http://localhost:8000/health) in a browser — you should see `{"status":"ok"}`.

### 2. Run the frontend (Terminal 2, separate window)

```bash
cd projects/01-prompt-lab/frontend

npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — that's the actual app.

### 3. (Optional but recommended) Get Ollama working with zero API keys

The Ollama path is the only one that works completely free, with no account or API key:

```bash
# Install Ollama from https://ollama.com if you haven't already, then:
ollama pull llama3.2   # downloads a small model (a few GB)
ollama serve            # starts Ollama's local server (may already be running)
```

With just this, you can tick only the "Ollama" checkbox in the app and get a full working result — a good first thing to try before setting up any paid API keys.

### 4. To stop everything

`Ctrl+C` in both terminals.
