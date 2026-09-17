"""
============================================================================
 PRICING — running cost meter, Project 1 se reuse kiya gaya
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Project 1 wala hi idea hai: per-token rates ko ek clearly-labelled jagah
par rakho, aur token count ko dollar estimate mein badal do. Yahan farak
sirf itna hai ki yeh KAHAN use hota hai — agent loop ki har OpenAI call
(main reasoning steps, aur vision ya image generation jaisi koi bhi
OpenAI-backed tool call) apna token usage wapas agent.py ko report karti
hai, jo poori conversation ke liye ek running total accumulate karta hai.
Ollama calls free hain — woh total mein kuch bhi add nahi karti, aur yahi
poora reason hai ki ek free local engine rakhna kaam ka hai.
============================================================================
"""

# USD per 1,000,000 tokens. Source: OpenAI ka pricing page — ise ek
# estimate maano, bill nahi; rates is file se zyada baar badalte hain.
CHAT_PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

# Flat per-image estimates (DALL-E token se price nahi karta).
IMAGE_GEN_PRICING = {
    "dall-e-3": 0.04,  # standard quality, 1024x1024
}


def estimate_chat_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = CHAT_PRICING.get(model)
    if rates is None:
        return 0.0  # unknown/local model — guess karne ki jagah free maan liya
    return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000


def estimate_image_cost(model: str) -> float:
    return IMAGE_GEN_PRICING.get(model, 0.0)
