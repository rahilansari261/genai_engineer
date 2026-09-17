"""
============================================================================
 TOOLS — paanch capabilities, teen reuse ki hui, do bilkul nayi
============================================================================
Yeh file kya karti hai, seedhi bhasha mein:

`calculator`, `search_handbook`, aur `wikipedia_search` bilkul Project 6
ke tools hain, bina kisi change ke — yeh proof hai ki ek agent ke liye
bane tools ek dusre agent mein bhi... bas kaam kar jaate hain, jab tak
calling convention (naam andar, text bahar) wahi rehti hai.

`describe_image` aur `generate_image` NAYE hain, aur inko woh cheez
chahiye jo baaki teen ko nahi chahiye: is SPECIFIC message ke saath attach
kiya gaya image tak access, aur woh khud jo image banaate hain use rakhne
ke liye kahin jagah. Ek plain function aisa per-request state apne paas
nahi rakh sakta, isliye yeh dono ek chhote `ToolContext` object ke methods
ke roop mein rehte hain — har chat request ke liye ek fresh instance
(agent.py dekho), jo attached image bytes andar leke aati hai aur koi bhi
generated images bahar leke jaati hai. Baaki har tool ek plain, stateless
function hi rehta hai, kyunki unko in mein se kuch bhi nahi chahiye.
============================================================================
"""

import ast
import operator

import httpx

import image_gen
import vision
from embeddings import embed
from vector_store import count, search

# --------------------------------------------------------------------------
# Stateless tools — spirit mein bilkul Project 6 ke tools.py jaise
# --------------------------------------------------------------------------

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


def search_handbook(query: str) -> str:
    if count() == 0:
        return "Error: the handbook hasn't been indexed yet — run ingest.py first."
    query_vector = embed([query])[0]
    results = search(query_vector, top_k=3)
    if not results:
        return "No relevant passages found in the handbook."
    return "\n\n".join(f"(from {r['source']}) {r['text']}" for r in results)


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
# Stateful tools — per-request context chahiye, isliye yeh functions nahi,
# methods hain
# --------------------------------------------------------------------------


class ToolContext:
    """Har chat request ke liye ek instance. Is SPECIFIC message ke saath
    attach hua image andar leke aata hai, aur is SPECIFIC turn ke dauraan
    generate hue kisi bhi image ko bahar collect karta hai — agent.py
    dekho, jo loop shuru hone se pehle inmein se ek banata hai aur loop
    khatam hone ke baad `generated_images` wapas padhta hai."""

    def __init__(
        self,
        image_bytes: bytes | None,
        vision_provider: str,
        vision_model: str,
        image_gen_provider: str,
        image_gen_model: str,
    ):
        self.image_bytes = image_bytes
        self.vision_provider = vision_provider
        self.vision_model = vision_model
        self.image_gen_provider = image_gen_provider
        self.image_gen_model = image_gen_model
        self.generated_images: list[str] = []  # is turn mein bane base64 PNGs

    async def describe_image(self, question: str) -> str:
        if self.image_bytes is None:
            return "Error: no image is attached to this message — ask the user to attach one first."
        if self.vision_provider == "openai":
            return await vision.describe_openai(self.image_bytes, question, self.vision_model)
        return await vision.describe_ollama(self.image_bytes, question, self.vision_model)

    async def generate_image(self, prompt: str) -> str:
        if self.image_gen_provider == "openai":
            image_base64 = await image_gen.generate_openai(prompt)
        else:
            image_base64 = image_gen.generate_huggingface(prompt, self.image_gen_model)
        self.generated_images.append(image_base64)
        return f"Generated an image for the prompt '{prompt}'. It will be shown to the user below this message."


TOOL_DESCRIPTIONS = {
    "calculator": "Evaluates a basic arithmetic expression (numbers and + - * / **). Input: a math expression as a string, e.g. '12 * (3 + 4)'.",
    "search_handbook": "Searches this project's own AI-engineering handbook (covers RAG, embeddings, prompt engineering, agents, safety, fine-tuning). Input: a search query.",
    "wikipedia_search": "Looks up a topic on Wikipedia and returns a short summary. Input: a topic or article title, e.g. 'Alan Turing'.",
    "describe_image": "Answers a question about the image attached to the current message, if any. Input: your question about the image.",
    "generate_image": "Generates a new image from a text description. Input: a description of the image to create.",
}


async def execute_tool(name: str, tool_input: str, ctx: ToolContext) -> str:
    """Woh ek jagah jahan agent loop kisi tool ko actually chalaane ke
    liye call karta hai — Project 6 ke execute_tool() jaisa hi hai, bas ab
    async hai (describe_image aur generate_image dono network calls karte
    hain) aur context-aware hai."""
    try:
        if name == "calculator":
            return calculator(tool_input)
        if name == "search_handbook":
            return search_handbook(tool_input)
        if name == "wikipedia_search":
            return wikipedia_search(tool_input)
        if name == "describe_image":
            return await ctx.describe_image(tool_input)
        if name == "generate_image":
            return await ctx.generate_image(tool_input)
    except Exception as exc:
        return f"Error running {name}: {exc}"
    return f"Error: no such tool '{name}'. Available tools: {', '.join(TOOL_DESCRIPTIONS)}."
