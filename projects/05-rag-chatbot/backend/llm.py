"""
============================================================================
 LLM — GENERATION step: retrieve kiye hue chunks + ek question se answer banana
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh docs/what-is-rag.md mein describe kiye gaye RAG pipeline ka stage 4
hai: retrieval step relevant chunks dhoondh chuka hota hai, phir unko user
ke question ke saath ek prompt template mein insert kiya jaata hai, aur ek
language model us text mein grounded ek answer generate karta hai. Yeh
file bas itna karti hai — "teen providers mein se ek ko ek finished prompt
ke saath call karo" — Projects 1 aur 2 wala wahi multi-provider pattern,
bas is project ki zarurat ke hisaab se trim kiya hua.
============================================================================
"""

import os
from typing import Optional

RAG_PROMPT_TEMPLATE = """Answer the question using ONLY the context below. If the context doesn't \
contain enough information to answer, say so plainly instead of guessing.

Context:
{context}

Question: {question}

Answer:"""


def build_prompt(question: str, chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(chunks)
    return RAG_PROMPT_TEMPLATE.format(context=context, question=question)


async def call_ollama(model: str, prompt: str) -> str:
    import ollama

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    client = ollama.AsyncClient(host=host)
    try:
        response = await client.chat(model=model, messages=[{"role": "user", "content": prompt}])
    except ollama.ResponseError as exc:
        raise RuntimeError(f"Ollama error: {exc.error} — did you run 'ollama pull {model}'?") from exc
    except Exception as exc:
        raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc
    return response["message"]["content"]


async def call_openai(model: str, prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    response = await client.chat.completions.create(model=model, messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content or ""


async def call_anthropic(model: str, prompt: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set — add it to backend/.env to enable this provider")

    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model=model, max_tokens=1024, messages=[{"role": "user", "content": prompt}]
    )
    return "".join(block.text for block in response.content if block.type == "text")


CALLERS = {"ollama": call_ollama, "openai": call_openai, "anthropic": call_anthropic}


async def generate(provider: str, model: str, question: str, chunks: list[str]) -> str:
    caller = CALLERS.get(provider)
    if caller is None:
        raise RuntimeError(f"unknown provider '{provider}'")
    prompt = build_prompt(question, chunks)
    return await caller(model, prompt)
