"""
============================================================================
 PRICING — OpenAI embedding index ka asal mein kitna cost aata hai
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Project 1 ke pricing.py wala hi idea: per-token rate ko ek clearly-labelled
jagah par rakho, ingest.py mein kahin dabe hue ek magic number ke bajaye.
Embeddings, chat completions se BAHUT sasti padti hain — inme "output"
wala side hota hi nahi, kyunki ek embedding call text generate nahi karti,
woh bas tumhare input text ko numbers ki ek list mein convert karti hai.
============================================================================
"""

# USD per 1,000,000 input tokens. Source: OpenAI ka pricing page. Is jaisa
# poora 50-note dataset embed karna ek cent ka fraction bhi nahi hai —
# genuinely ek paid AI API se kar sakne wali sabse sasti cheezon mein se
# ek hai.
OPENAI_EMBEDDING_PRICE_PER_1M_TOKENS = 0.02


def estimate_embedding_cost(total_tokens: int) -> float:
    return total_tokens * OPENAI_EMBEDDING_PRICE_PER_1M_TOKENS / 1_000_000
