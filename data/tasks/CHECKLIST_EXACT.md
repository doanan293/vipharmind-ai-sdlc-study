# Checklist items tagged [exact]

An item is tagged when passing it requires a literal value (name, id, string, message, number, route,
enum value, code, field name, env var) that the coding agent cannot find in `brief.md` or in the product
repo at the start commit (`parent`/`base`) as the agent sees it. The harness strips contaminant paths
from the workspace (`harness/src/sdlc_harness/workspace.py`: every directory named `superpowers`,
`.claude`, `.agents`, `.codex`, `.gemini`, `.cursor`, `.windsurf`, plus `CLAUDE.md`, `GEMINI.md`,
`skills-lock.json`, `.cursorrules`, `.windsurfrules`, `.github/copilot-instructions.md` and the root
`AGENTS.md`). So the design plans under `docs/superpowers/` and `backend/docs/superpowers/` do not count.
Code, tests, README, `.env.example` and other docs do count. A literal also counts as determinable when it
is part of a third-party contract the brief names (OpenAI, DeepInfra, Google OAuth/Gmail, fastapi-users,
Langfuse, AI SDK UI message stream, SKILL.md, RFC 9457) or follows from an existing convention in the code.
Doubtful cases stay untagged.

| Task | Items | Tagged | Reason |
| --- | --- | --- | --- |
| t01 | 15 | none | audit actions, roles exist in code |
| t02 | 14 | none | error codes exist in `account/errors.py` |
| t03 | 13 | 1, 7, 12 | 1: operationId = route name convention (not FastAPI default); 7: `Body_auth_jwt_login` sanitized form-schema names; 12: CLI message `wrote <path>` |
| t04 | 5 | 5 | dispatcher value `inline` (settings allow only `inprocess`, `cloud_tasks`) |
| t05 | 8 | none | |
| t06 | 6 | none | |
| t07 | 11 | 5, 6 | 5: section headings `## Tìm kiếm` / `## Trả lời`; 6: 12-char version |
| t08 | 11 | none | `…` and `max_chars` already used in code |
| t09 | 10 | 8 | error text "no parsed output" |
| t10 | 6 | none | paths follow fastapi-users documented setup; env var exists |
| t11 | 9 | none | |
| t12 | 8 | 1 | exact set of five skill ids (three appear nowhere) |
| t13 | 8 | none | span/score names stated as "in the reference"; `user.id`/`session.id` are Langfuse attributes |
| t14 | 8 | 8 | rerank protocol value `deepinfra` (settings allow `native_rerank`, `none`) |
| t15 | 9 | 8, 9 | 8: email provider value `gmail`; 9: setting name `GMAIL_REFRESH_TOKEN` |
| m01 | 23 | none | kinds, schema version exist in `domain/corpus/bundle.py` |
| m02 | 15 | 13, 14 | health check name `postgres` (no health checks exist; only `qdrant` in CLI) |
| m03 | 18 | 3, 4, 5 | custom chunk types `data-conversation`, `data-phase`, `data-skills`, `data-evidence` (source-document shape and metadata exist in `ui_message.py`) |
| m04 | 18 | 1, 13, 14 | 1: route `/api/v1/chat/stream`; 13, 14: health body fields and `ok`/`degraded` values |
| m05 | 22 | none | statuses and not-found errors exist in `domain/corpus/models.py` |
| f08 | 24 | 1, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 22, 23, 24 | 1: `urn:pharma-agent:problem:` type and title rule; 3: `VALIDATION_ERROR` and `errors` fields; 4: `NOT_FOUND`, `METHOD_NOT_ALLOWED`; 5, 8: `UNAUTHORIZED`, `FORBIDDEN`; 6: `SERVICE_STARTING`, `SERVICE_NOT_CONFIGURED`; 7: `INTERNAL_ERROR`; 9: page fields `items`/`next_cursor`; 13: cursor JSON keys `t`/`id`; 14: `INVALID_CURSOR`; 15: cursor max 512; 22: operationIds = route names; 23: `Body_<operation>` names; 24: `wrote <path>` |
| f14 | 25 | 1, 15, 20, 23, 24, 25 | 1: link path `/invitations/<token>`; 15: email subjects and role label; 20: invitation routes (`/api/v1/invitations/{token}`, `/accept`); 23: `/api/v1/account/audit`; 24: new operation ids; 25: `superadmin` CLI command |
| f15 | 20 | 3, 5, 11, 13, 14, 15 | 3: key prefixes `u-`/`o-`; 5: group names `mine`/`public`; 11: default quota 5, `collections_used`/`collections_limit`; 13: "purged N deleted collections"; 14: `/collections/quota`, `update_conversation`; 15: field `collection_ids` |

Totals: 45 tagged items out of 306, in 15 of 23 tasks (t03 3, t04 1, t07 2, t09 1, t12 1, t14 1, t15 2,
m02 2, m03 3, m04 3, f08 14, f14 6, f15 6). Item counts per checklist are unchanged.
