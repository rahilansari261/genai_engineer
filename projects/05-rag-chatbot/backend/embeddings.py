"""
============================================================================
 EMBEDDINGS — ek hi shared embedding model, dono pipelines use karte hain
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Project 4 mein embedding providers (local vs. OpenAI) compare karna tha —
woh topic already cover ho chuka hai. Yeh project jaan-bujh kar HAR jagah
EK hi embedding model use karta hai (Project 4 wala wahi free, local
Sentence Transformers model) taaki jab tum baad mein "raw" pipeline ko
"LangChain" pipeline se compare karo, ya Chroma ko Pinecone se, to sirf
WAHI cheez alag ho jo compare ki jaa rahi hai — koi alag embedding model
chupke se results ko affect na kar raha ho.
============================================================================
"""

LOCAL_MODEL_NAME = "all-MiniLM-L6-v2"

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
    return _local_model


def embed(texts: list[str]) -> list[list[float]]:
    """Texts ke ek batch ko embed karta hai, unit length par normalized
    (cosine distance ke liye normalization kyun matter karta hai, iske liye
    Project 4 ki embeddings.py dekho)."""
    model = _get_local_model()
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()


EMBEDDING_DIMENSIONS = 384  # all-MiniLM-L6-v2 ka output size — Pinecone ko yeh pehle se chahiye
