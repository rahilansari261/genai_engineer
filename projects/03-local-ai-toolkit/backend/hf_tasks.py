"""
============================================================================
 HF TASKS — Hugging Face ke HOSTED Inference API ko specific tasks ke liye call karna
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Hugging Face sirf "chat model lene ki ek aur jagah" nahi hai — yeh un
models ka ek hub hai jo sainkdo specific TASKS ke liye bane hain (sentiment
analysis, translation, summarization, image captioning, aur bahut kuch).
Yeh file un tasks mein se do ko Hugging Face ke hosted Inference API ke
through call karti hai, unke official `huggingface_hub` SDK ka use karke —
isliye Ollama ke ulat, yahan kuch bhi tumhari apni machine par nahi chalta;
HF model ko UNKE apne servers par chalata hai aur result wapas bhej deta
hai.

Yeh jaan-boojh kar ek chat/text-generation call NAHI hai (wo pattern tumhe
is project mein Ollama se, aur Projects 1-2 mein OpenAI/Anthropic se pehle
hi mil chuka hai). Is file ka poora point roadmap ka "Hugging Face Tasks"
wala hissa dikhana hai: yeh ki open-source models sirf chatting ke liye
use nahi hote — real-world AI engineering ka ek bada hissa chhote,
specific-purpose models ka hota hai jo EK kaam achhe se aur sasti keemat
mein karte hain.
============================================================================
"""

import os
from dataclasses import dataclass


def _client():
    """HF ke apne hosted inference ("hf-inference") ko point karne wala
    InferenceClient banata hai — yeh free/classic serverless tier hai —
    na ki koi doosra third-party inference provider jispar HF route bhi
    kar sakta hai."""

    from huggingface_hub import InferenceClient

    token = os.getenv("HF_TOKEN")
    if not token:
        raise RuntimeError(
            "HF_TOKEN not set — add a free token from https://huggingface.co/settings/tokens to backend/.env"
        )
    return InferenceClient(provider="hf-inference", token=token)


@dataclass
class ClassificationResult:
    label: str
    score: float


async def classify_sentiment(text: str, model: str) -> ClassificationResult:
    """
    Ek TEXT CLASSIFICATION task chalata hai — model text ko padhta hai aur
    ek fixed set mein se, jis par woh train hua tha, ek label chunta hai
    (yahan: POSITIVE/NEGATIVE). Yeh "aur text generate karo" wale task se
    bilkul alag shape ka kaam hai — output ek label + confidence score
    hota hai, koi likha hua jawab nahi.
    """
    client = _client()
    try:
        # Note: huggingface_hub ke InferenceClient methods natively async
        # NAHI hain — hum yahan ek regular (blocking) function call kar
        # rahe hain. Ek learning project ke liye yeh theek hai; ek
        # production app isko ek thread mein chalata (jaise FastAPI ka
        # `run_in_threadpool`) taaki ek slow HF request poore server ko
        # baaki requests handle karne se block na kare.
        results = client.text_classification(text, model=model)
    except Exception as exc:
        raise RuntimeError(
            f"Hugging Face classification failed for model '{model}': {exc}"
        ) from exc

    top = results[0]  # results score ke hisaab se sorted hote hain, sabse zyada score wala pehle
    return ClassificationResult(label=top.label, score=top.score)


async def summarize(text: str, model: str) -> str:
    """
    Ek SUMMARIZATION task chalata hai — ek lambe passage ko chhote mein
    condense kar deta hai. Phir se wahi baat: yeh exactly isi kaam ke liye
    train kiya gaya ek specific-purpose model hai, koi general chat model
    nahi jisse "please isko summarize kar do" bola gaya ho.
    """
    client = _client()
    try:
        result = client.summarization(text, model=model)
    except Exception as exc:
        raise RuntimeError(f"Hugging Face summarization failed for model '{model}': {exc}") from exc

    return result.summary_text
