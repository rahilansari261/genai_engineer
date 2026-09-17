# Embeddings and Vector Databases

An embedding is a list of numbers, typically a few hundred to a few thousand of them, produced by a model that has learned to represent the *meaning* of a piece of text as a point in a high-dimensional space. Two pieces of text with similar meaning end up as two points that are close together in that space, even if they don't share a single word in common. That single property — meaning becomes distance — is what every embedding-based feature in an AI application is built on, whether that's search, recommendations, or duplicate detection.

## How similarity is measured

The most common way to measure how close two embeddings are is cosine similarity, which looks at the angle between two vectors rather than the raw distance between them. Two vectors pointing in nearly the same direction have a cosine similarity close to 1, regardless of their length; vectors pointing in opposite directions score close to -1. Most embedding models produce vectors that are already normalized to length 1, which makes cosine similarity and squared Euclidean distance rank results identically, so libraries often just call this "distance" without much ceremony.

## Open-source versus hosted embedding models

Sentence Transformers is a widely used open-source library for producing embeddings locally, on your own hardware, at no per-call cost. A common small model, all-MiniLM-L6-v2, produces 384-dimensional vectors and runs comfortably on a CPU. Hosted embedding APIs, such as OpenAI's, tend to produce higher-dimensional, higher-quality vectors — OpenAI's text-embedding-3-small model produces 1536 dimensions — at a small per-token cost, with no local compute or download required. For most applications the practical difference in retrieval quality between a good local model and a hosted one is smaller than people expect; the deciding factor is usually cost, latency, and whether the text ever needs to leave your own infrastructure.

## What a vector database actually does

A regular database is built to answer questions like "find the row where id equals 42" extremely fast, using an index built for exact lookups. A vector database is built to answer a fundamentally different question fast: "of the ten million vectors I've stored, which ones are closest to this new vector?" Comparing a query against every single stored vector one at a time — called a brute-force or exact search — becomes too slow once a collection grows past a few hundred thousand items. Vector databases solve this with approximate nearest-neighbor indexing structures, the most common being HNSW (Hierarchical Navigable Small World graphs), which trade a tiny amount of accuracy for a very large speedup, typically finding the true nearest neighbors well over 95% of the time while being orders of magnitude faster than brute-force search at scale.

## Local versus managed vector databases

Chroma and LanceDB are examples of vector databases that run embedded, in-process, writing their index to local files — there is no separate server to install, which makes them a good default for development and for smaller applications. Pinecone, Weaviate Cloud, and Qdrant Cloud are examples of managed vector databases: a hosted service you connect to over the network, which handles scaling, replication, and uptime for you in exchange for a subscription cost. The migration path between the two is usually straightforward, since most vector databases expose a similar core interface — upsert vectors with an id and metadata, then query for nearest neighbors — which is exactly the interface this project's own vector store code is built around.
