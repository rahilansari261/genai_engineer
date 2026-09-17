"""
============================================================================
 AI AGENT ASSISTANT API
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Teen endpoints hain, ek-ek har engine ke liye, aur sab EXACT same tools
(tools.py) use karte hain aur EXACT same trace shape return karte hain —
{type, tool?, content} steps ki ek list, jo final answer ya error par
khatam hoti hai. Yahi shared shape hai jiski wajah se EK frontend
component teeno engines ki reasoning ko same tarike se render kar paata
hai — isliye jo differences tumhe ACTUALLY dikhenge, woh yeh hain ki har
engine apne answer tak kaise pahuncha, na ki alag-alag UIs ki wajah se.

  POST /agent/react      -> agent_react.py      (plain-text ReAct loop; Ollama ya OpenAI dono ke saath chalta hai)
  POST /agent/functions  -> agent_functions.py  (OpenAI ka native tool calling, manual loop)
  POST /agent/responses  -> agent_responses.py  (OpenAI Responses API — modern Assistants API ka replacement)
============================================================================
"""

from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import agent_functions
import agent_react
import agent_responses
import vector_store

load_dotenv()

app = FastAPI(title="AI Agent Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TraceStep(BaseModel):
    type: str  # in se ek value: "thought" | "action" | "observation" | "final" | "error"
    tool: Optional[str] = None
    content: str


class AgentResponse(BaseModel):
    trace: List[TraceStep]
    final_answer: Optional[str] = None
    error: Optional[str] = None


class ReactRequest(BaseModel):
    question: str
    provider: str = "ollama"
    model: str = "llama3.2"
    max_steps: int = 6


@app.post("/agent/react", response_model=AgentResponse)
async def react(req: ReactRequest):
    result = await agent_react.run(req.question, req.provider, req.model, req.max_steps)
    return AgentResponse(**result)


class OpenAIAgentRequest(BaseModel):
    question: str
    model: str = "gpt-4o-mini"
    max_steps: int = 6


@app.post("/agent/functions", response_model=AgentResponse)
async def functions(req: OpenAIAgentRequest):
    result = await agent_functions.run(req.question, req.model, req.max_steps)
    return AgentResponse(**result)


@app.post("/agent/responses", response_model=AgentResponse)
async def responses(req: OpenAIAgentRequest):
    result = await agent_responses.run(req.question, req.model, req.max_steps)
    return AgentResponse(**result)


@app.get("/status")
async def status():
    count = vector_store.count()
    return {"handbook_indexed": count > 0, "handbook_count": count}


@app.get("/health")
async def health():
    return {"status": "ok"}
