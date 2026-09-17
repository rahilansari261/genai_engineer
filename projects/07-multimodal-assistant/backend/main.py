"""
============================================================================
 MULTIMODAL ASSISTANT API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Chaar endpoints, ek har modality ke liye, har ek request ke hisaab se ya to
free/local engine par route hoti hai ya paid/hosted par — wahi
graceful-degradation pattern jo yahan har project mein hai: missing key ya
unreachable Ollama response mein ek clear error deta hai, kabhi crash nahi
karta.

  POST /vision       image + question  -> text answer        (Ollama moondream, ya OpenAI gpt-4o-mini)
  POST /image-gen     text prompt       -> generated image     (Hugging Face, ya OpenAI DALL-E)
  POST /transcribe    audio recording   -> text                (local faster-whisper, ya OpenAI Whisper)
  POST /speak          text             -> spoken audio (mp3)  (sirf OpenAI TTS — free option client-side hai, frontend dekho)

Image aur audio real file uploads ki tarah aate hain (multipart/form-data),
base64 JSON blobs ki tarah nahi — yahi zyada realistic tarika hai jisse
browser asal mein binary data bhejta hai, aur isi wajah se tum literally
apni awaaz record kar sakte ho ya photo pick kar sakte ho browser mein aur
woh yahan bina badle dikh jaati hai.
============================================================================
"""

import os
import tempfile
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

import chat
import image_gen
import speech_to_text
import text_to_speech
import vision

load_dotenv()

app = FastAPI(title="Multimodal Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class VisionResponse(BaseModel):
    answer: Optional[str] = None
    error: Optional[str] = None


@app.post("/vision", response_model=VisionResponse)
async def vision_endpoint(
    image: UploadFile = File(...),
    question: str = Form(...),
    provider: str = Form("ollama"),
    model: str = Form("moondream"),
):
    image_bytes = await image.read()
    try:
        if provider == "openai":
            answer = await vision.describe_openai(image_bytes, question, model)
        else:
            answer = await vision.describe_ollama(image_bytes, question, model)
    except Exception as exc:
        return VisionResponse(error=str(exc))
    return VisionResponse(answer=answer)


class ImageGenRequest(BaseModel):
    prompt: str
    provider: str = "huggingface"
    model: str = "black-forest-labs/FLUX.1-schnell"


class ImageGenResponse(BaseModel):
    image_base64: Optional[str] = None
    error: Optional[str] = None


@app.post("/image-gen", response_model=ImageGenResponse)
async def image_gen_endpoint(req: ImageGenRequest):
    try:
        if req.provider == "openai":
            image_base64 = await image_gen.generate_openai(req.prompt)
        else:
            image_base64 = image_gen.generate_huggingface(req.prompt, req.model)
    except Exception as exc:
        return ImageGenResponse(error=str(exc))
    return ImageGenResponse(image_base64=image_base64)


class TranscribeResponse(BaseModel):
    text: Optional[str] = None
    error: Optional[str] = None


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_endpoint(audio: UploadFile = File(...), provider: str = Form("local")):
    audio_bytes = await audio.read()

    # Neeche ke dono engines file PATH expect karte hain, memory mein raw
    # bytes nahi — dono ko ek hi code path se satisfy karne ka sabse
    # simple tarika hai upload ko ek baar temp file mein likh dena, chahe
    # koi bhi engine isko handle kare.
    suffix = os.path.splitext(audio.filename or "audio.webm")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        if provider == "openai":
            text = await speech_to_text.transcribe_openai(tmp_path)
        else:
            text = speech_to_text.transcribe_local(tmp_path)
    except Exception as exc:
        return TranscribeResponse(error=str(exc))
    finally:
        os.unlink(tmp_path)

    return TranscribeResponse(text=text)


class ChatRequest(BaseModel):
    text: str
    provider: str = "ollama"
    model: str = "llama3.2"


class ChatResponse(BaseModel):
    reply: Optional[str] = None
    error: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    try:
        reply_text = await chat.reply(req.text, req.provider, req.model)
    except Exception as exc:
        return ChatResponse(error=str(exc))
    return ChatResponse(reply=reply_text)


class SpeakRequest(BaseModel):
    text: str
    voice: str = "alloy"


@app.post("/speak")
async def speak_endpoint(req: SpeakRequest):
    try:
        audio_bytes = await text_to_speech.synthesize_openai(req.text, req.voice)
    except Exception as exc:
        return Response(content=str(exc), status_code=400, media_type="text/plain")
    return Response(content=audio_bytes, media_type="audio/mpeg")


@app.get("/health")
async def health():
    return {"status": "ok"}
