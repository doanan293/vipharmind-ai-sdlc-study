# Checklist m03
Source: hidden tests at 95d6913: backend/tests/api/test_chat_api.py, backend/tests/api/test_e2e_postgres.py, backend/tests/api/test_ui_stream.py, backend/tests/infrastructure/test_conversation_repository.py, backend/tests/infrastructure/test_migrations.py

1. The chat stream endpoint (POST /api/v1/chat/stream) responds 200 as text/event-stream in the AI SDK UI message stream v1 format, with headers x-vercel-ai-ui-message-stream: v1, cache-control: no-cache and x-accel-buffering: no.
2. SSE frames are data-only (no "event:" lines), each "data: <compact JSON>" frame separated by a blank line (CRLF), and the stream ends with "data: [DONE]".
3. The stream starts with a "start" chunk carrying messageId equal to the persisted assistant message id, followed by a transient "data-conversation" chunk with the conversation id and title. [exact]
4. Progress phases are sent as "data-phase" chunks sharing one fixed id (so the client replaces them), including the search round when present; selected skills are sent as a "data-skills" chunk. [exact]
5. Evidence is sent as a "data-evidence" chunk (fixed id) whose items use camelCase fields (index, source, title, section, startPage, endPage, snippet). [exact]
6. Answer tokens are sent as text-delta chunks in one text part: a single text-start before the first non-empty token and a single text-end after the last; empty tokens are ignored and no text part is emitted when there are no tokens.
7. Citation markers like "[1]" are never split across text-delta chunks.
8. Each citation is sent after text-end as a "source-document" chunk (media type text/markdown, a source id, provider metadata "pharma" with the citation index and isCurrent true); source indexes are unique and match exactly the markers in the text, in the citation order of the stored message.
9. The stream ends with exactly one "finish" chunk whose messageMetadata has status, createdAt (UTC, "Z" suffix), errorCode, usage (camelCase: llmCalls, promptTokens, completionTokens, searchRounds), runId and persisted.
10. finishReason is "stop" for completed, partial, abstained, blocked and redirected turns, and "error" for error and timeout turns (with the error code, e.g. DEADLINE_EXCEEDED, in the metadata).
11. A turn that could not be persisted is reported only via persisted=false in the finish metadata; no "error" chunk is emitted.
12. Errors detected before streaming starts (e.g. unknown conversation id) return a normal problem+json response (404, code CONVERSATION_NOT_FOUND), not a stream.
13. End to end against Postgres: register, log in, stream a cited answer, then the conversation is listed and feedback can be posted on the message id from the stream's start chunk.
14. Message citations are stored in their own table (message_citations), which exists after migrations, and the schema matches the models.
15. Citations round-trip: messages and single-message lookups return the assistant message's citations exactly as saved (user messages have none), including citations from an unpublished release and search-only hydration.
16. Each stored citation row records its index, cited chunk version, release, hydration strategy (e.g. "full_section", "search_only") and the list of block chunk versions it covers.
17. Appending a turn with a citation to a nonexistent chunk version fails and rolls back the whole turn (no messages saved, turn count unchanged).
18. A cited chunk version and its release cannot be deleted while a message cites them (foreign-key protection); once the conversation is deleted they can be deleted.
