"""
============================================================================
 EMBEDDINGS — text ko vectors mein badalna, do alag tariko se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Ek "embedding" bas numbers ki ek list hai (ek vector) jo kisi text ke
MEANING ko represent karti hai — similar meaning wale texts ke vectors
bhi similar nikalte hain, chahe unme ek bhi common word na ho. Isi project
ke peeche yehi poora trick hai: search, recommendations, aur anomaly
detection — yeh sab bas "vectors ke beech ki distance measure karo" hai,
using the embeddings jo yeh file banati hai.

Un vectors ko paane ke do tarike hain, jo is project ke banaye do
indexes se match karte hain (ingest.py dekho):

  embed_local()  — ek chhota open-source model (Sentence Transformers) jo
                    ek baar download hota hai aur uske baad poora tumhare
                    apne CPU par chalta hai. Free hai, lekin us particular
                    chhote model ki jitni bhi quality ho sakti hai, utni
                    tak hi limited ho.

  embed_openai() — OpenAI ka hosted embedding API. Thoda sa real paisa
                    lagta hai (pricing.py dekho) lekin generally quality
                    zyada achhi hoti hai aur koi local download ya compute
                    nahi chahiye.

Dono functions SAME shape return karte hain — ek list of vectors, har
input text ke liye ek, har ek pehle se length 1 tak normalized — isliye
baaki app (vector store, search, anomaly detection) ko kabhi jaanne ya
parwaah karne ki zaroorat nahi padti ki kisne banaya.
============================================================================
"""

import os

# Free, local embedder ka model name. "all-MiniLM-L6-v2" sabse zyada use
# hone wale chhote sentence-embedding models mein se ek hai — ek learning
# project ke liye speed, size (~80MB), aur quality ka achha default balance.
LOCAL_MODEL_NAME = "all-MiniLM-L6-v2"
OPENAI_MODEL_NAME = "text-embedding-3-small"

# Local model ek baar, lazily load hota hai, jab pehli baar asal mein
# zaroorat pade — import time par nahi. Download aur load karne mein
# kuch seconds lagte hain, aur agar app ka yeh run kabhi local embedder
# ko touch hi nahi karta (jaise tum sirf OpenAI use kar rahe ho), to
# woh cost bharne ki koi wajah nahi.
_local_model = None


def _get_local_model():
    global _local_model
    if _local_model is None:
        from sentence_transformers import SentenceTransformer

        _local_model = SentenceTransformer(LOCAL_MODEL_NAME)
    return _local_model


def embed_local(texts: list[str]) -> list[list[float]]:
    """Free, local Sentence Transformers model use karke texts ka ek batch embed karta hai."""
    model = _get_local_model()

    # normalize_embeddings=True har vector ko length 1 tak scale kar deta
    # hai. Yeh isliye kar rahe hain taaki "distance" ka matlab hamesha
    # same rahe (cosine distance) — chahe vector is function se aaya ho
    # ya OpenAI ke API se, jo already default mein normalized vectors
    # return karta hai.
    vectors = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vectors.tolist()


def embed_openai(texts: list[str]) -> list[list[float]]:
    """OpenAI ke hosted Embeddings API se texts ka ek batch embed karta hai."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this embedder")

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(model=OPENAI_MODEL_NAME, input=texts)

    # API results ko input list wahi order mein return karta hai, har text
    # ke liye ek object, har ek ke paas ek `.embedding` field — hum bas
    # unko nikaal ke ek plain list of lists bana dete hain.
    return [item.embedding for item in response.data]
