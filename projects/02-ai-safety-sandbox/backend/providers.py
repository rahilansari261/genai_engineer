"""
============================================================================
 PROVIDERS — asli chat model ko call karna (yahan jaan-bujh kar simple rakha gaya hai)
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Project 1 ke providers.py jaisa hi idea hai — har provider ke liye ek
function, sab bas reply text return karte hain. Yeh project providers ke
beech token costs compare karne ke baare mein nahi hai (woh Project 1 hai),
yeh safety ke baare mein hai, isliye humne ise minimum tak trim kar diya
hai: ek system prompt + ek message bhejo, text wapas lo.

Ek addition jo notice karne layak hai: call_openai() ek `user_id` accept
karta hai. OpenAI tumhe har request ke saath ek stable (lekin anonymous)
identifier attach karne deta hai `user` parameter ke through — roadmap
wale "end-user IDs". Iska AI ke answer se koi lena-dena nahi hai; yeh
sirf isliye hai taaki agar OpenAI ke abuse-detection systems ko policy-
violating requests ka koi pattern dikhe, to woh dekh sakein ki yeh SAME
end user se baar-baar aa raha hai (ek bad actor ko ban/rate-limit karne
ke liye useful), sirf "tumhari API key" ko culprit dekhne ke bajaye.
============================================================================
"""

import os
from typing import Optional

import httpx


async def call_openai(model: str, system: Optional[str], message: str, user_id: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})

    # `user=user_id` woh roadmap wala "end-user ID" concept action mein
    # hai — yeh kyun bhejne layak hai iske liye upar ka file-level comment
    # dekho.
    response = await client.chat.completions.create(model=model, messages=messages, user=user_id)
    return response.choices[0].message.content or ""


async def call_anthropic(model: str, system: Optional[str], message: str, user_id: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — add it to backend/.env to enable this provider")

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        system=system or "",
        messages=[{"role": "user", "content": message}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


async def call_ollama(model: str, system: Optional[str], message: str, user_id: str) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    payload = {"model": model, "prompt": message, "system": system or "", "stream": False}

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{host}/api/generate", json=payload)
            response.raise_for_status()
    except httpx.ConnectError as exc:
        raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Ollama error: {exc.response.text.strip()} — did you run 'ollama pull {model}'?"
        ) from exc

    return response.json().get("response", "")


CALLERS = {"openai": call_openai, "anthropic": call_anthropic, "ollama": call_ollama}
