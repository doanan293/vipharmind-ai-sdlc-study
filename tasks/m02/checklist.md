# Checklist m02
Source: hidden tests at 68edeac: backend/tests/application/test_queries.py, backend/tests/application/test_summarize.py, backend/tests/infrastructure/test_checkpointer.py, backend/tests/infrastructure/test_container.py, backend/tests/infrastructure/test_migrations.py

1. Listing a user's conversations returns their conversations (title and turn count) in the order the repository gives (most recently updated first).
2. Listing a conversation's messages returns the user and assistant messages in order with role and content, including the assistant message's recorded phases.
3. Renaming a conversation trims whitespace from the new title and sets its updated time to the current clock time.
4. Renaming to a blank title is rejected as invalid input.
5. Getting, listing messages of, renaming, or deleting a conversation the user does not own is reported as "conversation not found".
6. Deleting a conversation removes it from the owner's list.
7. The rolling summarizer does nothing (no LLM call, reports no summary made) when the conversation is not yet due for a summary (fewer new turns than the configured interval).
8. When due, the summarizer asks the summarizer LLM using only usable turns (blocked/error/timeout turns excluded from the prompt), stores the summary cut to the configured max characters, advances the summarized-turn count past all turns read, and reports that a summary was made.
9. When all new turns are unusable (e.g. error and timeout), the summarizer advances the summarized-turn count without calling the LLM and reports no summary made.
10. If the LLM call fails, the previous summary and summarized-turn count are kept and it reports no summary made.
11. Summarizing a conversation that does not exist is silently ignored (reports no summary made).
12. Chat graph state is checkpointed in Postgres: after a turn completes, the graph state for the run's thread can be read back and contains the completed agent run, with no warnings raised during the run.
13. Without an LLM configured, the service container exposes conversation queries and a working "postgres" health check, but no chat service and no summarizer. [exact]
14. With an LLM configured, the container builds the chat service and summarizer and exposes exactly the "postgres" and "qdrant" health checks. [exact]
15. After migrating to head, the database schema matches the app's table models with no differences, ignoring the LangGraph checkpointer's own tables (which migrations do not manage); downgrade/upgrade still round-trips.
