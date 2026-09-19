"""
============================================================================
 AI SAFETY SANDBOX API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh ek chat request ke liye traffic controller hai, aur yeh TEEN checks
ek strict order mein chalata hai — yehi order is poore project ka point
hai:

    1. INPUT MODERATE KARO   — kya user ka message khud hi ek policy
                                violation hai? Agar haan, to yahin ruk
                                jao. Hum expensive chat model ko call
                                karne ka paisa bhi kharch nahi karte.
    2. CHAT MODEL KO CALL KARO — jo bhi "guard mode" system prompt tumne
                                  choose kiya hai (none / basic / strong)
                                  uska use karke.
    3. OUTPUT MODERATE KARO   — achhe system prompt ke bawajood bhi, model
                                 kabhi-kabhi aisi cheez bol sakta hai jo
                                 usko nahi bolni chahiye. REPLY ko bhi
                                 check karo, user ko dikhane se pehle.

guardrails.py ka har attack step 2 ko specifically test karne ke liye
design kiya gaya hai (kya ek achhi tarah likha hua system prompt
manipulation resist kar sakta hai?), jabki moderation (steps 1 aur 3) ek
bilkul alag, independent safety net hai — ek real app mein DONO hone
chahiye, kyunki yeh alag-alag tarah ki problems pakadte hain.
============================================================================
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from guardrails import ATTACKS, GUARD_PROMPTS
from moderation import moderate
from providers import CALLERS

load_dotenv()

app = FastAPI(title="AI Safety Sandbox API")

# CORS kya hai: browser ek website (jaise Vercel par hosted frontend) ko
# doosri website (yeh backend) se data tabhi lene deta hai jab backend khud
# bole "haan, is website ko allowed hai". Express mein yeh
# `app.use(cors({ origin: [...] }))` jaisa hai.
#
# Pehle yahan sirf "http://localhost:3000" hardcoded tha, isliye deploy karne
# par (frontend ka URL alag hota hai) browser har request block kar deta tha.
# Ab list env variable CORS_ORIGINS se aati hai — comma se alag karke ek ya
# zyada origins likh sakte ho:
#     CORS_ORIGINS=https://my-app.vercel.app,http://localhost:3000
# Kuch set nahi kiya (ya khaali chhoda) to local default localhost:3000 hi
# rehta hai, isliye laptop par kuch badalna nahi padta. Origin exact hona
# chahiye (scheme + host, koi path nahi); peeche ka "/" hum khud hata dete hain.
allowed_origins = [
    origin.strip().rstrip("/")
    for origin in (os.getenv("CORS_ORIGINS") or "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    guard_mode: str = "strong"  # "none" | "basic" | "strong" — guardrails.py dekho
    use_moderation: bool = True
    # Ek real logged-in user ki ID ka stand-in. Real app mein yeh tumhare
    # auth system se aata — yahan yeh bas ek fixed demo string hai taaki
    # tum concept dekh sako (providers.py ka file comment dekho) bina is
    # learning project ke liye poora login system banaye.
    user_id: str = "demo-user"


class ChatResponse(BaseModel):
    text: Optional[str] = None
    blocked: bool = False
    # Kaunsi safety layer ne message ko roka, agar roka to: "input-moderation",
    # "output-moderation", ya None agar kuch bhi block nahi hua.
    blocked_layer: Optional[str] = None
    blocked_categories: List[str] = []
    moderation_available: bool = True
    guard_mode: str = "strong"
    provider: str = ""
    model: str = ""
    error: Optional[str] = None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    moderation_available = True

    # -------------------- STEP 1: INPUT MODERATE KARO --------------------
    if req.use_moderation:
        try:
            input_check = await moderate(req.message)
        except RuntimeError:
            # Koi OpenAI key configure nahi hai — moderation literally
            # chal hi nahi sakta. Hum response mein yeh note kar dete hain,
            # aisa dikhaane ke bajaye ki humne kuch check kiya jo humne
            # kiya hi nahi.
            moderation_available = False
        else:
            if input_check.flagged:
                # Yahin ruk jao. Hum jaan-bujh kar chat model ko bilkul
                # call NAHI karte — yehi "input pehle check karne" ka
                # "expensive model par paisa kharch hone se pehle pakad
                # lo" wala benefit hai.
                return ChatResponse(
                    blocked=True,
                    blocked_layer="input-moderation",
                    blocked_categories=input_check.categories,
                    moderation_available=True,
                    guard_mode=req.guard_mode,
                    provider=req.provider,
                    model=req.model,
                )

    # -------------------- STEP 2: CHAT MODEL KO CALL KARO --------------------
    caller = CALLERS.get(req.provider)
    if caller is None:
        return ChatResponse(error=f"unknown provider '{req.provider}'", guard_mode=req.guard_mode)

    system_prompt = GUARD_PROMPTS.get(req.guard_mode)
    try:
        reply_text = await caller(req.model, system_prompt, req.message, req.user_id)
    except Exception as exc:
        # Provider ki koi failure (galat key, model nahi mila, etc.) —
        # ise saaf-saaf surface karo, request crash karne ke bajaye.
        return ChatResponse(
            error=str(exc),
            moderation_available=moderation_available,
            guard_mode=req.guard_mode,
            provider=req.provider,
            model=req.model,
        )

    # -------------------- STEP 3: OUTPUT MODERATE KARO --------------------
    if req.use_moderation and moderation_available:
        try:
            output_check = await moderate(reply_text)
        except RuntimeError:
            moderation_available = False
        else:
            if output_check.flagged:
                # System prompt model ko woh cheez bolne se rokne mein
                # fail ho gaya jo usko nahi bolni chahiye thi — lekin
                # output moderation wala safety net ne use pakad liya user
                # tak pahunchne se pehle. Hum yahan jaan-bujh kar `text` ko
                # khaali chhod dete hain: output moderation ka poora point
                # hi yeh hai ki flagged reply user tak kabhi pahunchti hi
                # nahi.
                return ChatResponse(
                    blocked=True,
                    blocked_layer="output-moderation",
                    blocked_categories=output_check.categories,
                    moderation_available=True,
                    guard_mode=req.guard_mode,
                    provider=req.provider,
                    model=req.model,
                )

    return ChatResponse(
        text=reply_text,
        blocked=False,
        moderation_available=moderation_available,
        guard_mode=req.guard_mode,
        provider=req.provider,
        model=req.model,
    )


@app.get("/attacks")
async def get_attacks():
    """guardrails.py se fixed red-team attack suite wapas bhejta hai
    taaki frontend inko one-click buttons ki tarah render kar sake."""
    return ATTACKS


@app.get("/health")
async def health():
    return {"status": "ok"}
