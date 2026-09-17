"""
============================================================================
 VECTOR STORE — Chroma (local, default) aur Pinecone (managed cloud, optional)
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh roadmap wala "storage backend ko bina kuch aur badle swap karo" wala
lesson hai, asal mein implement kiya hua: do bilkul alag vector
databases — ek tumhare machine par local files ke roop mein chal raha hai,
doosra ek hosted cloud service ke roop mein — dono bilkul same teen
functions (`upsert`, `search`, `count`) ke through expose kiye gaye hain.
rag_raw.py ka RAG pipeline in functions ko call karta hai bina yeh pareshan
hue ki peeche asal mein kaunsa database hai.

**Chroma** embedded, in-process chalta hai, `chroma_data/` mein likhta
hai — Project 4 wala hi approach, bas ek collection ke saath kyunki yeh
project ek single, fixed embedding model use karta hai.

**Pinecone** ek managed, hosted vector database hai — koi local process
hai hi nahi, har upsert aur query Pinecone ke servers ko ek network
request hoti hai. Yeh yahan poori tarah optional hai: `PINECONE_API_KEY`
ke bina, app free local Chroma index par poori tarah kaam karta hai, aur
sirf UI mein "cloud" wala option unavailable dikhta hai — is repo ke har
provider key jaisa hi graceful-degradation pattern follow karte hue.

Ek quirk jo explicitly jaanna zaroori hai: Chroma COSINE DISTANCE report
karta hai (0 = identical, jitna bada utna kam similar), lekin Pinecone
ka cosine metric iske ulat COSINE SIMILARITY report karta hai (1 =
identical, jitna chhota utna kam similar) — bilkul opposite direction.
Yeh file Pinecone ki similarity ko distance mein convert kar deti hai
(`1 - similarity`) return karne se pehle, sirf isliye taaki baaki app —
aur UI — "distance" ka matlab hamesha same treat kar sake, chahe query ka
jawab kisi bhi backend ne diya ho.
============================================================================
"""

import os

# --------------------------------------------------------------------------
# Chroma (local, default)
# --------------------------------------------------------------------------
import chromadb

_CHROMA_DATA_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
_chroma_client = None


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=_CHROMA_DATA_DIR)
    return _chroma_client


def _get_chroma_collection(collection_name: str):
    return _get_chroma_client().get_or_create_collection(
        name=collection_name, metadata={"hnsw:space": "cosine"}
    )


def chroma_upsert(collection_name: str, ids: list[str], embeddings: list[list[float]], items: list[dict]) -> None:
    collection = _get_chroma_collection(collection_name)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=[item["text"] for item in items],
        metadatas=[{"source": item["source"]} for item in items],
    )


def chroma_search(collection_name: str, query_embedding: list[float], top_k: int) -> list[dict]:
    collection = _get_chroma_collection(collection_name)
    if collection.count() == 0:
        return []
    result = collection.query(
        query_embeddings=[query_embedding], n_results=top_k, include=["documents", "metadatas", "distances"]
    )
    return [
        {"id": id_, "text": doc, "source": meta["source"], "distance": dist}
        for id_, doc, meta, dist in zip(
            result["ids"][0], result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]


def chroma_count(collection_name: str) -> int:
    return _get_chroma_collection(collection_name).count()


# --------------------------------------------------------------------------
# Pinecone (managed cloud, optional)
# --------------------------------------------------------------------------

_pinecone_client = None


def pinecone_available() -> bool:
    return bool(os.getenv("PINECONE_API_KEY"))


def _get_pinecone_client():
    global _pinecone_client
    if _pinecone_client is None:
        from pinecone import Pinecone

        _pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return _pinecone_client


def _get_pinecone_index(index_name: str, dimension: int):
    """Pehli baar use hone par, agar index exist nahi karta to usko create
    kar deta hai — Pinecone ko vector dimension pehle se pata hona chahiye,
    isliye yeh function ek dimension parameter leta hai (embeddings.py ka
    EMBEDDING_DIMENSIONS dekho)."""
    pc = _get_pinecone_client()
    if not pc.has_index(index_name):
        from pinecone import ServerlessSpec

        pc.create_index(
            name=index_name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
    return pc.Index(name=index_name)


def pinecone_upsert(index_name: str, ids: list[str], embeddings: list[list[float]], items: list[dict], dimension: int) -> None:
    index = _get_pinecone_index(index_name, dimension)
    vectors = [
        {"id": id_, "values": emb, "metadata": {"text": item["text"], "source": item["source"]}}
        for id_, emb, item in zip(ids, embeddings, items)
    ]
    index.upsert(vectors=vectors)


def pinecone_search(index_name: str, query_embedding: list[float], top_k: int, dimension: int) -> list[dict]:
    index = _get_pinecone_index(index_name, dimension)
    result = index.query(vector=query_embedding, top_k=top_k, include_metadata=True)
    return [
        {
            "id": match["id"],
            "text": match["metadata"]["text"],
            "source": match["metadata"]["source"],
            # Pinecone ka cosine metric SIMILARITY return karta hai (jitna
            # zyada, utna close); isko DISTANCE mein flip karo (jitna kam,
            # utna close) taaki Chroma ke convention se match kare — isko
            # kyun kiya, uske liye is file ka top comment dekho.
            "distance": 1 - match["score"],
        }
        for match in result["matches"]
    ]


def pinecone_count(index_name: str, dimension: int) -> int:
    index = _get_pinecone_index(index_name, dimension)
    stats = index.describe_index_stats()
    return stats.get("total_vector_count", 0)
