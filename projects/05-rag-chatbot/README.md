# 05 — RAG Chatbot over Your Own Docs

Chat with a small AI engineering handbook (6 markdown docs shipped in `backend/docs/`, covering RAG, embeddings, prompt engineering, agents, safety, and fine-tuning) with cited sources — and implement the retrieval pipeline two different ways to see what a framework actually buys you.

## What problem does this solve?

Two questions come up the moment you want an LLM to answer from *your* documents instead of its training data: "why not just paste the whole document into the prompt?" (context limits and cost — you'll hit both) and "why not just fine-tune a model on my docs?" (slow, expensive, and wrong for anything that changes often). RAG is the practical middle ground, but frameworks like LangChain and LlamaIndex tend to hide the actual pipeline behind a few magic function calls, so a beginner learns the API but not the mechanism. This project builds the pipeline by hand first — so when you *do* use a framework afterward, you know exactly what it's doing for you instead of trusting a black box.

## What you'll learn

- **RAG Usecases / RAG vs Fine-tuning** — a written comparison, grounded in this actual project: why retrieval beats fine-tuning here
- **Chunking** — split real documents into chunks, and see firsthand how chunk size/overlap changes retrieval quality (too small loses context, too big dilutes relevance)
- **Embedding / Vector Database / Retrieval Process / Generation** — the full pipeline, reusing the vector DB skills from Project 4
- **Implementing RAG — Using SDKs Directly** — build the pipeline by hand once: chunk → embed → store → retrieve → stuff into a prompt → generate
- **Implementing RAG — Langchain / Llama Index** — rebuild the *same* pipeline using a framework, and compare code volume, control, and debuggability against your hand-rolled version
- **Popular Vector DBs** — swap your local Chroma index for a managed one (Pinecone) to see the cloud/production workflow — auth, indexes-as-a-service, network latency

## Builds on

[04 — Semantic Search & Recommender](../04-semantic-search-recommender/README.md) for embeddings + vector DB fundamentals; this project adds chunking and the generation step on top, and deliberately reuses the exact same free local embedding model from Project 4 (see `backend/embeddings.py`) so that comparing the two RAG pipelines isn't muddied by also comparing embedding providers — that ground is already covered.

## Tech stack

Python/FastAPI backend (a hand-rolled pipeline and a LangChain pipeline, side by side), Chroma (local) with an optional Pinecone (managed cloud) backend for the hand-rolled pipeline, Next.js chat UI with inline source citations. **This is the first project in the repo that runs its backend in Docker** — see below for why.

## Why Docker, starting with this project

Every project so far installed its dependencies into a Python venv on your own machine. This one pulls in a genuinely heavy stack — `torch`, `chromadb`, `langchain`, `pinecone` — and going forward, this repo runs backends like that in Docker instead, so those dependencies (and Ollama's own model weights) stay contained to a container rather than piling up on your host. The frontend stays a plain `npm run dev` on your host — lighter weight, and better for hot-reload during dev.

## How it works, in one picture

```
  backend/docs/*.md (6 markdown files)
        |
        +-- rag_raw.py:       chunking.py (hand-rolled) -> embeddings.py -> vector_store.py (Chroma or Pinecone)
        |
        +-- rag_langchain.py: RecursiveCharacterTextSplitter -> SharedEmbeddings -> langchain_chroma.Chroma
                                   (same embedding model as rag_raw.py, wrapped to satisfy LangChain's interface)

  POST /ask {question, pipeline, vector_store, llm_provider, llm_model}
        |
        v
  main.py routes to rag_raw.answer() or rag_langchain.answer():
    embed the question -> retrieve nearest chunks -> build a prompt -> generate with Ollama/OpenAI/Anthropic
        |
        v
  { answer, sources: [{source, snippet, distance}], latency_ms }
```

Every code file has big comments explaining what it does and why. Read `backend/rag_raw.py` and `backend/rag_langchain.py` back to back — same job, two implementations — that comparison is the whole point of this project. `backend/vector_store.py`'s comments explain the Chroma/Pinecone distance-convention quirk you'll want to know about if you wire in a different cloud vector DB later.

## What you'll build

- Two full RAG pipelines answering the same question over the same 6 documents: `rag_raw.py` (hand-rolled chunking, embedding, storage, retrieval, and prompt-building) and `rag_langchain.py` (`RecursiveCharacterTextSplitter`, `langchain-chroma`, and an LCEL `prompt | llm | parser` chain)
- A chat UI showing every answer's sources — which document, a text snippet, and the retrieval distance — not just a filename
- A comparison log that keeps every question you've asked visible, so switching pipeline/vector-store/LLM and re-asking the same question builds up a real side-by-side comparison instead of overwriting the last answer
- An optional managed cloud vector store (Pinecone) wired into the raw pipeline, behind the exact same `upsert`/`search`/`count` interface as the local Chroma backend

## Stretch goals

- Add a "no relevant context found" path — if every retrieved chunk's distance is above some threshold, say so instead of letting the model answer anyway from weak context
- Try re-ranking retrieved chunks before generation (e.g. a cross-encoder) and see if answer quality improves
- Wire Pinecone into the LangChain pipeline too, using `langchain-pinecone` (skipped here to keep the framework comparison focused on chunking/retrieval/generation, not also vector-store choice)
- Add `langchain-anthropic` so the LangChain pipeline supports all three LLM providers like the raw pipeline does

## Setup & run

The backend runs in Docker; the frontend runs natively with `npm run dev`.

### 1. Start the backend + Ollama (one command)

```bash
cd projects/05-rag-chatbot

# All keys optional — the app runs fully on the free local Chroma index +
# Ollama with nothing filled in here at all.
cp backend/.env.example backend/.env

docker compose up --build
```

First run takes a while — the backend image installs `torch`, `chromadb`, and `langchain`, all cached by Docker afterward so it's fast on every run after the first. Leave this running; check it worked with [http://localhost:8000/health](http://localhost:8000/health).

### 2. Pull an Ollama model (one-time, in a second terminal)

```bash
cd projects/05-rag-chatbot
docker compose exec ollama ollama pull llama3.2
```

### 3. Build the indexes (one-time, or after editing backend/docs/*.md)

```bash
docker compose exec backend python ingest.py
```

You should see a chunk count printed for the raw pipeline's Chroma index, the LangChain pipeline's Chroma index, and (if you added a `PINECONE_API_KEY`) the Pinecone index too.

### 4. Run the frontend (Terminal 2, or a third terminal)

```bash
cd projects/05-rag-chatbot/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — both pipelines should already show as indexed.

### 5. To stop everything

`Ctrl+C` the frontend, then `docker compose down` from `projects/05-rag-chatbot/` (add `-v` to also delete the vector index and downloaded Ollama model, if you want a truly clean slate next time).

Note: like every other project's backend, this one also publishes port 8000 (and now 11434 for Ollama too) — don't run another project's backend at the same time without changing ports.
