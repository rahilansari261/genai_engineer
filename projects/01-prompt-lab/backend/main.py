"""
============================================================================
 PROMPT LAB API — is project ka "dimaag"
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Tum browser mein EK prompt type karte ho. Is file ka kaam hai wahi prompt
teen alag-alag AI providers (OpenAI, Anthropic, Ollama) ko EK SAATH bhejna,
sabka jawab aane ka wait karna, aur ek clean list bana ke wapas dena —
text, kitne tokens use hue, kitna time laga, aur roughly kitna cost aaya.

"OpenAI se baat karo" / "Anthropic se baat karo" / "Ollama se baat karo"
wala asli logic providers.py mein hai — yeh file sirf traffic controller
hai: incoming request leti hai, jis-jis provider ko call karna hai unko
fire karti hai, aur response assemble karke bhejti hai. "Provider se baat
karna" aur "web request handle karna" ko alag files mein rakhna ek common
pattern hai — isse providers.py ko bina web server chalaye bhi test ya
reuse kiya ja sakta hai.
============================================================================
"""

import asyncio
import time
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pricing import estimate_cost
from providers import call_anthropic, call_ollama, call_openai

# .env file (jahan tumhari API keys pada hain) ko read karke environment
# mein load karta hai, taaki providers.py ke andar os.getenv("OPENAI_API_KEY")
# kaam kare.
load_dotenv()

# FastAPI ek web framework hai — yeh Python functions ko HTTP endpoints
# (URLs jinko frontend call kar sakta hai) mein convert karta hai. `app`
# hi poora web server hai.
app = FastAPI(title="Prompt Lab API")

# --------------------------------------------------------------------------
# CORS = "Cross-Origin Resource Sharing". Browser ek address par chal rahe
# webpage (localhost:3000, hamara Next.js frontend) ko dusre address ki API
# (localhost:8000, yeh backend) call karne se rokta hai — JAB TAK backend
# saaf-saaf na bole "it's fine, main us address ko trust karta hoon". Yeh
# block wahi permission slip hai. Isके bina, browser frontend ki har
# request chupchap reject kar dega.
# --------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ek lookup table: string "openai" us asli function ko point karta hai jo
# OpenAI ko call karna jaanta hai, waise hi baaki dono. Isse run_one() neeche
# bina bada if/elif/else chain likhe, sirf ek string dekh kar sahi function
# runtime par pick kar leta hai.
CALLERS = {"openai": call_openai, "anthropic": call_anthropic, "ollama": call_ollama}


# ----------------------------------------------------------------------
# PYDANTIC MODELS — inko JSON data ke "shape contracts" samjho. FastAPI
# inka use karke automatically check karta hai ki incoming request mein
# sahi fields hain (aur agar nahi hain to clear error ke saath reject
# karta hai), aur Python objects ko response ke liye automatically JSON
# mein convert kar deta hai. Ek baar shape describe karne se validation
# aur documentation dono free mein mil jaate hain.
# ----------------------------------------------------------------------


class ProviderRequest(BaseModel):
    """Incoming request ki ek entry: kaunsa provider, kaunsa model."""

    provider: str  # "openai" | "anthropic" | "ollama"
    model: str


class CompleteRequest(BaseModel):
    """Poora shape jo frontend POST /complete ko bhejta hai."""

    prompt: str
    system: Optional[str] = None  # optional system prompt, chhod bhi sakte ho
    providers: List[ProviderRequest]


class ProviderResult(BaseModel):
    """
    EK provider ke jawab ka shape jo hum frontend ko wapas bhejte hain.
    Sab kuch Optional hai kyunki kuch bhi galat ho sakta hai (API key
    missing, model nahi mila, network error) — us case mein `error` ke
    alawa har field khaali rehta hai, aur `error` mein plain English mein
    bataya jaata hai ki hua kya.
    """

    provider: str
    model: str
    text: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None


async def run_one(provider: str, model: str, prompt: str, system: Optional[str]) -> ProviderResult:
    """
    EK provider ko call karta hai aur jo bhi ho usse ProviderResult mein
    badal deta hai.

    Yahan ka important design choice: yeh function KABHI bhi exception
    upar throw nahi karta. Agar OpenAI ki key missing hai, ya Ollama
    chal hi nahi raha, to hum use catch karke `.error` mein daal dete hain,
    poori request crash nahi karte. Isi wajah se baaki do providers ka
    result aa sakta hai chahe ek fail ho jaaye — README mein isko
    "graceful degradation" bola gaya hai.
    """
    caller = CALLERS.get(provider)
    if caller is None:
        return ProviderResult(provider=provider, model=model, error=f"unknown provider '{provider}'")

    # Ek simple stopwatch: provider ko call karne se pehle time note karo,
    # aur turant baad phir se — taaki latency (kitna time laga) report kar
    # sakein.
    start = time.perf_counter()
    try:
        text, prompt_tokens, completion_tokens = await caller(model, prompt, system)
    except Exception as exc:
        # Provider call se aane wali KOI BHI failure (galat key, network
        # down, model exist hi nahi karta, etc.) ko catch karke ek readable
        # error banate hain, taaki poori API request na phat jaaye.
        return ProviderResult(provider=provider, model=model, error=str(exc))
    latency_ms = int((time.perf_counter() - start) * 1000)

    # Cost tabhi calculate karo jab token counts sach mein wapas mile hon.
    total_tokens = None
    cost_usd = None
    if prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
        cost_usd = estimate_cost(model, prompt_tokens, completion_tokens)

    return ProviderResult(
        provider=provider,
        model=model,
        text=text,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
    )


@app.post("/complete", response_model=List[ProviderResult])
async def complete(req: CompleteRequest):
    """
    Is API ka asli, ekmatra endpoint: POST /complete.

    Yeh "fan out, phir sabka wait karo" pattern hai. Hum "is provider ko
    call karo" tasks ki ek list banate hain (user ne jitne provider select
    kiye utne), aur sabko ek saath asyncio.gather() ko de dete hain.
    asyncio.gather() inko CONCURRENTLY chalata hai — matlab hum OpenAI ke
    finish hone ka wait nahi karte Anthropic se pehle poochne ke liye.
    Teeno requests ek saath in-flight rehti hain, isliye total time roughly
    "sabse SLOW provider jitna time leta hai" hota hai, "teeno ka total
    time" nahi. Yahi pura point hai plain, one-at-a-time Python calls ki
    jagah `async`/`await` use karne ka.
    """
    tasks = [run_one(p.provider, p.model, req.prompt, req.system) for p in req.providers]
    return await asyncio.gather(*tasks)


@app.post("/complete/stream")
async def complete_stream(req: CompleteRequest):
    """
    /complete jaisa hi kaam karta hai — same providers ko call karta hai —
    bas EK bada fark ke saath: yeh sabka wait karne ki jagah, har provider
    ka result jaise hi ready hota hai, TURANT stream kar deta hai.

    Pehle wale /complete mein `asyncio.gather()` tab tak return nahi karta
    jab tak SABSE SLOW provider (jaise koi bhara-bhara local Ollama model)
    bhi finish na ho jaaye — isliye fast provider (jaise OpenAI, 2 second
    mein hi ready) ka jawab bhi browser tak utni hi der se pahunchta tha
    jitni der Ollama ko lagti thi. Yahan hum `asyncio.as_completed()` use
    karte hain, jo tasks ko unke JITNE bhi order mein khatam hote hain
    usi order mein hume deta hai — jo bhi pehle ready ho, wahi pehle yield
    ho jaata hai.

    Response format NDJSON hai (newline-delimited JSON): har line apne
    aap mein ek complete, valid JSON object hai — ek provider ka poora
    result. Frontend ko poori response ka wait karne ki zaroorat nahi,
    wo stream ko line-by-line padh sakta hai aur jaise hi ek line aaye
    turant us provider ka panel update kar sakta hai.
    """

    async def result_stream():
        tasks = [run_one(p.provider, p.model, req.prompt, req.system) for p in req.providers]
        for finished in asyncio.as_completed(tasks):
            result = await finished
            yield result.model_dump_json() + "\n"

    return StreamingResponse(result_stream(), media_type="application/x-ndjson")


@app.get("/health")
async def health():
    """Ek chhota endpoint, koi asli logic nahi — bas isko curl/ping karke
    check karne ke liye ki "backend chal raha hai aur respond kar raha hai
    ya nahi" — koi bhi bigger cheez debug karne se pehle."""
    return {"status": "ok"}
