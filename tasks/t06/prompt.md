Add a retrieval audit to the domain layer that is derived from a finished agent run.
Provide `audit_from_run(run, citations, *, snippet_chars=300) -> list[RetrievalRunRecord]` in a new module `pharma_agent.domain.retrieval.audit`, where `run` is an `AgentRun` and `citations` are the answer's `Citation` objects.
The result has one `RetrievalRunRecord` per query per search round, in the order the searches happened, with `round` (starting at 1 for the first search action), `query_text` and a list of `hits`.
The hits of a record are the run's evidence items whose hit was matched by that query, sorted by score from highest to lowest, and a query that matched nothing (or a failed search) still gets a record with no hits.
Each hit is a `RetrievalHitRecord` with `rank` (starting at 1), `chunk_id`, `section_id`, `table_id`, `fusion_score`, `rerank_score`, `hydrate_strategy` (the strategy's value), `cited` and `snippet`.
`cited` is true when one of the citations points at the hit's chunk, and `snippet` is the chunk text with whitespace collapsed, cut to `snippet_chars` characters.
Both record types are frozen Pydantic models.
