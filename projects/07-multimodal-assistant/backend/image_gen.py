"""
============================================================================
 IMAGE GEN — text-to-image, do tarike se
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Do genuinely alag services jo text prompt ko picture mein badalti hain:
OpenAI ka DALL-E (paid, hosted, generally better aur zyada consistent
quality) aur ek Hugging Face-hosted open model (free bas ek token se,
quality aur availability thodi zyada upar-neeche hoti hai —
neeche wala note dekho).

Dono functions image ko base64-encoded PNG string ke roop mein return
karte hain, isliye main.py aur frontend ko kabhi jaanne ki zaroorat nahi
padti ki asal mein kaunsa provider ne banayi hai — wahi "bahar se same
shape, andar se alag engine" pattern jo is poore repo mein use hota hai.
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
    Note karo ki yeh wala async NAHI hai — huggingface_hub ka
    InferenceClient ek plain blocking HTTP call karta hai. Isko async
    FastAPI route ke andar se call karne se (main.py dekho) request ke
    poore duration tak event loop block ho jaata hai; production app mein
    isko thread pool mein chalaya jaata (FastAPI ka `run_in_threadpool`).
    Yahan jaan-boojh kar plain blocking call rakha hai taaki is file ka
    logic padhne mein easy rahe — wahi tradeoff jo Project 4 ki
    hf_tasks.py mein note kiya gaya tha.

    Text-to-image models Hugging Face ke free serverless tier par text
    models se zyada aate-jaate rehte hain (host karna mehenga padta hai)
    — agar configured model error deta hai, to yeh mat sochna ki code
    kharab hai, balki https://huggingface.co/models?pipeline_tag=text-to-image
    se koi doosra model id try karo.
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
