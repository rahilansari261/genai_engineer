# AI Agents and Tool Use

An AI agent is a system where a language model doesn't just generate one reply to one prompt, but repeatedly decides what to do next — including which external tools to call — based on what it observes after each step, continuing until it decides the task is complete. The defining feature of an agent is this loop of reasoning, acting, and observing, rather than a single request-response exchange.

## The ReAct pattern

ReAct, short for "Reason and Act," is the most common pattern underlying agent implementations. On each cycle, the model produces a short piece of reasoning about what it should do next, chooses an action (usually a tool call) based on that reasoning, receives the result of that action as an observation, and then repeats the cycle with that new information available. This continues until the model decides it has enough information to produce a final answer. Writing this loop by hand — rather than only ever using a framework's built-in agent class — is valuable specifically because it makes the mechanism visible: there is no hidden magic, just a model whose output is parsed for an action, that action is executed in ordinary code, and the result is appended back into the conversation before asking the model again.

## Tool calling, also called function calling

Most modern model providers support a structured way to give a model a list of available tools, each described by a name, a description, and a schema for its expected arguments. The model doesn't execute the tool itself — it can only output a request to call one, with specific argument values, which your own application code is responsible for actually running before feeding the result back to the model. This division of responsibility matters for safety: the model proposes, your code disposes, so a tool that deletes a file or sends a real payment still passes through code you control and can gate with confirmation, rate limits, or permission checks before it actually runs.

## When an agent is the right tool, and when it's overkill

A plain RAG chatbot answers a question by retrieving relevant text once and generating a single reply — it never decides on its own to make a second search, call a calculator, or check a different data source partway through. An agent is worth the added complexity specifically when a task genuinely requires multiple, dependent steps chosen dynamically: looking something up, then computing something based on what it found, then looking up something else based on that result. For a task that can be answered by a single retrieval and a single generation step, wrapping it in an agent loop adds latency, cost, and failure modes — extra model calls that can each go wrong — without adding real capability. The rule of thumb is to reach for an agent only once a single retrieve-then-generate step has been tried and shown to be insufficient.

## Common failure modes

Agents can loop indefinitely if a tool call keeps returning a result the model doesn't recognize as sufficient, which is why production agent implementations always include a maximum step count as a hard stop. Agents can also choose the wrong tool or invent arguments that don't correspond to anything the tool can actually do, particularly when tool descriptions are vague or too similar to each other. Testing an agent means testing not just whether it reaches the right final answer, but whether the sequence of tool calls it took along the way was sensible — two agents can arrive at the same correct answer, one by using three tools efficiently and the other by using nine tools and getting lucky, and only the trace of tool calls reveals the difference.
