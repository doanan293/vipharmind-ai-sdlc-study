# Feature-tier task review (F08, F14, F15)

This file is the draft for An's review (feature-tier plan, Task 2). For each range below:

1. Read the draft prompt and the name audit (every public name the hidden tests use, or that the
   support files restored from `end` need, marked as existing at `base`, named in the prompt, or GAP).
2. Write your verdict on the `An's verdict:` line, as `pass` or `fail` (a short reason is welcome).
3. Edit the draft prompt in place if needed. It must stay in English, 5-12 sentences of description
   plus a "Required interfaces" section that lists names only, and must not mention tests, hidden
   tests, test files or grading.

How the drafts were made: from the commit messages, `git diff base end -- backend/src`, the hidden
tests at `end`, the support files restored from `end`, and `tasks/feature-feasibility/coupling.json` /
`fakes_contract.json`. Each draft was then audited in the same way as `tasks/PROMPT_AUDIT.md`. Every GAP
the audit found was fixed in the draft before it was written here, so the audit tables show the final
state: no GAP remains.

Conventions used in the audit tables:

- **base**: the name already exists at the range's `base` commit (or comes from a library, or from a
  test helper that the range does not change).
- **support**: the name lives in a test support file that grading restores from `end`.
- **named**: the draft prompt names it (in the description or in "Required interfaces").
- **integration**: only a test marked `integration` uses it. The grader deselects those tests, but
  pytest still imports their modules, so a name they import at module level must exist or
  collection fails. Such import-level names are listed as **named**. Names that are only used inside
  integration test bodies are named too, but they do not affect grading.

Sizes count inserted plus deleted lines from `git diff --shortstat base end`.

## Summary

| task | commits | src lines (+/-) | test lines (+/-) | hidden test files | description sentences | required-interface entries | GAPs left | residual ambiguities |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| f08 | 6 | 764 (679/85) | 984 (920/64) | 15 | 12 | 14 | 0 | 4 (minor) |
| f14 | 4 | 1,464 (1,403/61) | 657 (655/2) | 7 | 12 | 16 | 0 | 4 (minor) |
| f15 | 5 | 1,367 (1,331/36) | 1,128 (1,118/10) | 14 | 12 | 20 | 0 | 5 (2 moderate, 3 minor) |

Cross-task notes:

- F08 contains the small-tier task t03 (`c3a88b2659`, OpenAPI) and the pilot p02. Sentences 11-12 of
  the F08 draft reuse the approved t03 prompt almost word for word.
- F14 starts at `c2935909a1`, which is small-tier task t01 (organization service). F15 starts where
  F14 ends, so F15's base already contains the F14 feature.
- All three prompts are long, near the 12-sentence limit, because the hidden tests pin many exact
  strings (error codes, email subjects, CLI output). The "Required interfaces" lists are longer than
  `coupling.json` suggests (6, 9 and 11 new symbols). The reason is that coupling.json counts only
  imported symbols. It leaves out constructor keywords, fields, method names, port methods that
  the restored fakes implement, route names checked through OpenAPI, and CLI commands.

---

## 1. f08: web API (problem details, keyset cursors, pre-created conversations, OpenAPI export)

- range: `45271fddc0236bc3f3336b30d99771abf626f14c..cc0f06a67bfa888ef5d7e1ebd1715a517079bbc9`
- commits (oldest first):
  - `8865ee9` feat(api): return RFC 9457 problem details for every error
  - `7106f74` feat(application): add opaque keyset cursor helpers
  - `62350a9` feat(api): page conversations and messages with keyset cursors
  - `a146825` feat(api): create conversations before the first message
  - `c3a88b2` feat(api): pin operation ids, document problem responses, export OpenAPI (= t03)
  - `cc0f06a` feat(chat): pre-generate turn message ids and report persisted on done
- size: backend/src 24 files, +679/-85 (764 lines); backend/tests 16 files, +920/-64 (984 lines)
- hidden tests (15):
  - `backend/tests/api/test_conversations_api.py` (M)
  - `backend/tests/api/test_e2e_postgres.py` (M, integration)
  - `backend/tests/api/test_openapi.py` (A)
  - `backend/tests/api/test_problem_details.py` (A)
  - `backend/tests/api/test_skills_api.py` (M)
  - `backend/tests/application/test_chat_service.py` (M)
  - `backend/tests/application/test_feedback_service.py` (M)
  - `backend/tests/application/test_pagination.py` (A)
  - `backend/tests/application/test_queries.py` (M)
  - `backend/tests/application/test_summarize.py` (M)
  - `backend/tests/domain/test_conversation.py` (M)
  - `backend/tests/infrastructure/test_container.py` (M, integration)
  - `backend/tests/infrastructure/test_conversation_repository.py` (M, integration)
  - `backend/tests/infrastructure/test_migrations.py` (M, integration)
  - `backend/tests/test_cli.py` (M)
- support files restored from `end`: `backend/tests/memory_repository.py`. Its
  `InMemoryConversationRepository.list_for_user` and `.messages` now take `cursor=` and no longer
  accept `before=`.

Draft prompt:

```text
Rework the HTTP API so that every error is an RFC 9457 problem document, conversation and message lists are paged with opaque keyset cursors, a conversation can be created before its first message, chat turns know their message ids up front, and the OpenAPI document matches what the API sends.
Every error response (application errors, `HTTPException`s including those of fastapi-users, request validation errors, routing errors such as 404 and 405, and unhandled exceptions) must have the media type `application/problem+json` and a `Problem` body with the fields `type`, `title`, `status`, `detail`, `code` and `errors` in that order, where `type` is `urn:pharma-agent:problem:` followed by the code in lower case with hyphens instead of underscores, `title` is the code with spaces instead of underscores and only its first letter capitalized, and `detail` and `errors` are left out when empty.
An application error keeps its `code` and uses its message as `detail`; a request validation error has the code `VALIDATION_ERROR`, no `detail`, and lists one `ProblemItem` (`loc`, `message`, `type`, in that order) per invalid field in `errors`; an unhandled exception gives `INTERNAL_ERROR` with no `detail`, so the exception text is never revealed; and an `HTTPException` keeps a detail that is an upper snake case code (or the `code` of a `{"code": ..., "reason": ...}` detail, with the reason as `detail`), otherwise uses the HTTP status name such as `NOT_FOUND`, `METHOD_NOT_ALLOWED` or `UNAUTHORIZED` as its code and keeps a detail text as `detail` only when it differs from the standard phrase of that status (a plain 404 or 401 has no `detail`), and always keeps its response headers.
Add the application errors `ServiceUnavailable` (`SERVICE_UNAVAILABLE`, HTTP 503) and its subclasses `ServiceStarting` (`SERVICE_STARTING`) and `ServiceNotConfigured` (`SERVICE_NOT_CONFIGURED`), make `AgentUnavailable` a subclass too, and raise them instead of plain 503 exceptions when the service is still starting or the database, skills or feedback are not configured (the database case with the message `the database is not configured`).
Add a module `pharma_agent.application.pagination` with `encode_cursor(timestamp, id)`, which returns the unpadded base64url encoding of the compact JSON `{"t": <the timestamp in UTC, ISO 8601>, "id": <id>}` and raises `ValueError` saying the timestamp must be timezone-aware for a naive one, and `decode_cursor(cursor)`, which also accepts padded input and hyphenated UUIDs, returns a `(UTC datetime, 32-character hex id)` tuple, and raises `InvalidCursor` (code `INVALID_CURSOR`, a subclass of `InvalidInput`) for anything malformed, including an empty string, a naive timestamp or an id that is not a UUID.
`ConversationQueries.list_conversations(user_id, *, limit, cursor=None)` and `ConversationQueries.list_messages(user_id, conversation_id, *, limit, cursor=None)` must return `ConversationPage` and `MessagePage` models with `items` and `next_cursor` (`None` on the last page, while an empty cursor string means the first page): conversations come newest first by `(updated_at, id)` and conversations without any turn are left out, and a message page holds the newest messages older than the cursor, oldest first, with `next_cursor` pointing to still older ones.
The conversation repository port's `list_for_user` and `messages` replace `before` with a keyword `cursor` holding a `(timestamp, id)` tuple and compare strictly on that pair (Postgres gets matching sort indexes that end with the id), and the HTTP list endpoints take `limit` (at most 100, default 20 for conversations and 30 for messages) and `cursor` (at most 512 characters) and return these page models.
Add `Conversation.create_empty(*, user_id, now, conversation_id=None)`, which uses the title `DEFAULT_TITLE` (`"Cuộc trò chuyện mới"`), and `Conversation.title_from_first_message(message) -> bool`, which only for a conversation that has no turns and still has the default title sets the title from the message the way `start` does (cleaned, cut to 80 characters, a blank message ignored) without changing `updated_at`, and returns whether the title changed.
Add `ConversationQueries.create(user_id)` and a `POST /api/v1/conversations` endpoint (route name `create_conversation`, status 201, returning `ConversationView`), and make the chat service name a pre-created conversation from its first message and save that title when the turn opens, so that turn's `conversation` event already carries it.
`build_turn_messages` must take the keyword arguments `user_message_id` and `assistant_message_id`, and `ChatService.open_turn` generates both ids up front (distinct 32-character hex) and exposes them as `ChatSession.user_message_id` and `ChatSession.assistant_message_id`; the first `conversation` event adds `message_id` (the assistant id), and the single `done` event carries `message_id` (null when the turn was not saved), `persisted` and `created_at` (the assistant message time as an ISO 8601 string, while `ChatTurnResult.created_at` holds the same time as a `datetime`) instead of a separate `PERSIST_FAILED` error event, so the CLI prints `!! Không lưu được lượt hội thoại này.` to stderr when it renders a `done` event whose `persisted` is false.
In the OpenAPI document every `operationId` must be the route name (for example `list_conversations`, or `auth:jwt.login` for the fastapi-users routes) and unique, every error status (400 and above) must document only `application/problem+json` with the `Problem` schema (the health endpoint's 503 also keeps its `application/json` `HealthResponse` body), routes must document the error statuses they can return (authenticated routes include 401, 422 and 503, and skill upload also 409 and 413), the unused `HTTPValidationError`, `ValidationError` and `ErrorModel` schemas must disappear, form body schemas must be named `Body_<operation id>` with every character outside `[A-Za-z0-9_]` replaced by an underscore, and calling `app.openapi()` repeatedly must return the same document.
Add `openapi_export_settings()` and `render_openapi(app)` to a new module `pharma_agent.api.openapi` (the first returns settings that need no environment or services and enable Google OAuth with placeholder credentials so its routes appear, the second returns the document as JSON with sorted keys, two-space indentation, non-ASCII characters kept and a trailing newline), and a `pharma-agent export-openapi --output <file>` command that writes that rendering to the file, creating missing parent directories, and prints `wrote <file>`.

Required interfaces:
- `pharma_agent.api.openapi`: `openapi_export_settings`, `render_openapi`
- OpenAPI component schemas: `Problem` (`type`, `title`, `status`, `detail`, `code`, `errors`), `ProblemItem` (`loc`, `message`, `type`), `ConversationPage`, `MessagePage`
- `pharma_agent.application.errors`: `ServiceUnavailable`, `ServiceStarting`, `ServiceNotConfigured`
- `pharma_agent.application.pagination`: `encode_cursor`, `decode_cursor`, `InvalidCursor`
- `pharma_agent.application.conversation.queries`: `ConversationPage`, `MessagePage` (`items`, `next_cursor`); `ConversationQueries.create`; keyword `cursor` of `ConversationQueries.list_conversations` and `ConversationQueries.list_messages`
- `pharma_agent.domain.conversation.ports.ConversationRepository`: keyword `cursor` of `list_for_user` and `messages`
- `pharma_agent.domain.conversation.models`: `DEFAULT_TITLE`, `Conversation.create_empty`, `Conversation.title_from_first_message`
- `pharma_agent.domain.conversation.turns.build_turn_messages`: keywords `user_message_id`, `assistant_message_id`
- `pharma_agent.application.chat.service`: `ChatSession.user_message_id`, `ChatSession.assistant_message_id`, `ChatTurnResult.created_at`
- Progress event data keys: `message_id` (conversation and done events), `persisted`, `created_at` (done event)
- Error codes: `VALIDATION_ERROR`, `INTERNAL_ERROR`, `SERVICE_UNAVAILABLE`, `SERVICE_STARTING`, `SERVICE_NOT_CONFIGURED`, `INVALID_CURSOR`
- Route name: `create_conversation`
- CLI command: `pharma-agent export-openapi --output <file>`
- Postgres indexes: `ix_conversations_user_updated_id`, `ix_messages_conversation_created_id`
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `create_app`, `tests.api.harness` (`build_harness(agent=, authenticated=)`, `Harness.app/.repo/.container/.llm/.client`, `OWNER`), `tests.api.test_chat_api.script_turn`, `tests.api.asgi.running` | api tests | base |
| `harness.container.skills = None`, `.feedback = None` | test_problem_details | base |
| `fastapi.HTTPException`, `fastapi_users.router.common.ErrorCode` | test_problem_details | base (library) |
| media type `application/problem+json`; body keys `type`, `title`, `status`, `detail`, `code`, `errors`; `type`/`title` derivation | test_problem_details | named |
| codes `CONVERSATION_NOT_FOUND`, `AGENT_UNAVAILABLE` | test_problem_details | base |
| codes `VALIDATION_ERROR`, `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `UNAUTHORIZED`, `FORBIDDEN`, `INTERNAL_ERROR`, `SERVICE_STARTING`, `SERVICE_NOT_CONFIGURED`, `INVALID_CURSOR`; fastapi-users codes passed through | test_problem_details, test_conversations_api, test_e2e_postgres | named |
| `errors` items `loc`, `message`, `type` | test_problem_details | named |
| `Allow` / `WWW-Authenticate` headers kept | test_problem_details | named ("keeps its response headers") |
| detail `the database is not configured` | test_problem_details | named |
| `detail` = app-error message (`"lowercase" in detail`) | test_skills_api | named |
| `pharma_agent.api.openapi.openapi_export_settings`, `render_openapi` | test_openapi, test_cli | named |
| operation ids `health` ... `oauth:google.jwt.callback` (existing route names) | test_openapi | base (rule "operationId = route name" named) |
| operation id `create_conversation` | test_openapi | named |
| schema components `ConversationView`, `FeedbackView`, `SkillView`, `HealthResponse` | test_openapi | base |
| schema components `Problem`, `ProblemItem`, `ConversationPage`, `MessagePage` | test_openapi | named |
| `Problem.required == [type, title, status, code]`, `ProblemItem.required == [loc, message, type]` (field order) | test_openapi | named ("in that order") |
| `Body_auth_jwt_login`, `Body_upload_skill`; absence of `HTTPValidationError`, `ValidationError`, `ErrorModel` | test_openapi | named (rule) |
| `pharma_agent.application.pagination.encode_cursor`, `decode_cursor`, `InvalidCursor` | test_pagination, test_queries | named |
| `InvalidCursor.code == "INVALID_CURSOR"`, subclass of `InvalidInput` | test_pagination | named |
| payload `{"t", "id"}`, UTC normalisation, `ValueError` match `timezone-aware` | test_pagination | named |
| `InvalidInput`, `ConversationNotFound` | test_pagination, test_queries | base |
| `ConversationQueries(repo, clock)`, `.get_conversation`, `.rename`, `.delete` | test_queries | base |
| `ConversationQueries.list_conversations(..., cursor=)`, `.list_messages(..., cursor=)`, `.create(user_id)`; `.items`, `.next_cursor` | test_queries, test_conversations_api, test_container | named |
| `ConversationView.id/title/turn_count/created_at/updated_at`; `MessageView.id/role/content/phases/created_at` | test_queries, test_conversations_api | base |
| JSON `{"items", "next_cursor"}`; query params `limit`, `cursor`; `limit=101` and 513-char cursor → 422 `VALIDATION_ERROR` | test_conversations_api | named |
| `POST /api/v1/conversations` → 201 with exactly the 5 `ConversationView` keys | test_conversations_api | named |
| `InMemoryConversationRepository.list_for_user(cursor=)`, `.messages(cursor=)` (called by the agent's queries) | support | named (port keyword `cursor`) |
| `InMemoryConversationRepository.rows`, `.message_log`, `.audit`, `.create`, `.append_turn`, `.update_title` | support / base | base |
| `DEFAULT_TITLE`, `Conversation.create_empty`, `Conversation.title_from_first_message` | test_conversation, test_chat_service | named |
| `Conversation.start`, `.rename`, `.record_turn`, `.turn_count`, `InvalidTitle`, `MessageRole` | test_conversation | base |
| `build_turn_messages(user_message_id=, assistant_message_id=, ...)` | 6 test files | named |
| `pharma_agent.domain.shared.ids.new_id` | 5 test files | base |
| `ChatService(...)`, `.open_turn`, `.ask`, `ChatSession.events/.result/.conversation_id`, `MemoryPolicy`, `ChatTurnRunner`, `build_chat_graph` | test_chat_service | base |
| `ChatSession.user_message_id`, `.assistant_message_id`; `ChatTurnResult.created_at` | test_chat_service | named |
| event data `message_id`, `persisted`, `created_at`; one `done` event, no error event | test_chat_service | named |
| `EventType.DONE`, `ProgressEvent(type=, data=)` | test_chat_service, test_cli | base |
| `pharma_agent.cli._render(event, evidence)` | test_cli | base (private but exists) |
| stderr `!! Không lưu được lượt hội thoại này.` | test_cli | named |
| CLI `export-openapi --output`, output `wrote <file>`, sorted keys, trailing newline | test_cli | named |
| `/api/v1/auth/google/authorize` operation id `oauth:google.jwt.authorize` | test_cli | base |
| `ix_conversations_user_updated_id`, `ix_messages_conversation_created_id` (old names absent) | test_migrations (integration) | named |
| `repo.messages(..., cursor=(created_at, id))`, `list_for_user(..., cursor=...)` on `PostgresConversationRepository` | test_conversation_repository (integration) | named (port keyword) |
| `container.queries.list_conversations(...).items/.next_cursor` | test_container (integration) | named |

GAPs: 0. The first pass had three GAPs, all now fixed in the draft: the field order of
`Problem`/`ProblemItem` (pydantic emits `required` in declaration order), the `cursor` keyword on the
repository port (the restored fake no longer accepts `before`), and the Postgres index names.

Residual ambiguities:

1. Problem `detail` when an application error has an empty message: the original drops an empty
   detail. The prompt says "left out when empty", which covers this. Untested.
2. `title_from_first_message` "cleaned the way `start` does": the test expects
   `"  Paracetamol   uống bao nhiêu? "` → `"Paracetamol uống bao nhiêu?"` and a 200-character message
   cut to 80. Both behaviours come from the existing `_clean_title` and `MAX_TITLE_CHARS`, so an
   agent that reuses them passes. Minor.
3. Message paging with tied timestamps: page boundaries must break ties on the id. The repository
   fake handles this. The agent's queries only need to build the cursor from the oldest item of a
   message page (or the last item of a conversation page) and fetch `limit + 1` rows. The prompt
   gives the semantics, not this method. Minor.
4. `HTTPException` whose detail equals the status phrase (Starlette's 404 `"Not Found"`): the test
   expects no `detail` key. "keeps any custom detail text" implies the phrase is not custom, but this
   is implicit. Minor.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (FEATURE_REVIEW_fable.md)

---

## 2. f14: organization invitations, audit log, organization API, account memberships

- range: `c2935909a101b7274c58ec0e678371c0a13b3d07..11079ab21c7fa8299bd59f73b7e6a901ba98ffc4`
- commits (oldest first):
  - `a7cb058` feat(organizations): invite by email with approval for member invites
  - `ad31679` feat(audit): read organization, personal and global audit logs
  - `239e502` feat(api): organizations, invitations and audit endpoints
  - `11079ab` feat(account): expose memberships and the SMS switch, grant superadmin from the CLI
- size: backend/src 23 files, +1,403/-61 (1,464 lines); backend/tests 9 files, +655/-2 (657 lines)
- hidden tests (7):
  - `backend/tests/api/test_openapi.py` (M)
  - `backend/tests/api/test_organizations_api_postgres.py` (A, integration)
  - `backend/tests/application/test_account_settings_service.py` (M)
  - `backend/tests/application/test_audit_service.py` (A)
  - `backend/tests/application/test_invitation_messages.py` (A)
  - `backend/tests/application/test_invitation_service.py` (A)
  - `backend/tests/infrastructure/test_superadmin_cli.py` (A, integration)
- support files restored from `end`:
  - `backend/tests/account_fakes.py`: imports `MembershipLookup` from
    `pharma_agent.domain.organizations.ports` at module level, and passes `memberships=` to
    `AccountService`. Without both, every account test fails to import.
  - `backend/tests/api/postgres_app.py`: imports `build_organization_services` at module level and
    passes `Container(organizations=...)`.

Draft prompt:

```text
Add email invitations to organizations, read access to the audit log, HTTP endpoints for organizations, invitations and the audit log, and extend the account with its organization memberships, an SMS switch and a superadmin command.
Add a class `InvitationService` in `pharma_agent.application.organizations.invitations`, constructed with the keyword arguments `organizations`, `invitations`, `accounts`, `audit`, `tx`, `email`, `limiter`, `clock` and `policy` (an `InvitationPolicy` with `frontend_url` and hourly limits defaulting to 20 invitation emails per inviter and 5 per address), which uses the existing invitation repository, token helpers, `INVITATION_TTL`, access policy functions and organization errors and provides the async methods `list(actor, organization_id)`, `invite(actor, organization_id, email, role, *, locale)`, `approve(actor, organization_id, invitation_id, *, locale)`, `reject(actor, organization_id, invitation_id)`, `revoke(actor, organization_id, invitation_id)`, `resend(actor, organization_id, invitation_id, *, locale)`, `preview(token)`, `accept(actor, token)` and `decline(actor, token)`.
Invitations from owners and editors are sent at once, while a member's invitation waits in `PENDING_APPROVAL`, without any email, until an owner or editor approves it (a member who tries gets `ForbiddenRole`) or rejects it, and approving, rejecting, revoking or resending an invitation that is not in a state that allows it raises `InvitationNotPending`; the roles one may invite follow the existing policy (`ForbiddenRole` otherwise), outsiders get `OrganizationNotFound`, and after the email is normalized an address that already belongs to a member gets `AlreadyMember` and one with an open invitation gets `InvitationAlreadyOpen`.
Sending issues a fresh token, stores only its hash, sets the expiry seven days ahead and emails the link `<frontend_url>/invitations/<token>` in the text body, so a resend makes the previous link stop working; going over a rate limit raises `RateLimited`, which moves to `pharma_agent.application.errors` (still importable from the account errors module), and a delivery failure raises `DeliveryFailed` and leaves nothing changed.
The organization-side methods return an `InvitationView` (`id`, `organization_id`, `email`, `role`, `status`, `invited_by`, `invited_by_name`, `created_at`, `expires_at`), and `list` shows owners and editors every invitation but members only the ones they sent.
`preview(token)` returns an `InvitationPreview` (`organization_name`, `inviter_name`, `role`, `email_hint`) and raises `InvitationNotFound` for a token that is unknown, replaced, expired or no longer open, where the function `email_hint(email)` keeps only the first character of the local part and replaces the rest with `**` (`an@example.com` becomes `a**@example.com`).
`accept` requires the actor's account to have a verified email equal to the invited address (`InvitationEmailMismatch` otherwise), raises `InvitationExpired` from the expiry time on and `InvitationNotPending` once the invitation is closed, adds the member with the invited role even if the inviter has since left, and returns the existing `OrganizationView`, while `decline` marks the invitation `DECLINED`; every change records its audit event (`INVITATION_CREATED`, `INVITATION_APPROVED`, `INVITATION_REJECTED`, `INVITATION_REVOKED`, `INVITATION_RESENT`, `INVITATION_DECLINED`, `MEMBER_JOINED`) in the same transaction.
Add `invitation_email(*, organization, inviter, role, link, locale)` in `pharma_agent.application.organizations.messages`, returning the existing email content type (`subject`, `text`, `html`) in Vietnamese (subject `Lời mời tham gia <organization> trên ViPharMind`, roles `chủ sở hữu`, `biên tập viên`, `thành viên`) or English (subject `Join <organization> on ViPharMind`, roles `owner`, `editor`, `member`), with the link in the text and as an HTML-escaped button link in the HTML.
Add a class `AuditService` in `pharma_agent.application.audit.service`, constructed with the keyword arguments `audit`, `accounts`, `organizations` and `clock`, with the async methods `for_organization(actor, organization_id, *, limit, cursor)`, `mine(actor, *, limit, cursor)` and `everything(actor, *, limit, cursor)`, each returning an `AuditPage` (`items`, `next_cursor`) of `AuditEventView` items (the event's fields plus `actor_name`: the display name, else the email, else the phone number) newest first and paged with the existing opaque cursor helpers; an organization's log raises `OrganizationNotFound` for outsiders and `ForbiddenRole` for members, `mine` lists the events whose subject is the actor, and `everything` is for superadmins only (`ForbiddenRole` otherwise).
`AccountService` takes an optional keyword argument `memberships` (a new `MembershipLookup` protocol in `pharma_agent.domain.organizations.ports` with `async list_for_user(user_id) -> list[tuple[Organization, Role]]`), `AccountView` replaces `is_superuser` with `is_superadmin` and adds `memberships` (`MembershipView` items with `organization_id`, `name`, `role`) and `phone_sign_in_enabled` (the value of `sms_enabled`), and `AccountPolicy` gets `sms_enabled` (default true, false when `PHARMA_SMS__PROVIDER=none`, a new allowed value), which when false makes `request_phone_login` and `request_phone_change` raise `PhoneSignInDisabled` (code `PHONE_SIGN_IN_DISABLED`, a `ServiceUnavailable`) before anything is sent.
Expose the services as `OrganizationServices` (`actors`, `organizations`, `invitations`, `audit`), built by `build_organization_services(settings, sessions, *, clock, email=None)` in `pharma_agent.infrastructure.organizations_factory` and held in `Container.organizations`, and add endpoints under `/api/v1/organizations`, `/api/v1/invitations/{token}` and `/api/v1/account/audit` with exactly the route names listed below and no other new routes (`everything` gets no endpoint), documenting their error statuses as problem responses like the existing routers (403 for `ForbiddenRole`, 404 for anything not found, 409 for `LastOwner`, `AlreadyMember` and the invitation conflicts, 429 for `RateLimited`).
Add the commands `pharma-agent superadmin grant <email>` and `pharma-agent superadmin revoke <email>` (the email matched case-insensitively, exit code 1 when no account matches) and `pharma-agent superadmin list`, which set and list the superadmin flag directly in Postgres.

Required interfaces:
- `pharma_agent.application.organizations.invitations`: `InvitationService`, `InvitationPolicy`, `InvitationView`, `InvitationPreview`, `email_hint`
- `InvitationService` constructor keywords: `organizations`, `invitations`, `accounts`, `audit`, `tx`, `email`, `limiter`, `clock`, `policy`; methods `list`, `invite`, `approve`, `reject`, `revoke`, `resend`, `preview`, `accept`, `decline`
- `InvitationPolicy` fields: `frontend_url`, `invites_per_inviter_per_hour`, `invites_per_email_per_hour`
- `pharma_agent.application.organizations.messages`: `invitation_email`
- `pharma_agent.application.errors`: `RateLimited`
- `pharma_agent.application.audit.service`: `AuditService`, `AuditPage`, `AuditEventView` (`actor_name`); methods `for_organization`, `mine`, `everything`
- `pharma_agent.domain.organizations.ports`: `MembershipLookup` (`list_for_user`)
- `pharma_agent.application.account.service`: keyword `memberships` of `AccountService`; `AccountPolicy.sms_enabled`; `AccountView.is_superadmin`, `AccountView.memberships`, `AccountView.phone_sign_in_enabled`; `MembershipView` (`organization_id`, `name`, `role`)
- `pharma_agent.application.account.errors`: `PhoneSignInDisabled`
- `pharma_agent.infrastructure.organizations_factory`: `OrganizationServices`, `build_organization_services`
- `pharma_agent.infrastructure.container.Container`: field `organizations`
- Setting value: `PHARMA_SMS__PROVIDER=none`
- Route names: `organizations:list`, `organizations:create`, `organizations:get`, `organizations:rename`, `organizations:delete`, `organizations:members.list`, `organizations:members.set_role`, `organizations:members.remove`, `organizations:leave`, `invitations:list`, `invitations:create`, `invitations:approve`, `invitations:reject`, `invitations:revoke`, `invitations:resend`, `invitations:preview`, `invitations:accept`, `invitations:decline`, `audit:organization`, `audit:mine`
- Paths: `/organizations`, `/organizations/{organization_id}`, `/organizations/{organization_id}/members`, `/organizations/{organization_id}/members/{user_id}`, `/organizations/{organization_id}/leave`, `/organizations/{organization_id}/invitations`, `/organizations/{organization_id}/invitations/{invitation_id}/approve` (also `/reject`, `/revoke`, `/resend`), `/organizations/{organization_id}/audit`, `/invitations/{token}`, `/invitations/{token}/accept`, `/invitations/{token}/decline`, `/account/audit`
- Error code: `PHONE_SIGN_IN_DISABLED`
- CLI commands: `pharma-agent superadmin grant`, `pharma-agent superadmin revoke`, `pharma-agent superadmin list`
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `pharma_agent.application.organizations.invitations.InvitationService`, `InvitationPolicy(frontend_url=)` | test_invitation_service | named |
| constructor keywords `organizations`, `invitations`, `accounts`, `audit`, `tx`, `email`, `limiter`, `clock`, `policy` | test_invitation_service | named |
| methods `invite(actor, org_id, email, role, locale=)`, `approve(..., locale=)`, `reject`, `revoke`, `resend(..., locale=)`, `preview`, `accept`, `decline`, `list` | test_invitation_service | named |
| `view.status`, `view.email`, `view.id` (InvitationView); `preview.organization_name/.role/.email_hint` | test_invitation_service | named |
| `accept(...)` result `.role`, `.id` (`OrganizationView`) | test_invitation_service | base (`OrganizationView` exists; return type named) |
| `RateLimited` from `pharma_agent.application.errors` | test_invitation_service | named |
| `RateLimited` from `pharma_agent.application.account.errors` | test_account_settings_service | base (stays importable; named) |
| `AlreadyMember`, `ForbiddenRole`, `InvitationAlreadyOpen`, `InvitationEmailMismatch`, `InvitationExpired`, `InvitationNotFound`, `InvitationNotPending`, `OrganizationNotFound` from `...organizations.errors` | test_invitation_service, test_audit_service | base |
| `Actor`, `Role`, `AuditAction.MEMBER_JOINED`, `.INVITATION_APPROVED`, `.ORGANIZATION_RENAMED`, `.USER_ENABLED`, `new_event`, `InvitationStatus.SENT/PENDING_APPROVAL/REJECTED/REVOKED/DECLINED`, `Organization` | several | base |
| `tests.organization_fakes` (`InMemoryAuditLog`, `InMemoryInvitations`, `InMemoryOrganizations`, `InMemoryTransactions`, `actor`) | several | base |
| `tests.account_fakes` (`START`, `InMemoryAccounts`, `InMemoryLimiter`, `MutableClock`, `RecordingEmailSender`, `OTP_SECRET`, `build_account_service`) | several | support (restored) / base |
| `InMemoryLimiter.acquire/.release`, `InMemoryInvitations.get/get_by_token_hash/list_for_organization/open_for/create/update`, `InMemoryOrganizations.memberships_of/add_member/member_count/get` (called by the agent's service) | support / base | base |
| link `/invitations/<token>` in email text, token chars `[A-Za-z0-9_-]` | test_invitation_service | named (link) / base (`generate_invitation_token`) |
| 7-day expiry; 5 sends per address per hour | test_invitation_service | named |
| `pharma_agent.application.organizations.invitations.email_hint` | test_invitation_messages | named |
| `pharma_agent.application.organizations.messages.invitation_email(organization=, inviter=, role=, link=, locale=)`; `.subject`, `.text`, `.html` | test_invitation_messages | named |
| subjects `Lời mời tham gia Khoa Dược trên ViPharMind`, `Join Khoa Dược on ViPharMind`; `biên tập viên`, `editor`; escaped `href` | test_invitation_messages | named |
| `pharma_agent.application.audit.service.AuditService(audit=, accounts=, organizations=, clock=)` | test_audit_service | named |
| `for_organization(actor, org_id, limit=, cursor=)`, `mine(actor, limit=, cursor=)`, `everything(actor, limit=, cursor=)`; `.items`, `.next_cursor`; item `.details`, `.actor_name`, `.action` | test_audit_service | named |
| `InMemoryAuditLog.for_organization/for_user/all(limit=, cursor=(datetime, hex))` (called by the agent) | base fake | base (port `Cursor` exists); cursor helpers named "existing opaque cursor helpers" |
| `MembershipLookup` in `pharma_agent.domain.organizations.ports` | support `account_fakes.py` (module import) | named |
| `AccountService(..., memberships=)` | support `account_fakes.py` | named |
| `AccountPolicy(otp_secret=, sms_enabled=)` | test_account_settings_service | named (`otp_secret` base) |
| `PhoneSignInDisabled` in `...account.errors` | test_account_settings_service | named |
| `service.request_phone_login(phone, locale=, client_ip=)`, `.request_phone_change(...)`, `.get_account` | test_account_settings_service | base |
| `view.memberships[i].organization_id/.name/.role`, `view.is_superadmin`, `view.phone_sign_in_enabled` | test_account_settings_service | named |
| `fakes.sms.sent` | test_account_settings_service | support |
| operation ids `organizations:*`, `invitations:*`, `audit:organization`, `audit:mine` (20) | test_openapi | named |
| every error response of new routes is problem+json only | test_openapi | named ("as problem responses like the existing routers") |
| `build_organization_services(resolved, sessions, clock=, email=)` in `pharma_agent.infrastructure.organizations_factory` | support `postgres_app.py` (module import) | named |
| `Container(organizations=...)` | support `postgres_app.py` | named |
| HTTP paths and JSON (`name`, `role`, `member_count`, `status`, `organization_name`, `confirm_name`, `items`, `action`, codes `FORBIDDEN_ROLE`, `LAST_OWNER`) | test_organizations_api_postgres (integration) | named (paths) / base (`OrganizationService`, `OrganizationView`, error codes) |
| `superadmin grant/revoke/list`, exit code 1, case-insensitive email | test_superadmin_cli (integration) | named |

GAPs: 0. The first pass had five GAPs, all now fixed: `MembershipLookup` and the `memberships`
keyword (the restored `account_fakes.py` would break every account test without them),
`build_organization_services` (module import in the restored `postgres_app.py`), the twenty route
names checked through OpenAPI, and `RateLimited` in `pharma_agent.application.errors`.

Residual ambiguities:

1. Rate-limit counting: a resend must count against the per-address limit (invite + 4 resends
   allowed, the 6th send in the hour refused, allowed again after an hour). "5 per address" per
   hour of invitation emails covers it. An agent that also adds a per-invitation resend cooldown
   longer than 60 seconds would fail. Minor.
2. `reject` and `revoke` signatures are given without `locale`, and `decline` has no return value.
   The tests do not depend on either beyond the call shape. Minor.
3. Audit cursor shape: `AuditService` must decode the opaque cursor into the audit-log port's
   existing `Cursor` (`(datetime, hex id)`), which is what `decode_cursor` returns. The prompt says
   "the existing opaque cursor helpers" and does not name the port type. Minor.
4. `OrganizationView.role` after `accept` for an actor who is already a member: untested. Minor.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (FEATURE_REVIEW_fable.md)

---

## 3. f15: owned collections with visibility, scoped retrieval, conversation sources

- range: `11079ab21c7fa8299bd59f73b7e6a901ba98ffc4..ef23fe8cb40354573c362e570f8a399ad4328c42`
- commits (oldest first):
  - `88f0c17` feat(db): collections belong to a user, an organization or the system; conversations keep a source scope
  - `17f4f6b` feat(corpus): collections owned by users or organizations with visibility rules
  - `997dd69` feat(chat): search only the collections the user may see, narrowed per conversation
  - `dc3b602` feat(api): collection management and per-conversation source scope
  - `ef23fe8` test(retrieval): prove the search scope follows membership and visibility
- size: backend/src 37 files, +1,331/-36 (1,367 lines); backend/tests 19 files, +1,118/-10 (1,128 lines)
- hidden tests (14):
  - `backend/tests/api/test_collections_api_postgres.py` (A, integration)
  - `backend/tests/api/test_conversations_api.py` (M)
  - `backend/tests/api/test_openapi.py` (M)
  - `backend/tests/application/test_chat_service.py` (M)
  - `backend/tests/application/test_collection_service.py` (A)
  - `backend/tests/application/test_conversation_service.py` (M)
  - `backend/tests/domain/corpus/test_corpus_models.py` (M)
  - `backend/tests/domain/test_retrieval_service.py` (M)
  - `backend/tests/infrastructure/test_collection_repository.py` (A, integration)
  - `backend/tests/infrastructure/test_migrations.py` (M, integration)
  - `backend/tests/infrastructure/test_qdrant_adapter.py` (M)
  - `backend/tests/infrastructure/test_scope_resolver.py` (A, integration)
  - `backend/tests/infrastructure/test_scope_retrieval_integration.py` (A, integration)
  - `backend/tests/test_cli_corpus.py` (M)
- support files restored from `end`:
  - `backend/tests/collection_fakes.py` (new): imports `CollectionService`, `QuotaPolicy`,
    `CollectionOwner`. It implements the `CollectionRepository` methods listed in the prompt and
    builds `CollectionService` with nine keyword arguments.
  - `backend/tests/fakes.py`: imports `ReleaseScope`. `FakeRetriever.search_many(queries, top_k, scope=None)`.
  - `backend/tests/memory_repository.py`: adds `InMemoryConversationRepository.update_scope`.
  - `backend/tests/api/postgres_app.py`: imports `build_collection_service` from
    `pharma_agent.infrastructure.collections_factory` and passes `Container(collections=...)`.
  - `backend/tests/corpus_rows.py`: seeds system collections as `public`.

Draft prompt:

```text
Let users and organizations own document collections with visibility rules, and make every chat search read only the collections the user may see, optionally narrowed to the sources chosen for a conversation.
Add a frozen `CollectionOwner` to `pharma_agent.domain.corpus.models` (`user_id` and `organization_id`, both defaulting to `None`, raising `ValueError` when both are set, with `is_system` true when neither is), and make `build_snapshot` produce an ownerless `PUBLIC` collection, since imported bundles are the public system corpus.
Add a `CollectionRepository` protocol to `pharma_agent.domain.corpus.ports` with the async methods `get(collection_id)`, `visible_for(actor)`, `count_owned(owner)`, `create(collection, now, tx)`, `rename(collection_id, title, now, tx)`, `set_visibility(collection_id, visibility, now, tx)`, `mark_deleted(collection_id, now, tx)`, `current_releases(collection_ids)` (a mapping from each live collection that has a current release to that release), `live_release_ids(collection_id)` and `deleted_with_releases()`, where a deleted collection is invisible to every method except the last two, and implement it as `PostgresCollectionRepository(sessions)` in `pharma_agent.infrastructure.persistence.postgres.collection_repository`, with migrations for organization owners, the one-owner and public-system-corpus rules, soft deletion and conversation sources.
Add a class `CollectionService` in `pharma_agent.application.corpus.collections`, constructed with the keyword arguments `collections`, `organizations`, `accounts`, `corpus`, `index`, `audit`, `tx`, `clock` and `quotas` (a `QuotaPolicy` with the defaults `document_chars=200_000`, `documents_per_collection=100`, `user_text_bytes=1_000_000`, `user_collections=5`, `org_text_bytes=5_000_000` and `org_collections=20`), with the async methods `visible(actor)`, `get(actor, collection_id)`, `quota(actor, *, owner_organization_id)`, `create(actor, *, title, owner_organization_id)`, `rename(actor, collection_id, title)`, `set_visibility(actor, collection_id, visibility)`, `delete(actor, collection_id)` and `purge_deleted()`.
Single collections are returned as `CollectionView` (`id`, `key`, `title`, `visibility`, `owner_user_id`, `owner_organization_id`, `owner_name`, `is_system`, `can_edit`, `can_set_public`, `current_release_id`, `current_release_number`), `visible` returns `CollectionGroups` with `public`, `organizations` (one `OrganizationCollections` with `organization_id`, `name`, `role` and `items` per organization the actor belongs to, sorted by name), `mine` and `others` (what only a superadmin sees), and `quota` returns `QuotaUsage` (`text_used`, which is 0 until documents can be authored, `text_limit`, `collections_used`, `collections_limit`), where an organization's own quota fields override the defaults.
`create` makes a private collection owned by the actor, or by the given organization, with the key `u-<random hex>` or `o-<random hex>` and the id `collection_id_for(key)`, and raises `ForbiddenRole` when the actor's role may not create there, `OrganizationNotFound` for an organization the actor cannot see, `InvalidInput` for a blank title, and `QuotaExceeded(unit=..., used=..., limit=...)` (code `QUOTA_EXCEEDED`, a subclass of `InvalidInput` keeping those attributes) when the owner already has its limit of collections.
Access follows the existing access policy functions: a collection the actor may not see, or a deleted one, raises `CollectionNotFoundForActor` (code `COLLECTION_NOT_FOUND`), a change to a system collection by anyone but a superadmin (and any visibility change of one) raises `SystemCollectionReadOnly`, other refused changes raise `ForbiddenRole`, and only a superadmin may make a collection public; put these errors in a new module `pharma_agent.application.corpus.errors`.
Every change records one audit event (`COLLECTION_CREATED`, `COLLECTION_RENAMED`, `COLLECTION_VISIBILITY_CHANGED`, `COLLECTION_DELETED`) with the collection's owner organization as organization, its owner user as subject, the collection id and only the details `title`, plus `from` and `to` for a rename or a visibility change (visibilities as their string values).
`delete` hides the collection at once, then deletes the index points of its releases that are not retired, retires those releases and purges retired rows, and `purge_deleted()` does the same for every deleted collection that still has such releases and returns how many it cleaned; the service is built by `build_collection_service(settings, sessions, *, index, clock)` in `pharma_agent.infrastructure.collections_factory`, held in `Container.collections` and `CorpusServices.collections`, and used by a new `pharma-agent corpus purge-deleted` command that prints `purged <n> deleted collections`.
For search, add `ReleaseScope` (a mapping from collection id to release id) to `pharma_agent.domain.retrieval.models`, an optional third parameter `scope` to `Retriever.search_many(queries, top_k, scope=None)` and a keyword `scope` to `RetrievalService.search`, where `None` keeps the configured default collections, an empty scope gives an empty result with no error and no retriever call (and the Qdrant retriever answers it with one empty list per query without querying), and a given scope replaces the configured collections and is filtered with the existing `release_scope_filter`.
Add a `ScopeResolver` protocol with `async resolve(*, user_id, requested)` (`user_id` is the string id the chat service receives, passed on unchanged) to `pharma_agent.domain.retrieval.ports`, implemented as `PostgresScopeResolver(actors, collections)` in `pharma_agent.infrastructure.retrieval.scope_resolver`, which maps the collections the user may see, narrowed to `requested` when it is not `None`, to their current releases; `ChatService` takes an optional keyword argument `scopes`, resolves the scope once per turn with the conversation's stored sources, and passes it to every search of that turn.
Store the sources on `Conversation.collection_ids` (a tuple of collection UUIDs, or `None` for everything the user may see) through a new repository method `update_scope(conversation)` and expose them on `ConversationView.collection_ids` as a list or null; `ChatService.open_turn` and `ask` accept `collection_ids`, which apply only when a new conversation is created (deduplicated, order kept, as in `update`), `ConversationService.update(user_id, conversation_id, *, title=..., collection_ids=...)` changes whichever argument is passed, next to the existing `rename`, which stays (an omitted one stays as it is, `None` restores every source, and an empty list raises `InvalidInput`), and the HTTP API adds `collection_ids` to the chat request, replaces the route `rename_conversation` with `update_conversation` (a PATCH taking `title` and/or `collection_ids`), and adds `/api/v1/collections` endpoints with exactly the route names listed below.

Required interfaces:
- `pharma_agent.domain.corpus.models`: `CollectionOwner` (`user_id`, `organization_id`, `is_system`)
- `pharma_agent.domain.corpus.ports`: `CollectionRepository` (`get`, `visible_for`, `count_owned`, `create`, `rename`, `set_visibility`, `mark_deleted`, `current_releases`, `live_release_ids`, `deleted_with_releases`)
- `pharma_agent.application.corpus.collections`: `CollectionService`, `QuotaPolicy`, `CollectionView`, `CollectionGroups`, `OrganizationCollections`, `QuotaUsage`
- `CollectionService` constructor keywords: `collections`, `organizations`, `accounts`, `corpus`, `index`, `audit`, `tx`, `clock`, `quotas`; methods `visible`, `get`, `quota`, `create`, `rename`, `set_visibility`, `delete`, `purge_deleted`
- `QuotaPolicy` fields: `document_chars`, `documents_per_collection`, `user_text_bytes`, `user_collections`, `org_text_bytes`, `org_collections`
- `pharma_agent.application.corpus.errors`: `CollectionNotFoundForActor`, `SystemCollectionReadOnly`, `QuotaExceeded` (`unit`, `used`, `limit`)
- `pharma_agent.domain.retrieval.models`: `ReleaseScope`
- `pharma_agent.domain.retrieval.ports`: `ScopeResolver` (`resolve`); parameter `scope` of `Retriever.search_many`
- `pharma_agent.domain.retrieval.service`: keyword `scope` of `RetrievalService.search`
- `pharma_agent.infrastructure.persistence.postgres.collection_repository`: `PostgresCollectionRepository`
- `pharma_agent.infrastructure.retrieval.scope_resolver`: `PostgresScopeResolver`
- `pharma_agent.infrastructure.collections_factory`: `build_collection_service`
- `pharma_agent.infrastructure.container.Container`: field `collections`; `pharma_agent.infrastructure.corpus_factory.CorpusServices`: field `collections`
- `pharma_agent.domain.conversation.models`: `Conversation.collection_ids`
- `pharma_agent.domain.conversation.ports.ConversationRepository`: `update_scope`
- `pharma_agent.application.conversation.service`: `ConversationService.update`; `ConversationView.collection_ids`
- `pharma_agent.application.chat.service`: keyword `scopes` of `ChatService`; keyword `collection_ids` of `ChatService.open_turn` and `ChatService.ask`
- Route names: `update_conversation` (replacing `rename_conversation`), `collections:list`, `collections:create`, `collections:quota`, `collections:get`, `collections:update`, `collections:delete`
- Paths: `/collections`, `/collections/quota`, `/collections/{collection_id}`
- CLI command: `pharma-agent corpus purge-deleted`
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `CollectionService`, `QuotaPolicy` in `pharma_agent.application.corpus.collections` | test_collection_service, support `collection_fakes.py` | named |
| constructor keywords `collections`, `organizations`, `accounts`, `corpus`, `index`, `audit`, `tx`, `clock`, `quotas`; `QuotaPolicy(user_collections=, org_collections=)` | test_collection_service, support | named |
| `CollectionRepository` methods `get`, `visible_for`, `count_owned`, `create(c, now, tx)`, `rename(id, title, now, tx)`, `set_visibility(id, v, now, tx)`, `mark_deleted(id, now, tx)`, `current_releases`, `live_release_ids`, `deleted_with_releases` (implemented by `InMemoryCollections`, called by the agent's service) | support `collection_fakes.py`, test_collection_service | named |
| service methods `create(actor, title=, owner_organization_id=)`, `visible`, `quota(actor, owner_organization_id=)`, `get`, `rename`, `set_visibility`, `delete`, `purge_deleted` | test_collection_service, support | named |
| view fields `.key`, `.id`, `.visibility`, `.can_edit`, `.is_system`, `.current_release_number`; groups `.mine`, `.public`, `.organizations[i].name/.items`; quota `.collections_used`, `.collections_limit` | test_collection_service | named |
| key prefixes `u-` / `o-`; `id == collection_id_for(key)` | test_collection_service | named |
| `CollectionNotFoundForActor`, `QuotaExceeded` (`.used`, `.limit`), `SystemCollectionReadOnly` in `pharma_agent.application.corpus.errors` | test_collection_service | named |
| `ForbiddenRole` from `pharma_agent.application.errors` | test_collection_service | base (moved there by F14) |
| audit `COLLECTION_CREATED`, `COLLECTION_VISIBILITY_CHANGED`, `COLLECTION_DELETED`; `events[0].subject_user_id`; details `{"title", "from", "to"}`; `actor_was_superadmin` | test_collection_service | named (enum members and `new_event` base) |
| `CollectionOwner(user_id=, organization_id=)`, `ValueError`, `.is_system` | test_collection_service, support | named |
| `Collection(...).is_system`, `Visibility.PRIVATE/ORGANIZATION/PUBLIC`, `collection_id_for`, `Organization`, `Actor`, `Role`, `AuditAction` | several | base |
| `tests.corpus_memory` (`CorpusAdapters`, `build_importer`, `InMemoryCorpusRepository`, `InMemoryVectorIndex`, `.index.points`), `tests.corpus_fixtures`, `FakeEmbedder` | test_collection_service | base |
| `CorpusRepository.get_release/index_items/retire/purge_retired`, `VectorIndex.delete` (called by the agent's service) | base fakes | base |
| `build_snapshot(...).collection.visibility is Visibility.PUBLIC`, `.is_system` | test_corpus_models | named |
| `ReleaseScope` in `pharma_agent.domain.retrieval.models` | test_retrieval_service, test_chat_service, support `fakes.py` | named |
| `RetrievalService.search(..., scope=)`; empty scope → no retriever call, `items == []`, `error is None`; default passes `None` | test_retrieval_service | named |
| `FakeRetriever.search_many(queries, top_k, scope=None)` (called by the agent's `RetrievalService`) | support `fakes.py` | named |
| `QdrantHybridRetriever.search_many(..., scope=)`; given scope skips `reader.current_releases`; filter `release_scope_filter(scope)`; `{}` → `[[]]` and no query | test_qdrant_adapter | named (`release_scope_filter` base) |
| `ChatService(..., scopes=)`; `open_turn(..., collection_ids=)`; `ask(..., conversation_id=)` | test_chat_service | named |
| `resolve(user_id=, requested=)` called once with the stored sources; `retriever.scopes` all equal the scope | test_chat_service | named |
| `Conversation.collection_ids` (tuple), `model_copy(update={"collection_ids": ...})` | test_chat_service, test_conversation_service | named |
| `InMemoryConversationRepository.update_scope` (called by the agent's service) | support `memory_repository.py` | named |
| `ConversationService.update(user_id, id, collection_ids=)`, `update(..., title=, collection_ids=None)`; `[]` → `InvalidInput`; stranger → `ConversationNotFound` | test_conversation_service | named |
| `ConversationService.create`, `service_for` helper, `InvalidInput`, `ConversationNotFound` | test_conversation_service | base |
| `ConversationView.collection_ids` (list or `None`); POST `/conversations` body keys incl. `collection_ids` | test_conversation_service, test_conversations_api | named |
| operation ids `update_conversation`, `collections:list/create/quota/get/update/delete` | test_openapi | named |
| `CorpusServices(..., collections=)` | test_cli_corpus | named |
| `tests.collection_fakes.build_collection_service(repo, index, clock=)` | test_cli_corpus | support |
| `corpus purge-deleted`, output `purged 0 deleted collections` | test_cli_corpus | named |
| `build_collection_service(settings, sessions, index=, clock=)` in `pharma_agent.infrastructure.collections_factory`; `Container(collections=)` | support `postgres_app.py` (module import) | named |
| `PostgresCollectionRepository` in `...postgres.collection_repository` | test_collection_repository, test_scope_resolver, test_scope_retrieval_integration (integration, module import) | named |
| `PostgresScopeResolver` in `...retrieval.scope_resolver` | test_scope_resolver, test_scope_retrieval_integration (integration, module import) | named |
| `ActorResolver`, `PostgresAccountRepository`, `PostgresOrganizationRepository`, `PostgresTransactionFactory`, `CollectionTable`, `ReleaseTable`, `build_retrieval_service`, `open_corpus_services`, `Membership` | integration tests | base |
| migration details (constraint names, `conversations.collection_ids` column, soft-delete column) | test_migrations (integration) | named only as "migrations for ..."; integration-only, ungraded |
| `/api/v1/collections` JSON (`title`, `owner_organization_id`, `visibility`, `mine`, `collections_used`, `code`) | test_collections_api_postgres (integration) | named |

GAPs: 0. The first pass had six GAPs, all now fixed: the ten `CollectionRepository` method names
(the restored fake implements them, and the agent's service must call them by these names),
`update_scope`, `CorpusServices.collections`, the `scope` parameter as the third positional argument of
`search_many`, `PostgresCollectionRepository` / `PostgresScopeResolver` / `build_collection_service`
(module-level imports in integration tests and in `postgres_app.py`), and the operation id
`update_conversation`.

Residual ambiguities:

1. **Moderate.** Grouping in `visible`: the test expects a personal private collection in `mine`,
   an organization's collection in `organizations` under the organization's name, and the system
   corpus in `public`. The prompt names the groups but not the precedence when a collection
   matches several (for example, a public collection that the actor owns goes to `public` first in
   the original). The tested cases are not ambiguous. Untested cases could be classified
   differently.
2. **Moderate.** The scope must reach the retriever through the chat graph. The prompt says "passes
   it to every search of that turn", but the path (`ChatService` → runner → turn context →
   retrieval node → `RetrievalService.search(scope=)`) is internal and not named. An agent that sets
   the scope on only one search round fails `all(s == scope for s in retriever.scopes)`.
3. Minor. `ConversationService.update` needs a sentinel default so that "omitted" differs from
   `None`. The prompt states the semantics but not the sentinel (the original uses `KEEP`). The
   tests only call it with `collection_ids` passed, so either design passes.
4. Minor. Audit `subject_user_id` for an organization-owned collection is `None` in the original.
   Only the personal case is tested.
5. Minor. Per-user quota overrides (`AccountUser.text_quota_bytes` / `collection_quota`, added in this
   range) are not mentioned. The tests use only the `QuotaPolicy` defaults and organization fields
   that already exist, so leaving them out is harmless.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (FEATURE_REVIEW_fable.md)
