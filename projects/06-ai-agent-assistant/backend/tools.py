"""
============================================================================
 TOOLS — teen cheezein jo yeh agent actually kar sakta hai
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

Is project ka har agent engine (agent_react.py, agent_functions.py,
agent_responses.py) yeh EXACT same set of tools share karta hai aur inhe
run karne ke liye EXACT same execute_tool() function call karta hai. Yeh
jaan-bujh kar kiya gaya hai: is project ka comparison "teen engines tool
use ko kitne alag tarike se orchestrate kar sakte hain" ke baare mein hai,
"kya unke paas alag tools hain" ke baare mein nahi — capabilities kabhi
change nahi hoti, sirf model unhe use karne tak kaise pahunchta hai,
woh change hota hai.

Teen tools hain, har ek genuinely ek alag tarah ki capability:

  calculator       — pure computation, koi network bilkul nahi
  search_handbook  — PRIVATE knowledge: is project ka apna local document
                      index (Project 5 wali wahi AI-engineering handbook)
  wikipedia_search — PUBLIC knowledge: ek free, keyless API ko asli
                      network call

Ek achhe multi-step test question ke liye inme se ek se zyada chahiye
hote hain — jaise "Handbook mein dekho RAG kya hai, phir Wikipedia par
'HNSW' dekho, aur batao dono ka relation kya hai" — isko genuinely do
alag tool calls chahiye, uske baad hi model ke paas answer dene layak
kaafi information hoti hai.
============================================================================
"""

import ast
import operator

import httpx

# --------------------------------------------------------------------------
# Tool 1: calculator
# --------------------------------------------------------------------------
# Jaan-bujh kar Python ka `eval()` use NAHI kiya — usse ek malicious (ya
# bas creative) prompt arbitrary Python code inject kar sakta tha, kyunki
# eval() KUCH BHI run kar deta hai, sirf arithmetic nahi. Iske bajaye,
# `ast.parse()` expression ke structure ka ek tree banata hai, aur
# _eval_node() ko sirf ek chhoti, fixed allow-list ke node types chalana
# aata hai: numbers aur unke beech +, -, *, /, **. Kuch aur bhi (function
# call, variable name, import) ke liye neeche koi matching case nahi hai,
# aur woh chupchap chalne ke bajaye raise karta hai.

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"unsupported expression: {ast.dump(node)}")


def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
    except Exception:
        return f"Error: '{expression}' isn't a valid arithmetic expression (only numbers and + - * / ** are allowed)."
    return str(result)


# --------------------------------------------------------------------------
# Tool 2: search_handbook — is project ka apna local document index
# --------------------------------------------------------------------------


def search_handbook(query: str) -> str:
    from embeddings import embed
    from vector_store import count, search

    if count() == 0:
        return "Error: the handbook hasn't been indexed yet — run ingest.py first."

    query_vector = embed([query])[0]
    results = search(query_vector, top_k=3)
    if not results:
        return "No relevant passages found in the handbook."

    return "\n\n".join(f"(from {r['source']}) {r['text']}" for r in results)


# --------------------------------------------------------------------------
# Tool 3: wikipedia_search — asli network call, koi API key nahi chahiye
# --------------------------------------------------------------------------


def wikipedia_search(topic: str) -> str:
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic.strip().replace(' ', '_')}"
    try:
        response = httpx.get(url, timeout=10, headers={"User-Agent": "ai-engineer-learning-project"})
    except httpx.RequestError as exc:
        return f"Error: couldn't reach Wikipedia ({exc})."

    if response.status_code == 404:
        return f"No Wikipedia page found for '{topic}'. Try a different or more specific topic."
    if response.status_code != 200:
        return f"Error: Wikipedia returned status {response.status_code}."

    return response.json().get("extract", "No summary available for this page.")


# --------------------------------------------------------------------------
# Shared registry — har engine isi ek dictionary ke through dispatch
# karta hai, isliye baad mein 4tha tool add karna matlab isko yahan EK
# BAAR add karna hai, teen jagah nahi.
# --------------------------------------------------------------------------

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "search_handbook": search_handbook,
    "wikipedia_search": wikipedia_search,
}

# Plain-language descriptions, jo BOTH ReAct text prompt (agent_react.py
# inhe haath se prompt mein build karta hai) aur neeche ke tool schemas
# (OPENAI_TOOL_SCHEMAS inhi descriptions ko structured JSON format mein
# badal deta hai jo OpenAI ki function calling expect karti hai) dono
# share karte hain.
TOOL_DESCRIPTIONS = {
    "calculator": "Evaluates a basic arithmetic expression (numbers and + - * / **). Input: a math expression as a string, e.g. '12 * (3 + 4)'.",
    "search_handbook": "Searches this project's own AI-engineering handbook (covers RAG, embeddings, prompt engineering, agents, safety, fine-tuning). Input: a search query.",
    "wikipedia_search": "Looks up a topic on Wikipedia and returns a short summary. Input: a topic or article title, e.g. 'Alan Turing'.",
}

OPENAI_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": {"input": {"type": "string", "description": "The input to this tool."}},
                "required": ["input"],
            },
        },
    }
    for name, description in TOOL_DESCRIPTIONS.items()
]


def execute_tool(name: str, tool_input: str) -> str:
    """Woh ek jagah jise har engine ek tool ko actually RUN karne ke liye
    call karta hai. Kabhi raise nahi karta — ek unknown tool name ho ya
    tool-level failure, dono ek plain string ban ke wapas aate hain,
    kyunki model ke nazariye se ek fail hua tool call bas ek aur
    observation hai jispar reason karna hai, koi crash nahi."""
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Error: no such tool '{name}'. Available tools: {', '.join(TOOL_FUNCTIONS)}."
    try:
        return func(tool_input)
    except Exception as exc:
        return f"Error running {name}: {exc}"
