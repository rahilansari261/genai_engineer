"""
============================================================================
 RAG CHATBOT API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Ek hi asli endpoint, `POST /ask`, jo ek question ko route karta hai jo bhi
combination tumne choose kiya ho uske hisaab se: `raw` pipeline
(rag_raw.py) ya `langchain` pipeline (rag_langchain.py), aur — sirf raw
pipeline ke liye — jo bhi vector store backend (local Chroma ya managed
Pinecone). Har combination SAME question ka jawab SAME documents par se
deta hai, isliye jo response differences tumhe dikhte hain woh genuinely
pipeline ke baare mein hote hain, alag data ke baare mein nahi.

`GET /status` isliye hai taaki frontend un options ko grey out kar sake jo
abhi tak index nahi hue (ya, Pinecone ke case mein, configured hi nahi
hain) — isse tum aisa combination select hi nahi kar paoge jo sirf fail
ho sakta hai.
============================================================================
"""

import time
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()
import rag_langchain
import rag_raw
import vector_store
from docs_loader import load_docs


app = FastAPI(title="RAG Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str
    pipeline: str = "raw"  # "raw" | "langchain"
    vector_store: str = "chroma"  # "chroma" | "pinecone" — sirf tab use hota hai jab pipeline == "raw"
    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    top_k: int = 4


class Source(BaseModel):
    source: str
    snippet: str
    distance: float


class AskResponse(BaseModel):
    answer: Optional[str] = None
    sources: List[Source] = []
    error: Optional[str] = None
    pipeline: str
    vector_store: str
    latency_ms: int


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    start = time.perf_counter()

    if req.pipeline == "langchain":
        result = await rag_langchain.answer(req.question, req.llm_provider, req.llm_model, req.top_k)
    else:
        result = await rag_raw.answer(
            req.question, req.llm_provider, req.llm_model, req.top_k, vector_store_backend=req.vector_store
        )

    latency_ms = int((time.perf_counter() - start) * 1000)

    return AskResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
        error=result["error"],
        pipeline=req.pipeline,
        vector_store=req.vector_store if req.pipeline == "raw" else "chroma",
        latency_ms=latency_ms,
    )


class IndexStatus(BaseModel):
    available: bool
    indexed: bool
    count: int


class StatusResponse(BaseModel):
    raw_chroma: IndexStatus
    raw_pinecone: IndexStatus
    langchain_chroma: IndexStatus


@app.get("/status", response_model=StatusResponse)
async def status():
    raw_chroma_count = vector_store.chroma_count(rag_raw.CHROMA_COLLECTION)
    langchain_chroma_count = vector_store.chroma_count(rag_langchain.CHROMA_COLLECTION)

    pinecone_ok = vector_store.pinecone_available()
    raw_pinecone_count = 0
    if pinecone_ok:
        try:
            raw_pinecone_count = vector_store.pinecone_count(rag_raw.PINECONE_INDEX, 384)
        except Exception:
            raw_pinecone_count = 0

    return StatusResponse(
        raw_chroma=IndexStatus(available=True, indexed=raw_chroma_count > 0, count=raw_chroma_count),
        raw_pinecone=IndexStatus(available=pinecone_ok, indexed=raw_pinecone_count > 0, count=raw_pinecone_count),
        langchain_chroma=IndexStatus(available=True, indexed=langchain_chroma_count > 0, count=langchain_chroma_count),
    )


@app.get("/corpus")
async def corpus():
    # Jaan-bujh kar "/docs" naam nahi rakha — FastAPI us path ko apne
    # auto-generated Swagger UI ke liye reserve karta hai (khud visit karo
    # http://localhost:8000/docs par), aur tumhara define kiya hua route
    # usko override nahi karta.
    return {"docs": [d["source"] for d in load_docs()]}


@app.get("/health")
async def health():
    return {"status": "ok"}
