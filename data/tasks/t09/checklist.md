# Checklist t09
Source: hidden tests at c04c67d: backend/tests/infrastructure/test_openai_adapter.py

1. Structured LLM calls use the OpenAI chat-completions parse API with the requested schema as the response format and return the parsed object plus token usage (prompt/completion tokens).
2. Messages are sent in OpenAI format: a list of {"role": ..., "content": ...} with roles "system", "user", "assistant".
3. Each LLM role resolves its own endpoint/model; roles without an override use the default endpoint, and the default model for the guardrail role is gpt-5-nano while the default for the answer role is gpt-5-mini.
4. A per-role endpoint override (base URL, API key, model) is used for that role (e.g. answer role sent to a local server with model "qwen").
5. Streaming calls request stream=true with stream_options include_usage=true and yield text deltas in order, followed by a final item carrying token usage.
6. SDK clients are created once per distinct endpoint (base URL + key) and shared across roles that use the same endpoint.
7. OpenAI SDK errors are converted to the app's own LLM error type, preserving the message (e.g. "rate limited").
8. A structured response with no parsed output (e.g. refusal) is raised as an LLM error mentioning "no parsed output". [exact]
9. Against the real OpenAI SDK over HTTP, structured calls POST to /v1/chat/completions with a strict json_schema response format and parse the JSON content into the schema.
10. Against the real SDK, server-sent-event streaming is consumed into the full text ("Xin chào") with final usage reported.
