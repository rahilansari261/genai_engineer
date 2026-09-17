"""
============================================================================
 IMAGE GEN — text-to-image, do tareeke se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Do genuinely different services jo ek text prompt ko picture mein badalte
hain: OpenAI ka DALL-E (paid, hosted, generally zyada aur consistent
quality) aur ek Hugging Face-hosted open model (free, bas ek token chahiye,
quality aur availability zyada vary karti hai — neeche wala note dekho).

Dono functions image ko base64-encoded PNG string ke roop mein return
karte hain, taaki main.py aur frontend ko kabhi jaanne ki zaroorat na pade
ki actually kaunse provider ne banayi — wahi "bahar se same shape, andar
alag engine" pattern jo poore repo mein use hota hai.
============================================================================
"""

import base64
import io
import os


async def generate_openai(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.images.generate(
        model="dall-e-3", prompt=prompt, size="1024x1024", response_format="b64_json", n=1
    )
    return response.data[0].b64_json


def generate_huggingface(prompt: str, model: str) -> str:
    """
    Note karo ki yeh async NAHI hai — huggingface_hub ka InferenceClient ek
    plain blocking HTTP call karta hai. Isko ek async FastAPI route ke
    andar se call karne par (main.py dekho) request ke duration tak event
    loop block ho jaata hai; ek production app isko ek thread pool
    (FastAPI ke `run_in_threadpool`) mein chalata. Yahan isko plain
    blocking call hi rehne diya hai taaki is file ka logic padhne mein
    aasan rahe — wahi tradeoff jo Project 4 ke hf_tasks.py mein note kiya
    gaya tha.

    Text-to-image models Hugging Face ke free serverless tier par text
    models se zyada aate-jaate rehte hain (unko host karna mehenga hota
    hai) — agar configured model error deta hai, to yeh maan lene ki jagah
    ki code hi broken hai, https://huggingface.co/models?pipeline_tag=text-to-image
    se koi alag model id try karo.
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError(
            "HF_TOKEN not set — add a free token from https://huggingface.co/settings/tokens to backend/.env"
        )

    from huggingface_hub import InferenceClient

    client = InferenceClient(token=token)
    try:
        image = client.text_to_image(prompt, model=model)
    except Exception as exc:
        raise RuntimeError(
            f"Hugging Face image generation failed for model '{model}': {exc}"
        ) from exc

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()
