# Checklist t06
Source: hidden tests at 77cd48c: backend/tests/domain/test_audit.py

1. The retrieval audit built from a finished agent run has one record per query per search round, in order, each carrying its round number (1-based) and query text.
2. Each query's hits are those whose matched queries include that query, ranked by rerank score descending with 1-based ranks.
3. Each hit is marked as cited if its chunk appears among the answer's citations, otherwise not cited.
4. Each hit keeps its rerank score and a text snippet truncated to a configurable number of characters.
5. A query in a round that matched no results gets a record with an empty hit list.
6. A search round that failed (error, no results) still produces a record for its query, with no hits.
