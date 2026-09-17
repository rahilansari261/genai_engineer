"""
Ek single local Chroma collection — yeh project vector stores compare nahi
karta (woh Project 5 tha), isko bas `search_handbook` tool ke liye search
karne ke liye KAHIN chahiye. Vector database kya karta hai aur yahan cosine
distance kyun use kiya gaya hai, iska fuller explanation Project 4/5 ke
vector_store.py mein dekho.
"""

import os

import chromadb

_DATA_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")
_client = None
COLLECTION_NAME = "handbook"


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=_DATA_DIR)
    return _client


def _get_collection():
    return _get_client().get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def upsert(ids: list[str], embeddings: list[list[float]], items: list[dict]) -> None:
    _get_collection().upsert(
        ids=ids,
        embeddings=embeddings,
        documents=[item["text"] for item in items],
        metadatas=[{"source": item["source"]} for item in items],
    )


def search(query_embedding: list[float], top_k: int) -> list[dict]:
    collection = _get_collection()
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


def count() -> int:
    return _get_collection().count()
