"""
============================================================================
 KEYWORD SEARCH — jaan-boojh kar rakha gaya "dumb" baseline
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh deliberately search karne ka OLD tarika hai: query ko words mein
todo, har note ko bhi words mein todo, aur note ko score karo ki usne
query ke saath kitne words share kiye. Koi AI nahi, koi embeddings nahi,
koi meaning nahi — bas text matching. Yeh sirf UI mein ek comparison
point ke taur par hai, semantic search results ke bagal mein baitha hua,
taaki "matching words" aur "matching meaning" ka fark tum apni aankhon se
same screen par side by side dekh sako, sirf believe karne ke bajaye.
============================================================================
"""

import re

# Common words jo scoring se exclude kiye gaye hain taaki "the" ya "how"
# ek meaningful match na gine jaayein — agar yeh na karein to almost har
# note, almost har query ke against sirf shared filler words ki wajah se
# score > 0 kar dega.
STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "to", "of", "in", "on", "for", "and", "or", "but", "with", "at",
    "by", "from", "how", "what", "why", "when", "your", "you", "it",
    "this", "that", "do", "does", "my", "i",
    # Generic filler/modifier words — itne content-free ki query ke saath
    # inme se EK bhi share hona ek real topical match nahi ginna chahiye.
    # (Testing mein pata chala ki "well" akela, "well-behaved" aur
    # "well-mannered" se, do bilkul unrelated notes ke beech ek false
    # keyword match banane ke liye kaafi tha — isliye add kiya gaya —
    # project README ke search demo mein dekho.)
    "well", "good", "new", "just", "really", "get", "gets", "getting",
    "one", "into", "not", "much", "more", "most", "so", "very", "also",
    "even", "still", "actually", "basically", "roughly", "own", "any",
}


def _tokenize(text: str) -> set[str]:
    """Text ko lowercase karke individual words ke ek set mein todta hai,
    punctuation aur stopwords hata ke. `set` isliye (list nahi) kyunki
    humein sirf itna parwaah hai ki koi word shared hai YA NAHI, kitni
    baar repeat hua yeh nahi."""
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {w for w in words if w not in STOPWORDS}


def search(query: str, items: list[dict], top_k: int) -> list[dict]:
    """
    Har item ko score karta hai ki usne query ke saath kitne non-stopword
    tokens share kiye, aur top_k sabse high-scoring wale return karta hai
    (ties original order se broken hote hain). Yahan score 0 hona ek
    bilkul valid, common result hai — iska matlab bas itna hai ki "koi
    shared words hi nahi", aur yeh exactly wahi case hai jise semantic
    search behtar handle karne ke liye bana hai.
    """
    query_words = _tokenize(query)

    scored = []
    for item in items:
        item_words = _tokenize(item["text"])
        shared = query_words & item_words
        scored.append({**item, "score": len(shared)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
