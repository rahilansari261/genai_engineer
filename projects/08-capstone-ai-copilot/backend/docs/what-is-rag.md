# What Is RAG?

Retrieval-Augmented Generation, or RAG, is a technique for getting a language model to answer questions using information it was never trained on. Instead of relying only on what the model memorized during training, a RAG system first searches an external collection of documents for passages relevant to the user's question, then feeds those passages into the model's prompt alongside the question itself. The model's job shifts from "recall an answer from memory" to "read this evidence and answer based on it."

## Why RAG exists

Language models have two structural limitations that RAG works around. First, a model's knowledge is frozen at whatever point its training data was collected — it cannot know about a document written yesterday, or about your company's internal wiki, no matter how good the model is. Second, even if you wanted to teach a model new information by putting it directly in the prompt, most models have a maximum context window, and stuffing an entire document collection into every prompt is both impossible past a certain size and wasteful even when it fits, since most of that context is irrelevant to any single question.

RAG solves both problems by keeping the knowledge outside the model, in a searchable index, and only pulling in the small number of passages that are actually relevant to the current question.

## The four stages of a RAG pipeline

1. **Chunking.** Documents are split into smaller pieces, typically a few hundred words each, often with some overlap between consecutive chunks so a sentence that spans a chunk boundary isn't cut off from its context on both sides.
2. **Embedding.** Each chunk is converted into a vector — a list of numbers capturing its meaning — using an embedding model. The same is done to the user's question at query time.
3. **Retrieval.** The question's embedding is compared against every chunk's embedding, usually using cosine similarity, and the closest matching chunks are pulled out. This step is what a vector database is built for.
4. **Generation.** The retrieved chunks are inserted into a prompt template alongside the original question, and the language model generates an answer grounded in that retrieved text, typically citing which passages it used.

## RAG versus just using a bigger context window

A common question once context windows grew large: if a model can now accept hundreds of thousands of tokens, why bother retrieving anything — why not just paste the whole document collection into every prompt? Two answers. Cost is the practical one: every token in the prompt is billed and adds latency, every single time, even for a one-line question. Precision is the deeper one: models tend to pay less attention to the middle of a very long context than to the beginning and end, a phenomenon sometimes called "lost in the middle," so retrieval that narrows the input down to only the relevant handful of passages tends to produce more accurate answers than dumping everything in and hoping the model finds the right part.

## When RAG is the right tool

RAG is the standard choice whenever an application needs to answer questions grounded in a specific, changeable body of text: customer support over a product's documentation, a chatbot over a company's internal knowledge base, search over a personal note collection, or legal and medical assistants that must cite specific source passages rather than generate from general training knowledge. It is a poor fit for tasks that require the model to have absorbed a new *skill* or *style* rather than new *facts* — that is what fine-tuning is for instead, a distinction covered in this handbook's fine-tuning comparison document.
