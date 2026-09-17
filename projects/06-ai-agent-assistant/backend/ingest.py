"""docs/*.md se handbook ka search index banata hai. `python ingest.py`
se run karo (backend container ke andar) ek baar, ya kisi doc ko edit
karne ke baad dobara. Naive paragraph split ke bajaye Project 5 wala hi
chunking.py splitter use karta hai (chunk_size=800, chunk_overlap=100) —
yeh yahan specifically kyun matter karta hai iske liye chunking.py ka file
comment dekho: ek naive splitter ne testing ke waqt search_handbook tool
ko heading-only fragments de diye the, aur agent ne unse ek answer
hallucinate kar diya tha."""

from chunking import split_text
from docs_loader import load_docs
from embeddings import embed
from vector_store import upsert

if __name__ == "__main__":
    docs = load_docs()

    ids, items = [], []
    for doc in docs:
        for i, chunk_text in enumerate(split_text(doc["text"], chunk_size=800, chunk_overlap=100)):
            ids.append(f"{doc['source']}::{i}")
            items.append({"text": chunk_text, "source": doc["source"]})

    vectors = embed([item["text"] for item in items])
    upsert(ids, vectors, items)

    print(f"Indexed {len(docs)} docs -> {len(items)} chunks in the 'handbook' collection.")
