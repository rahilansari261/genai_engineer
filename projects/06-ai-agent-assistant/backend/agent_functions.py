"""
============================================================================
 AGENT FUNCTIONS — wahi loop, lekin OpenAI ke native tool calling ke saath
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Isko agent_react.py se compare karo. Kaam wahi hai — model ka response
padho, dekho ki woh koi tool call karna chahta hai ya nahi, tool run karo,
result wapas feed karo, aur repeat karo — lekin model ke "Action:
calculator" jaisa plain text likhne ke bajaye jise HUM regex se parse
karte hain, OpenAI ka API humein tool SCHEMAS ki ek list dene deta hai
(tools.py ka OPENAI_TOOL_SCHEMAS — structured JSON jo har tool ka naam
aur inputs describe karta hai), aur model free text ke bajaye ek
structured `tool_calls` field ke saath reply karta hai. Koi parsing nahi
chahiye — lekin dhyan rahe, yeh sirf us provider ke saath kaam karta hai
jiska API actually is feature ko support karta hai (yahan OpenAI; Ollama
ka chat API yeh same structured tool-calling contract offer nahi karta),
aur isi wajah se agent_react.py ka plain-text approach jaanna abhi bhi
important hai: woh har jagah kaam karta hai.

Yeh abhi bhi ek MANUAL implementation hai — yahan kuch bhi koi "agent
framework" nahi hai. Loop humesha hum khud likh rahe hain: model ko call
karo, tool_calls check karo, unhe khud run karo, results append karo,
model ko phir se call karo. OpenAI ka contribution bas ek cleaner tarika
hai tool request maangne aur paane ka, khud loop nahi.
============================================================================
"""

import json
import os

from tools import OPENAI_TOOL_SCHEMAS, execute_tool

SYSTEM_PROMPT = "You are a helpful assistant. Use the available tools whenever they would help answer the question."


async def run(question: str, model: str, max_steps: int = 6) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        error = "OPENAI_API_KEY not set — add it to backend/.env to enable this engine"
        return {"trace": [{"type": "error", "content": error}], "final_answer": None, "error": error}

    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    trace = []

    for step in range(max_steps):
        try:
            response = await client.chat.completions.create(model=model, messages=messages, tools=OPENAI_TOOL_SCHEMAS)
        except Exception as exc:
            trace.append({"type": "error", "content": str(exc)})
            return {"trace": trace, "final_answer": None, "error": str(exc)}

        message = response.choices[0].message

        if not message.tool_calls:
            final_answer = message.content or ""
            trace.append({"type": "final", "content": final_answer})
            return {"trace": trace, "final_answer": final_answer, "error": None}

        # Model ek hi turn mein MULTIPLE tool calls request kar sakta hai —
        # OpenAI ka API isko support karta hai, chahe hamara ReAct text
        # format (ek turn mein ek Action) support nahi karta. Hum har ek
        # ko run karte hain aur model ko continue karne se pehle sabka
        # jawab report kar dete hain.
        messages.append(message.model_dump(exclude_unset=True))

        for tool_call in message.tool_calls:
            try:
                tool_input = json.loads(tool_call.function.arguments).get("input", "")
            except json.JSONDecodeError:
                tool_input = tool_call.function.arguments  # model ne valid JSON nahi bheja — jaisa hai waisa hi aage bhej do

            trace.append({"type": "action", "tool": tool_call.function.name, "content": tool_input})
            observation = execute_tool(tool_call.function.name, tool_input)
            trace.append({"type": "observation", "tool": tool_call.function.name, "content": observation})

            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": observation})

    trace.append({"type": "error", "content": f"Stopped after {max_steps} steps without a final answer."})
    return {"trace": trace, "final_answer": None, "error": f"Ran out of steps ({max_steps}) before reaching a final answer."}
