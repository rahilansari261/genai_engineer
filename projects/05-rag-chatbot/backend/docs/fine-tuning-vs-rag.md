# Fine-Tuning versus RAG

Fine-tuning and RAG are both ways of adapting a general-purpose language model to a specific need, but they solve different problems, and the most common mistake teams make is reaching for fine-tuning when RAG was the right tool, or the reverse.

## What fine-tuning actually changes

Fine-tuning continues training an existing model's weights on a smaller, task-specific dataset, nudging its internal parameters so it produces outputs closer to the examples it was fine-tuned on. This is genuinely effective at teaching a model a *style*, a *format*, or a *skill* — for example, always responding in a particular brand voice, reliably producing a specific structured output format, or getting noticeably better at a narrow task like classifying support tickets into a fixed set of categories. What fine-tuning does not reliably do is teach a model new *facts* in a way it can dependably recall and cite later — a model can be fine-tuned on thousands of examples containing a fact and still fail to reproduce that fact accurately in a new context, because fine-tuning nudges general behavior rather than storing retrievable, citable information.

## What RAG actually changes

RAG changes nothing about the model itself. It changes what information the model has in front of it at the moment it generates an answer, by retrieving relevant text and placing it directly in the prompt. This makes RAG the correct tool specifically for factual, citable, frequently-changing information: today's inventory levels, this week's documentation update, a specific customer's account history. Update the underlying documents and a RAG system's answers update immediately, with no retraining step at all.

## Cost and latency tradeoffs

Fine-tuning has a significant upfront cost — preparing a quality training dataset, running the training job, and evaluating the result — but a relatively low per-query cost afterward, since a fine-tuned model answers directly with no retrieval step. RAG has a much lower upfront cost — there's no training job, only building an index over existing documents — but a nonzero per-query cost and latency overhead, since every question requires an embedding call and a retrieval step before generation even starts. For a knowledge base that changes daily, RAG's low upfront cost and instant updates usually win. For a narrow, stable task where response format and style matter more than citing sources, fine-tuning's lower per-query overhead can win instead.

## Using both together

The two techniques are not mutually exclusive. A common production pattern fine-tunes a model to be better at a specific narrow skill — for instance, reliably producing well-formatted answers that cite retrieved sources in a particular style — while still using RAG to supply the actual factual content that skill is applied to. In that combination, fine-tuning shapes *how* the model behaves and RAG supplies *what* it knows, and each is used for the part of the problem it actually solves well, rather than treating either one as a general-purpose fix.
