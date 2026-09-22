# GEN-AI Engineer — Learning Path 

## What is this repo?

A full-stack engineer's hands-on path into AI engineering, built as a sequence of real (small but real) projects instead of tutorials. The syllabus is [roadmap.sh's AI Engineer roadmap](ai-engineer.pdf) — every node on that roadmap is covered by at least one project below, and each project's README explains exactly which nodes it teaches and why.

## What problem does this solve?

Most "learn AI engineering" resources are either theory (read about RAG, watch a video on embeddings) or a single giant tutorial you copy-paste without understanding. Neither leaves you able to build something of your own afterwards. This repo is neither of those:

- Every concept is learned by **building a small, real, runnable thing** — not reading about it
- Every project's README says **exactly what you're about to understand and why it matters**, before you write any code
- Every project's code is **commented in plain language**, so the "why", not just the "what", is visible while you read it
- Projects get **progressively more mixed** — later ones reuse pieces built in earlier ones, the same way real AI features in a real product get built on top of each other, instead of every project being an isolated island

## How this repo is organized

Each project lives in `projects/NN-name/` with its own README (what it teaches, what problem it solves, what you're building, how to run it) and its own code. Start at project 1 and work forward — later projects assume you've built the earlier ones.

## Provider & tooling primer

| Provider / tool | What it is | Why it's here |
|---|---|---|
| **OpenAI** | Hosted API for GPT models, embeddings, DALL-E, Whisper, Moderation, Assistants | Most complete API surface — covers chat, embeddings, vision, image gen, speech, moderation in one account |
| **Anthropic (Claude)** | Hosted API for Claude models | Second opinion for provider-comparison projects; different tool-use/prompting conventions worth knowing |
| **Ollama** | Runs open-source LLMs locally (Llama, Mistral, etc.) | Free, offline, no API key — the default for most projects so you can iterate without burning budget |
| **Hugging Face** | Hub of open-source models + Inference SDK | Where you go for open-source embeddings, classification, and specialized models |

You don't need every key to start. `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are optional almost everywhere — projects are built to degrade gracefully to Ollama when a key is missing, and will say so clearly in the UI rather than failing silently.

## Project map

| # | Project | Roadmap.sh nodes covered | Status |
|---|---|---|---|
| 1 | [Prompt Lab & Token Inspector](projects/01-prompt-lab/README.md) | What is an AI Engineer / vs ML Engineer, LLMs, Inference, AI vs AGI, Pre-trained Models (OpenAI/Anthropic/Ollama), Chat Completions API, Writing Prompts, Managing Tokens, Pricing Considerations | 🟢 Built |
| 2 | [AI Safety Sandbox](projects/02-ai-safety-sandbox/README.md) | AI Safety and Ethics, Prompt Injection Attacks, Bias and Fairness, Security/Privacy, Adversarial Testing, OpenAI Moderation API, End-user IDs, Robust Prompt Engineering, Constraining Outputs | 🟢 Built |
| 3 | [Local AI Toolkit](projects/03-local-ai-toolkit/README.md) | Open vs Closed Source Models, Hugging Face Hub/Tasks, Inference SDK, Transformers.js, Ollama, Ollama SDK | 🟢 Built |
| 4 | [Semantic Search & Recommender](projects/04-semantic-search-recommender/README.md) | Embeddings (semantic search, recommendation, anomaly detection, classification), OpenAI Embeddings API, Open-Source Embeddings (Sentence Transformers), Vector Databases, Indexing, Similarity Search | 🟢 Built |
| 5 | [RAG Chatbot over Your Own Docs](projects/05-rag-chatbot/README.md) | RAG Usecases, RAG vs Fine-tuning, Chunking, Retrieval Process, Generation, Implementing RAG (SDKs, LangChain, LlamaIndex), managed cloud Vector DB | 🟢 Built |
| 6 | [AI Agent Assistant](projects/06-ai-agent-assistant/README.md) | AI Agents, Agent Usecases, ReAct Prompting, Manual Implementation, OpenAI Functions/Tools, OpenAI Assistant API (built against its modern replacement, the Responses API — see project README) | 🟢 Built |
| 7 | [Multimodal Assistant](projects/07-multimodal-assistant/README.md) | Multimodal AI, Image Understanding/Generation, Audio Processing, TTS/STT, OpenAI Vision/DALL-E/Whisper APIs, Hugging Face multimodal models | 🟢 Built |
| 8 | [Capstone — AI Copilot](projects/08-capstone-ai-copilot/README.md) | Integrates RAG + Agents + Multimodal + Safety into one product | 🟢 Built |

Update the Status column yourself as you go (⚪ Not started → 🟡 In progress → 🟢 Built) — it's your tracker, not a build artifact. All 8 are built as of 2026-09-11 — the full roadmap, one concept per project, ending in the capstone where they all had to work together. Working through each project yourself (reading the code, running it, breaking it) is still the actual point, not just having it built.

*Not a dedicated project: **Development Tools** (AI code editors, code completion tools) is a roadmap node about what you build **with**, not what you build. Try an AI code editor (Cursor, GitHub Copilot, or Claude Code itself) while working through these projects — that's the whole point of the node.*

## Global setup

- **Node.js** 20+ and npm — every project's frontend runs natively with `npm run dev`
- **Python** 3.11+ for every project's backend — each has its own `requirements.txt`; create a venv per project: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Also **Ollama** installed natively — [ollama.com](https://ollama.com), then `ollama pull llama3.2` (individual projects pull other models too, e.g. `moondream` for vision — see each project's own README).
- **API keys (optional)** — copy each project's `.env.example` to `.env` and fill in what you have:
  - `OPENAI_API_KEY` — [platform.openai.com](https://platform.openai.com)
  - `ANTHROPIC_API_KEY` — [console.anthropic.com](https://console.anthropic.com)
  - `PINECONE_API_KEY` (Project 5 only, for the managed cloud vector DB option) — [app.pinecone.io](https://app.pinecone.io)

## How to work through this

1. Read the project's README first — the "What you'll learn" section tells you what to pay attention to, not just what to run.
2. Run it, break it, read the code — these are intentionally small enough to hold in your head in one sitting.
3. Each README has "Stretch goals" — optional detours if a topic grabs you before moving to the next project.
4. Move to the next project once the current one runs end to end and you could explain, out loud, what each piece does and why.
