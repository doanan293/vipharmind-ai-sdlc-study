Add a `RetrievalService` to the domain layer that orchestrates the existing retrieval ports (retriever, reranker, hydrator) for one search round.
Put it in a new module `pharma_agent.domain.retrieval.service`, constructed as `RetrievalService(retriever, reranker, hydrator, config)` with a frozen `RetrievalConfig` model holding `candidate_k` (default 30) and `rerank_top_n` (default 8).
Its async method `search(queries, rerank_query)` returns a `SearchResult` model with `items` (a list of `RetrievedItem`), `queries`, `rerank_failed`, `error` and a `succeeded` property that is true when there is no error.
It asks the retriever for `candidate_k` candidates per query in one `search_many` call, then merges hits of the same chunk across queries, keeping the highest fusion score and the union of the matched queries in order of first appearance.
The merged hits are reranked against `rerank_query`, keeping `rerank_top_n` of them.
If the reranker raises a `RetrievalError`, the service falls back to the top `rerank_top_n` hits by fusion score and sets `rerank_failed`.
Each kept hit is then hydrated with its own hydrate strategy, except that search-only hits get no chunks and a hydration error leaves that hit without chunks.
A retriever failure must not raise: the result has no items and `error` holds the error message.
