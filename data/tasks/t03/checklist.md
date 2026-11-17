# Checklist t03
Source: hidden tests at c3a88b2: backend/tests/api/test_openapi.py, backend/tests/test_cli.py

1. Every operation in the generated OpenAPI document has a unique operationId; ids follow the route names (e.g. list_conversations, chat_stream, submit_feedback, and auth:jwt.login / oauth:google.jwt.authorize for the auth library routes), covering all API routes including Google OAuth ones. [exact]
2. Every documented error response (status >= 400) has the shared Problem schema under application/problem+json, and that is its only content type.
3. Exception: the health endpoint's 503 response documents both the problem body and the normal HealthResponse JSON body.
4. Authenticated routes such as listing conversations document 401, 422 and 503 error responses.
5. Skill upload documents 401, 409, 413, 422 and 503 error responses; registration documents its 400 error as a problem.
6. Success bodies stay correct: creating a conversation documents 201 with the conversation view; listing documents 200 with the conversation page.
7. The schema components include Problem, ProblemItem, the conversation/message/feedback/skill/health views, and form-body schemas named after the operation (e.g. Body_auth_jwt_login, Body_upload_skill). [exact]
8. The unused default validation-error schemas (HTTPValidationError, ValidationError, ErrorModel) are absent.
9. All component schema names match the OpenAPI 3.1 key pattern [A-Za-z0-9.\-_]+ (no colons or other illegal characters).
10. The Problem schema requires type, title, status and code; ProblemItem requires loc, message and type.
11. Generating the OpenAPI document repeatedly on the same app yields an identical document (post-processing is idempotent).
12. A CLI command exports the OpenAPI document to a given output file, creating missing parent directories, exiting 0 and printing "wrote <path>". [exact]
13. The exported file is deterministic (same bytes on repeated exports), equals the app's own document rendering, has sorted top-level keys, and ends with a newline; the export includes the Google OAuth authorize route without needing real credentials/environment.
