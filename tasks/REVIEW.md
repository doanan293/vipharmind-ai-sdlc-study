# Task review (criterion 3 and prompts)

This file is the draft for An's review (Task 4, step 6). For each commit below, in review order:

1. Read the AI proposal for criterion 3 (do the hidden tests check behaviour through an interface the
   prompt can name: API path, function signature, public class?).
2. Write your verdict on the `An:` line, as `An: pass` or `An: fail` (a short reason is welcome).
3. Edit the draft prompt in place if needed. It must stay in English, 5-10 sentences, and must not
   mention tests, hidden tests, test files or grading.

Task ids are assigned only after the review (step 7), by `select`: it walks this order and accepts an
approved commit into its layer while the layer still has quota; the first two approved commits that
fit no quota become the pilots. Review in order and stop once every quota is filled and two pilots
are found.

- Review order: `review_order` over the 42 stratifiable eligible commits, seed 20261115.
- Quotas from `quotas(k=15)`: api 1, application 2, domain 5, infrastructure 7 (total 15).
- Drafted: the first 32 commits in review order. AI proposes pass for 26 and fail
  for 6.
- Proposed passes per layer: api 2, application 6, domain 9, infrastructure 9.
- Stopping rule: draft until proposed passes exceed quota total + 2 pilots + 5 spare = 22.
  Drafting went a few commits further so that `infrastructure` (quota
  7) also has spare commits.
- Three proposed passes (#12, #20, #30) have hidden tests whose behaviour checks are
  integration-only, so grading would check little; their reasons say so.
- Excluded, no layer: `4ba674d359` feat(backend): add serve/migrate commands, Postgres end-to-end test and API docs. It changes no
  file under `pharma_agent/<layer>/`, so it cannot be stratified.

## 1. `c2935909a1` feat(organizations): create, rename, delete organizations and manage members

- sha: `c2935909a101b7274c58ec0e678371c0a13b3d07`
- layer: application
- src_lines: 311
- hidden tests:
  - `backend/tests/application/test_organization_service.py`
- AI criterion 3: **pass**. Every symbol the test uses is either a public class, method, model field or error class the prompt names, or already exists at the parent (the in-memory fakes, `Role`, `AuditAction`, `InvalidInput`).

Draft prompt:

```text
Add organization use cases to the application layer as a new class `OrganizationService` in `pharma_agent.application.organizations.service`, constructed with the keyword arguments `organizations`, `audit`, `tx` and `clock` (the existing organization repository, audit log, transaction factory and clock ports).
It must provide the async methods `list_mine(actor)`, `get(actor, organization_id)`, `create(actor, name)`, `rename(actor, organization_id, name)`, `delete(actor, organization_id, *, confirm_name)`, `members(actor, organization_id)`, `set_role(actor, organization_id, user_id, role)`, `remove_member(actor, organization_id, user_id)` and `leave(actor, organization_id)`.
Organization reads return an `OrganizationView` model with `id`, `name`, `role` (the actor's role, or `None` for a superadmin who is not a member), `member_count` and `created_at`, and `members` returns `MemberItem` models with `user_id`, `display_name`, `email`, `role` and `joined_at`.
The creator becomes the first owner, and names are trimmed and checked with the existing domain name rule, raising `OrganizationNameInvalid` (a subclass of `InvalidInput`) when invalid.
Define the errors in a new module `pharma_agent.application.organizations.errors`: callers who cannot see an organization, including outsiders trying to leave, get `OrganizationNotFound`, members without the required role get `ForbiddenRole`, an unknown member gets `MemberNotFound`, and any change that would leave an organization without an owner raises `LastOwner`.
Deleting requires `confirm_name` to equal the current name exactly, otherwise `InvalidInput` is raised.
Every successful change records exactly one audit event in the same transaction as the change (organization created, renamed or deleted, member role changed, member removed, member left), so a change that fails records nothing.
A role change event carries the affected user as its subject and the details `{"from": <old role value>, "to": <new role value>}`, and the deletion event keeps the organization id with the details `{"name": <name>}`.
```

An: 

## 2. `1b52f20309` feat(infra): add checkpoint retention cleanup

- sha: `1b52f20309a50832272cbf1a8172506da15a8aad`
- layer: infrastructure
- src_lines: 100
- hidden tests:
  - `backend/tests/infrastructure/test_checkpoint_cleanup.py`
  - `backend/tests/test_cli.py`
- AI criterion 3: **fail**. The integration test is never run, and the only other hidden test monkeypatches `pharma_agent.cli.delete_expired_checkpoints`, so it passes only if the CLI module imports that function under that exact name, an internal wiring detail.

Draft prompt:

```text
Add a retention cleanup for LangGraph checkpoints stored in Postgres.
Provide an async function `delete_expired_checkpoints(conninfo: str, *, retention_days: int) -> int` in `pharma_agent.infrastructure.langgraph.cleanup` that deletes checkpoints older than the retention window together with their writes and any blobs left orphaned, and returns the number of checkpoints deleted.
Add a `checkpoints` settings group with a `retention_days` value, configurable through the environment variable `PHARMA_CHECKPOINTS__RETENTION_DAYS`.
Add a `pharma-agent cleanup-checkpoints` command with an optional `--days` option that overrides the configured retention.
The command connects using the configured Postgres DSN converted to a plain `postgresql://` connection string (without the SQLAlchemy driver suffix).
On success it prints `deleted <n> checkpoints older than <days> days` and exits with code 0.
The service should also run this cleanup once in the background when it starts.
```

An: 

## 3. `f8949eca39` feat(backend): add account settings use cases (contacts, password, Google, sessions)

- sha: `f8949eca395e8425c885899d887810e1100a0c64`
- layer: application
- src_lines: 197
- hidden tests:
  - `backend/tests/application/test_account_settings_service.py`
- AI criterion 3: **pass**. All calls go to public methods of the existing `AccountService` that the prompt names, and the error classes, `session_id_of` and the account fakes already exist at the parent.

Draft prompt:

```text
Extend the existing `AccountService` in `pharma_agent.application.account.service` with account settings use cases.
Add an `AccountView` model (`id`, `email`, `phone_number`, `display_name`, `is_active`, `is_superuser`, `is_verified`, `email_verified`, `phone_verified`, `password_set`, `google_linked`, where `is_verified` means the email or the phone is verified) and a `SessionView` model (`id`, `created_at`, `last_used_at`, `user_agent`, `ip_address`, `current`).
Add the async methods `get_account(user_id)`, `update_profile(user_id, display_name)` (the name is trimmed), `request_email_change(user_id, email, *, locale, client_ip)`, `confirm_email_change(user_id, email, code, *, locale)`, `request_phone_change(user_id, phone, *, locale, client_ip)` and `confirm_phone_change(user_id, phone, code)`; the account-returning ones return an `AccountView`.
Email addresses and phone numbers are normalized as elsewhere in the service, a code is sent to the new address or number, and an address or number owned by another account raises `EmailAlreadyUsed` or `PhoneAlreadyUsed`.
A confirmation code issued for another user raises `InvalidCode`, and after an email change the previous address receives a notice that names the new address.
Add `change_password(user_id, *, current_password, new_password)`, which raises `CurrentPasswordInvalid` when the account already has a password and the current one is missing or wrong, but lets accounts without a password set their first one.
Add `unlink_google(user_id)`, which raises `LastSignInMethod` when Google is the account's only way to sign in.
Add `list_sessions(user_id, current_token)`, which never exposes raw tokens (session ids come from the existing `session_id_of`) and marks the session of `current_token` as current, `revoke_session(user_id, session_id)`, which raises `SessionNotFound` for an unknown id, and `revoke_other_sessions(user_id, current_token)`, which returns how many sessions it removed.
Unknown users raise `AccountNotFound` everywhere.
```

An: 

## 4. `c3a88b2659` feat(api): pin operation ids, document problem responses, export OpenAPI

- sha: `c3a88b2659d708cb6e23c09cdb5d00bb99be2626`
- layer: api
- src_lines: 198
- hidden tests:
  - `backend/tests/api/test_openapi.py`
  - `backend/tests/test_cli.py`
- AI criterion 3: **pass**. The tests use only `create_app`, the new public `openapi_export_settings` and `render_openapi` functions, the `export-openapi` command and the generated OpenAPI document, all of which the prompt can name.

Draft prompt:

```text
Make the generated OpenAPI document of the HTTP API match what the API actually sends, and add a way to export it.
Every route's `operationId` must be its route name (for example `list_conversations`, or `auth:jwt.login` for the fastapi-users routes), and the ids must be unique.
Every error response (status 400 and above) must document `application/problem+json` with the existing `Problem` schema as its only content, except that the health endpoint's 503 response keeps its `application/json` `HealthResponse` body alongside the problem body.
Document the error statuses each route can return (authenticated routes include 401, 422 and 503, and skill upload also 409 and 413), and keep the success bodies such as `ConversationView` for 201 on creating a conversation and `ConversationPage` for listing.
The unused `HTTPValidationError`, `ValidationError` and `ErrorModel` schemas must disappear, form body schemas must be named `Body_<operation id>` with every character outside `[A-Za-z0-9_]` replaced by an underscore, and calling `app.openapi()` repeatedly must return the same document.
Add `openapi_export_settings()` and `render_openapi(app)` to a new module `pharma_agent.api.openapi`: the first returns settings that need no environment or services and enable Google OAuth with placeholder credentials so its routes appear, and the second returns the document as JSON with sorted keys, two-space indentation, non-ASCII characters kept and a trailing newline.
Add a `pharma-agent export-openapi --output <file>` command that writes that rendering to the file, creating missing parent directories, and prints `wrote <file>`.
```

An: 

## 5. `f2b898af97` feat(deploy): run the backend as a Vercel Function

- sha: `f2b898af9761002477c139fe876e50be3eb50ef5`
- layer: infrastructure
- src_lines: 73
- hidden tests:
  - `backend/tests/infrastructure/test_inline_dispatcher.py`
  - `backend/tests/infrastructure/test_settings.py`
- AI criterion 3: **pass**. The tests use only the new public `InlineDispatcher` class (constructor and `enqueue`) and the `jobs.dispatcher` setting, both nameable in the prompt.

Draft prompt:

```text
Let publish jobs run inside the request that queued them, for serverless hosts that may freeze a function once it has answered.
Add a class `InlineDispatcher` in `pharma_agent.infrastructure.jobs.inline`, constructed as `InlineDispatcher(run, *, retry_delay_seconds=2.0, max_runs=3)` where `run` is an async callable taking a job id.
Its async method `enqueue(job_id)` must return only after the job has run successfully or has used all of its runs.
When `run` raises, the dispatcher waits briefly and calls it again, up to `max_runs` calls in total.
A job that keeps failing must not make `enqueue` raise, so the publish request still succeeds.
Accept `inline` as a value of the `jobs.dispatcher` setting (environment variable `PHARMA_JOBS__DISPATCHER`), select this dispatcher for publishing when it is configured, and treat it like `inprocess` for internal call authentication.
Also expose a module-level ASGI `app` in `pharma_agent.api.asgi` for hosts that import an application object instead of running the server command.
```

An: 

## 6. `650abbd0eb` feat(domain): add fail-open guardrail with regex groups and LLM classifier

- sha: `650abbd0ebecab538c6ba71a9c0118f5add6ede8`
- layer: domain
- src_lines: 186
- hidden tests:
  - `backend/tests/domain/test_guardrail.py`
- AI criterion 3: **pass**. The tests use `regex_screen`, `GuardrailService`, `LlmGuardVerdict` and `VerdictSource`, which the prompt names with their modules, plus the LLM port types and the `GUARDRAIL` role that already exist at the parent.

Draft prompt:

```text
Add an input guardrail to the domain layer that screens user questions before the drug-information assistant answers them.
Create a package `pharma_agent.domain.guardrail` with a `VerdictSource` string enum (`regex`, `llm`, `skipped`), a frozen `Verdict` model (`passed`, `in_scope`, `source`, `label`, `reason`) and an `LlmGuardVerdict` model (`is_attack`, `in_scope`, `reason`) that the LLM fills as structured output.
Provide `regex_screen(query) -> Verdict | None` in `pharma_agent.domain.guardrail.groups`, which returns a blocking regex verdict when the question matches high-risk pattern groups for prompt injection, jailbreak, data leak or bypass attempts in Vietnamese or English, and `None` for ordinary drug questions.
Provide a class `GuardrailService(llm)` in `pharma_agent.domain.guardrail.service` with an async `check(query)` that returns a `GuardrailOutcome` holding the `verdict`, the LLM `usage` and an `llm_failed` flag.
A regex hit decides alone, without calling the LLM, and reports empty usage.
Otherwise the service asks the LLM port for an `LlmGuardVerdict` with the existing `GUARDRAIL` role and a Vietnamese system prompt: an attack is blocked and marked out of scope, an off-topic question passes but is marked out of scope, and the LLM usage is reported.
Any LLM error fails open, passing the question as in scope with source `skipped` and `llm_failed` set.
```

An: 

## 7. `77cd48cd29` feat(domain): derive retrieval audit records from an agent run

- sha: `77cd48cd29330296a16774bb1d86f0b5601e4cbf`
- layer: domain
- src_lines: 67
- hidden tests:
  - `backend/tests/domain/test_audit.py`
- AI criterion 3: **pass**. The test calls only the new public `audit_from_run` and reads the fields of the records it returns; `AgentRun.record_search`, `SearchResult`, `Citation` and the factories already exist at the parent.

Draft prompt:

```text
Add a retrieval audit to the domain layer that is derived from a finished agent run.
Provide `audit_from_run(run, citations, *, snippet_chars=300) -> list[RetrievalRunRecord]` in a new module `pharma_agent.domain.retrieval.audit`, where `run` is an `AgentRun` and `citations` are the answer's `Citation` objects.
The result has one `RetrievalRunRecord` per query per search round, in the order the searches happened, with `round` (starting at 1 for the first search action), `query_text` and a list of `hits`.
The hits of a record are the run's evidence items whose hit was matched by that query, sorted by score from highest to lowest, and a query that matched nothing (or a failed search) still gets a record with no hits.
Each hit is a `RetrievalHitRecord` with `rank` (starting at 1), `chunk_id`, `section_id`, `table_id`, `fusion_score`, `rerank_score`, `hydrate_strategy` (the strategy's value), `cited` and `snippet`.
`cited` is true when one of the citations points at the hit's chunk, and `snippet` is the chunk text with whitespace collapsed, cut to `snippet_chars` characters.
Both record types are frozen Pydantic models.
```

An: 

## 8. `cd9ce5833b` feat(domain): add conversation context and SKILL.md skill model

- sha: `cd9ce5833b47e8e8ff0fc2933802f5281dbe57a3`
- layer: domain
- src_lines: 232
- hidden tests:
  - `backend/tests/domain/test_conversation_context.py`
  - `backend/tests/domain/test_skill.py`
- AI criterion 3: **pass**. The tests use only `context_for_rephrase`, `Turn`, `Skill`, `SkillMetadata`, `SkillParseError`, `parse_skill_markdown` and `resolve_selected`, all public names with modules the prompt can state.

Draft prompt:

```text
Add two domain models: the conversation context used to rephrase a follow-up question, and skills written as SKILL.md files.
In `pharma_agent.domain.conversation.models`, add a frozen `Turn` (`user_text`, `assistant_text`, `status`, with a size equal to the length of both texts) and a `ConversationContext` (`summary`, `turns`, and an `is_empty` property that is true only when both are empty), alongside a `MessageRole` enum, a `Citation` model and a `ConversationSummary` model.
In `pharma_agent.domain.conversation.context`, add `context_for_rephrase(summary, turns, *, max_turns=4, max_chars=4000)`, which cuts the summary to `max_chars`, drops turns whose status is `blocked`, `error` or `timeout`, keeps the last `max_turns` remaining turns, and then drops the oldest turns until the turns fit in what the summary leaves of `max_chars`.
In `pharma_agent.domain.skill.parser`, add `parse_skill_markdown(text)` returning a `ParsedSkill` with `name`, `description`, `search_guidance`, `answer_guidance` and `version` (the first 12 hex characters of the SHA-256 of the text), raising `SkillParseError` (a domain error) on invalid input.
A valid file starts with a YAML frontmatter block whose keys are exactly a non-empty `name` and `description`, and its body has a `## Tìm kiếm` (or `## Search`) section and/or a `## Trả lời` (or `## Answer`) section whose stripped contents become the two guidance fields; a file with neither section is invalid.
In `pharma_agent.domain.skill.models`, add a frozen `SkillMetadata` (`skill_id`, `name`, `description`) and a `Skill` model whose `skill_id` must be lowercase words joined by hyphens, with `metadata()` and `to_selected()` (returning the existing `SelectedSkill`) projections and an `is_system` property for skills without an owner.
In `pharma_agent.domain.skill.resolver`, add `resolve_selected(catalog, selected_ids, *, max_selected=3)`, which keeps only ids present in the catalog, without duplicates, in the order given, up to `max_selected`.
Also add a `SkillCatalog` protocol port for listing the catalog and fetching skills by id.
```

An: 

## 9. `8dd6a9cdc9` feat(domain): add shared text normalization and snippet helpers

- sha: `8dd6a9cdc9c43f37280a039d6a24f4e957d3c435`
- layer: domain
- src_lines: 43
- hidden tests:
  - `backend/tests/domain/test_text.py`
- AI criterion 3: **pass**. The tests call only the two new public functions `normalize_text` and `make_snippet`, whose module and signatures the prompt states.

Draft prompt:

```text
Add shared text helpers to the domain layer in a new module `pharma_agent.domain.shared.text`.
Provide `normalize_text(text: str) -> str`, which converts the text to Unicode NFC, turns every `\r\n` or lone `\r` into a line break, strips trailing whitespace from each line, and removes blank lines at the start and end while keeping inner blank lines and leading indentation.
It must be idempotent and return an empty string for empty or whitespace-only input.
Provide `make_snippet(text: str, max_chars: int) -> str`, which builds a one-line preview: Markdown table separator rows are dropped, table pipes are removed, and all whitespace runs collapse to single spaces with the ends trimmed.
If the result fits in `max_chars` it is returned unchanged; otherwise it is cut at the last word boundary so that the kept words plus a trailing `…` fit within `max_chars`, keeping a word that ends exactly at the cut.
When a single word is longer than the limit, the word itself is cut so that the text plus `…` is exactly `max_chars` characters.
A `max_chars` of zero or less raises `ValueError` with a message that mentions `max_chars`.
```

An: 

## 10. `c04c67decc` feat(infra): add OpenAI Chat Completions adapter for structured output and streaming

- sha: `c04c67decc634e5e3c3b09dc0b4c60da723d32d9`
- layer: infrastructure
- src_lines: 120
- hidden tests:
  - `backend/tests/infrastructure/test_openai_adapter.py`
- AI criterion 3: **pass**. The tests use the new public `OpenAiLlmAdapter` (constructor with `client_factory`, `structured`, `stream`) and the OpenAI SDK client surface it calls, plus settings and LLM port types that already exist at the parent.

Draft prompt:

```text
Add an infrastructure adapter that implements the existing LLM port over the OpenAI SDK's Chat Completions API, so any OpenAI-compatible server can be used.
Create the class `OpenAiLlmAdapter(settings: LlmSettings, client_factory=default_client_factory)` in `pharma_agent.infrastructure.llm.openai_adapter`, where a client factory is called as `factory(endpoint, timeout, max_retries)` with the role's resolved endpoint and the settings' timeout and retry count and returns an `AsyncOpenAI`-compatible client.
Each role uses the endpoint and model resolved by the existing `LlmSettings.resolve`, and clients are created lazily and shared between roles that resolve to the same base URL and API key.
`structured(role, messages, schema)` must call `client.chat.completions.parse` with the role's `model`, the messages as a list of `{"role", "content"}` dicts and `response_format=schema`, and return the parsed object together with an `LlmUsage` built from the response's token counts.
`stream(role, messages)` must call `client.chat.completions.create` with `stream=True` and `stream_options={"include_usage": True}`, yield a `StreamDelta` with the text of each non-empty content delta, and yield a final `StreamDelta` carrying the usage when the server reports it.
Any `OpenAIError` must be raised as the port's `LlmError` with the original message included, and a response without parsed output (for example a refusal) must raise `LlmError` with a message containing `no parsed output`.
Also provide `default_client_factory` building a plain `AsyncOpenAI` client, and `langfuse_client_factory` building Langfuse's drop-in `AsyncOpenAI` wrapper.
```

An: 

## 11. `44466f373d` feat(infra): wire fastapi-users JWT auth with optional Google OAuth

- sha: `44466f373da672594dbf8a4d419505f662c712f1`
- layer: infrastructure
- src_lines: 141
- hidden tests:
  - `backend/tests/infrastructure/test_auth_wiring.py`
- AI criterion 3: **pass**. The tests use the new public `build_auth` and `include_auth_routes` functions, the returned object's `google` attribute and the route paths, together with the existing `AuthSettings`.

Draft prompt:

```text
Wire user authentication with fastapi-users into the infrastructure layer, in a new module `pharma_agent.infrastructure.auth.users`.
Provide `build_auth(settings: AuthSettings, resolve_sessions)` that returns an `Auth` object, where `resolve_sessions` is a callable taking the request and returning an async SQLAlchemy session factory for the existing user and OAuth account tables.
The object exposes the configured `FastAPIUsers` instance, a JWT bearer authentication backend whose token URL is `/api/v1/auth/jwt/login` and whose lifetime comes from the settings, a dependency for the current active user, and a `google` attribute.
`google` is a Google OAuth2 client when Google sign-in is enabled with a client id and secret, and `None` otherwise.
When no JWT secret is configured, `build_auth` must fail immediately with the existing settings error that names `PHARMA_AUTH__JWT_SECRET`.
Provide `include_auth_routes(router, auth)` that mounts the login and logout routes under `/auth/jwt`, registration under `/auth` (giving `/auth/register`), the user routes under `/users` (including `/users/me`), and, only when Google is configured, the OAuth authorize and callback routes under `/auth/google`.
The Google callback must redirect to `<frontend_url>/auth/google/callback`, link accounts by email and mark new Google users as verified.
```

An: 

## 12. `0147ea532a` feat(api): author, upload and publish collection content

- sha: `0147ea532ab4066245f37c0573b0a4d633794b4e`
- layer: api
- src_lines: 244
- hidden tests:
  - `backend/tests/api/test_documents_api_postgres.py`
  - `backend/tests/api/test_openapi.py`
- AI criterion 3: **pass**. The runnable hidden test checks only the OpenAPI operation ids of the new routes, which the prompt can list (the Postgres behaviour test is integration-only and never runs, so grading would check route names rather than behaviour).

Draft prompt:

```text
Add HTTP routes for authoring, uploading and publishing the content of a collection.
Under `/api/v1/collections/{collection_id}`, add `GET` and `POST` `/documents` (`documents:list`, `documents:create`, the create returning 201), `POST /documents/upload` (`documents:upload`), and `GET`, `PUT` and `DELETE` `/documents/{document_id}` (`documents:get`, `documents:update`, `documents:delete`, the delete returning 204).
In the same collection scope, add `GET` and `PUT` `/glossary` (`collections:glossary.get`, `collections:glossary.put`), `GET` and `PUT` `/colloquial` (`collections:colloquial.get`, `collections:colloquial.put`) and `GET /sections` (`collections:sections`), listing the section keys a colloquial name may point to.
Add `POST /api/v1/collections/{collection_id}/publish` (`collections:publish`, answering 202 with the queued job), `POST /api/v1/collections/{collection_id}/rollback` (`collections:rollback`), `GET /api/v1/collections/{collection_id}/releases` (`collections:releases`) and `GET /api/v1/ingest-jobs/{job_id}` (`jobs:get`) for the progress of a publish job.
The names in parentheses are the route names and therefore the OpenAPI operation ids, and every error response must be documented as a problem response like the existing routes.
The upload accepts a UTF-8 `.md`, `.markdown` or `.txt` file of at most 1,000,000 bytes and returns a draft with `title`, `markdown` and `char_count` without saving anything; a Markdown file takes its first `# ` heading as the title, otherwise the file name without its extension is used.
Other file types, text that is not UTF-8 and empty files are rejected as invalid input (422), and oversized files as too large (413).
The routes reuse the existing collection content use cases and the current-actor dependency.
```

An: 

## 13. `3f87109556` feat(domain): add RetrievalService with dedupe, rerank fallback and hydration

- sha: `3f87109556c371c2da9e9f7bdc9fe7e3ec87087e`
- layer: domain
- src_lines: 102
- hidden tests:
  - `backend/tests/domain/test_retrieval_service.py`
- AI criterion 3: **pass**. The tests use the new public `RetrievalService` and `RetrievalConfig` and the fields of the returned result, with fakes that implement retrieval ports already present at the parent.

Draft prompt:

```text
Add a `RetrievalService` to the domain layer that orchestrates the existing retrieval ports (retriever, reranker, hydrator) for one search round.
Put it in a new module `pharma_agent.domain.retrieval.service`, constructed as `RetrievalService(retriever, reranker, hydrator, config)` with a frozen `RetrievalConfig` model holding `candidate_k` (default 30) and `rerank_top_n` (default 8).
Its async method `search(queries, rerank_query)` returns a `SearchResult` model with `items` (a list of `RetrievedItem`), `queries`, `rerank_failed`, `error` and a `succeeded` property that is true when there is no error.
It asks the retriever for `candidate_k` candidates per query in one `search_many` call, then merges hits of the same chunk across queries, keeping the highest fusion score and the union of the matched queries in order of first appearance.
The merged hits are reranked against `rerank_query`, keeping `rerank_top_n` of them.
If the reranker raises a `RetrievalError`, the service falls back to the top `rerank_top_n` hits by fusion score and sets `rerank_failed`.
Each kept hit is then hydrated with its own hydrate strategy, except that search-only hits get no chunks and a hydration error leaves that hit without chunks.
A retriever failure must not raise: the result has no items and `error` holds the error message.
```

An: 

## 14. `98a46b6fe7` feat(corpus): build a knowledge bundle from authored Markdown documents

- sha: `98a46b6fe75bb89e0b44fe715a7c4ea394f8263f`
- layer: domain
- src_lines: 201
- hidden tests:
  - `backend/tests/domain/corpus/test_authoring.py`
- AI criterion 3: **pass**. The tests call the five public functions of the new `pharma_agent.domain.corpus.authoring` module named in the prompt and otherwise use bundle, collection and snapshot models that already exist at the parent.

Draft prompt:

```text
Build a knowledge bundle from authored Markdown documents, in a new domain module `pharma_agent.domain.corpus.authoring`, so authored content can go through the existing bundle import.
Provide `split_markdown(markdown, *, fallback_heading)` returning sections with `heading`, `path` (the tuple of enclosing headings, empty for the first section), `ordinal` and `blocks` (existing `BlockRecord` values); headings inside fenced code do not count, text before the first heading (or a document without headings) is a section titled `fallback_heading`, and sections with no content are dropped.
Inside a section, each run of table rows (lines starting with `|`) becomes a table block with a `table_key` of `t1`, `t2` and so on, numbered across the whole document, and the text between tables becomes stripped prose blocks.
Provide `slugify(text, *, max_length=80)` producing lowercase ASCII words joined by hyphens with Vietnamese marks removed (so `Đường uống` becomes `duong-uong`), and `section_key(document_key, path)` returning `<document_key>#<slugified path parts joined by "/">`, or `<document_key>#body` for an empty path.
Document keys in the bundle are the collection key and the document key joined by a colon, so chunk ids never collide across collections.
Provide `section_choices(collection, documents)` returning `(section key, label)` pairs in reading order, where the label is the document title followed by the heading path, joined by ` › `.
Provide `build_bundle(collection, documents, glossary, colloquial)` returning a `KnowledgeBundle` with documents sorted by key, one section record per section, the glossary as given, colloquial mappings whose section keys that do not exist are removed, and a manifest that carries the collection key and title and the document and section counts.
The bundle must be deterministic, so the same content always gives the same bundle digest.
```

An: 

## 15. `fa34e23d15` feat(backend): add account messages and email/SMS senders

- sha: `fa34e23d15f810f5c1fb2d873791a6ba03a1d869`
- layer: infrastructure
- src_lines: 245
- hidden tests:
  - `backend/tests/application/test_account_messages.py`
  - `backend/tests/infrastructure/test_notifications.py`
- AI criterion 3: **fail**. Two SMTP tests monkeypatch `email_module.aiosmtplib.send`, so they pass only if the email module imports `aiosmtplib` as a module and calls `aiosmtplib.send`, an implementation detail the prompt would have to dictate.

Draft prompt:

```text
Add the messages and senders that deliver account codes by email and SMS.
In a new module `pharma_agent.application.account.messages`, provide a `Locale` type (`"vi"` or `"en"`), an `EmailContent` value with `subject`, `text` and `html`, and `locale_from_accept_language(header)`, which returns `en` when the first language of an `Accept-Language` header starts with `en` and `vi` otherwise (including a missing header).
Provide `code_email(purpose, code, locale)` and `code_sms(purpose, code, locale)` for every existing `OtpPurpose`, where the email has a subject and includes the code in both its text and HTML, and the SMS includes the code, is plain ASCII and fits in 160 characters.
Provide `email_changed_notice(new_email, locale)`, an email telling the old address which new address was set, with the address HTML-escaped in the HTML body.
In `pharma_agent.infrastructure.notifications.email`, add `LogEmailSender` (writes to the log), `SmtpEmailSender(host, port, username, password, sender, timeout)` (sends a multipart text-plus-HTML message with `From` and `To` headers through `aiosmtplib` using STARTTLS and login) and `ResendEmailSender(api_key, sender, timeout)` (posts to `https://api.resend.com/emails` with a bearer token and the recipient in a `to` list), each with an async `send(*, to, subject, text, html)`.
SMTP failures and non-success Resend responses must be raised as the existing `DeliveryError`.
Add `LogSmsSender` with an async `send(*, to, text)` in `pharma_agent.infrastructure.notifications.sms`.
In `pharma_agent.infrastructure.notifications.factory`, add `build_email_sender(settings)`, which picks the sender from `EmailSettings.provider` and raises `ValueError` naming `PHARMA_EMAIL__SMTP_USERNAME` or `PHARMA_EMAIL__RESEND_API_KEY` when the provider's credentials are missing, and `build_sms_sender(settings)`, which returns the log sender.
```

An: 

## 16. `94a54f8696` feat(skills): ship five system SKILL.md playbooks with a filesystem catalog

- sha: `94a54f86965e4a7277dc9219a392a29f50c4c274`
- layer: infrastructure
- src_lines: 45
- hidden tests:
  - `backend/tests/infrastructure/test_filesystem_catalog.py`
- AI criterion 3: **pass**. The tests use the new public `load_system_skills` and `FileSystemSkillCatalog` plus the five skill ids, which the prompt names; note the developer must also author the five SKILL.md files under `backend/skills/`.

Draft prompt:

```text
Ship the assistant's system skills as SKILL.md playbooks in the repository and serve them through a filesystem catalog.
Add five skills under `backend/skills/<skill-id>/SKILL.md` with the ids `brand-to-generic`, `dosing-by-population`, `drug-interaction`, `drug-monograph` and `plain-language`, written in Vietnamese in the existing SKILL.md format.
Each playbook must have a name, a description that tells the skill selector when to use it, and both a search section and an answer section with concrete guidance for that kind of drug question.
The playbooks must not add a disclaimer that the assistant does not replace a doctor or pharmacist (in Vietnamese, the phrase "không thay thế").
In a new module `pharma_agent.infrastructure.skills.filesystem_catalog`, provide `load_system_skills(root: Path) -> list[Skill]`, which reads every `<folder>/SKILL.md` under `root` in folder name order with the existing SKILL.md parser and builds an enabled system skill (no owner) whose id is the folder name.
An invalid file or a folder name that is not a valid skill id must raise an error instead of being skipped, and a missing root gives an empty list.
Provide `FileSystemSkillCatalog(root)`, implementing the existing skill catalog port: `list_catalog(user_id, limit)` returns the metadata of up to `limit` enabled skills, and `get_by_ids(skill_ids)` returns the known skills among the ids and ignores unknown ones.
```

An: 

## 17. `69be18bc62` feat(infra): add Qdrant hybrid RRF retriever, embedder and hydrator

- sha: `69be18bc62e4069a3c9bcc6499cf0d6377b0e61d`
- layer: infrastructure
- src_lines: 231
- hidden tests:
  - `backend/tests/infrastructure/test_qdrant_adapter.py`
  - `backend/tests/infrastructure/test_qdrant_integration.py`
- AI criterion 3: **fail**. The unit tests pin the exact `qdrant_client` call shape (the `query_points` keyword arguments, a dense prefetch plus a BM25 `Document` prefetch, an `RrfQuery`, and `scroll` filter conditions on `section_id` and `chunk_index`), so the prompt would have to dictate the implementation, not just the interface.

Draft prompt:

```text
Add Qdrant adapters for the retrieval ports, matching the corpus pipeline's collection layout of a dense vector plus a BM25 sparse vector fused with reciprocal rank fusion.
In a new module `pharma_agent.infrastructure.retrieval.qdrant_adapter`, define the vector names `DENSE_VECTOR_NAME` and `BM25_SPARSE_VECTOR_NAME` and the sparse model name `BM25_MODEL_NAME = "Qdrant/bm25"`.
Provide `hit_from_point(payload, score, query_text)`, which maps a point payload (chunk and section ids, chunk index, hydrate strategy, titles, pages, texts, optional colloquial mapping and term annotations) to a `Hit` whose fusion score is `score` and whose matched queries are `[query_text]`.
Provide `OpenAiEmbedder(client, *, model, dimension)`, whose async `embed(texts)` calls an OpenAI-compatible embeddings endpoint, returns the vectors in input order and raises `RetrievalError` mentioning the dimension when a vector has the wrong size.
Provide `QdrantHybridRetriever(client, embedder, collection, *, mode="hybrid", prefetch_k=50, rrf_k=2, max_concurrent=3)` implementing `search_many(queries, top_k)`: in hybrid mode each query prefetches `prefetch_k` dense and `prefetch_k` BM25 candidates and fuses them with RRF using `rrf_k`, and in dense mode it queries the dense vector only, returning at most `top_k` hits with payloads per query.
Its `verify_collection(expected_dimension)` raises `RetrievalError` mentioning the dimension when the collection's dense vector size differs.
Provide `QdrantHydrator(client, collection, *, window=1)` whose `hydrate(hit, strategy)` returns the chunks of the hit's section sorted by chunk index for the full-section strategy, only the chunks within `window` of the hit's index for the chunk-window strategy, and nothing for search-only hits.
```

An: 

## 18. `cc0f06a67b` feat(chat): pre-generate turn message ids and report persisted on done

- sha: `cc0f06a67bfa888ef5d7e1ebd1715a517079bbc9`
- layer: application
- src_lines: 46
- hidden tests:
  - `backend/tests/api/test_conversations_api.py`
  - `backend/tests/application/test_chat_service.py`
  - `backend/tests/application/test_feedback_service.py`
  - `backend/tests/application/test_queries.py`
  - `backend/tests/application/test_summarize.py`
  - `backend/tests/domain/test_conversation.py`
  - `backend/tests/test_cli.py`
- AI criterion 3: **pass**. The tests use the existing `ChatService.open_turn`, `ChatSession`, `build_turn_messages`, progress events and the CLI's existing `_render`, plus new properties and parameters (`user_message_id`, `assistant_message_id`, `persisted`, `created_at`) that the prompt names.

Draft prompt:

```text
Pre-generate the message ids of a chat turn so clients know them from the start of the stream, and report on the final event whether the turn was saved.
When `ChatService.open_turn` creates a `ChatSession`, it must generate two distinct ids with the existing `new_id` helper and expose them as the read-only properties `user_message_id` and `assistant_message_id`.
`build_turn_messages` in `pharma_agent.domain.conversation.turns` must take these ids as the new required keyword arguments `user_message_id` and `assistant_message_id` and use them for the stored user and assistant messages instead of generating ids itself.
The first `conversation` progress event must also carry `message_id`, set to the assistant message id.
The final `done` event must carry `message_id` (the assistant message id, or `None` when saving failed), `persisted` (whether the turn was saved) and `created_at` (the ISO timestamp of the stored assistant message).
`ChatTurnResult` gains `user_message_id`, `assistant_message_id` and `created_at`, the latter equal to the stored assistant message's creation time.
A failed save must no longer emit a separate `error` event after `done`: remove the `error` event type, the `PERSIST_FAILED` code and its message, so `done` is always the last and only completion event and the answer is still delivered.
The CLI's event rendering must print `!! Không lưu được lượt hội thoại này.` to standard error when a `done` event reports `persisted` as false, and print nothing to standard error otherwise.
```

An: 

## 19. `9965bdf1bf` feat(domain): add Vietnamese prompts for rephrase, skills, judge, refine and answer

- sha: `9965bdf1bf8c0051df1fa7da070c22eb7c63b22b`
- layer: domain
- src_lines: 220
- hidden tests:
  - `backend/tests/domain/test_prompts.py`
- AI criterion 3: **fail**. The functions are nameable, but the tests assert exact Vietnamese wording inside the generated prompt text (`chuyên môn`, `chưa đủ`, `không tìm thấy`, `[n]`, a `DISCLAIMER_PHRASES` list), which the prompt would have to dictate word for word.

Draft prompt:

```text
Add the Vietnamese LLM prompts of the drug-information agent to a new domain module `pharma_agent.domain.agent.prompts`, as functions that return lists of chat messages.
Provide `rephrase_messages(original_query, context)`, which turns a follow-up question into a standalone one using the conversation summary and recent turns, and `skill_selection_messages(query, catalog)`, which lists each skill id with its description so the model can pick playbooks.
Provide `judge_messages(run, evidence_summary)`, which shows the standalone question, the audience, the evidence summary and the search guidance of the run's selected skills, and `refine_messages(run, gaps, term_hints)`, which shows the queries already used, the missing aspects and the term hints so the model can write new queries.
Provide `answer_messages(run, plan, context_text)`, whose instructions depend on the plan's answer mode, the run's audience (with professional-level wording for professionals) and language, include the selected skills' answer guidance, and for grounded answers include the numbered context and require `[n]` citation markers.
A partial grounded plan must tell the model that the evidence is not yet sufficient, and an abstaining plan must tell the user that nothing relevant was found in the source, without any citation.
Provide `fallback_text(status)` returning a short Vietnamese apology about the drug question for timeouts and for other failures.
Define a `DISCLAIMER_PHRASES` tuple of medical-disclaimer phrases in Vietnamese and English, and make sure none of these phrases appears in any prompt or fallback text.
```

An: 

## 20. `8363fdd98c` feat(db): add organizations, members, invitations, audit events and quota columns

- sha: `8363fdd98ce3f4d2ff7afea5f03da16a0b07e3b1`
- layer: infrastructure
- src_lines: 276
- hidden tests:
  - `backend/tests/infrastructure/test_migrations.py`
  - `backend/tests/infrastructure/test_persistence_metadata.py`
- AI criterion 3: **pass**. The only runnable hidden test checks that the four new table names are registered in the SQLAlchemy metadata, which the prompt names (the migration tests are integration-only and never run, so grading barely checks this feature).

Draft prompt:

```text
Add the database schema for organizations, their members and invitations, an audit log, and quota overrides.
Add the SQLAlchemy tables `organizations` (`id`, `name`, `text_quota_bytes`, `collection_quota`, `created_at`, `updated_at`), `organization_members` (`organization_id` and `user_id` as the primary key, `role`, `joined_at`) and `organization_invitations` (`id`, `organization_id`, `email`, `role`, `invited_by`, `status`, `token_hash`, `created_at`, `expires_at`, `decided_by`, `decided_at`) to the existing persistence metadata in `pharma_agent.infrastructure.persistence.postgres.tables`.
Roles are limited to `owner`, `editor` and `member`, and invitation statuses to `pending_approval`, `sent`, `accepted`, `declined`, `rejected`, `revoked` and `expired`.
An organization may have at most one open invitation (status `pending_approval` or `sent`) per email address, and invitation token hashes are unique.
Add an append-only `audit_events` table (`id`, `occurred_at`, `actor_user_id`, `actor_was_superadmin`, `action`, `organization_id`, `subject_user_id`, `collection_id`, `details` as JSONB defaulting to an empty object) whose subject columns have no foreign keys, so an event outlives what it describes, indexed for reading by organization, by subject user and by time.
Deleting an organization removes its members and invitations, and deleting a user removes their memberships but keeps invitations and events with the user reference set to null.
Add nullable `text_quota_bytes` and `collection_quota` override columns to the existing `user` table as well.
Write Alembic migration `0017` on top of `0016` that creates exactly this schema, so the migrated database matches the metadata.
```

An: 

## 21. `d14fd6c5a4` feat(cli): add pharma-agent corpus import and release commands

- sha: `d14fd6c5a43df888ed5f20562c145ef5536501fc`
- layer: infrastructure
- src_lines: 306
- hidden tests:
  - `backend/tests/infrastructure/test_corpus_factory.py`
  - `backend/tests/infrastructure/test_settings.py`
  - `backend/tests/test_cli_corpus.py`
- AI criterion 3: **fail**. The CLI tests monkeypatch `pharma_agent.cli.open_corpus_services` and assert many exact output lines, so they pass only if the CLI module imports the factory under that name and prints the original wording, which the prompt would have to dictate.

Draft prompt:

```text
Add `pharma-agent corpus` commands for importing knowledge bundles and managing corpus releases from the command line.
In a new module `pharma_agent.infrastructure.corpus_factory`, provide a `CorpusServices` dataclass (`importer`, `releases`, `index`, `embedder`) and an async context manager `open_corpus_services(settings, *, embedder=None, alias=<current alias>)` that opens its own database engine, Qdrant client and embedding client from the settings, yields the existing import and release services wired to them, and closes everything on exit.
Without an injected embedder it builds an `OpenAiEmbedder` from the embedding settings, and the Qdrant vector index's collection name follows the embedder's model and dimension while its alias is the given `alias`.
Add a `corpus` settings group with `embed_batch_size` (default 32, at least 1), `embed_max_concurrent` (default 1) and `gc_keep` (default 2), configurable through `PHARMA_CORPUS__*` environment variables.
Add the commands `corpus import <dir> --collection <key> [--publish]`, `corpus releases [--collection <key>]`, `corpus publish <release id>`, `corpus rollback --collection <key>`, `corpus gc --collection <key> [--keep <n>]` and `corpus reindex --collection <key>`.
`import` validates the bundle before opening any services, exits with code 2 when the bundle is invalid or belongs to another collection, and reports whether a new release was imported or nothing changed, with chunk and point counts.
The other commands print one line per release (marking the current one), the rollback target, the published release, how many releases were retired and how many points were upserted, and they exit with code 1 and the error code (for example `RELEASE_NOT_FOUND` or `COLLECTION_NOT_FOUND`) on application errors.
```

An: 

## 22. `ad31679e10` feat(audit): read organization, personal and global audit logs

- sha: `ad31679e10df0da3b2c8587e37ebaa1303ca6b9c`
- layer: application
- src_lines: 149
- hidden tests:
  - `backend/tests/application/test_audit_service.py`
- AI criterion 3: **pass**. The tests use the new public `AuditService` (keyword constructor, `for_organization`, `mine`, `everything`) and the returned page fields, while the error classes, audit models, policy and fakes already exist at the parent.

Draft prompt:

```text
Add read access to the audit log as a new application service `AuditService` in `pharma_agent.application.audit.service`, constructed with the keyword arguments `audit`, `accounts`, `organizations` and `clock`.
It provides three async methods, each taking `limit` and `cursor` as keyword arguments and returning an `AuditPage`: `for_organization(actor, organization_id, *, limit, cursor)`, `mine(actor, *, limit, cursor)` and `everything(actor, *, limit, cursor)`.
An `AuditPage` has `items` (newest first) and `next_cursor`, which is an opaque cursor made with the existing keyset cursor helpers when more events remain and `None` on the last page.
Each item is an `AuditEventView` with the event's `id`, `occurred_at`, `actor_user_id`, `actor_was_superadmin`, `action`, `organization_id`, `subject_user_id`, `collection_id` and `details`, plus `actor_name`, the actor's display name, email or phone number (or an empty string when unknown).
The organization log follows the existing access policy: callers who cannot see the organization (or when it does not exist) get `OrganizationNotFound`, and members who may see it but not its log get `ForbiddenRole`.
`mine` returns the events whose subject is the calling user, and `everything` returns all events but raises `ForbiddenRole` for anyone who is not a superadmin.
Move `ForbiddenRole` and `OrganizationNotFound` into `pharma_agent.application.errors` and keep importing them from `pharma_agent.application.organizations.errors` working.
```

An: 

## 23. `a146825676` feat(api): create conversations before the first message

- sha: `a1468256769c3db82ae7a4ec69cf27190b1b416c`
- layer: domain
- src_lines: 55
- hidden tests:
  - `backend/tests/api/test_conversations_api.py`
  - `backend/tests/application/test_chat_service.py`
  - `backend/tests/application/test_queries.py`
  - `backend/tests/domain/test_conversation.py`
- AI criterion 3: **pass**. The tests use the HTTP route `POST /api/v1/conversations`, the existing `ConversationQueries`, `ChatService` and `Conversation`, and the new public names `DEFAULT_TITLE`, `Conversation.create_empty`, `Conversation.title_from_first_message` and `ConversationQueries.create`, all nameable in the prompt.

Draft prompt:

```text
Let clients create an empty conversation before sending its first message.
Add `POST /api/v1/conversations`, which creates an empty conversation for the current user and answers 201 with the existing `ConversationView` (`id`, `title`, `turn_count`, `created_at`, `updated_at`), backed by a new `ConversationQueries.create(user_id)` method.
In `pharma_agent.domain.conversation.models`, add the constant `DEFAULT_TITLE = "Cuộc trò chuyện mới"` and a class method `Conversation.create_empty(*, user_id, now, conversation_id=None)` that makes a conversation with that title, no turns, both timestamps set to `now` and a new 32-character id when none is given.
Add `Conversation.title_from_first_message(message) -> bool`, which sets the title from the cleaned first message (whitespace collapsed, cut to 80 characters) only when the conversation still has the default title and no turns, returns whether the title changed, and leaves `updated_at` untouched.
A blank message, a renamed conversation or a conversation that already has turns keeps its title.
`Conversation.start` must reuse this behaviour, so a blank first message gives the default title.
When the first chat turn is sent to a pre-created conversation, the chat service names the conversation from that message and stores the new title, while later turns and conversations renamed before their first message keep their titles.
Empty conversations must not appear in the conversation list until they have a turn, but they can be fetched by id.
```

An: 

## 24. `7106f74799` feat(application): add opaque keyset cursor helpers

- sha: `7106f74799b645fcce5361c9dd434fdbd13ae783`
- layer: application
- src_lines: 52
- hidden tests:
  - `backend/tests/application/test_pagination.py`
- AI criterion 3: **pass**. The tests use only the new public `encode_cursor`, `decode_cursor` and `InvalidCursor` and the cursor's encoded format, all of which the prompt specifies, plus the existing `InvalidInput`.

Draft prompt:

```text
Add opaque keyset pagination cursors to the application layer in a new module `pharma_agent.application.pagination`.
Provide `encode_cursor(timestamp: datetime, id: str) -> str`, which encodes the JSON object `{"t": <timestamp>, "id": <id>}` as URL-safe base64 with the `=` padding removed, where the timestamp is converted to UTC and written in ISO 8601 format with microseconds.
It must raise `ValueError` with a message containing `timezone-aware` when the timestamp is naive.
Provide `decode_cursor(cursor: str) -> tuple[datetime, str]`, which reverses the encoding, accepts cursors with or without padding, returns the timestamp in UTC, and returns the id as a UUID in 32-character hexadecimal form (hyphenated UUIDs are accepted).
Any malformed cursor must raise `InvalidCursor`: invalid base64 or characters, JSON that is not an object with exactly string `t` and `id` values, a timestamp that is not a timezone-aware ISO 8601 value, or an id that is not a UUID.
`InvalidCursor` must subclass the existing `InvalidInput` error and use the error code `INVALID_CURSOR`.
Keep the error message generic so it does not echo the cursor back.
```

An: 

## 25. `7757b6cc65` feat(observability): trace chat turns in Langfuse and store skills in Postgres

- sha: `7757b6cc65a57e566b2e3bba4b021000dbbe3c99`
- layer: infrastructure
- src_lines: 148
- hidden tests:
  - `backend/tests/infrastructure/test_container.py`
  - `backend/tests/infrastructure/test_langfuse_tracing.py`
- AI criterion 3: **pass**. The runnable test uses the new public `LangfuseTracing` (constructor, `trace_id_for`, `record_feedback`, `flush`) and its two name constants, together with the existing chat runner and tracer protocol (the container test is integration-only).

Draft prompt:

```text
Trace every chat turn in Langfuse and record user feedback as a score on the same trace.
Add a class `LangfuseTracing(client: Langfuse)` in a new module `pharma_agent.infrastructure.observability.langfuse_tracing`, implementing the existing turn tracer protocol, with a `from_settings(settings)` class method, `trace_id_for(run_id)`, `trace_turn(run)`, `record_feedback(*, run_id, rating, note)`, `flush()` and `shutdown()`.
Define the constants `TURN_OBSERVATION_NAME = "chat_turn"` and `FEEDBACK_SCORE_NAME = "user_feedback"`.
`trace_id_for` must derive a deterministic Langfuse trace id from the run id, so the turn and its later feedback share one trace.
`trace_turn` opens one observation named `chat_turn` on that trace, carrying the run's user id and conversation id as the Langfuse user and session, the original query as input and the final answer text as output, and its handle provides LangChain callbacks so the LangGraph node spans (for example `guard` and `answer`) are nested in the same trace.
`record_feedback` creates a numeric `user_feedback` score on the run's trace with the value 1.0 for an `up` rating and 0.0 otherwise, using the note as the comment.
Add a `Tracing` protocol in `pharma_agent.application.tracing` that combines the turn tracer and score sink, and use `LangfuseTracing` in the container when Langfuse is configured.
The container should also sync the system skills into Postgres at startup and let the agent read its skill catalog from there.
```

An: 

## 26. `bc3c787409` feat(corpus): port glossary, colloquial and embedding text enrichment

- sha: `bc3c787409971fa98aed52839e426c2150da4281`
- layer: domain
- src_lines: 161
- hidden tests:
  - `backend/tests/domain/corpus/test_enrichment.py`
- AI criterion 3: **fail**. The four functions are nameable, but the tests compare byte-exact embedding text ported from the external corpus pipeline (labels, separators, deduplication, the eight-match limit that skips terms without expansions), so a 5-10 sentence prompt cannot specify it without dictating the implementation.

Draft prompt:

```text
Port the corpus enrichment rules (glossary terms, colloquial names and embedding text) into a new domain module `pharma_agent.domain.corpus.enrichment`.
Provide `build_context_header(title, context_path)`, which joins the title and the non-empty path items with `\n> `, dropping blank lines and any `Tên gọi khác:` or `Dấu hiệu nhận biết:` label lines (case-insensitive).
Provide `detect_terms(text, glossary)`, which returns a `TermAnnotation` (`term`, `vi`, `en`) for each glossary entry whose term or alias occurs in the text as a whole word (Vietnamese letters count as word characters, and case matters only for case-sensitive entries), ordered by first occurrence, with whitespace-normalized and de-duplicated expansions, and at most 8 annotations among entries that have expansions.
Provide `mapping_for_section(section_key, mappings)`, which returns the compacted `ColloquialMapping` (key, de-duplicated aliases, visual sign, product names) of the first record that lists the section key, or `None` when no record lists it or the record carries nothing useful.
Provide `compose_embedding_text(*, context_header, chunk_text, colloquial, terms)`, which joins with blank lines the header, a colloquial block, the chunk text and a term block, leaving out empty parts.
The colloquial block has a `Tên gọi khác: ` line listing aliases not already visible in the chunk and a `Dấu hiệu nhận biết: ` line when the visual sign is not already visible, both checks ignoring case.
The term block is `Thuật ngữ: ` followed by `TERM = expansion; expansion` entries joined by ` | `, merging repeated terms, and it is omitted when the chunk already contains a term block.
```

An: 

## 27. `1f00fc352f` feat(domain): add conversation repository port and summarizer prompt

- sha: `1f00fc352f28011340cd70f633743a443111c675`
- layer: domain
- src_lines: 80
- hidden tests:
  - `backend/tests/domain/test_summary_prompt.py`
- AI criterion 3: **pass**. The tests call only the new public `summary_messages` and read the message contents, while `Turn` and `DISCLAIMER_PHRASES` already exist at the parent.

Draft prompt:

```text
Add the conversation summarizer prompt and the conversation repository port to the domain layer.
In a new module `pharma_agent.domain.conversation.prompts`, provide `summary_messages(previous_summary, turns, *, max_chars) -> list[ChatMessage]` that returns a system message and a user message for an LLM that keeps a rolling summary of a drug-information conversation.
The system message, in Vietnamese, asks for a JSON object with a `summary` field, says what to keep (drug and brand names, the patient group, symptoms, doses discussed and what the user still wants to know) and what to drop (greetings, repetition, `[n]` citation markers), and states the limit of `max_chars` characters as a number.
The user message contains the previous summary, or the placeholder `(chưa có)` when it is empty, followed by every new turn rendered with both the user text and the assistant text.
No text may contain any phrase from the existing `DISCLAIMER_PHRASES`.
In `pharma_agent.domain.conversation.ports`, add a `ConversationRepository` protocol with async methods to create, get, list, rename, update the summary of and delete a user's conversations, append a turn's messages, read recent turns and the turns since a given count, and page through messages.
```

An: 

## 28. `2541825733` feat(application): add rolling conversation summary and conversation queries

- sha: `2541825733ff82c2388a826b4afdebeccf89c872`
- layer: application
- src_lines: 173
- hidden tests:
  - `backend/tests/application/test_queries.py`
  - `backend/tests/application/test_summarize.py`
- AI criterion 3: **pass**. The tests use the new public `ConversationQueries` and `SummarizeConversation` classes with their methods and result fields, while the repository fake, `Conversation` helpers, `summary_messages` and the fake LLM already exist at the parent.

Draft prompt:

```text
Add conversation read and management use cases and a rolling conversation summary to the application layer.
Create `ConversationQueries(conversations, clock)` in `pharma_agent.application.conversation.queries` with async methods `list_conversations(user_id, *, limit, before=None)`, `get_conversation(user_id, conversation_id)`, `list_messages(user_id, conversation_id, *, limit, ...)`, `rename(user_id, conversation_id, title)` and `delete(user_id, conversation_id)`.
Conversations are returned as `ConversationView` models (`id`, `title`, `turn_count`, `created_at`, `updated_at`) in the order the repository lists them, and messages as `MessageView` models (`id`, `role` as a string, `content`, `status`, `citations`, `phases`, `created_at`) in chronological order.
`rename` trims the title, stamps `updated_at` with the clock's time and raises `InvalidInput` for an invalid title, and every method raises `ConversationNotFound` when the conversation does not exist or belongs to another user.
Create `SummarizeConversation(llm, conversations, clock, *, every, max_chars)` in `pharma_agent.application.memory.summarize` with an async `run_if_needed(*, user_id, conversation_id) -> bool`.
It does nothing and returns `False` when the conversation is missing or fewer than `every` turns have been added since the last summary.
Otherwise it reads the turns added since the last summary, leaves out turns whose status is `blocked`, `error` or `timeout`, and asks the LLM with the `SUMMARIZER` role and the existing `summary_messages` prompt to fold them into the previous summary; the result is cut to `max_chars`, stored with the number of turns it now covers, and `True` is returned.
If only excluded turns were added, the covered turn count advances without calling the LLM and it returns `False`, and if the LLM fails the previous summary and count are kept and it returns `False`.
```

An: 

## 29. `86a0dae1a6` feat(retrieval): rerank through DeepInfra's inference endpoint

- sha: `86a0dae1a6e14253c2bf4e1b730c112fdcfd01c6`
- layer: infrastructure
- src_lines: 68
- hidden tests:
  - `backend/tests/infrastructure/test_deepinfra_reranker.py`
- AI criterion 3: **pass**. The tests use the new public `DeepInfraReranker` (constructor, `rerank`), DeepInfra's documented HTTP contract that the prompt states, and the existing `build_reranker` and `RerankSettings`.

Draft prompt:

```text
Support reranking through DeepInfra's inference endpoint as a new reranker protocol.
Add a class `DeepInfraReranker(http: httpx.AsyncClient, *, model: str, max_concurrent: int = 2)` in a new module `pharma_agent.infrastructure.retrieval.deepinfra_reranker`, implementing the existing reranker port with `rerank(query, hits, top_n)` and an `aclose()` that closes the HTTP client.
`rerank` posts to `/v1/inference/<model>` a JSON body with `queries` (the query repeated once per candidate) and `documents` (each candidate's document text, built the same way as for the existing llama.cpp reranker), and reads one score per pair from the `scores` list of the response.
It returns the `top_n` candidates sorted by score, highest first, with each score stored as the hit's rerank score.
An HTTP error, an invalid JSON answer, a missing `scores` list or a score count that differs from the candidate count must raise `RetrievalError`.
With no candidates it returns an empty list without sending any request.
Accept `deepinfra` as a value of the rerank `protocol` setting (`PHARMA_RETRIEVAL__RERANK__PROTOCOL`), and make the existing `build_reranker(settings)` return a `DeepInfraReranker` for it, using the configured base URL, bearer API key and model.
```

An: 

## 30. `7631b0a4b3` feat(skills): add Postgres skill repository, slug helper and skills table

- sha: `7631b0a4b3b837980f76c8d4f3875f45e8e56988`
- layer: infrastructure
- src_lines: 294
- hidden tests:
  - `backend/tests/domain/test_slug.py`
  - `backend/tests/infrastructure/test_skill_repository.py`
- AI criterion 3: **pass**. The only runnable hidden test calls the new public `slugify` in `pharma_agent.domain.skill.slug`, which the prompt names (the repository tests are integration-only and never run, so grading checks only the slug helper).

Draft prompt:

```text
Store skills in Postgres and add a slug helper for user skill ids.
Add `slugify(text: str) -> str` in a new module `pharma_agent.domain.skill.slug`, which folds Vietnamese text to lowercase ASCII (including `đ` to `d`), joins the words with single hyphens, drops punctuation, returns `skill` when nothing is left, and never returns more than 60 characters.
Add a `SkillRepository` protocol to `pharma_agent.domain.skill.ports` that extends the existing skill catalog port with `upsert_system(skills)`, `create(skill)`, `list_for_user(user_id)`, `get_owned(user_id, skill_id)`, `set_enabled(user_id, skill_id, enabled)` and `delete_owned(user_id, skill_id)`.
Implement it as `PostgresSkillRepository(sessions)` in `pharma_agent.infrastructure.persistence.postgres.skill_repository`, backed by a new `skills` table and Alembic migration `0002`.
Upserting system skills is idempotent and updates a system skill whose version changed.
The catalog for a user lists the enabled system skills plus that user's own enabled skills, up to the limit, while `list_for_user` returns only the user's own skills.
Owned-skill operations ignore skills that belong to other users: `get_owned` and `set_enabled` return `None` for them and `delete_owned` returns `False`.
User skills are deleted together with their owner.
```

An: 

## 31. `36f7328ba2` feat(domain): add streaming citation sanitizer

- sha: `36f7328ba26e5bfc934716a8912026921cfdba82`
- layer: domain
- src_lines: 74
- hidden tests:
  - `backend/tests/domain/test_citations.py`
- AI criterion 3: **pass**. The tests use the new public `CitationSanitizer` (`feed`, `flush`, `used`) and `citations_from`, while `EvidenceSet`, `RetrievedItem`, `Citation` and the hit factory already exist at the parent.

Draft prompt:

```text
Add a streaming citation sanitizer to the domain layer in a new module `pharma_agent.domain.agent.citations`, for answers that arrive from the LLM in small text deltas.
Provide a class `CitationSanitizer(valid_indexes)` with `feed(delta) -> str`, `flush() -> str` and a `used` attribute listing the valid citation numbers in the order they first appeared, without duplicates.
A citation marker is a number of one to three digits in square brackets, like `[2]`, and it must be recognized even when it is split across several deltas.
Markers whose number is in `valid_indexes` pass through unchanged, while markers with any other number are removed from the output, leaving the surrounding text (including spaces) untouched.
Brackets that do not hold a citation number, such as `[ghi chú]`, pass through unchanged.
While the end of a delta might be the start of a marker, `feed` holds that part back, and `flush` returns whatever is still held, verbatim.
Also provide `citations_from(numbered, used) -> list[Citation]`, where `numbered` is the list of `(index, evidence)` pairs produced by the existing `EvidenceSet.context_view`, returning one `Citation` per used index in the order of `used` with the index and the hit's chunk id, section id, title, section, start and end pages and table id, and skipping indexes that are not numbered.
```

An: 

## 32. `0a6b1f0680` feat(email): send through the Gmail API, since Render Free blocks outbound SMTP

- sha: `0a6b1f0680aa824d1f5621a6bcb6716748242f61`
- layer: infrastructure
- src_lines: 121
- hidden tests:
  - `backend/tests/infrastructure/test_notifications.py`
- AI criterion 3: **pass**. The new tests use the public `GmailApiEmailSender` (constructor and `send`) against Google's documented token and Gmail send endpoints, plus the existing `build_email_sender` and `EmailSettings`; the older SMTP tests in the file already pass at the parent.

Draft prompt:

```text
Add a Gmail API email provider, because the hosting platform blocks outbound SMTP.
Add a class `GmailApiEmailSender(client_id, client_secret, refresh_token, sender, timeout)` to `pharma_agent.infrastructure.notifications.email`, with the same async `send(*, to, subject, text, html)` as the other email senders.
It obtains an access token by posting a `refresh_token` grant with the client id, secret and refresh token to `https://oauth2.googleapis.com/token`, and reuses that token for later messages until shortly before it expires.
It sends each message by posting JSON `{"raw": ...}` to `https://gmail.googleapis.com/gmail/v1/users/me/messages/send` with a bearer authorization header, where `raw` is the URL-safe base64 encoding of a `multipart/alternative` MIME message (plain text and HTML) with the `From` and `To` headers set.
A failed token request or send request must raise the existing `DeliveryError`, with a message that includes Google's error code (for example `invalid_grant`) or the HTTP status.
Accept `gmail` as an email `provider` and add the settings `gmail_client_id`, `gmail_client_secret` and `gmail_refresh_token` (the last two secret).
Make `build_email_sender` return this sender for the `gmail` provider, and raise `ValueError` naming `PHARMA_EMAIL__GMAIL_CLIENT_ID`, `PHARMA_EMAIL__GMAIL_CLIENT_SECRET` and `PHARMA_EMAIL__GMAIL_REFRESH_TOKEN` when any of them is missing.
```

An: 

## Not drafted yet (rest of the review order)

Drafted on request if the commits above do not fill the quotas after review.

33. `32ffcf95d0` (infrastructure) feat(cli): add cleanup-sessions for expired cookie sessions
34. `6443cf55bb` (domain) feat(domain): add Conversation aggregate, Message and turn builder
35. `acb48cc1da` (infrastructure) feat(backend): add account tables and migration 0013
36. `5e96fe064b` (domain) feat(corpus): port prose, table and entry-list splitters
37. `8865ee944f` (api) feat(api): return RFC 9457 problem details for every error
38. `507a4ae31e` (domain) feat(corpus): add deterministic section revision and chunk version ids
39. `e967c0c6f8` (infrastructure) feat(backend): add composition root and pharma-agent CLI
40. `afaac9e8bd` (infrastructure) feat(audit): record release ids and chunk version ids for retrieval runs
41. `0898d85ed3` (domain) feat(domain): add retrieval models, ports and EvidenceSet packing
42. `82a51e2e14` (infrastructure) feat(infra): add llama.cpp rerankers with pipeline-identical qwen3 prompt
