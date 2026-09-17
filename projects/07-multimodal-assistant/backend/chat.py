"""
============================================================================
 CHAT — voice loop ka woh step jo plain-text reply deta hai
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Voice assistant tab ek asli pipeline hai, sirf transcription demo nahi:
apni awaaz record karo -> usko text mein transcribe karo (speech_to_text.py)
-> jo bola uska text REPLY lo (yeh file) -> uss reply ko wapas bolo
(text_to_speech.py, ya khud browser). Yeh file bas woh beech wala step hai
— ek simple one-turn chat completion, wahi multi-provider pattern jo is
poore repo mein use hota hai (Projects 1, 2, 6), bas is tab ko jitna
chahiye utna hi trim kiya hua.
============================================================================
"""

import os


async def reply_ollama(text: str, model: str) -> str:
    import ollama

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama.AsyncClient(host=host)
    try:
        response = await client.chat(model=model, messages=[{"role": "user", "content": text}])
    except ollama.ResponseError as exc:
        raise RuntimeError(f"Ollama error: {exc.error} — did you run 'ollama pull {model}'?") from exc
    except Exception as exc:
        raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc
    return response["message"]["content"]


async def reply_openai(text: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(model=model, messages=[{"role": "user", "content": text}])
    return response.choices[0].message.content or ""


async def reply(text: str, provider: str, model: str) -> str:
    if provider == "openai":
        return await reply_openai(text, model)
    return await reply_ollama(text, model)
