"""
============================================================================
 ANOMALY — jo items fit nahi hote unhe dhoondna, sirf distance ke through
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Sabse pehla, sabse simple idea jo tumhe sujhega woh hai: "har vector ko
average karke ek centroid bana do, phir items ko us centroid se distance
ke hisaab se rank karo". Sunne mein sahi lagta hai, lekin hai nahi — yeh
asal mein measure karta hai ki "yeh note kitna strongly on-topic hai",
"yeh note kitna isolated hai" nahi. Precise, topic-specific language use
karne wala note (jaise ek exact protein-per-pound figure) ek hi direction
mein strongly point karta hai aur centroid se FAR chala jaata hai, jabki
woh ek bilkul typical, well-clustered fitness note hi hota hai. Doosri
taraf, ek vague, generic sentence accidentally sabke beech mein, centre
ke paas land kar sakta hai. Humne pehle exactly wahi version banaya,
chalaya, aur usne dataset ke do deliberately unrelated notes ki jagah
ordinary on-topic notes surface kiye — yeh jaanna zaroori hai ki yeh ek
common trap hai, seedha fix pe jump nahi karna chahiye.

Jo approach asal mein kaam karta hai woh hai K-NEAREST-NEIGHBOR DISTANCE:

  Har item ke liye, uske K sabse close neighbors dhoondo (cosine distance
  ke hisaab se) baaki har OTHER item mein se, aur un K distances ka
  average nikaalo.

Jo item similar notes ke ek tight cluster ke andar baitha hai uske
neighbors paas hi milte hain, isliye yeh average chhota hota hai. Jis
item ka dataset mein koi real counterpart nahi hai, usse apne "nearest"
neighbors dhoondne ke liye bilkul unrelated notes tak pahunchna padta hai,
isliye yeh average bada hota hai — yeh "yeh point kitna isolated hai" ka
kahin zyada direct measurement hai, aur "the odd ones out" ka asal matlab
yahi hai.
============================================================================
"""

import numpy as np


def find_anomalies(items: list[dict], top_k: int, k_neighbors: int = 5) -> list[dict]:
    """
    `items` woh list hai jo vector_store.get_all() se return hoti hai —
    har ek ke paas ek `embedding` field hota hai. `top_k` items return
    karta hai jinki apne k nearest neighbors se average distance sabse
    LARGEST hai, sabse isolated wala sabse pehle sorted.
    """
    vectors = np.array([item["embedding"] for item in items])  # shape: (n_items, n_dimensions)
    n = len(items)
    k = min(k_neighbors, n - 1)  # baaki items se zyada neighbors maang nahi sakte

    # Har embedding pehle se hi unit-length hai (embeddings.py dekho), isliye
    # do vectors ke beech ka dot product hi unki cosine similarity HAI — yahan
    # extra normalization ki zaroorat nahi. `vectors @ vectors.T` yeh har pair
    # ke liye ek saath compute kar deta hai: ek (n x n) similarity matrix.
    similarity_matrix = vectors @ vectors.T
    distance_matrix = 1 - similarity_matrix

    # Har item khud se distance 0 par hota hai (diagonal wala) — usko
    # infinity set kar do taaki woh kabhi bhi apne hi "nearest neighbors"
    # mein count na ho.
    np.fill_diagonal(distance_matrix, np.inf)

    # Har row (har item ki baaki sab items se distances) ko smallest-first
    # sort karo, phir sirf pehle `k` ka average nikaalo — yehi hai "mere k
    # nearest neighbors tak ki distance" har item ke liye, ek hi vectorized
    # step mein compute ho jaata hai, Python loop ki zaroorat nahi.
    nearest_k_mean_distance = np.sort(distance_matrix, axis=1)[:, :k].mean(axis=1)

    scored = [
        {**item, "distance": float(dist)} for item, dist in zip(items, nearest_k_mean_distance)
    ]
    scored.sort(key=lambda x: x["distance"], reverse=True)

    # Return karne se pehle raw embedding vector hata do — API response ko
    # iski zaroorat nahi, yeh sirf is calculation ke liye chahiye tha.
    return [{k: v for k, v in item.items() if k != "embedding"} for item in scored[:top_k]]
