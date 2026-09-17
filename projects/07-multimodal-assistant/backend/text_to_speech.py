"""
============================================================================
 TEXT TO SPEECH — sirf ek hi backend engine, aur yeh jaan-boojh kar hai
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Bas OpenAI ka TTS API. Is modality ke liye FREE alternative koi backend
call hai hi nahi — woh hai browser ka apna built-in `speechSynthesis` API
(frontend/components/SpeechPanel.tsx dekho), jo text ko poori tarah
client-side hi bol deta hai, na koi network request, na koi server involve
hota hai. Yeh "text to speech" paane ka ek genuinely alag, aur genuinely
free, tarika hai — janna zaroori hai ki yeh bhi ek option hai, sirf koi
Hugging Face model nahi jise tumhe khud host karna pade. Yeh file sirf
paid, better-quality alternative ke liye hai.
============================================================================
"""

import os


async def synthesize_openai(text: str, voice: str = "alloy") -> bytes:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.audio.speech.create(model="tts-1", voice=voice, input=text)
    return response.content
