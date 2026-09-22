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

Python/FastAPI backend (a hand-rolled pipeline and a LangChain pipeline, side by side), Chroma (local) with an optional Pinecone (managed cloud) backend for the hand-rolled pipeline, Next.js chat UI with inline source citations. Same setup as Projects 1-4: a Python venv for the backend, Ollama installed natively on your machine, `npm run dev` for the frontend.

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

You need [Ollama](https://ollama.com) installed and running on your machine (it listens on `localhost:11434` by default), with a model pulled:

```bash
ollama pull llama3.2
```

### 1. Set up and build the indexes (Terminal 1, one-time step)

```bash
cd projects/05-rag-chatbot/backend

python3 -m venv .venv            # on Windows: python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt  # inside the venv, plain `python` and `pip` work

# All keys optional — the app runs fully on the free local Chroma index +
# Ollama with nothing filled in here at all.
cp .env.example .env

# Builds the vector indexes from docs/*.md. Re-run this any time you edit
# a doc in docs/.
python ingest.py
```

First run takes a while — `pip install` pulls in `torch`, `chromadb`, and `langchain`, and `ingest.py` downloads the embedding model (skipped if you already ran Project 4, which uses the same one). You should see a chunk count printed for the raw pipeline's Chroma index, the LangChain pipeline's Chroma index, and (if you added a `PINECONE_API_KEY`) the Pinecone index too.

### 2. Run the backend (same terminal)

```bash
uvicorn main:app --reload --port 8000
```

Check it worked: [http://localhost:8000/health](http://localhost:8000/health) should show `{"status":"ok"}`.

### 3. Run the frontend (Terminal 2)

```bash
cd projects/05-rag-chatbot/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — both pipelines should already show as indexed.

### 4. To stop everything

`Ctrl+C` in both terminals. The vector index lives in `backend/chroma_data/` (git-ignored) — delete that folder and re-run `python ingest.py` if you want a clean slate.

Note: this project's backend also defaults to port 8000. Don't run it at the same time as another project's backend without changing one of their ports (`uvicorn main:app --port 8030`, and update the frontend's `.env.local` to match).
