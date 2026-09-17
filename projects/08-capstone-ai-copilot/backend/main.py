"""
============================================================================
 AI COPILOT API — capstone
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Ek hi asli endpoint, `POST /chat`, jo ek message receive karta hai
(optionally ek attached image ke saath), pehle ki conversation history, aur
har provider ka choice — aur in sabko agent.py ke ek hi guarded,
tool-using, cost-tracked loop mein route kar deta hai. Yeh poora repo pichle
saat projects mein jo kuch bhi bana raha tha — safety, RAG, agents,
multimodal, provider cost-awareness — sab is ek function call par converge
karta hai.

Request multipart form data ke roop mein aati hai, JSON ke roop mein
nahi, kyunki ek image upload ko plain text fields ke saath hi ek request
mein jaana padta hai — wahi shape jo Project 7 ke /vision endpoint mein tha,
bas ab ek `history` field extend kiya gaya hai jo poori conversation ko ek
JSON string ke roop mein carry karta hai (form fields hamesha strings hote
hain; hum ise khud decode karte hain).
============================================================================
"""

import json
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agent
import vector_store
from docs_loader import load_docs

load_dotenv()

app = FastAPI(title="AI Copilot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TraceStep(BaseModel):
    type: str
    tool: Optional[str] = None
    content: str


class ChatResponse(BaseModel):
    trace: List[TraceStep] = []
    final_answer: Optional[str] = None
    blocked: bool = False
    blocked_layer: Optional[str] = None
    blocked_categories: List[str] = []
    moderation_available: bool = True
    attachments: List[str] = []  # is turn mein generate hue base64 PNGs
    cost_usd: float = 0.0
    error: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat(
    message: str = Form(...),
    history: str = Form("[]"),  # {role, content} ki JSON-encoded list
    provider: str = Form("ollama"),
    model: str = Form("llama3.2"),
    vision_provider: str = Form("ollama"),
    vision_model: str = Form("moondream"),
    image_gen_provider: str = Form("huggingface"),
    image_gen_model: str = Form("black-forest-labs/FLUX.1-schnell"),
    safety: bool = Form(True),
    user_id: str = Form("demo-user"),
    max_steps: int = Form(6),
    image: Optional[UploadFile] = File(None),
):
    try:
        history_list = json.loads(history)
    except json.JSONDecodeError:
        history_list = []

    image_bytes = await image.read() if image is not None else None

    result = await agent.run(
        message=message,
        history=history_list,
        provider=provider,
        model=model,
        image_bytes=image_bytes,
        vision_provider=vision_provider,
        vision_model=vision_model,
        image_gen_provider=image_gen_provider,
        image_gen_model=image_gen_model,
        safety=safety,
        user_id=user_id,
        max_steps=max_steps,
    )
    return ChatResponse(**result)


@app.get("/status")
async def status():
    count = vector_store.count()
    return {"handbook_indexed": count > 0, "handbook_count": count, "docs": [d["source"] for d in load_docs()]}


@app.get("/health")
async def health():
    return {"status": "ok"}
