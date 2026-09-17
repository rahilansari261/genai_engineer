"""
============================================================================
 AGENT REACT — ReAct loop, poori tarah plain text se bana hua
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Yeh agents banane ka ORIGINAL tarika hai, us waqt se pehle jab kisi bhi
model provider ne structured "function calling" offer nahi ki thi — aur
isko pehle banana isliye zaroori hai kyunki yeh KISI BHI chat model ke
saath kaam karta hai, free local models (Ollama ke through) bhi included,
kyunki isko model ki bas ek text format follow karne ki ability chahiye,
aur kuch nahi.

Idea (ReAct paper se — "Reason and Act"): hum model ko, uske instructions
mein, hamesha in do shapes mein se ek mein respond karne ko bolte hain:

    Thought: <reasoning>
    Action: <tool name>
    Action Input: <input to the tool>

ya, jab uske paas answer dene layak kaafi information ho jaaye:

    Thought: <reasoning>
    Final Answer: <the answer>

HUM — na ki model, na koi framework — hi woh text plain string parsing se
padhte hain (dekho _parse()), pata karte hain ki usne kaunsa tool maanga
hai, usko actually run karte hain (tools.py), aur result ko model ke agle
turn ke liye "Observation:" bana ke wapas paste kar dete hain. Is loop ka
har hissa is file mein tumhe seedha dikh raha hai — koi hidden mechanism
nahi hai.
============================================================================
"""

import os
import re

from tools import TOOL_DESCRIPTIONS, execute_tool

SYSTEM_PROMPT = """You are an assistant that can use tools to answer questions. You have access to these tools:

{tool_list}

Use EXACTLY this format, one block per turn:

Thought: <your reasoning about what to do next>
Action: <one tool name, exactly as listed above>
Action Input: <the input to give that tool>

Stop immediately after "Action Input:" and wait — you will be given an "Observation:" with the tool's result before you continue.

Once you have enough information to answer the original question, respond with:

Thought: <your final reasoning>
Final Answer: <your answer to the question>

Never skip straight to an answer without at least one Thought. Never invent an Observation yourself — only react to the real ones you're given."""


def _build_system_prompt() -> str:
    tool_list = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items())
    return SYSTEM_PROMPT.format(tool_list=tool_list)


def _parse(text: str) -> dict:
    """Model ke raw text reply mein se ek Thought/Action/Action Input block
    YA ek Thought/Final Answer block nikalta hai. Agar model ne format
    follow nahi kiya to poore reply ko hi final answer maan leta hai —
    chhote/local models kabhi-kabhi format se bhatak jaate hain, aur
    unparseable text par hamesha ke liye loop karna, usne jo actually kaha
    woh dikha dena se zyada bura hoga."""
    thought_match = re.search(r"Thought:\s*(.+?)(?=\n(?:Action|Final Answer):|\Z)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else None

    final_match = re.search(r"Final Answer:\s*(.+)", text, re.DOTALL)
    if final_match:
        return {"thought": thought, "final_answer": final_match.group(1).strip()}

    action_match = re.search(r"Action:\s*(.+)", text)
    input_match = re.search(r"Action Input:\s*(.+?)(?=\n|\Z)", text, re.DOTALL)
    if action_match and input_match:
        return {"thought": thought, "action": action_match.group(1).strip(), "action_input": input_match.group(1).strip()}

    # Format follow nahi hua — raw text ko hi best-effort answer maan lo.
    return {"thought": thought, "final_answer": text.strip()}


async def _call_model(provider: str, model: str, messages: list[dict]) -> str:
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
        return response["message"]["content"]

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set — add it to backend/.env to enable this provider")
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key)
        response = await client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content or ""

    raise RuntimeError(f"unknown provider '{provider}' (the ReAct engine supports ollama and openai)")


async def run(question: str, provider: str, model: str, max_steps: int = 6) -> dict:
    """ReAct loop ko start se end tak chalata hai aur poora trace return
    karta hai — raaste mein aaya har thought, action, aur observation, na
    ki sirf final answer, taaki UI poora reasoning process dikha sake."""
    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {"role": "user", "content": question},
    ]
    trace = []

    for step in range(max_steps):
        try:
            reply = await _call_model(provider, model, messages)
        except Exception as exc:
            trace.append({"type": "error", "content": str(exc)})
            return {"trace": trace, "final_answer": None, "error": str(exc)}

        parsed = _parse(reply)
        messages.append({"role": "assistant", "content": reply})

        if parsed.get("thought"):
            trace.append({"type": "thought", "content": parsed["thought"]})

        if "final_answer" in parsed:
            trace.append({"type": "final", "content": parsed["final_answer"]})
            return {"trace": trace, "final_answer": parsed["final_answer"], "error": None}

        tool_name = parsed["action"]
        tool_input = parsed["action_input"]
        trace.append({"type": "action", "tool": tool_name, "content": tool_input})

        observation = execute_tool(tool_name, tool_input)
        trace.append({"type": "observation", "tool": tool_name, "content": observation})
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    # Steps khatam ho gaye — yeh project ke stretch goals wala "steps ki
    # ginti cap karo" behavior hai, chhupaya nahi gaya balki saaf dikhaya
    # gaya hai.
    trace.append({"type": "error", "content": f"Stopped after {max_steps} steps without a final answer."})
    return {"trace": trace, "final_answer": None, "error": f"Ran out of steps ({max_steps}) before reaching a final answer."}
