"""
============================================================================
 INGEST — data/notes.json se vector index(es) banata hai
============================================================================
Yeh script kya karta hai, seedhi bhasha mein:

Yeh ek ONE-TIME (waise, jab bhi data change ho tab run karo) setup step
hai, terminal se haath se run kiya jaata hai — web server har request pe
yeh nahi karta. Yeh data/notes.json ke 50 notes ko padhta hai, har ek ko
ek embedding vector mein badalta hai, aur un vectors ko Chroma mein store
karta hai taaki main.py ke API endpoints ke paas search karne ke liye
kuch ho.

Yeh hamesha FREE local index banata hai (Sentence Transformers — koi API
key nahi chahiye). Yeh OpenAI index tabhi banata hai jab OPENAI_API_KEY
set ho, kyunki uspe chalane mein thoda sa real paisa lagta hai (pricing.py
dekho) — tum key add karke isme khud opt-in karte ho, yeh chupke se nahi
hota.

Isko is tarah run karo: `python ingest.py`, backend/ ke andar se, venv
active rakh ke. Har embedder ke liye progress print hote hue dikhna
chahiye jaise yeh chalta hai.
============================================================================
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from embeddings import embed_local, embed_openai
from pricing import estimate_embedding_cost
from vector_store import upsert_items

load_dotenv()

DATA_PATH = Path(__file__).parent / "data" / "notes.json"


def load_notes() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)


def ingest_local(notes: list[dict]) -> None:
    print(f"[local] embedding {len(notes)} notes with Sentence Transformers (first run downloads the model)...")
    vectors = embed_local([n["text"] for n in notes])
    upsert_items("local", [n["id"] for n in notes], vectors, notes)
    print(f"[local] done — {len(notes)} items indexed in the 'notes_local' collection.")


def ingest_openai(notes: list[dict]) -> None:
    if not os.getenv("OPENAI_API_KEY"):
        print("[openai] skipped — no OPENAI_API_KEY set in backend/.env")
        return

    print(f"[openai] embedding {len(notes)} notes via the OpenAI Embeddings API...")
    vectors = embed_openai([n["text"] for n in notes])
    upsert_items("openai", [n["id"] for n in notes], vectors, notes)

    # Ek rough token estimate (English mein roughly 4 characters ek token
    # ke barabar) bas ek ballpark cost dikhane ke liye — "kya yeh basically
    # free hai" janne ke liye kaafi hai, ek real bill jitna precise nahi.
    approx_tokens = sum(len(n["text"]) for n in notes) // 4
    print(
        f"[openai] done — {len(notes)} items indexed in the 'notes_openai' collection "
        f"(~{approx_tokens} tokens, roughly ${estimate_embedding_cost(approx_tokens):.6f})."
    )


if __name__ == "__main__":
    notes = load_notes()
    print(f"Loaded {len(notes)} notes from {DATA_PATH}\n")
    ingest_local(notes)
    print()
    ingest_openai(notes)
