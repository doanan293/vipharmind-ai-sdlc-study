# Checklist t14
Source: hidden tests at 86a0dae: backend/tests/infrastructure/test_deepinfra_reranker.py

1. A DeepInfra reranker POSTs to the DeepInfra inference endpoint for the model, i.e. /v1/inference/<model> (e.g. /v1/inference/Qwen/Qwen3-Reranker-4B).
2. The request body pairs the query with each document: "queries" repeats the query once per hit and "documents" has one entry per hit.
3. The returned "scores" are attached to hits as rerank scores, and hits are returned sorted by score descending, limited to top_n.
4. A response whose scores count does not match the number of documents is treated as a retrieval error.
5. A response missing the scores field is treated as a retrieval error.
6. An HTTP error status (e.g. 500) from DeepInfra is treated as a retrieval error.
7. Reranking an empty list of hits returns an empty list without making any HTTP request.
8. Setting the rerank protocol setting to "deepinfra" makes the reranker factory build the DeepInfra reranker. [exact]
