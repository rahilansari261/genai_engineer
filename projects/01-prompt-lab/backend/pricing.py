"""
============================================================================
 PRICING — token counts ko dollar estimate mein badalna
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

AI providers per-token charge karte hain, aur — yeh important hai — INPUT
tokens (tumhara prompt) aur OUTPUT tokens (AI ka jawab) usually ALAG price
par hote hain. Output typically input se 3-5x zyada mehenga hota hai,
kyunki text generate karna sirf padhne se computationally zyada costly hai.

Rates normally "$ per 1 million tokens" mein quote hote hain. Yeh file sab
rates ko ek hi, clearly-labelled dictionary (PRICING) mein rakhti hai,
bajaye "0.15" aur "0.60" jaise unexplained numbers providers.py/main.py
ki request logic mein bikhraane ke — agar kisi provider ne apna price
badla, to sirf yahin ek jagah update karna hoga.
============================================================================
"""

from typing import Optional

# USD per 1,000,000 tokens. Source: har provider ka published pricing page.
# Rates is file se zyada baar badalte hain — isko sirf ek rough estimate
# samjho seekhne ke liye, real paisa budget karne ke liye bharosa mat karo.
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    # Ollama models jaan-bujh kar yahan LIST nahi kiye — wo tumhare apne
    # computer par chalte hain, isliye koi per-token bill hi nahi hai.
    # Neeche estimate_cost() kisi bhi na-pehchaane model ke liye None
    # return karta hai, aur frontend usko "free / unpriced" dikha deta hai.
}


def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> Optional[float]:
    """
    Asli maths yahi karta hai: (kitne tokens use hue) x (per-token price),
    input side aur output side dono ke liye, phir dono ko jod dete hain.

    Jis model ka price hume pata hi nahi, uske liye 0 ki jagah — ya crash
    karne ki jagah — None return karta hai. Yeh jaan-bujh kar kiya gaya
    choice hai: "humein price pata nahi" aur "price bilkul zero hai" do
    alag facts hain, aur frontend inko alag treat karta hai (dono ko
    "free / unpriced" dikhata hai, lekin yeh difference tab matter karega
    jab kabhi isko aage extend karoge).
    """
    rates = PRICING.get(model)
    if rates is None:
        return None

    # 1,000,000 se divide kar rahe hain kyunki upar wale rates "per
    # million tokens" hain, lekin prompt_tokens/completion_tokens raw
    # counts hain.
    return (prompt_tokens * rates["input"] + completion_tokens * rates["output"]) / 1_000_000
