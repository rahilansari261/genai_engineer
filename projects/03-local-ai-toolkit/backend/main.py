"""
============================================================================
 LOCAL AI TOOLKIT API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Teen endpoints hain, aur har ek open-source model chalane ka genuinely
alag tareeka hai:

  POST /ollama/generate  -> ek model jo TUMHARE APNE computer par chal
                             raha hai (official Ollama SDK ke through —
                             dekho ollama_local.py)
  POST /hf/classify       -> ek chhota task-specific model jo Hugging
                             Face ke servers par chal raha hai (sentiment
                             analysis)
  POST /hf/summarize      -> ek alag task-specific model, wo bhi Hugging
                             Face ke servers par (summarization)

Open-source model chalane ka TEESRA tareeka — poore ka poora browser ke
andar, Transformers.js ke through — uska koi backend endpoint hai hi
nahi, jaan-boojh kar: woh is server ko kabhi touch hi nahi karta. Wo wala
dekhna ho to frontend/components/BrowserClassifier.tsx mein dekho.

Isi repo ke baaki har project jaisa hi graceful-degradation rule yahan bhi
hai: koi missing token ya unreachable Ollama server request ko crash karne
ki jagah response mein ek saaf, readable error de deta hai.
============================================================================
"""

from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hf_tasks import classify_sentiment, summarize
from ollama_local import generate

load_dotenv()

app = FastAPI(title="Local AI Toolkit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class OllamaRequest(BaseModel):
    model: str
    prompt: str


class OllamaResponse(BaseModel):
    text: Optional[str] = None
    error: Optional[str] = None


@app.post("/ollama/generate", response_model=OllamaResponse)
async def ollama_generate(req: OllamaRequest):
    try:
        text = await generate(req.model, req.prompt)
    except Exception as exc:
        return OllamaResponse(error=str(exc))
    return OllamaResponse(text=text)


class ClassifyRequest(BaseModel):
    text: str
    model: str = "distilbert-base-uncased-finetuned-sst-2-english"


class ClassifyResponse(BaseModel):
    label: Optional[str] = None
    score: Optional[float] = None
    error: Optional[str] = None


@app.post("/hf/classify", response_model=ClassifyResponse)
async def hf_classify(req: ClassifyRequest):
    try:
        result = await classify_sentiment(req.text, req.model)
    except Exception as exc:
        return ClassifyResponse(error=str(exc))
    return ClassifyResponse(label=result.label, score=result.score)


class SummarizeRequest(BaseModel):
    text: str
    model: str = "sshleifer/distilbart-cnn-12-6"


class SummarizeResponse(BaseModel):
    summary: Optional[str] = None
    error: Optional[str] = None


@app.post("/hf/summarize", response_model=SummarizeResponse)
async def hf_summarize(req: SummarizeRequest):
    try:
        summary_text = await summarize(req.text, req.model)
    except Exception as exc:
        return SummarizeResponse(error=str(exc))
    return SummarizeResponse(summary=summary_text)


@app.get("/health")
async def health():
    return {"status": "ok"}
