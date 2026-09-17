"""
============================================================================
 OLLAMA LOCAL — Ollama se uske official SDK se baat karna, raw HTTP se nahi
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Projects 1 aur 2 mein, humne Ollama ko `httpx` se haath se call kiya tha —
khud JSON payload banate the aur `/api/generate` par POST karte the. Yeh
kaam to karta hai, lekin iska matlab hai ki HUMEIN Ollama ki exact URL
shape pata honi chahiye, HUMEIN response parse karna padta hai, aur agar
Ollama apna API badal de to humein apna code update karna padega.

`ollama` Python package (official "Ollama SDK") yeh sab kuch tumhare liye
wrap kar deta hai: tum `.chat(model=..., messages=...)` call karte ho aur
ek typed response object wapas milta hai — bilkul waisi hi shape ka call
jaisa tum OpenAI ya Anthropic ke apne SDKs ko karte. Yeh file khaas isi
farak ko dikhane ke liye hai — is file ko Project 1 ke providers.py ke
`call_ollama()` function se compare karo, jo yehi kaam haath se karta hai.

Hand-rolled HTTP calls ki jagah ek official SDK use karna generally real
projects mein sahi default hota hai: kam code, aur compatibility layer ko
maintain karne ka jhanjhat koi aur uthata hai.
============================================================================
"""

import os
from typing import Optional


async def generate(model: str, prompt: str) -> str:
    """Ek local Ollama model ko ek prompt bhejta hai aur uska reply text wapas deta hai."""

    # File ke top par import karne ki jagah yahan andar import kiya hai,
    # baaki projects jaisi hi wajah se: agar tum is function ko kabhi
    # touch hi nahi karte, to tumhe baaki app chalane ke liye yeh package
    # sahi se install hona zaroori nahi hai.
    import ollama

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    # AsyncClient SDK ka async-capable client hai — wahi "network ka wait
    # karte waqt block mat ho" wala idea jo is poore repo mein har jagah
    # use hua hai.
    client = ollama.AsyncClient(host=host)

    try:
        response = await client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
    except ollama.ResponseError as exc:
        # SDK API-level errors (jaise "model not found") ke liye apna
        # KHAAS exception type raise karta hai — khud HTTP status code
        # parse karne se kahin zyada achha, aur yahi to poora point hai
        # ek SDK use karne ka.
        raise RuntimeError(f"Ollama error: {exc.error} — did you run 'ollama pull {model}'?") from exc
    except Exception as exc:
        # "Ollama chal hi nahi raha" wala case cover karta hai — SDK ka
        # underlying HTTP client ek connection error raise karta hai, jise
        # hum Project 1 jaisa hi ek human-readable message mein badal dete
        # hain.
        raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc

    return response["message"]["content"]
