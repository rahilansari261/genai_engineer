"""
============================================================================
 SEMANTIC SEARCH & RECOMMENDER API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yahan har endpoint ek ALAG sawaal ka jawab deta hai, lekin sab ke sab
exact same underlying operation par tike hain: "ek vector diya hai, index
mein sabse nearest wale dhoondo" (ya, anomalies ke liye, "ek specific
vector — centroid — se sabse FURTHEST wale dhoondo"). Yeh reuse hi is
poore project ka point hai: semantic search, recommendations, aur anomaly
detection — teeno ek hi embedding index se poochhe gaye teen sawaal hain,
teen alag systems nahi.

  POST /search        -> query ko embed karo, index search karo, aur
                          comparison ke liye usi data par ek plain
                          keyword search bhi chalao (keyword_search.py
                          dekho)
  GET  /similar/{id}   -> kisi existing item ki apni embedding dekho,
                          phir USKO query bana ke index search karo
  GET  /anomalies      -> har embedding ka centroid compute karo, har
                          item ko usse distance ke hisaab se rank karo
                          (anomaly.py dekho)
  GET  /items          -> bas sab kuch list karta hai, "browse" UI ke liye
  GET  /embedders      -> kaunse embedders exist karte hain aur woh
                          actually indexed hain ya nahi (matlab tumne
                          ingest.py run kiya ya nahi)

Inme se koi bhi endpoint khud index nahi banata — woh tabhi hota hai jab
tum haath se `python ingest.py` run karte ho. Agar abhi tak run nahi
kiya, to yeh endpoints ek empty index par crash hone ke bajaye ek clear
error return karte hain.
============================================================================
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import keyword_search
import vector_store
from anomaly import find_anomalies
from embeddings import embed_local, embed_openai

load_dotenv()

app = FastAPI(title="Semantic Search & Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

EMBED_FUNCS = {"local": embed_local, "openai": embed_openai}


def _not_indexed_error(embedder: str) -> str:
    return (
        f"The '{embedder}' index is empty — run `python ingest.py` in the backend "
        "folder first (see the project README)."
    )


class EmbedderInfo(BaseModel):
    id: str
    label: str
    available: bool
    indexed: bool
    count: int


@app.get("/embedders", response_model=List[EmbedderInfo])
async def list_embedders():
    local_count = vector_store.count("local")
    openai_available = bool(os.getenv("OPENAI_API_KEY"))
    openai_count = vector_store.count("openai") if openai_available else 0

    return [
        EmbedderInfo(id="local", label="Local (Sentence Transformers)", available=True, indexed=local_count > 0, count=local_count),
        EmbedderInfo(id="openai", label="OpenAI Embeddings", available=openai_available, indexed=openai_count > 0, count=openai_count),
    ]


class SearchRequest(BaseModel):
    query: str
    embedder: str = "local"
    top_k: int = 5


class ScoredItem(BaseModel):
    id: str
    text: str
    category: str
    distance: float


class KeywordMatch(BaseModel):
    id: str
    text: str
    category: str
    score: int


class SearchResponse(BaseModel):
    semantic: List[ScoredItem] = []
    keyword: List[KeywordMatch] = []
    error: Optional[str] = None


@app.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    if vector_store.count(req.embedder) == 0:
        return SearchResponse(error=_not_indexed_error(req.embedder))

    embed_fn = EMBED_FUNCS.get(req.embedder)
    if embed_fn is None:
        return SearchResponse(error=f"unknown embedder '{req.embedder}'")

    try:
        query_vector = embed_fn([req.query])[0]
    except Exception as exc:
        return SearchResponse(error=str(exc))

    semantic_results = vector_store.search(req.embedder, query_vector, req.top_k)

    # Keyword baseline har item ke against chalta hai, chahe koi bhi
    # embedder active ho — yeh embeddings use hi nahi karta, isliye isme
    # "local" ya "openai" jaisa kuch hai hi nahi. Hum local collection ko
    # bas har item ke plain text ka ek convenient source samajh ke reuse
    # kar rahe hain.
    all_items = vector_store.get_all("local" if vector_store.count("local") else req.embedder)
    keyword_results = keyword_search.search(req.query, all_items, req.top_k)

    return SearchResponse(
        semantic=[ScoredItem(**r) for r in semantic_results],
        keyword=[KeywordMatch(**{k: v for k, v in r.items() if k != "embedding"}) for r in keyword_results],
    )


class SimilarResponse(BaseModel):
    results: List[ScoredItem] = []
    error: Optional[str] = None


@app.get("/similar/{item_id}", response_model=SimilarResponse)
async def similar(item_id: str, embedder: str = "local", top_k: int = 5):
    if vector_store.count(embedder) == 0:
        return SimilarResponse(error=_not_indexed_error(embedder))

    collection = vector_store.get_collection(embedder)
    found = collection.get(ids=[item_id], include=["embeddings"])
    if not found["ids"]:
        return SimilarResponse(error=f"no item with id '{item_id}' in the '{embedder}' index")

    item_vector = found["embeddings"][0]

    # Ek extra result maango, kyunki item ka nearest neighbor hamesha
    # khud hi hota hai (distance 0) — usko neeche filter karke hata denge,
    # Chroma se yeh karwane ke bajaye, kyunki Chroma ke paas "exclude this
    # id" jaisa koi option nahi hai.
    raw_results = vector_store.search(embedder, item_vector, top_k + 1)
    results = [r for r in raw_results if r["id"] != item_id][:top_k]

    return SimilarResponse(results=[ScoredItem(**r) for r in results])


class AnomaliesResponse(BaseModel):
    results: List[ScoredItem] = []
    error: Optional[str] = None


@app.get("/anomalies", response_model=AnomaliesResponse)
async def anomalies(embedder: str = "local", top_k: int = 5):
    if vector_store.count(embedder) == 0:
        return AnomaliesResponse(error=_not_indexed_error(embedder))

    all_items = vector_store.get_all(embedder)
    results = find_anomalies(all_items, top_k)
    return AnomaliesResponse(results=[ScoredItem(**r) for r in results])


class Item(BaseModel):
    id: str
    text: str
    category: str


class ItemsResponse(BaseModel):
    items: List[Item] = []


@app.get("/items", response_model=ItemsResponse)
async def items(embedder: str = "local"):
    if vector_store.count(embedder) == 0:
        return ItemsResponse(items=[])
    all_items = vector_store.get_all(embedder)
    return ItemsResponse(items=[Item(id=i["id"], text=i["text"], category=i["category"]) for i in all_items])


@app.get("/health")
async def health():
    return {"status": "ok"}
