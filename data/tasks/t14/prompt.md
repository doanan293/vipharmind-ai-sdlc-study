Support reranking through DeepInfra's inference endpoint as a new reranker protocol.
Add a class `DeepInfraReranker(http: httpx.AsyncClient, *, model: str, max_concurrent: int = 2)` in a new module `pharma_agent.infrastructure.retrieval.deepinfra_reranker`, implementing the existing reranker port with `rerank(query, hits, top_n)` and an `aclose()` that closes the HTTP client.
`rerank` posts to `/v1/inference/<model>` a JSON body with `queries` (the query repeated once per candidate) and `documents` (each candidate's document text, built the same way as for the existing llama.cpp reranker), and reads one score per pair from the `scores` list of the response.
It returns the `top_n` candidates sorted by score, highest first, with each score stored as the hit's rerank score.
An HTTP error, an invalid JSON answer, a missing `scores` list or a score count that differs from the candidate count must raise `RetrievalError`.
With no candidates it returns an empty list without sending any request.
Accept `deepinfra` as a value of the rerank `protocol` setting (`PHARMA_RETRIEVAL__RERANK__PROTOCOL`), and make the existing `build_reranker(settings)` return a `DeepInfraReranker` for it, using the configured base URL, bearer API key and model.
