"""
============================================================================
 TEXT TO SPEECH — sirf ek backend engine, aur yeh jaan-boojh kar hai
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Bas OpenAI ka TTS API. Is modality ke liye FREE alternative koi backend
call hai hi nahi — woh browser ka apna built-in `speechSynthesis` API hai
(frontend/components/SpeechPanel.tsx dekho), jo text ko poori tarah
client-side hi bol kar sunata hai, koi network request nahi aur koi server
involved hi nahi. Yeh "text to speech" paane ka ek genuinely alag, aur
genuinely free, tareeka hai — jaanne layak option hai, na ki bas ek
Hugging Face model jise tumhe khud host karna padta. Yeh file sirf paid,
higher-quality alternative ke liye hai.
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
