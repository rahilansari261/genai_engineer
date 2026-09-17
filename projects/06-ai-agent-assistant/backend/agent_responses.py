"""
============================================================================
 AGENT RESPONSES — OpenAI ka managed, stateful API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Roadmap is node ko "OpenAI Assistant API" bolta hai — lekin jab tak yeh
project banaya gaya, OpenAI apne hi SDK mein poore Assistants API ko
(`client.beta.assistants`, `client.beta.threads`) deprecated maark kar
chuka tha. Ek dead API sikhane ke bajaye, yeh engine uske replacement ko
use karta hai: **Responses API** (`client.responses`), jo isi idea ka
OpenAI ka current, actively-supported jawab hai — ek single API jo
conversation state TUMHARE liye manage karta hai, taaki tum
agent_functions.py ki tarah ek badhti hui `messages` list ko manually
maintain na kar rahe ho.

Mechanism: `previous_response_id` ek call ko agle se link karta hai — tum
kabhi poori conversation history khud dobara nahi bhejte, bas itna kehte
ho "yeh naya input us pehle wale response se continue hota hai." Tool
calls abhi bhi response mein structured items ki tarah dikhte hain (wahi
idea jo agent_functions.py ke `tool_calls` ka hai), aur tumhe abhi bhi
unhe khud run karke result wapas bhejna padta hai — OpenAI CONVERSATION
state manage karta hai, TOOL EXECUTION loop nahi. Woh hissa abhi bhi
tumhara hai, is file mein, jaise is project mein har jagah hai.

Ek shape ka farak jo notice karne layak hai agar isko agent_functions.py
ke OPENAI_TOOL_SCHEMAS se compare karo: Responses API ka tool schema FLAT
hai (`{"type": "function", "name": ..., "parameters": ...}`), Chat
Completions ke schema ki tarah `"function"` key ke andar nested nahi hai —
agar tum maan lo ki har OpenAI API ek hi tool format share karta hai to
yeh galti karna bahut aasaan hai.
============================================================================
"""

import json
import os

from tools import TOOL_DESCRIPTIONS, execute_tool

SYSTEM_PROMPT = "You are a helpful assistant. Use the available tools whenever they would help answer the question."

RESPONSES_TOOL_SCHEMAS = [
    {
        "type": "function",
        "name": name,
        "description": description,
        "parameters": {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "The input to this tool."}},
            "required": ["input"],
        },
    }
    for name, description in TOOL_DESCRIPTIONS.items()
]


async def run(question: str, model: str, max_steps: int = 6) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error = "OPENAI_API_KEY not set — add it to backend/.env to enable this engine"
        return {"trace": [{"type": "error", "content": error}], "final_answer": None, "error": error}

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    trace = []

    # Pehli call conversation start karti hai; uske baad ki har call apne
    # aap history dobara bhejne ke bajaye previous_response_id se peeche
    # link kar deti hai.
    try:
        response = await client.responses.create(
            model=model, instructions=SYSTEM_PROMPT, input=question, tools=RESPONSES_TOOL_SCHEMAS
        )
    except Exception as exc:
        return {"trace": [{"type": "error", "content": str(exc)}], "final_answer": None, "error": str(exc)}

    for step in range(max_steps):
        function_calls = [item for item in response.output if item.type == "function_call"]

        if not function_calls:
            final_answer = response.output_text
            trace.append({"type": "final", "content": final_answer})
            return {"trace": trace, "final_answer": final_answer, "error": None}

        tool_outputs = []
        for call in function_calls:
            try:
                tool_input = json.loads(call.arguments).get("input", "")
            except json.JSONDecodeError:
                tool_input = call.arguments

            trace.append({"type": "action", "tool": call.name, "content": tool_input})
            observation = execute_tool(call.name, tool_input)
            trace.append({"type": "observation", "tool": call.name, "content": observation})

            tool_outputs.append({"type": "function_call_output", "call_id": call.call_id, "output": observation})

        try:
            response = await client.responses.create(
                model=model,
                previous_response_id=response.id,
                input=tool_outputs,
                tools=RESPONSES_TOOL_SCHEMAS,
            )
        except Exception as exc:
            trace.append({"type": "error", "content": str(exc)})
            return {"trace": trace, "final_answer": None, "error": str(exc)}

    trace.append({"type": "error", "content": f"Stopped after {max_steps} steps without a final answer."})
    return {"trace": trace, "final_answer": None, "error": f"Ran out of steps ({max_steps}) before reaching a final answer."}
