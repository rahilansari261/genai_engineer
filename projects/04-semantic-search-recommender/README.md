# 04 — Semantic Search & Recommender

One embedding index over a small dataset (your own notes, or a sample product catalog), driving three different features: search, "find similar," and outlier detection.

## What problem does this solve?

Keyword search fails in an obvious, familiar way: search "puppy training" and it won't find a note titled "how to raise a dog," even though a human instantly sees they're related. "Embeddings" is the roadmap's answer to that, but the word stays abstract until you've searched by *meaning* yourself and watched it work where keyword search would've failed. It's also easy to think semantic search, recommendations, and anomaly detection are three separate technologies — this project builds them on the exact same embedding index, so you see firsthand that they're really one idea (measure distance between vectors) applied three different ways.

## What you'll learn

- **What are Embeddings** — turn text into vectors and actually look at what "similar" means geometrically (cosine distance between two real embeddings you compute yourself)
- **Use Cases for Embeddings — Semantic Search, Recommendation Systems, Anomaly Detection, Data Classification** — one shared index, three different queries against it, so the *use case* is what differs, not the underlying tech
- **OpenAI Embeddings API / Pricing Considerations** — call it directly, see the cost per embedding at scale
- **Open-Source Embeddings — Sentence Transformers** — swap in a free local embedding model and compare quality/speed against OpenAI's
- **Vector Databases — Purpose and Functionality, Indexing Embeddings, Performing Similarity Search** — Chroma or LanceDB, running locally, no account needed

## Builds on

Nothing directly, but this is the first project that introduces embeddings + vector DB — everything from Project 5 onward depends on what you build here.

## Tech stack

Python/FastAPI backend (Chroma running embedded/local, `sentence-transformers`, OpenAI Embeddings API), Next.js/TypeScript frontend for search, browsing, and anomaly detection.

## How it works, in one picture

```
  data/notes.json (50 short personal notes across 8 topics, plus 2 deliberate outliers)
        |
        v
  ingest.py  --embed_local()--> Sentence Transformers -->  Chroma collection "notes_local"   (free, always built)
             --embed_openai()-> OpenAI Embeddings API  -->  Chroma collection "notes_openai"  (only if OPENAI_API_KEY set)
        |
        v
  main.py's endpoints all do the SAME underlying thing — "find nearest vectors" — for three
  different jobs:
    POST /search       embed your query,        then find nearest items    (semantic search)
    GET  /similar/{id} look up an item's vector, then find nearest items   (recommendations)
    GET  /anomalies     compute the centroid,     then find FURTHEST items  (anomaly detection)
```

Every code file has big comments explaining what it does and why. Read `backend/embeddings.py` and `backend/vector_store.py` first — together they're the whole idea of this project. Then `backend/anomaly.py`, which is surprisingly short for what it does.

## What you'll build

- `ingest.py` — a standalone script that embeds all 50 notes and builds one or two Chroma collections (local always, OpenAI if you add a key)
- A **search** tab: type a query, and see semantic results next to a plain keyword-search baseline, side by side, on the exact same data — the default query "raising a well-mannered canine companion" shares essentially no words with the note about raising a puppy, so keyword search scores it 0 (and instead surfaces an unrelated gardening note that happens to contain the word "companion"), while semantic search ranks the puppy note first by meaning
- A **browse & similar** tab: every note listed, with a "Find similar" button that runs the recommendation-via-nearest-neighbors pattern on whichever note you pick
- An **anomalies** tab: one click to rank every note by how far it sits from its own nearest neighbors (see `backend/anomaly.py`) — the two deliberately unrelated notes in the dataset (a typewriter restoration note, a choir rehearsal note) reliably land in the top 5, right alongside a couple of perfectly ordinary notes that just happen to use unusually specific vocabulary (a Roth IRA explanation, a database index explanation). That mix is real, not a bug to hide — it's the actual lesson: this technique measures "how isolated is this point in embedding space", which correlates with "genuinely off-topic" but isn't identical to it. We tried the more obvious approach first (distance from the dataset's average vector) and it did *worse* — it surfaced only vocabulary-distinctive notes and missed both real outliers entirely. `anomaly.py`'s comments walk through why
- A switch between the free local index and the paid OpenAI index (if you've added a key), so you can compare result quality directly on identical data

## Stretch goals

- Swap in your own notes (edit `data/notes.json`, re-run `python ingest.py`) — the whole app works on any short-text dataset
- Try Qdrant or LanceDB instead of Chroma for one index and compare how much of `vector_store.py` actually has to change
- Add a 4th "classification" tab: given a new note, find its nearest neighbor and use *that* note's category as a predicted label — a minimal working classifier built from nothing but embeddings

## Setup & run

### 1. Set up and build the index (Terminal 1, one-time step)

```bash
cd projects/04-semantic-search-recommender/backend

python -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# OPENAI_API_KEY is optional — add it to also build the paid comparison
# index; without it, you still get the full app on the free local index.
cp .env.example .env

# Builds the vector index(es) from data/notes.json. Re-run this any time
# you edit notes.json, or to build the OpenAI index after adding a key.
python ingest.py
```

You should see progress printed for each embedder, ending with an item count for each collection that got built.

### 2. Run the backend (same terminal)

```bash
uvicorn main:app --reload --port 8000
```

Check it worked: [http://localhost:8000/health](http://localhost:8000/health) should show `{"status":"ok"}`.

### 3. Run the frontend (Terminal 2)

```bash
cd projects/04-semantic-search-recommender/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) — the local index should already show as available and indexed.

### 4. To stop everything

`Ctrl+C` in both terminals.

Note: this project's backend also defaults to port 8000. Don't run it at the same time as another project's backend without changing one of their ports (`uvicorn main:app --port 8030`, and update that project's frontend `.env.local` to match).
