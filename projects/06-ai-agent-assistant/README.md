# 06 — AI Agent Assistant

A tool-using agent — built three different ways — that plans multi-step tasks and calls real tools (a calculator, a private document search, a live Wikipedia lookup) to get things done, not just answer in one shot.

## What problem does this solve?

"Agent" has become a marketing word slapped on almost anything that calls an LLM, so it's genuinely hard to tell what actually makes something an agent versus just a chatbot with a clever system prompt. The real difference is concrete: an agent decides *for itself*, step by step, which tools to call and in what order, based on what it observes along the way — a single RAG lookup can't do that. This project builds that reasoning loop by hand first (no framework hiding it), so "the model chose to call a tool" stops being magic and becomes a mechanism you understand and can debug.

## What you'll learn

- **AI Agents / Agents Usecases / RAG Alternative** — see where an agent earns its complexity over a plain RAG chatbot: when a task needs *multiple* steps and tool calls, not just one retrieval
- **ReAct Prompting / Manual Implementation** — a bare-bones reason-act-observe loop, built entirely out of plain text and a regex parser, that works with ANY chat model — including free, local Ollama
- **OpenAI Functions / Tools** — the same manual loop, rebuilt using OpenAI's structured tool-calling instead of text parsing
- **OpenAI Assistant API** — see the note below on why this project uses the **Responses API** instead, and what that substitution itself teaches
- **Building AI Agents** — three working implementations of the same agent, sharing one tool registry, so the comparison is honest

## A note on "OpenAI Assistant API"

The roadmap names this node, but by the time this project was built, OpenAI's own Python SDK had marked the entire Assistants API (`client.beta.assistants`, `client.beta.threads`) as deprecated — confirmed by inspecting the installed SDK directly rather than assuming. Teaching a dead API would be a bad trade, so this project's third engine uses the **Responses API** (`client.responses`) instead — OpenAI's current, actively-supported answer to the same underlying idea: a managed API that tracks conversation state for you (via `previous_response_id`) instead of you maintaining a growing message list by hand. The lesson underneath — "here's what a provider's own managed state-tracking buys you over doing it yourself" — is the same one the roadmap intended; only the specific API changed. See `backend/agent_responses.py`'s file comment for the full explanation, including a real gotcha: the Responses API's tool schema is a different (flatter) shape than Chat Completions', discovered by inspecting the SDK's types rather than guessing.

## Builds on

[05 — RAG Chatbot](../05-rag-chatbot/README.md) — the `search_handbook` tool is the same retrieval idea (embed a query, search a Chroma index, return the closest chunks) reused as ONE callable tool instead of the whole app. This project ships its own copy of the same 6-doc handbook so it works standalone.

## Tech stack

Python/FastAPI backend, three agent engines sharing one tool registry, Next.js frontend that renders every engine's step-by-step trace (thought → action → observation) the same way. Same setup as every other project: a Python venv for the backend, Ollama installed natively on your machine, `npm run dev` for the frontend.

## How it works, in one picture

```
  tools.py: calculator (safe ast-based eval, no real eval()) | search_handbook (local Chroma) | wikipedia_search (free, no-key API)
        |
        +-- agent_react.py:      plain-text "Thought/Action/Action Input" prompt, WE parse it with regex   (Ollama or OpenAI)
        +-- agent_functions.py:  OpenAI's native tool_calls, WE still write the loop                       (OpenAI only)
        +-- agent_responses.py:  OpenAI Responses API, previous_response_id tracks state for us             (OpenAI only)
        |
        v
  POST /agent/{react,functions,responses} -> { trace: [{type, tool?, content}, ...], final_answer, error }
        |
        v
  Frontend's TraceView renders any engine's trace the same way — the comparison is fair because the shape never changes
```

Read `backend/tools.py` first (the shared capabilities), then `backend/agent_react.py` and `backend/agent_functions.py` back to back — same job, text parsing vs. structured tool calls.

## What you'll build

- Three agent engines answering the same question with the same three tools: `agent_react.py` (provider-agnostic text parsing), `agent_functions.py` (OpenAI native tool calling), `agent_responses.py` (OpenAI's managed Responses API)
- A calculator tool that's actually safe — built on Python's `ast` module rather than `eval()`, so a prompt can't inject arbitrary code through it (verified directly: `calculator('__import__("os").system("echo pwned")')` correctly returns an error, not a shell command execution)
- A live trace view showing every thought, tool call, and observation, not just the final answer
- A configurable step cap, so you can watch an agent get cut off mid-reasoning instead of just reading about it as a hypothetical

## What actually happened when this was tested

Two real things surfaced during verification, both left as-is rather than smoothed over, because they're honest lessons:

1. **A chunking bug changed the answer.** The first version of `ingest.py` split the handbook naively on blank lines, which turned each markdown heading into its own tiny, content-free chunk. `search_handbook` returned those heading fragments instead of real explanations, and llama3.2 confidently hallucinated that "RAG" stood for "Rejection-Augmentation-Guidance." Swapping in Project 5's proper chunker (`chunking.py`, merges small pieces up to `chunk_size`) fixed it — a direct, visible example of why chunking quality matters, not just a claim.
2. **A real run hit the step cap.** Asked to connect the handbook's explanation of RAG to Wikipedia's HNSW article, llama3.2 (a small model) kept searching instead of synthesizing an answer, and the ReAct engine correctly stopped it after 6 steps with a clear "ran out of steps" error — exactly the stretch goal behavior, produced by an honest run, not staged.

## Stretch goals

- Swap in a bigger or different Ollama model for the ReAct engine and see if it reaches a final answer in fewer steps on the same question
- Add a 4th tool and watch all three engines pick it up automatically (they all read from the same `tools.py` registry)
- Add `anthropic` support to `agent_react.py`'s `_call_model()` — it already supports two providers, a third follows the same pattern

## Setup & run

You need [Ollama](https://ollama.com) installed and running on your machine (it listens on `localhost:11434` by default), with a model pulled:

```bash
ollama pull llama3.2
```

### 1. Set up and build the handbook search index (Terminal 1, one-time step)

```bash
cd projects/06-ai-agent-assistant/backend

python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env   # OPENAI_API_KEY optional — ReAct + Ollama works with nothing filled in

python ingest.py
```

### 2. Run the backend (same terminal)

```bash
uvicorn main:app --reload --port 8000
```

Check it worked: [http://localhost:8000/health](http://localhost:8000/health).

### 3. Run the frontend (Terminal 2)

```bash
cd projects/06-ai-agent-assistant/frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). The ReAct engine (Ollama) works with zero API keys — try it first, then add `OPENAI_API_KEY` to unlock the other two engines.

### 4. To stop everything

`Ctrl+C` in both terminals.

Note: this project's backend also defaults to port 8000. Don't run it at the same time as another project's backend without changing one of their ports (`uvicorn main:app --port 8030`, and update the frontend's `.env.local` to match).
