# Checklist m04
Source: hidden tests at 4ba674d: backend/tests/api/test_chat_api.py, backend/tests/api/test_conversations_api.py, backend/tests/api/test_e2e_postgres.py, backend/tests/api/test_health_api.py, backend/tests/test_cli.py

1. POST /api/v1/chat/stream returns 200 text/event-stream with named SSE events: "conversation" first, then phase, evidence, token and citations events, and "done" last. [exact]
2. The "done" event reports the turn status (e.g. completed), the persisted assistant message id, and the same conversation id announced in the first "conversation" event; the new conversation belongs to the authenticated user.
3. POST /api/v1/chat (non-streaming) returns 200 with the full answer as JSON, including the conversation id, citations and a persisted flag (true when saved).
4. Sending a follow-up chat with an existing conversation id continues that conversation (turn count increases), and a rolling summary is generated in the background once due.
5. Chatting with a well-formed but unknown/foreign conversation id returns 404 with problem code CONVERSATION_NOT_FOUND.
6. A malformed conversation id or an empty message is rejected with 422.
7. When the agent (LLM) is not configured, chat endpoints return 503 with problem code AGENT_UNAVAILABLE.
8. Chat endpoints require authentication: unauthenticated requests get 401.
9. GET /api/v1/conversations lists only the caller's conversations (titles), and is empty after the caller deletes them.
10. GET /api/v1/conversations/{id} returns the conversation with its turn count; GET /api/v1/conversations/{id}/messages returns its messages in order (user, assistant).
11. PATCH /api/v1/conversations/{id} with a title renames it (200, new title returned); an empty title is rejected with 422.
12. Getting or deleting another user's conversation returns 404; deleting one's own returns 204.
13. GET /api/v1/health returns 200 {"status": "ok", "agent": true, "checks": {...}} when all checks pass and the agent is available, without requiring authentication. [exact]
14. When any check fails, health returns 503 {"status": "degraded", "agent": <bool>, "checks": {name: bool...}} reporting each check result. [exact]
15. End to end with Postgres: a user can register (201, with display name), log in via /api/v1/auth/jwt/login to get a bearer token, read /api/v1/users/me, stream a chat turn, and see the conversation and its messages listed; messages and retrieval audit rows are persisted in the database.
16. The app can be built with an injectable service-container factory that supplies the services (queries, chat, health checks) for its lifetime.
17. A "migrate" CLI command upgrades the database to the latest migration (head) using the packaged migrations.
18. A "serve" CLI command runs uvicorn with the app factory (factory mode), honoring a --host option and the port from settings (PHARMA_API__PORT).
