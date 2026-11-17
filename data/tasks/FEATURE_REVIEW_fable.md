# Independent review of the feature-tier prompts (f08, f14, f15)

Reviewer: Fable (independent of the drafter). Date: 2026-11-15.

Method: for each range I read the hidden tests and restored support files at `end`, the base code at
`base`, and the original source diff, without relying on the drafter's audit tables. Test line numbers
refer to the file at the range `end`. "Base" means the file at the range `base`.

## Summary

| task | verdict | blocking-risk issues | minor issues | drafter ambiguities to fix |
| --- | --- | --- | --- | --- |
| f08 | APPROVE WITH EDITS | 3 | 2 | #4 (fix); #1-#3 leave |
| f14 | APPROVE WITH EDITS | 2 | 3 | none; #1-#4 leave |
| f15 | APPROVE WITH EDITS | 3 | 3 | both moderate ones: leave |

No REJECT. I found no name of the p01 class (module path, class, field, keyword, port method, route
name, error code) that is missing at base and unnamed in a prompt. Every issue below is a behaviour
that a test pins exactly and the prompt leaves open, or states in a way that points away from what
the test accepts. All proposed edits are insertions inside existing sentences, so every prompt stays
at 12 sentences.

Facts about grading that change how the drafter's audit should be read (`code/harness/src/sdlc_harness/grade.py`):

- Hidden ids come from the reference run at `end`, and `backend/pyproject.toml` has
  `addopts = ["-m", "not integration"]`. Integration tests are therefore never in the hidden set, and
  an import error in an integration module does not affect `task_pass`. The drafter's note that
  such imports make "collection fail" is wrong for grading. `tests/api/postgres_app.py` is imported
  only by integration modules (all carry `pytestmark = pytest.mark.integration`), so
  `build_organization_services`, `Container.organizations`, `build_collection_service`,
  `Container.collections`, `PostgresCollectionRepository`, `PostgresScopeResolver`, the index names and
  the superadmin CLI are ungraded. Naming them is still correct (they are part of the feature), but
  they are not hidden-contract names.
- The one support import that does gate graded tests is `MembershipLookup` in `tests/account_fakes.py`
  (f14). It is named.
- `test_openapi.py` asserts `set(ids) == EXPECTED_OPERATION_IDS` in all three tasks. One extra route
  fails the task. This matters for f14 (see F14-1).

Format, all three: English, 12 lines that are each one sentence, a "Required interfaces" section, no
mention of tests. The 12-sentence limit is met only in the letter: sentences run to 100-130 words with
several semicolon clauses. I accept this because the tests pin that much, but nothing more should be
added as new sentences. The "names only" rule is bent slightly in two places (f08 index column lists,
f14 "re-exported from ..."); see F08-5 and F14-4.

Fairness between arms: I found nothing in any prompt that helps one arm only. No prompt refers to a
design document, a plan or a process. The size of the prompts favours neither arm in content, though
the spec arm will spend more of its time budget restating them; that is a property of the tier, not of
these drafts.

---

## f08: APPROVE WITH EDITS

Names: all verified. Base already has `Conversation.start` with the `"Cuộc trò chuyện mới"` fallback,
`_clean_title`, `MAX_TITLE_CHARS`, `cli._render(event, evidence)`, `create_app(settings)`, the path
pattern on `conversation_id` and `min_length=1` on the chat message (so the validation test needs no
new validation), `build_harness(agent=, authenticated=)`, `Container.skills/.feedback`, and all route
function names in `EXPECTED_OPERATION_IDS` except `create_conversation` (named).

### Issues

**F08-1 (blocking risk). When `detail` must be absent is not stated for three cases.**
The prompt says only that `detail` is "left out when empty". The tests require no `detail` key at all:

- validation error: `test_problem_details.py:44` (`assert "detail" not in body`);
- unhandled exception: `test_problem_details.py:164`;
- `HTTPException` whose detail is the default status phrase: `test_problem_details.py:64` (routing 404,
  Starlette detail `"Not Found"`) and `:91`/`:112` (401 with `detail=None`, which Starlette turns into
  `"Unauthorized"`; expected `detail` is `None`).

An agent that writes `detail="Request validation failed"`, `detail="Internal server error"`, or
passes Starlette's `"Not Found"` through as "custom detail text" is following the prompt and fails.
This is the drafter's ambiguity #4, and it is tested twice, so it is not minor. Fix.

Edit, sentence 3. Replace

> a request validation error has the code `VALIDATION_ERROR` and lists one `ProblemItem` (`loc`, `message`, `type`, in that order) per invalid field in `errors`; an unhandled exception gives `INTERNAL_ERROR` without revealing the exception text;

with

> a request validation error has the code `VALIDATION_ERROR`, no `detail`, and lists one `ProblemItem` (`loc`, `message`, `type`, in that order) per invalid field in `errors`; an unhandled exception gives `INTERNAL_ERROR` with no `detail`, so the exception text is never revealed;

and replace

> and keeps any custom detail text as `detail`,

with

> and keeps a detail text as `detail` only when it differs from the standard phrase of that status (a plain 404 or 401 has no `detail`),

**F08-2 (blocking risk). The type of `ChatTurnResult.created_at` is open.**
Prompt: "`created_at` (the assistant message time in ISO format, also stored as
`ChatTurnResult.created_at`)". This reads as "the ISO string is also stored". The test compares with a
`datetime`: `test_chat_service.py:117` (`session.result.created_at == assistant_msg.created_at`), while
the event carries the string (`done.data["created_at"] == assistant_msg.created_at.isoformat()`).

Edit, sentence 10. Replace

> `created_at` (the assistant message time in ISO format, also stored as `ChatTurnResult.created_at`)

with

> `created_at` (the assistant message time as an ISO 8601 string, while `ChatTurnResult.created_at` holds the same time as a `datetime`)

**F08-3 (blocking risk). When a pre-created conversation gets its title is open.**
Prompt: "make the chat service name a pre-created conversation from its first message and save that
title". `test_chat_service.py:178-196` requires the first `conversation` event of that turn to already
carry the new title with `"created": False` (exact dict equality on `events[0].data`). An agent that
sets the title when the turn is persisted (a natural place, next to `record_turn`) passes the stored
title check and fails this one.

Edit, sentence 9. Replace

> and make the chat service name a pre-created conversation from its first message and save that title.

with

> and make the chat service name a pre-created conversation from its first message and save that title when the turn opens, so that turn's `conversation` event already carries it.

**F08-4 (minor). `decode_cursor("")` versus "an empty cursor string means the first page".**
`test_pagination.py:59` requires `decode_cursor("")` to raise `InvalidCursor`, while
`test_queries.py` requires `list_conversations(..., cursor="")` to return the first page. Both are
stated, in different sentences, and an agent may put the empty-string rule inside `decode_cursor`.

Edit, sentence 5 (optional but cheap). Replace "for anything malformed, including a naive timestamp"
with "for anything malformed, including an empty string, a naive timestamp".

**F08-5 (minor, format). "Required interfaces" has more than names in its last entry.**
The `Postgres indexes` entry lists column tuples and "replacing ...". Only integration tests read
these names (`test_migrations.py`), so they are ungraded. Suggest shortening to
"Postgres indexes: `ix_conversations_user_updated_id`, `ix_messages_conversation_created_id`". Not
required for approval.

### Drafter's ambiguities

1. Empty application-error message: leave (covered by "left out when empty", untested).
2. `title_from_first_message` cleaning: leave ("the way `start` does" points at base code that both
   arms can read; `test_conversation.py` passes for any agent that reuses it).
3. Tie-breaking and `limit + 1`: leave. The prompt states the observable rule (`None` on the last
   page, strict comparison on the pair). Saying how to detect the last page would be an approach leak.
4. Status phrase as detail: fix, see F08-1.

### Leak check

Sentence 5 gives the cursor wire format (`{"t", "id"}`, unpadded base64url). `test_pagination.py`
asserts the decoded payload byte for byte, so the format has to be stated; it is a contract, not an
algorithm. Sentences 11-12 repeat the approved t03 prompt. No step-by-step solution, no test
description. Acceptable.

Not an issue but worth knowing: `test_openapi.py:65` requires the problem content to equal exactly
`{"schema": {"$ref": ...}}`, so an agent that keeps fastapi-users' `examples` in the error responses
fails. The wording ("only `application/problem+json` with the `Problem` schema") is the same as in
approved t03; leave for consistency between tiers.

---

## f14: APPROVE WITH EDITS

Names: all verified. Base has `InvitationStatus`, `OPEN_STATUSES`, `Invitation.effective_status`,
`INVITATION_TTL`, token helpers, every policy function used (`invitable_roles`,
`invite_needs_approval`, `can_decide_invitation`, `can_cancel_invitation`, `can_view_audit`), all
invitation errors, all `AuditAction` members listed, `normalize_email`, `encode_cursor`/`decode_cursor`,
the audit port `Cursor`, `OrganizationView`, and fakes for every port the service must call
(`InMemoryInvitations`, `InMemoryLimiter.acquire/release`, `InMemoryAuditLog.for_organization/for_user/all`).
`AuditAction` has no `INVITATION_ACCEPTED`, so `audit.actions()[-1] is MEMBER_JOINED`
(`test_invitation_service.py`, first test) is safe.

### Issues

**F14-1 (blocking risk). An extra route fails the task, and the prompt invites one.**
`test_openapi.py:88` asserts set equality with exactly the 20 new route names. The prompt defines
`AuditService.everything` (superadmin-only) but the expected set has no route for it. An agent that
exposes it (for example `audit:all`) is doing reasonable work and fails. The prompt says "with the
route names listed below", which does not say the list is closed.

Edit, sentence 11. Replace

> and add endpoints under `/api/v1/organizations`, `/api/v1/invitations/{token}` and `/api/v1/account/audit` with the route names listed below,

with

> and add endpoints under `/api/v1/organizations`, `/api/v1/invitations/{token}` and `/api/v1/account/audit` with exactly the route names listed below and no other new routes (`everything` gets no endpoint),

**F14-2 (blocking risk). `InvitationNotPending` for organization-side actions is not stated.**
The prompt gives `InvitationNotPending` only for `accept`. `test_invitation_service.py:129-136`
approves an invitation that was already rejected and expects `InvitationNotPending`. `InvitationNotFound`
or `ForbiddenRole` are equally defensible readings of the prompt.

Edit, sentence 3. Replace

> until an owner or editor approves it (a member who tries gets `ForbiddenRole`) or rejects it;

with

> until an owner or editor approves it (a member who tries gets `ForbiddenRole`) or rejects it, and approving, rejecting, revoking or resending an invitation that is not in a state that allows it raises `InvitationNotPending`;

**F14-3 (minor). "after the expiry" points at the wrong boundary.**
`test_invitation_service.py:191-196` advances the clock by exactly seven days and expects
`InvitationExpired` from `accept` and `InvitationNotFound` from `preview`. The expiry instant itself is
expired (base `Invitation.effective_status` uses `now >= expires_at`). An agent that reuses the base
helper passes; one that writes `now > expires_at` because the prompt says "after" fails.

Edit, sentence 7. Replace "raises `InvitationExpired` after the expiry" with "raises
`InvitationExpired` from the expiry time on".

**F14-4 (minor, over-specification and format).** The entry

> `pharma_agent.application.errors`: `RateLimited`, `DeliveryFailed`, `ForbiddenRole`, `OrganizationNotFound` (re-exported from the account and organization error modules)

prescribes three moves the description never mentions and no f14 test needs. The tests import
`RateLimited` from `pharma_agent.application.errors` (`test_invitation_service.py:6`) and from the
account errors module (`test_account_settings_service.py`), and import `ForbiddenRole` and
`OrganizationNotFound` from `pharma_agent.application.organizations.errors`, where they are at base.
It also is not "names only". Suggest: "`pharma_agent.application.errors`: `RateLimited`". Sentence 4
already says it stays importable from the account errors module.

**F14-5 (minor). Two values are implied, not stated.**

- `email_hint`: the example is the only statement of the mask. The original always appends `**`
  (`n**@example.com` for `new@...`, `test_invitation_service.py`, first test; `a**@example.com`,
  `test_invitation_messages.py:22`). One star per hidden character gives `a*` and fails. The example
  does disambiguate, so this is optional: replace "keeps only the first character of the local part"
  with "keeps only the first character of the local part and replaces the rest with `**`".
- `phone_sign_in_enabled` must equal `sms_enabled` (`test_account_settings_service.py:210`, `:224`).
  Optional: "and `phone_sign_in_enabled` (the value of `sms_enabled`)".

### Drafter's ambiguities

1. Resends count against the per-address limit: leave. "20 invitation emails per inviter and 5 per
   address" per hour is clear, and the base limiter fake uses a fixed window that the test's timings fit
   (`test_invitation_service.py:263-270`). An invented cooldown longer than 60 seconds is the agent's
   own risk.
2. `reject`/`revoke` without `locale`, `decline` returning nothing: leave.
3. Audit cursor type: leave. `decode_cursor` already returns the port's `Cursor` shape at base.
4. Role of an already-member after `accept`: leave (untested).

One thing I checked because it could have been a trap: `test_audit_service.py:72-75` builds a member
as an `Actor` whose membership exists only in `Actor.memberships`, not in the repository fake. A service
that asks the repository for the role would raise `OrganizationNotFound` instead of `ForbiddenRole`.
Base `OrganizationService` and every policy function take the role from the `Actor`, and the prompt
says to use the existing policy functions, so this follows the code base's convention. No edit.

### Leak check

The prompt is detailed (limits, token hashing, expiry, audit events) but describes observable
behaviour. "which uses the existing invitation repository, token helpers, `INVITATION_TTL`, access
policy functions and organization errors" is a pointer to base code, not an algorithm; it is available
to both arms and lowers hidden-contract risk against the fakes. Acceptable. No test description.

---

## f15: APPROVE WITH EDITS

Names: all verified. Base (the f14 end) has `Collection.owner_user_id`, `.owner_organization_id`,
`.is_system`, `Visibility`, `collection_id_for`, `ReleaseStatus.RETIRED`, the policy functions
`can_view_collection`, `can_edit_collection`, `can_set_visibility`, `can_create_collection_for`,
`release_scope_filter`, `ForbiddenRole` in `pharma_agent.application.errors`, and the base corpus fakes
have `get_release`, `index_items`, `retire`, `purge_retired` and `VectorIndex.delete`. The base
`InMemoryCorpusRepository` keeps an existing collection's owner and visibility on import, which the
delete and purge tests rely on. `TurnDeps`, `build_deps` and the `ChatTurnRunner` constructor are
unchanged in the restored `tests/fakes.py`, so the path from `ChatService` to the retriever has no
hidden name.

### Issues

**F15-1 (blocking risk). `text_used` has no source, and inventing one breaks against the fake.**
The prompt lists `QuotaUsage.text_used` and `QuotaPolicy.user_text_bytes`/`org_text_bytes` without
saying how used text is measured. In the original it is the constant 0 ("counted once documents
exist"). No port at base can report it, and the restored `InMemoryCollections` has exactly the ten
listed methods. An agent that adds a repository method to measure text calls a method the fake does
not have, and `test_collection_service.py:92` (`await w.service.quota(...)`) fails with
`AttributeError`. This is the p01 defect class in a different form: the contract is "do not add port
methods", and the prompt does not say it.

Edit, sentence 5. Replace

> and `quota` returns `QuotaUsage` (`text_used`, `text_limit`, `collections_used`, `collections_limit`),

with

> and `quota` returns `QuotaUsage` (`text_used`, which is 0 until documents can be authored, `text_limit`, `collections_used`, `collections_limit`),

**F15-2 (blocking risk). The type of `user_id` passed to `ScopeResolver.resolve` is open.**
The prompt gives `async resolve(*, user_id, requested)` with no types. `test_chat_service.py:262` and
`:284` assert `scopes.calls == [(OWNER, [chosen])]` where `OWNER` is the 32-character hex string the
chat service receives. The Postgres implementation needs a UUID to load the actor, so declaring the
port with `user_id: uuid.UUID` and converting inside `ChatService` is a natural design, and it fails
both tests.

Edit, sentence 11. Replace

> Add a `ScopeResolver` protocol with `async resolve(*, user_id, requested)` to `pharma_agent.domain.retrieval.ports`,

with

> Add a `ScopeResolver` protocol with `async resolve(*, user_id, requested)` (`user_id` is the string id the chat service receives, passed on unchanged) to `pharma_agent.domain.retrieval.ports`,

**F15-3 (blocking risk). `ConversationService.rename` must survive, and "replaces" suggests otherwise.**
The hidden `test_conversation_service.py:95`, `:101` and `:105` still call `service.rename(...)`. The
prompt introduces `ConversationService.update` and says the HTTP API "replaces the route
`rename_conversation` with `update_conversation`". An agent that makes the same replacement in the
service fails three assertions in a test that passed at base.

Edit, sentence 12. Replace

> changes whichever argument is passed (an omitted one stays as it is,

with

> changes whichever argument is passed, next to the existing `rename`, which stays (an omitted one stays as it is,

**F15-4 (minor). Deduplication must keep order.**
`test_conversation_service.py:188` asserts `narrowed.collection_ids == chosen` for two ids. An agent
that deduplicates through a `set` fails about half of the runs, which would show up as noise between
repetitions.

Edit, sentence 12. Replace "(deduplicated)" with "(deduplicated, order kept, as in `update`)".

**F15-5 (minor). Closed route list.** Same as F14-1: `test_openapi.py:94` is a set equality. The risk
is lower here because the prompt defines no service method without a route, but for consistency
replace "adds `/api/v1/collections` endpoints with the route names listed below" with "adds
`/api/v1/collections` endpoints with exactly the route names listed below".

**F15-6 (minor). Audit details are compared exactly.**
`test_collection_service.py:126` asserts `changed.details == {"title": "x", "from": "private", "to": "public"}`.
"the details `title`, plus `from` and `to`" reads as complete, but one extra key (for example `key`)
fails. Optional: replace "and the details `title`" with "and only the details `title`".

### Drafter's ambiguities

1. **Grouping precedence in `visible` (drafter: moderate). Leave.** I checked every assertion on
   groups: `test_collection_service.py:77-80` (personal private in `mine`, organization collection
   under the organization), `:140` (system collection in `public`) and the `mine == []` check after
   delete. None has a collection that fits two groups, so every reasonable precedence passes. Stating
   the precedence would lengthen the longest sentence in the set for no effect on grading. If An
   prefers a fully determined spec, the smallest wording is to add, after "(what only a superadmin
   sees)": ", each collection in the first group that fits, in the order public, mine, organizations,
   others". I do not recommend it.
2. **Scope through the chat graph (drafter: moderate). Leave.** The prompt states the requirement
   exactly as the test checks it: "resolves the scope once per turn ... and passes it to every search
   of that turn" against `scopes.calls == [...]` (one call) and `all(s == scope for s in retriever.scopes)`
   (`test_chat_service.py:262-263`). The route through runner, context and node involves no name the
   tests or restored fakes use, so there is no hidden contract. An agent that scopes only the first
   search round has an implementation bug that the test is right to catch. Naming the path would be
   an implementation-approach leak and would remove a real difficulty of the task.
3. Sentinel for `update`: leave. The tests always pass `collection_ids`, so any sentinel works.
4. `subject_user_id` of an organization-owned collection: leave (untested, and "its owner user as
   subject" already implies none).
5. Per-user quota overrides: leave. Nothing restored from `end` needs the new `AccountUser` fields.

### Leak check

Sentence 9 lists what `delete` does in order (hide, delete points, retire, purge). That is close to
an approach, but the restored fake defines `live_release_ids` and `deleted_with_releases` in terms of
non-retired releases, and `test_collection_service.py:181-183` (`purge_deleted()` returns 1, then 0) is
only satisfiable if releases are retired. Without the sentence the task would have a hidden contract.
Acceptable. Sentence 3 lists the ten port methods; needed for the same reason. No test description.

Observation for the experiment, not a prompt defect: roughly a third of this prompt (the Postgres
repository, the Postgres scope resolver, the migrations, the factory, the `/collections` HTTP behaviour
beyond route names) is exercised only by integration tests and is therefore ungraded. Both arms see
the same text, so it is fair, but pass rates for f15 will measure the in-memory half of the feature.
The same holds for the superadmin CLI and the organization endpoints in f14.

---

## Edits in priority order

Must apply before the prompts are frozen (each closes a case where a faithful reading fails a graded test):

1. F08-1 `detail` absent for validation, internal and status-phrase errors.
2. F08-2 `ChatTurnResult.created_at` is a `datetime`.
3. F08-3 the title is set when the turn opens.
4. F14-1 closed route list, no endpoint for `everything`.
5. F14-2 `InvitationNotPending` for organization-side actions.
6. F15-1 `text_used` is 0.
7. F15-2 `user_id` passed to `resolve` is the string id.
8. F15-3 `rename` stays.

Should apply (cheap, remove noise): F08-4, F14-3, F15-4, F15-5.

Optional: F08-5, F14-4, F14-5, F15-6.
