# Checklist t13
Source: hidden tests at 7757b6c: backend/tests/infrastructure/test_container.py, backend/tests/infrastructure/test_langfuse_tracing.py

1. With no LLM configured, the app container still provides a skill service and a feedback service (chat and summarizer stay unavailable).
2. With no LLM configured, listing skills for a user with no skills returns an empty list, and the Postgres health check and conversation queries keep working.
3. A chat turn traced through Langfuse produces one turn-level observation (named "chat_turn" in the reference) on a trace whose id is derived deterministically from the run id.
4. The turn observation carries the user id as the Langfuse user (user.id) and the conversation id as the session (session.id).
5. The turn observation's output is the final answer text of the turn.
6. The LangGraph node spans of the turn (e.g. "guard" and "answer") are recorded, and every span of the turn shares the same trace id.
7. Recording user feedback for a run creates exactly one Langfuse score on that run's trace (same derived trace id as the turn).
8. The feedback score is numeric: 0.0 for a "down" rating (1.0 for "up"), uses a fixed score name ("user_feedback" in the reference), and carries the user's note as the comment.
