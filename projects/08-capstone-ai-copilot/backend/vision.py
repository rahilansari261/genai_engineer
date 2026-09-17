"""
============================================================================
 VISION — image samajhna, do tareeke se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

"Vision" ka yahan bas itna matlab hai: ek model ko ek image AUR ek question
bhejo jo dono padh sakta hai, aur wapas ek text answer lo jo picture mein
actually jo hai usi par grounded ho. Neeche wale dono engines conceptually
bilkul wahi cheez karte hain — asli farak sirf itna hai ki image request
mein kaise attach hota hai, jo provider-specific hai:

  Ollama:  image message ke apne `images` field mein base64 ke roop mein
           jaata hai
  OpenAI:  image ek CONTENT PART ke roop mein jaata hai baaki parts ke
           saath (text question ke saath) — chat messages sirf strings
           nahi rehte jab tum ek se zyada tarah ka content bhej rahe ho

`moondream` (Ollama) ek chhota (~1.7GB), fast, genuinely free vision model
hai — bina kisi API key ke try karne ke liye ek acha default hai.
============================================================================
"""

import base64
import os


async def describe_ollama(image_bytes: bytes, question: str, model: str) -> str:
    import ollama

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama.AsyncClient(host=host)
    image_b64 = base64.b64encode(image_bytes).decode()

    try:
        response = await client.chat(
            model=model,
            messages=[{"role": "user", "content": question, "images": [image_b64]}],
        )
    except ollama.ResponseError as exc:
        raise RuntimeError(f"Ollama error: {exc.error} — did you run 'ollama pull {model}'?") from exc
    except Exception as exc:
        raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc

    return response["message"]["content"]


async def describe_openai(image_bytes: bytes, question: str, model: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    image_b64 = base64.b64encode(image_bytes).decode()

    # Yahan message ka `content` ek plain string nahi, ek typed parts ki
    # LIST hai — ek "text" part question ke liye, ek "image_url" part jo
    # image ko base64 data URL ke roop mein carry karta hai (koi file
    # upload endpoint nahi chahiye; image bas request body ke andar hi
    # travel karti hai).
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            }
        ],
    )
    return response.choices[0].message.content or ""
