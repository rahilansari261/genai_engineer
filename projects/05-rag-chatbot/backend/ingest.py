"""
============================================================================
 INGEST — docs/*.md se DONO pipelines ke indexes banata hai
============================================================================
`python ingest.py` se run karo (backend container ke andar, ya native
chalate ho to host wale venv se) jab bhi docs/ ki koi file edit karo, ya
project pehli baar set up kar rahe ho. Yeh teen indexes banata hai:

  1. Raw pipeline ka local Chroma collection ("docs_raw") — hamesha banta hai
  2. Raw pipeline ka Pinecone index — sirf tab jab PINECONE_API_KEY set ho
  3. LangChain pipeline ka local Chroma collection ("docs_langchain") — hamesha banta hai

Har case mein "ingest" ka asli matlab kya hai, uske liye rag_raw.py aur
rag_langchain.py dekho.
============================================================================
"""

from dotenv import load_dotenv

load_dotenv()

import rag_langchain
import rag_raw
import vector_store

if __name__ == "__main__":
    print("Ingesting for the RAW pipeline (local Chroma)...")
    summary = rag_raw.ingest(vector_store_backend="chroma")
    print(f"  {summary['docs']} docs -> {summary['chunks']} chunks in Chroma collection 'docs_raw'")

    if vector_store.pinecone_available():
        print("\nIngesting for the RAW pipeline (Pinecone)...")
        summary = rag_raw.ingest(vector_store_backend="pinecone")
        print(f"  {summary['docs']} docs -> {summary['chunks']} chunks in Pinecone index 'ai-engineer-rag-raw'")
    else:
        print("\n[pinecone] skipped — no PINECONE_API_KEY set in backend/.env")

    print("\nIngesting for the LANGCHAIN pipeline (local Chroma)...")
    summary = rag_langchain.ingest()
    print(f"  {summary['docs']} docs -> {summary['chunks']} chunks in Chroma collection 'docs_langchain'")
