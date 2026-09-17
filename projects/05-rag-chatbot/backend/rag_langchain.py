"""
============================================================================
 RAG LANGCHAIN — bilkul wahi pipeline, bas ek framework ke saath banaya gaya
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Kaam bilkul rag_raw.py jaisa hi hai — chunk, embed, store, retrieve,
generate — lekin hand-written code ki jagah LangChain ke building blocks
use karke: chunking.py ki jagah `RecursiveCharacterTextSplitter`,
vector_store.py ki manual Chroma calls ki jagah LangChain ka `Chroma`
vectorstore wrapper, aur llm.py ki manual prompt-building ki jagah ek
chhota sa LCEL chain (`prompt | llm | output_parser`, LangChain ka
`|`-based composition syntax).

Yeh file rag_raw.py ke turant baad padho. Interesting question yeh nahi
hai ki "kaunsa better hai" — balki yeh hai ki "framework ne asal mein kya
save kiya, aur kya mujhse chhupa diya?" Yahan orchestration code ki lines
kam hain, lekin cost yeh hai ki tumhe plain Python data structures ki
jagah LangChain ke apne abstractions (Documents, Runnables, output
parsers) samajhne padenge.

Sirf Ollama aur OpenAI generation ke liye support karta hai (Anthropic
nahi, rag_raw.py ke ulat) — yeh jaan-bujh kar scope kam kiya gaya hai,
taaki sirf isi comparison ke liye ek aur framework integration package
(`langchain-anthropic`) na khinchna pade; neeche wale OpenAI branch jaisa
hi pattern follow karke isko wire karna ek reasonable stretch goal hai.
============================================================================
"""

import os

import chromadb
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

import embeddings as shared_embeddings
from docs_loader import load_docs

CHROMA_COLLECTION = "docs_langchain"
CHROMA_DATA_DIR = os.path.join(os.path.dirname(__file__), "chroma_data")


class SharedEmbeddings(Embeddings):
    """Hamare apne embeddings.embed() function (Sentence Transformers) ko
    wrap karta hai taaki LangChain ke Embeddings interface ko satisfy kare.
    Iska matlab hai ki LangChain pipeline EXACT wahi embedding model use
    karta hai jo raw pipeline use karta hai — fair comparison ke liye yeh
    kyun matter karta hai, uske liye embeddings.py ka file comment dekho."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return shared_embeddings.embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return shared_embeddings.embed([text])[0]


def _get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=CHROMA_COLLECTION,
        embedding_function=SharedEmbeddings(),
        persist_directory=CHROMA_DATA_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )


def _get_chat_model(provider: str, model: str):
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return ChatOllama(model=model, base_url=host)

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model, api_key=api_key)

    raise RuntimeError(f"unknown provider '{provider}' (the LangChain pipeline supports ollama and openai only)")


def ingest(chunk_size: int = 800, chunk_overlap: int = 100) -> dict:
    docs = load_docs()

    # LangChain ka apna recursive splitter — chunking.py jaisi hi
    # chunk_size/chunk_overlap settings, taaki resulting chunks mein jo bhi
    # difference aaye woh SPLITTING LOGIC ki wajah se ho, alag settings ki
    # wajah se nahi.
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    texts, metadatas, ids = [], [], []
    for doc in docs:
        for i, chunk in enumerate(splitter.split_text(doc["text"])):
            texts.append(chunk)
            metadatas.append({"source": doc["source"]})
            ids.append(f"{doc['source']}::{i}")

    # Har ingest run par collection ko scratch se rebuild karo, taaki koi
    # doc edit karke isko re-run karne par purane, stale chunks peeche na
    # reh jaayein. (vector_store.py ke chroma_upsert ke ulat, LangChain ka
    # Chroma wrapper humein waisa hi explicit upsert-by-id guarantee nahi
    # deta, isliye clean rebuild hi isko idempotent rakhne ka sabse simple
    # tareeka hai.)
    client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
    try:
        client.delete_collection(CHROMA_COLLECTION)
    except Exception:
        pass  # pehli run par collection abhi tha hi nahi — delete karne ko kuch nahi tha

    Chroma.from_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
        embedding=SharedEmbeddings(),
        collection_name=CHROMA_COLLECTION,
        persist_directory=CHROMA_DATA_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )

    return {"docs": len(docs), "chunks": len(texts)}


async def answer(question: str, llm_provider: str, llm_model: str, top_k: int = 4) -> dict:
    import vector_store  # yahan sirf iska count() helper use karne ke liye, neeche dekho

    if vector_store.chroma_count(CHROMA_COLLECTION) == 0:
        return {"answer": None, "sources": [], "error": "No chunks indexed yet — run ingest.py first (see the project README)."}

    vectorstore = _get_vectorstore()
    # LangChain ka retrieval call, ek hi line mein — yeh comparison ka wahi
    # "SDK tumhare liye kar deta hai" wala side hai, rag_raw.py ke
    # embed-then-search ke against.
    results = vectorstore.similarity_search_with_score(question, k=top_k)

    sources = [
        {"source": doc.metadata["source"], "snippet": doc.page_content[:220], "distance": score}
        for doc, score in results
    ]

    try:
        llm = _get_chat_model(llm_provider, llm_model)
    except Exception as exc:
        return {"answer": None, "sources": sources, "error": str(exc)}

    # LCEL: LangChain ka `|`-based composition. Yeh ek hi expression ek
    # prompt template, ek chat model, aur ek output parser ko ek runnable
    # pipeline mein wire kar deta hai — isko compare karo raw pipeline ke
    # llm.py wale plain `build_prompt()` + direct provider call se.
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Answer the question using ONLY the context below. If the context doesn't "
                "contain enough information to answer, say so plainly instead of guessing.",
            ),
            ("human", "Context:\n{context}\n\nQuestion: {question}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()

    context = "\n\n---\n\n".join(doc.page_content for doc, _ in results)
    try:
        answer_text = await chain.ainvoke({"context": context, "question": question})
    except Exception as exc:
        return {"answer": None, "sources": sources, "error": str(exc)}

    return {"answer": answer_text, "sources": sources, "error": None}
