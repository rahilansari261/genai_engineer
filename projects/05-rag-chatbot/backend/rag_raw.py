"""
============================================================================
 RAG RAW — poora pipeline, haath se bana hua, koi framework nahi
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh RAG hai jisme har step plain Python mein likh diya gaya hai: docs ko
chunk karo (chunking.py), chunks ko embed karo (embeddings.py), unko ek
vector database mein store karo (vector_store.py — Chroma ya Pinecone,
tumhari marzi), aur query time par, question ko embed karo, sabse close
chunks retrieve karo, aur unko ek LLM (llm.py) ko de do answer generate
karne ke liye. Yahan kuch bhi framework ke peeche chhupa hua nahi hai —
is pipeline ki har line aisi cheez hai jispar tum ungli rakh ke explain
kar sakte ho. Isko rag_langchain.py se compare karo, jo bilkul wahi kaam
LangChain use karke karta hai.
============================================================================
"""

import embeddings
import llm
import vector_store
from docs_loader import load_docs

CHROMA_COLLECTION = "docs_raw"
PINECONE_INDEX = "ai-engineer-rag-raw"


def ingest(chunk_size: int = 800, chunk_overlap: int = 100, vector_store_backend: str = "chroma") -> dict:
    """Har doc ko chunk karta hai, har chunk ko embed karta hai, aur unko
    store karta hai. Ek chhota sa summary dict return karta hai taaki
    ingest.py (ya koi API endpoint) yeh report kar sake ki kya hua, is
    function ke andar se directly print karne ki jagah."""
    from chunking import split_text

    docs = load_docs()

    ids: list[str] = []
    items: list[dict] = []
    for doc in docs:
        chunks = split_text(doc["text"], chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        for i, chunk in enumerate(chunks):
            ids.append(f"{doc['source']}::{i}")
            items.append({"text": chunk, "source": doc["source"]})

    vectors = embeddings.embed([item["text"] for item in items])

    if vector_store_backend == "pinecone":
        vector_store.pinecone_upsert(PINECONE_INDEX, ids, vectors, items, embeddings.EMBEDDING_DIMENSIONS)
    else:
        vector_store.chroma_upsert(CHROMA_COLLECTION, ids, vectors, items)

    return {"docs": len(docs), "chunks": len(items), "backend": vector_store_backend}


async def answer(question: str, llm_provider: str, llm_model: str, top_k: int = 4, vector_store_backend: str = "chroma") -> dict:
    """Ek question ke liye poora raw pipeline chalata hai: embed -> retrieve -> generate."""
    query_vector = embeddings.embed([question])[0]

    if vector_store_backend == "pinecone":
        results = vector_store.pinecone_search(PINECONE_INDEX, query_vector, top_k, embeddings.EMBEDDING_DIMENSIONS)
    else:
        results = vector_store.chroma_search(CHROMA_COLLECTION, query_vector, top_k)

    if not results:
        return {
            "answer": None,
            "sources": [],
            "error": "No chunks indexed yet — run ingest.py first (see the project README).",
        }

    chunk_texts = [r["text"] for r in results]
    try:
        answer_text = await llm.generate(llm_provider, llm_model, question, chunk_texts)
    except Exception as exc:
        # Retrieval ho gaya, lekin generation fail ho gaya (galat key, model
        # pull nahi kiya hua, etc.) — phir bhi jo sources mile hain wo
        # return karo, taaki UI "in sources se hum yeh answer dete" wala
        # kuch dikha sake, error ke saath saath.
        return {
            "answer": None,
            "sources": [{"source": r["source"], "snippet": r["text"][:220], "distance": r["distance"]} for r in results],
            "error": str(exc),
        }

    return {
        "answer": answer_text,
        "sources": [{"source": r["source"], "snippet": r["text"][:220], "distance": r["distance"]} for r in results],
        "error": None,
    }
