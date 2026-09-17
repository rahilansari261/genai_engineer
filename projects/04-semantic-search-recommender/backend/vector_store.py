"""
============================================================================
 VECTOR STORE — Chroma, hamare local vector database, ke around ek thin wrapper
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Ek "vector database" specifically ek sawaal ko fast jawab dene ke liye
bana hota hai, chahe entries millions mein kyun na ho: "kaunse stored
vectors is vector ke sabse close hain?" Ek normal SQL database ke paas
iska koi efficient jawab nahi hai — usko tumhari query ko har single row
ke against compare karna padega. Chroma (aur generally vector DBs) pehle
se hi ek special index bana ke rakhte hain jo "nearest neighbors dhoondo"
ko fast bana deta hai.

Hum `chromadb.PersistentClient` use kar rahe hain, jo Chroma ko IN-PROCESS
chalata hai — koi alag database server install ya run nahi karna padta,
yeh bas ek local folder (`chroma_data/`, isi file ke bagal mein banta
hai) mein files padhta aur likhta hai. Isi wajah se yeh ek learning
project ke liye achha free/local choice hai: zero signup, zero
infrastructure, aur phir bhi yeh wahi approximate-nearest-neighbor
indexing (HNSW) use karta hai jo ek hosted vector DB andar se use karta
hai.

Hum har embedder ke liye ek ALAG collection rakhte hain ("notes_local",
"notes_openai"), ek shared collection ke bajaye, kyunki alag-alag models
se aayi embeddings ek doosre se comparable nahi hotin — ek OpenAI vector
aur ek Sentence Transformers vector ke beech nikali gayi distance
bemani (meaningless) hogi.
============================================================================
"""

import os

import chromadb

_DATA_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=_DATA_DIR)
    return _client


def get_collection(embedder: str):
    """
    Ek embedder ke liye Chroma collection return karta hai (zaroorat
    padne par bana bhi deta hai). `metadata={"hnsw:space": "cosine"}`
    Chroma ko batata hai ki results ko uske default (squared Euclidean)
    ke bajaye COSINE distance se rank kare — text embeddings ke liye
    cosine standard choice hai, aur isi wajah se "distance" ka 0 hona
    "identical meaning" ka matlab hota hai aur bade numbers ka matlab
    "less similar" — yehi assumption is project ke baaki code (aur
    frontend) mein use hoti hai.
    """
    client = _get_client()
    return client.get_or_create_collection(name=f"notes_{embedder}", metadata={"hnsw:space": "cosine"})


def upsert_items(embedder: str, ids: list[str], embeddings: list[list[float]], items: list[dict]) -> None:
    """Items ko ek embedder ki collection mein add karta hai (ya overwrite,
    agar ids pehle se exist karte hain).

    Deliberately `.upsert()` call kiya hai, `.add()` nahi — Chroma ka
    `.add()` kisi bhi existing id ko chupchap SKIP kar deta hai, update
    karne ke bajaye, jisse `python ingest.py` ko dusri baar run karne par
    (jaise data/notes.json edit karne ke baad) yeh ek no-op ban jaata.
    `.upsert()` "insert or update" wala version hai.
    """
    collection = get_collection(embedder)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=[item["text"] for item in items],
        metadatas=[{"category": item["category"]} for item in items],
    )


def search(embedder: str, query_embedding: list[float], top_k: int) -> list[dict]:
    """Core "is vector ke nearest neighbors dhoondo" operation — semantic
    search ke liye use hota hai (query embedding typed text se aata hai)
    aur "more like this" ke liye bhi (query embedding kisi existing item
    se aata hai)."""
    collection = get_collection(embedder)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
    # Chroma ka result shape ek saath MULTIPLE queries batch karne ko
    # support karta hai — har field ek list of lists hoti hai, har query
    # ke liye ek inner list. Hum hamesha ek time par sirf ek hi query
    # embedding bhejte hain, isliye hamesha `[0]` se unwrap karte hain.
    return [
        {"id": id_, "text": doc, "category": meta["category"], "distance": dist}
        for id_, doc, meta, dist in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


def get_all(embedder: str) -> list[dict]:
    """Ek embedder ki collection ka har item return karta hai, uski
    embedding vector ke SAATH — anomaly detection ke liye zaroori hai,
    jisko unka shared centroid compute karne ke liye ek saath har vector
    ko dekhna padta hai (anomaly.py dekho)."""
    collection = get_collection(embedder)
    result = collection.get(include=["embeddings", "documents", "metadatas"])
    return [
        {"id": id_, "text": doc, "category": meta["category"], "embedding": emb}
        for id_, doc, meta, emb in zip(
            result["ids"], result["documents"], result["metadatas"], result["embeddings"]
        )
    ]


def count(embedder: str) -> int:
    return get_collection(embedder).count()
