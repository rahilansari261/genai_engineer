"""
============================================================================
 AGENT — poora capstone ek hi loop mein: guarded, tool-using, cost-tracked
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh Project 6 ka ReAct loop hai (agent_react.py) — wahi text-based
Thought/Action/Action Input format, wahi regex parser, wahi provider-
agnostic design (Ollama free, OpenAI paid) — bas iske upar teen cheezein
jod di gayi hain jo isko "ek agent demo" se badal kar "woh cheez jiske liye
poora repo ban raha tha" bana deti hain:

  1. SAFETY (Project 2) — user ka message loop shuru hone se PEHLE moderate
     hota hai, aur final answer bhi user ko dikhane se pehle dobara
     moderate hota hai, bilkul AI Safety Sandbox ki tarah. Toggle ko off
     karke dekho, ek prompt-injection attempt jo normally pakda jaata
     (guardrails.py dekho) seedha through nikal jaata hai — wahi
     before/after comparison, bas ab yeh ek plain chat ki jagah ek
     tool-using agent ko defend kar raha hai.

  2. MULTIMODAL TOOLS (Project 7) — `describe_image` aur `generate_image`
     bas tool list mein do aur entries hain. Agent decide karta hai ki
     attached image ko dekhna hai, naya image generate karna hai, ya
     kuch bhi nahi — bilkul usi tarah jaise woh decide karta hai ki
     handbook search karna hai ya arithmetic karni hai. Vision aur image
     generation ko yahan special-case nahi kiya gaya — woh bhi baaki
     tools jaise hi tools hain.

  3. COST TRACKING (Project 1) — is loop ki har OpenAI call (reasoning
     steps khud, plus koi bhi OpenAI-backed tool call) apni token cost
     wapas yahan report karti hai, jo poore turn ke liye ek total mein
     accumulate hoti hai. Ollama calls $0 contribute karti hain, kyunki
     woh free hain — yahi to pura point hai ek free engine rakhne ka.

CONVERSATION MEMORY bhi naya hai: `history` is conversation ke pehle ke
turns hain (frontend ke paas rakhe jaate hain, har request ke saath wapas
bheje jaate hain — main.py dekho), jo messages list mein naye question se
pehle prepend kiye jaate hain, taaki agent ko sach mein yaad rahe ki tumne
teen message pehle kya poocha tha.
============================================================================
"""

import os
import re

from guardrails import SYSTEM_PROMPT
from moderation import moderate
from pricing import estimate_chat_cost
from tools import TOOL_DESCRIPTIONS, ToolContext, execute_tool

REACT_FORMAT = """You have access to these tools:

{tool_list}

Use EXACTLY this format, one block per turn:

Thought: <your reasoning about what to do next>
Action: <one tool name, exactly as listed above>
Action Input: <the input to give that tool>

Stop immediately after "Action Input:" and wait — you will be given an "Observation:" with the tool's result before you continue.

Once you have enough information to answer, respond with:

Thought: <your final reasoning>
Final Answer: <your answer to the user's message>

Never skip straight to an answer without at least one Thought. Never invent an Observation yourself — only react to the real ones you're given."""


def _build_system_prompt(safety: bool) -> str:
    tool_list = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items())
    react_block = REACT_FORMAT.format(tool_list=tool_list)
    # Safety off hone par agent ko SIRF bare tool instructions milte hain —
    # koi defensive rules bilkul nahi. Yahi gap hi to pura point hai: dekho
    # kitni aasani se ek prompt injection andar ghus jaata hai jab kuch bhi
    # guard karne wala na ho.
    return f"{SYSTEM_PROMPT}\n\n{react_block}" if safety else react_block


def _parse(text: str) -> dict:
    """Project 6 ke parser jaisa hi hai — poora explanation ke liye
    agent_react.py dekho. Agar model format follow nahi karta to poore
    reply ko hi final answer maan liya jaata hai (fallback)."""
    thought_match = re.search(r"Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|\Z)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else None

    final_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if final_match:
        return {"thought": thought, "final_answer": final_match.group(1).strip()}

    action_match = re.search(r"Action:\s*(.+)", text)
    # `.*?` (na ki `.+?`) isliye use kiya hai taaki yeh tab bhi MATCH ho
    # jab model "Action Input:" likh kar usko khaali chhod de — chhote
    # local models sach mein aisa karte hain. `.+?` (kam se kam ek
    # character zaroori) ke saath, ek empty Action Input ki wajah se yeh
    # poora regex match hi nahi karta tha, jo chupchap "raw text ko hi
    # final answer maan lo" wale case mein fall through ho jaata tha aur
    # ek garbled reply banta tha jismein literal words "Action:" aur
    # "Action Input:" aa jaate the — yeh bug testing ke dauraan pakda gaya,
    # project README mein dekho.
    input_match = re.search(r"Action Input:\s*(.*?)(?=\n|\Z)", text, re.DOTALL)
    if action_match and input_match:
        return {"thought": thought, "action": action_match.group(1).strip(), "action_input": input_match.group(1).strip()}

    return {"thought": thought, "final_answer": text.strip()}


async def _call_model(provider: str, model: str, messages: list[dict], user_id: str) -> tuple[str, float]:
    """Return karta hai (reply_text, is_call_ki_cost_usd). Ollama hamesha
    free hai; OpenAI ki cost API ke bataye hue asli token usage se aati
    hai."""
    if provider == "ollama":
        import ollama

        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        client = ollama.AsyncClient(host=host)
        try:
            response = await client.chat(model=model, messages=messages)
        except ollama.ResponseError as exc:
            raise RuntimeError(f"Ollama error: {exc.error} — did you run 'ollama pull {model}'?") from exc
        except Exception as exc:
            raise RuntimeError(f"Can't reach Ollama at {host} — is it running? (try: ollama serve)") from exc
        return response["message"]["content"], 0.0

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        # `user=user_id` — wahi end-user ID pattern jo Project 2 ke
        # providers.py mein tha, taaki OpenAI ka apna abuse detection ek
        # asli user ke requests ka pattern pehchaan sake, na ki sirf ek
        # shared API key ka.
        response = await client.chat.completions.create(model=model, messages=messages, user=user_id)
        usage = response.usage
        cost = estimate_chat_cost(model, usage.prompt_tokens, usage.completion_tokens) if usage else 0.0
        return response.choices[0].message.content or "", cost

    raise RuntimeError(f"unknown provider '{provider}'")


def _empty_result(**overrides) -> dict:
    base = {
        "trace": [],
        "final_answer": None,
        "blocked": False,
        "blocked_layer": None,
        "blocked_categories": [],
        "moderation_available": True,
        "attachments": [],
        "cost_usd": 0.0,
        "error": None,
    }
    base.update(overrides)
    return base


async def run(
    message: str,
    history: list[dict],
    provider: str,
    model: str,
    image_bytes: bytes | None,
    vision_provider: str,
    vision_model: str,
    image_gen_provider: str,
    image_gen_model: str,
    safety: bool,
    user_id: str,
    max_steps: int = 6,
) -> dict:
    total_cost = 0.0
    moderation_available = True

    # -------------------- STEP 1: INPUT KO MODERATE KARO --------------------
    if safety:
        try:
            input_check = await moderate(message)
        except RuntimeError:
            moderation_available = False  # OPENAI_API_KEY nahi hai — note kar liya, fatal nahi hai
        else:
            if input_check.flagged:
                return _empty_result(
                    blocked=True,
                    blocked_layer="input-moderation",
                    blocked_categories=input_check.categories,
                    moderation_available=True,
                )

    ctx = ToolContext(image_bytes, vision_provider, vision_model, image_gen_provider, image_gen_model)
    messages = [
        {"role": "system", "content": _build_system_prompt(safety)},
        *history,
        {"role": "user", "content": message},
    ]
    trace = []

    for _step in range(max_steps):
        try:
            reply_text, step_cost = await _call_model(provider, model, messages, user_id)
        except Exception as exc:
            return _empty_result(
                trace=trace,
                attachments=ctx.generated_images,
                cost_usd=total_cost,
                moderation_available=moderation_available,
                error=str(exc),
            )

        total_cost += step_cost
        parsed = _parse(reply_text)
        messages.append({"role": "assistant", "content": reply_text})

        if parsed.get("thought"):
            trace.append({"type": "thought", "content": parsed["thought"]})

        if "final_answer" in parsed:
            final_answer = parsed["final_answer"]

            # -------------------- STEP 3: OUTPUT KO MODERATE KARO --------------------
            if safety and moderation_available:
                try:
                    output_check = await moderate(final_answer)
                except RuntimeError:
                    pass
                else:
                    if output_check.flagged:
                        return _empty_result(
                            trace=trace,
                            blocked=True,
                            blocked_layer="output-moderation",
                            blocked_categories=output_check.categories,
                            cost_usd=total_cost,
                            moderation_available=True,
                        )

            trace.append({"type": "final", "content": final_answer})
            return _empty_result(
                trace=trace,
                final_answer=final_answer,
                attachments=ctx.generated_images,
                cost_usd=total_cost,
                moderation_available=moderation_available,
            )

        # -------------------- STEP 2: JO TOOL MODEL NE MAANGA HAI USE CHALAO --------------------
        tool_name = parsed["action"]
        tool_input = parsed["action_input"]
        trace.append({"type": "action", "tool": tool_name, "content": tool_input})

        observation = await execute_tool(tool_name, tool_input, ctx)
        trace.append({"type": "observation", "tool": tool_name, "content": observation})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    trace.append({"type": "error", "content": f"Stopped after {max_steps} steps without a final answer."})
    return _empty_result(
        trace=trace,
        attachments=ctx.generated_images,
        cost_usd=total_cost,
        moderation_available=moderation_available,
        error=f"Ran out of steps ({max_steps}) before reaching a final answer.",
    )
