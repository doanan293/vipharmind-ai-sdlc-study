# Checklist t11
Source: hidden tests at 3f87109: backend/tests/domain/test_retrieval_service.py

1. Retrieval searches all given queries in one batch, asking the retriever for a configurable number of candidates per query.
2. Hits returned by several queries are deduplicated by chunk id before reranking, so the reranker sees each chunk once.
3. A deduplicated hit keeps its best (highest) fusion score and records every query that matched it, in query order.
4. Deduplicated candidates are reranked against a single rerank query and only the configured top N are returned.
5. Each returned result is hydrated with its surrounding chunk text according to its hydration strategy.
6. Hits whose strategy is search-only are returned without hydrated chunks.
7. A successful search reports no error and no rerank failure.
8. If reranking fails, the search still succeeds using fusion-score order truncated to top N, and the result flags that reranking failed.
9. If the retriever fails, the search does not raise; it returns no items and reports the error message (e.g. "qdrant down").
