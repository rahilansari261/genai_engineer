"""Projects 4 aur 5 wala hi free, local embedding model (Sentence
Transformers, all-MiniLM-L6-v2) — yahan reuse kiya gaya hai taaki
`search_handbook` tool ke paas search karne ke liye kuch ho. Ek fixed
embedder poore project mein kyun use kiya jaata hai iski fuller
explanation ke liye Project 5 ka embeddings.py dekho."""

LOCAL_MODEL_NAME = "all-MiniLM-L6-v2"

_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
    return _local_model


def embed(texts: list[str]) -> list[list[float]]:
    model = _get_local_model()
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()
