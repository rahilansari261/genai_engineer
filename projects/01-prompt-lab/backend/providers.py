"""
============================================================================
 PROVIDERS — yeh code hi asal mein har AI service se baat karta hai
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Har AI provider (OpenAI, Anthropic, Ollama) ka apna ALAG tarika hai call
hone ka: alag Python library, alag shape ki request, aur tokens kitne use
hue yeh batane ka bhi alag tarika. Yeh file un sab differences ko teen
functions ke peeche chhupa deti hai, jo bahar se dekhne mein bilkul same
lagte hain:

    call_openai(model, prompt, system)    -> (text, tokens_in, tokens_out)
    call_anthropic(model, prompt, system) -> (text, tokens_in, tokens_out)
    call_ollama(model, prompt, system)    -> (text, tokens_in, tokens_out)

Kyunki teeno EXACT same shape return karte hain, main.py ko yeh jaanne ya
sochne ki zaroorat hi nahi ki wo kaunsa provider call kar raha hai — yahi
fayda hai har provider ke liye is tarah ka "adapter" function likhne ka.

Yahan har function `async` hai, matlab: "yeh function kuch wait karta hai
(network response ke liye), aur Python ko permission hai ki wo waiting ke
dauraan koi aur kaam kar le, bajaye wahin frozen baithe rehne ke."

Agar kuch galat ho jaaye (API key missing, provider tak pahunch nahi paa
rahe), to har function ek plain RuntimeError raise karta hai jiska message
insaan ke padhne layak likha gaya hai — main.py usko catch karke UI mein
dikha deta hai, crash nahi hota.
============================================================================
"""

import os
from typing import Optional, Tuple

import httpx
import tiktoken


def _count_tokens_openai(model: str, text: str) -> int:
    """
    "Tokens" text ke chhote-chhote tukde hote hain (roughly words ke parts)
    jinko AI models asal mein padhte aur generate karte hain — na poora
    word, na single letter. Har provider tumse tokens ke hisaab se bill
    karta hai, isliye khud count kar paana (kisi guess par bharosa karne ki
    jagah) matter karta hai.

    tiktoken OpenAI ki apni tokenizer library hai — yeh text ko bilkul
    waise hi tokens mein todta hai jaise khud OpenAI model todega. Hume
    isकी zaroorat sirf FALLBACK ke taur par padti hai, jab OpenAI hume
    `usage` ke through direct token count nahi deta (normally deta hai,
    lekin yeh function dono situation mein safe rehta hai).
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # tiktoken ko yeh model pehchanta nahi (jaise koi bilkul naya model
        # naam) — cl100k_base ek accha general-purpose fallback encoding hai.
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


async def call_openai(model: str, prompt: str, system: Optional[str]) -> Tuple[str, int, int]:
    """OpenAI ka Chat Completions API call karta hai — wahi API jo ChatGPT ko chalata hai."""

    # API key environment se read karte hain (main.py ne .env se load ki
    # thi). Agar missing hai, to CHUP-CHAAP kuch na karne ki jagah LOUDLY
    # fail karo ek clear message ke saath — isi se frontend sirf isi
    # provider ke liye "no API key configured" dikha paata hai, poora app
    # nahi tootta.
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    # Yahan import kiya hai (file ke top par nahi), taaki agar tum OpenAI
    # kabhi use hi nahi karte, to `openai` package sahi se install na bhi
    # ho tab bhi baaki app chalta rahe.
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)

    # OpenAI ka chat API ek LIST of messages expect karta hai, har ek ka
    # apna "role" hota hai. "system" = AI ko kaise behave karna hai uski
    # instructions (optional). "user" = insaan ne asal mein kya poocha.
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(model=model, messages=messages)
    text = response.choices[0].message.content or ""

    # OpenAI usually humein `response.usage` mein exact token count bata
    # deta hai — wahi ground truth hai. Hum tabhi khud count karte hain
    # (tiktoken se) jab yeh field missing ho.
    usage = response.usage
    prompt_tokens = usage.prompt_tokens if usage else _count_tokens_openai(model, prompt)
    completion_tokens = usage.completion_tokens if usage else _count_tokens_openai(model, text)
    return text, prompt_tokens, completion_tokens


async def call_anthropic(model: str, prompt: str, system: Optional[str]) -> Tuple[str, int, int]:
    """Anthropic ka Messages API call karta hai — jo Claude ke peeche wala API hai."""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — add it to backend/.env to enable this provider")

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)

    # Notice karo Anthropic ka shape OpenAI se thoda alag hai: system
    # prompt apne aap mein EK ALAG argument hai, messages list ka part
    # nahi. Yahi exact wo type ka "har provider thoda alag hota hai"
    # wala detail hai jise chhupane ke liye yeh file bani hai.
    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        system=system or "",
        messages=[{"role": "user", "content": prompt}],
    )

    # Claude ka reply "content blocks" ki ek LIST mein aata hai (theory
    # mein text ke saath aur block types bhi mix ho sakte hain), isliye
    # hum sirf text wale blocks ko jod ke ek string bana dete hain.
    text = "".join(block.text for block in response.content if block.type == "text")

    # Anthropic hamesha usage direct report karta hai — yahan koi fallback
    # nahi chahiye.
    return text, response.usage.input_tokens, response.usage.output_tokens


async def call_ollama(
    model: str, prompt: str, system: Optional[str]
) -> Tuple[str, Optional[int], Optional[int]]:
    """
    Ek LOCAL Ollama server ko call karta hai — tumhare apne machine par
    chalne wala program jo open-source AI models serve karta hai. Koi API
    key nahi chahiye kyunki kuch bhi computer ke bahar nahi jaata; hum bas
    Ollama ke local web server ko (by default localhost:11434 par) ek
    normal HTTP request bhejte hain.
    """
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    payload = {"model": model, "prompt": prompt, "system": system or "", "stream": False}

    try:
        # httpx bas ek HTTP request banane wali library hai (`requests` jaisi,
        # bas async support ke saath). Hum isko 120 seconds dete hain kyunki
        # modest hardware par local models genuinely slow ho sakte hain.
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(f"{host}/api/generate", json=payload)
            response.raise_for_status()  # 4xx/5xx HTTP status ko Python exception mein badal deta hai
    except httpx.ConnectError as exc:
        # Beginners ke liye sabse common failure yehi hai: Ollama abhi
        # chal hi nahi raha. Cryptic network error ki jagah seedha yehi
        # bata do.
        raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc
    except httpx.HTTPStatusError as exc:
        # Dusra sabse common failure: Ollama chal to raha hai, lekin jo
        # model maanga hai wo abhi tak download ("pull") nahi kiya.
        raise RuntimeError(
            f"Ollama error: {exc.response.text.strip()} — did you run 'ollama pull {model}'?"
        ) from exc

    data = response.json()
    text = data.get("response", "")

    # Ollama bhi token counts deta hai, lekin APNE model ke tokenizer se
    # — isliye Ollama ke "50 tokens" aur OpenAI ke "50 tokens" jaruri
    # nahi ki text ko same tarike se count kar rahe hon. Ek provider ke
    # andar cost compare karne ke liye theek hai, providers ke beech
    # ekdum fair apples-to-apples number nahi hai.
    prompt_tokens = data.get("prompt_eval_count")
    completion_tokens = data.get("eval_count")
    return text, prompt_tokens, completion_tokens
