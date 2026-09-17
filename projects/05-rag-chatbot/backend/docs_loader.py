"""Chhota sa shared helper: docs/ ke andar har markdown file ko memory mein
padh leta hai. Jaan-bujh kar yeh EKLAUTA piece of code hai jo rag_raw.py aur
rag_langchain.py ke beech shared hai — asli RAG mechanism (chunking,
storing, retrieving, generating) se related sab kuch dono files mein alag
alag aur poori tarah implement kiya gaya hai, jaan-bujh kar, taaki dono
honestly comparable rahein."""

import glob
import os

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")


def load_docs() -> list[dict]:
    docs = []
    for path in sorted(glob.glob(os.path.join(DOCS_DIR, "*.md"))):
        with open(path) as f:
            docs.append({"source": os.path.basename(path), "text": f.read()})
    return docs
