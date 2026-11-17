# Medium tier m01-m05 (amended selection rule), and the rejected large ranges F07 and F04

This file is the draft for An's review of the medium tier (2-3 consecutive commits, 300-700 lines in
`backend/src`), which sits between the small single-commit tasks (43-311 lines) and the large ranges
(764-1,464 lines). It replaces the first draft of 2026-11-15, whose m01-m05 were picked by hand. The
tier is now the mechanical result of the amended rule in `docs/prereg/prereg-v1.1-draft.md`, applied to every
candidate in `data/tasks/feature-feasibility/medium_candidates.json`. For each task:

1. Read the selection data, the draft prompt and the name audit.
2. Write your verdict on the `An's verdict:` line, as `pass` or `fail` (a short reason is welcome).
3. Edit the draft prompt in place if needed. It must stay in English, 5-12 sentences of description
   plus a "Required interfaces" section that lists names only, and must not mention tests, hidden
   tests, test files or grading.

No agent was run on any candidate. Selection used only task-construction data: commits, sizes, the
original patch graded by the harness, the hidden tests, and coverage of the original code.

## The rule (summary; the binding text is `docs/prereg/prereg-v1.1-draft.md`)

A window is eligible when it is 2-3 consecutive first-parent commits of one plan (one of the 16
sub-ranges), has no `test`/`refactor`/`chore`/`docs` commit, changes only `backend/`, has 300-700
`backend/src` lines, shares no commit with t01-t15, p01, p02, f08, f14 or f15, its original patch grades
`task_pass` with no regression, at least 5 graded hidden tests fail at base, at most 50% of its
exercised src lines are exercised only by integration-marked tests, and it needs at most 20 names.

- Integration share (`medium_coverage.py`): pytest-cov with per-test contexts at `end`, once for the
  graded run (`-m "not integration"`) and once for `-m integration` (Docker). Over the statements on
  lines the window adds or changes in `backend/src` (lines that only run at import time dropped), the
  share is the part run by an integration test and by no graded test.
- Required names (`medium_names.py`): over hidden tests and restored support files, the names that do not
  exist at base: imported `pharma_agent` symbols, new routes, new CLI commands, new UPPER_SNAKE codes the
  tests use, new enum members, and new port methods that the restored fakes implement (methods the src
  defines at `end` but not at base). Fields, keywords, methods of the new classes and free-text
  strings are not counted (the prompts still name what the tests pin; the audits check that).
- Layer: the one of domain/application/infrastructure/api holding most of the window's src lines.
- Selection (`medium_select.py`): greedy, at most 5, no two selected windows share a commit; order =
  names, then src lines, then `end` hash. Pass 1 takes the first window of each layer (domain,
  application, infrastructure, api); pass 2 fills the rest from all eligible windows.

The name count is not the "required names" column of the first draft (that counted the entries of a
hand-written "Required interfaces" list); every window, old picks included, is counted the same way.

## Summary

| task | window | range | commits | layer | src lines | required names | graded hidden tests (fail at base) | integration-only share | pass | sentences | GAPs | verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| m01 | F05_69-70 | `af9d4173a9..507a4ae31e` | 2 | domain | 478 | 7 | 23 (23) | 0% | 1 | 12 | 0 | viable |
| m02 | F03_44-45 | `a133d4cd1c..68edeac53e` | 2 | application | 335 | 5 | 6 (6) | 32% | 1 | 9 | 0 | viable |
| m03 | F09_107-109 | `a24bd49080..95d69130cd` | 3 | infrastructure | 413 | 3 | 17 (14) | 44% | 1 | 7 | 0 | viable |
| m04 | F03_47-48 | `44466f373d..4ba674d359` | 2 | api | 362 | 11 | 9 (7) | 4% | 1 | 8 | 0 | viable, harness note |
| m05 | F06_80-81 | `067e562740..adf89a7b62` | 2 | application | 515 | 5 | 13 (13) | 0% | 2 | 11 | 0 | viable |

No two medium tasks share a commit, and none shares a commit with a small, pilot or large task (the
hidden test files that share a path with another tier are listed in the prereg draft).

### Change from the first draft's m01-m05

| first draft | window | now | why |
| --- | --- | --- | --- |
| m01 | F03_43-44 | not selected (eligible, 7 names) | shares `2541825` with the new m02 (F03_44-45, 5 names), which ranks first in the application layer |
| m02 | F03_47-48 | **m04** | the only eligible api window; draft and audit unchanged |
| m03 | F05_71-73 | not selected (eligible, 13 names) | domain pass 1 takes F05_69-70 (7 names); pass 2 takes F06_80-81 (5 names) |
| m04 | F02_29-30 | not selected (eligible, 13 names) | infrastructure pass 1 takes F09_107-109 (3 names) |
| m05 | F12_370-371 | **ineligible** | 57% of its exercised src lines are integration-only (> 50%) |

So the tier differs from the first draft in four of five tasks; only F03_47-48 stays (renumbered m04).

### All candidates

Each window's criteria, metrics and outcome are in `medium_candidates.json` (fields `eligible`,
`reason`, `selected`, `selection_pass`, `selected_as`; the first draft's verdicts are kept under
`previous_selection`). A window is counted under the first criterion it fails.

| outcome | count | windows |
| --- | --- | --- |
| selected | 5 | F05_69-70 (m01), F03_44-45 (m02), F09_107-109 (m03), F03_47-48 (m04), F06_80-81 (m05) |
| eligible, shares a commit with a selected window | 7 | F03_42-44, F03_43-44, F03_43-45 (m02); F05_69-71 (m01); F06_79-80 (m05); F09_106-107, F09_106-108 (m03) |
| eligible, ranked after the selected windows | 9 | F02_29-30 (13 names), F04_54-55 (13), F04_54-56 (18), F04_55-56 (15), F05_71-73 (13), F05_72-74 (13), F12_368-369 (14), F12_371-372 (20), F13_391-392 (12) |
| outside the 16 sub-ranges | 1 | product-launch_410-411 |
| contains a `test` commit | 5 | F06_75-76, F06_76-77, F07_82-83, F07_82-84, F09_110-112 |
| shares a commit with t01-t15, p01, p02, f08, f14 or f15 | 42 | every F01 window except F01_24-25; F02_27-29, F02_28-29, F02_28-30, F02_29-31, F02_30-31, F02_30-32, F02_31-32; F03_37-39, F03_38-40, F03_39-41, F03_44-46, F03_45-46, F03_45-47, F03_46-47, F03_46-48; F04_55-57, F04_56-58, F04_57-59; F05_67-69; all F08 windows; F12_371-373, F12_372-373; all F14 windows; F15_402-403; F16_405-406 |
| changes files outside `backend/` | 2 | F12_367-368, F12_367-369 (root `uv.lock`) |
| src lines outside 300-700 | 11 | F01_24-25, F02_26-27, F03_41-42, F04_53-55, F05_72-73, F06_79-81, F09_108-109, F09_109-111, F12_374-375, F13_391-393, F13_393-394 |
| fewer than 5 graded hidden tests fail at base | 4 | F03_40-41 (2), F03_42-43 (4), F12_369-370 (1), F13_392-393 (4) |
| integration-only share above 50% | 5 | F04_53-54 (54%), F09_108-110 (74%), F09_109-110 (74%), F09_110-111 (52%), F12_370-371 (57%) |
| more than 20 required names | 2 | F05_68-69 (23), F05_68-70 (28) |

Every graded window's original patch grades clean (F03_47-48 with the `superpowers` paths left out of
the diff; see m04), so no window fails criterion 6.

---

## Large ranges F07 and F04 (rejected)

Both were graded and checked against the unchanged large-tier rule (one contiguous range, at least
750 `backend/src` lines, at most 35 names). No agent was run. Both are rejected on names, so the large
tier stays f08, f14, f15.

| range | commits | src lines | graded hidden tests (fail at base) | original patch | names | reason |
| --- | --- | --- | --- | --- | --- | --- |
| F07 `adf89a7b62..c36b6e91e9` | 7 (3 `test`/`refactor`) | 1,364 | 92 (69) | clean | ~70 | the refactor `6f5111a` (777 src lines) changes the field sets of `Hit`, `Chunk`, `Citation` and the audit records that the restored factories build; plus the `CorpusReader` port, corpus factory and composition, Qdrant release filter keys, `CORPUS_NOT_READY`, settings and 5 corpus CLI commands |
| F04 `432d790170..5445f66dbb` | 7 (contains t13) | 1,187 | 23 (19) | clean without the `superpowers` paths | ~60 | 15 new symbols in 7 modules, 14 service/tracing methods, 13 port methods fixed by the restored fakes, 5 routes, 3 error codes, `cleanup-checkpoints` |

(Hand counts of the names a prompt would have to give, as in `FEATURE_REVIEW.md`; details in
`large_rechecks` of `medium_candidates.json`.)

An's verdict on rejecting F07: approved in bulk 2026-11-15 (reject)

An's verdict on rejecting F04: approved in bulk 2026-11-15 (reject)

---

## 1. m01: knowledge bundle read/write with full validation, corpus identities (domain)

- range: `af9d4173a9f4578ff2040a8cb73e6ce95372cf26..507a4ae31ea47eef1a195ac074aca1f5515a9ba0`
- commits (oldest first):
  - `28f791b` feat(corpus): read and write knowledge bundles with full validation
  - `507a4ae` feat(corpus): add deterministic section revision and chunk version ids
- plan: 2026-09-13-corpus-domain (F05, first-parent 69-70); no overlap with any task
- selection: pass 1, layer domain (478 of 478 src lines); 7 required names, fewest among eligible
  domain windows
- size: backend/src 2 files, +477/-1 (478 lines); backend/tests 2 files, +611/-0
- hidden tests (2 files, 23 graded tests, all fail at base):
  - `backend/tests/domain/corpus/test_bundle_io.py` (A)
  - `backend/tests/domain/corpus/test_identity.py` (A)
- support files: none
- grading: the original patch grades clean; integration-only share 0% (no integration test).
- note: the module docstring at base already announces `read_bundle`/`write_bundle`; the format
  spec it cites (`backend/docs/superpowers/specs/...`) is stripped from the workspace, so the
  prompt spells out every rule the tests pin.

Final prompt (the draft with every edit of `EXTRA_REVIEW_fable.md` applied; identical to `data/tasks/<id>/prompt.md`):

```text
Add reading and writing of `knowledge-bundle/v1` directories to `pharma_agent.domain.corpus.bundle`, with every problem of an invalid bundle reported at once, and deterministic ids for section revisions and chunk versions in a new module `pharma_agent.domain.corpus.identity`.
A bundle directory holds `manifest.json`, `documents.jsonl` and `sections.jsonl` (one record per line, UTF-8 without escaping), `glossary.json` and `colloquial_mappings.json` (JSON lists), and for each embedding model `embeddings/<model_slug(model)>.jsonl` with lines `{"embedding_text_sha256", "dims", "vector"}` whose vector is `encode_vector(...)`; `write_bundle(bundle, directory)` writes these files deterministically (embedding models and hashes in sorted order, the `embeddings` folder only when there are embeddings) and returns, and writes as `manifest.json`, a `BundleManifest` that keeps the input manifest's `schema_version`, `collection`, `generator` and `source_digests` but recomputes `document_count`, `section_count`, `files` (the four record files in the order above, then the embedding files, each name to a `BundleFile` with the hex SHA-256 and the byte size of its content) and `embeddings` (one `BundleEmbeddingFile` per model with its single vector length).
Before writing anything, `write_bundle` runs the content checks below (with a document's or section's 1-based position as its line) and checks each embedding model, prefix `embeddings['<model>']: `, for the first that applies of `model name must contain letters or digits` (empty slug), `model slug collides with another model` and `vectors must share one non-zero length, got <sorted distinct lengths, e.g. [3, 4]>`, and otherwise reports `'<hash>' is not a sha256 hex digest` for each key that is not 64 lowercase hex characters, and raises `BundleValidationError` with all problems if there are any.
`read_bundle(directory)` returns the `KnowledgeBundle` or raises `BundleValidationError` whose `problems` are strings in the order given here, where values in quotes are Python reprs, a validation problem is `<where>: <location>: <pydantic message>` with the location built from field names joined by `.` and list indexes written `[i]`, and a missing or invalid manifest stops reading with only `manifest.json: file is missing` or the manifest's validation problems.
It then checks each manifest embedding entry `i`, prefix `manifest.json: embeddings[i]`, for `.model: must contain letters or digits` (which skips the rest of that entry), `.model: duplicate model '<model>'`, `.dims: must be >= 1, got <dims>`, and either `.file: expected '<embeddings/slug.jsonl>', got '<file>'` or `.file: '<file>' is not listed in files`, then reports `manifest.json: files.<name>: missing entry` for each of the four record files absent from `files`.
Next, for each `files` entry in manifest order, a name that is neither a record file nor the expected file of an embedding entry gives `manifest.json: files.<name>: not part of knowledge-bundle/v1`, and otherwise the file gives `<name>: file is missing`, or `<name>: size <actual> bytes does not match manifest (<listed>)`, `<name>: sha256 does not match manifest` and `<name>: file is not valid UTF-8` as they apply.
The JSONL files are validated line by line as `DocumentRecord` and `SectionRecord` (where `<file>:<line>`, 1-based, blank lines skipped), the two JSON files each as one list of `GlossaryEntry` or `ColloquialMappingRecord` (where `<file>`; a list with any validation problem counts as empty in the later checks, while an invalid JSONL line drops only that record), and then `manifest.json: document_count: <n> does not match documents.jsonl (<k> records)` and the same for `section_count` and `sections.jsonl` are reported, counting non-blank lines.
The content checks, shared with `write_bundle`, treat a string that is blank after stripping whitespace as empty and report per document `documents.jsonl:<line>: key: must not be empty` or `key: duplicate document key '<key>' (first on line <l>)`, and per section `sections.jsonl:<line>: ` followed by, in this order, `key: must not be empty` or `key: duplicate section key '<key>' (first on line <l>)`, `document_key: unknown document '<key>'`, `ordinal: duplicate ordinal <n> in document '<key>' (first on line <l>)`, the page problems, `blocks: must contain at least one block`, and for each block `blocks[<i>].markdown: must not be empty` followed by its page problems.
Page problems are `<prefix>start_page: must be >= 1, got <page>`, the same for `end_page`, and `<prefix>start_page: <start> is after end_page <end>`, with an empty prefix for the section and `blocks[<i>].` for a block; glossary entry `i` gives `glossary.json: [i].term: must not be empty` or `glossary.json: [i].term: duplicate term '<stripped term>' (case-insensitive, first at [j])`, and mapping `i` gives for its section key `j` either `colloquial_mappings.json: [i].section_keys[j]: unknown section '<key>'` or `... section '<key>' is already mapped by [<earlier mapping index>]`.
Last, for each manifest embedding entry with `dims` of at least 1 whose `file` was read, that file is read line by line as a strict object whose `embedding_text_sha256` must match `^[0-9a-f]{64}$` (validation problems as above), reporting `<file>:<line>: dims: <d> does not match manifest dims <dims>`, else `<file>:<line>: embedding_text_sha256: duplicate of line <l>` (the first line with that hash whose dims matched, whether or not its vector decoded), else `<file>:<line>: vector: <message>` when the existing `decode_vector` raises, and the bundle's `embeddings` map each model to its hashes and decoded vectors.
In `pharma_agent.domain.corpus.identity`, `CORPUS_NAMESPACE` is `uuid.uuid5(uuid.NAMESPACE_URL, "pharma-agent:corpus:v1")`, `canonical_json(value)` is compact JSON (`","` and `":"` separators, sorted keys, no ASCII escaping, no NaN) of the value with every string normalized by the existing `normalize_text`, and `sha256_hex(text)` is the hex SHA-256 of the UTF-8 text.
`section_revision_id(section_key, blocks)` is `uuid5(CORPUS_NAMESPACE, "section-revision\x1f<section_key>\x1f<sha256_hex(canonical_json of the blocks' model_dump(mode="json") list)>")` and `chunk_version_id(section_key, chunk_text, embedding_text, chunker_version)` is `uuid5(CORPUS_NAMESPACE, "chunk\x1f" + sha256_hex(the four values joined by "\x1f", the two texts normalized by normalize_text))`.

Required interfaces:
- `pharma_agent.domain.corpus.bundle`: `read_bundle`, `write_bundle`
- `pharma_agent.domain.corpus.identity`: `CORPUS_NAMESPACE`, `canonical_json`, `sha256_hex`, `section_revision_id`, `chunk_version_id`
- Bundle files: `manifest.json`, `documents.jsonl`, `sections.jsonl`, `glossary.json`, `colloquial_mappings.json`, `embeddings/<model slug>.jsonl`
```

Name audit:

| name used by hidden tests | where | status |
| --- | --- | --- |
| `BUNDLE_SCHEMA_VERSION`, `BlockKind`, `BlockRecord`, `BundleCollection`, `BundleEmbeddingFile`, `BundleFile`, `BundleGenerator`, `BundleManifest`, `BundleValidationError` (`.problems`), `ColloquialMappingRecord`, `DocumentKind`, `DocumentRecord`, `GlossaryEntry`, `KnowledgeBundle`, `SectionRecord`, `SourceInfo`, `encode_vector` | test_bundle_io, test_identity | base |
| `model_slug`, `decode_vector` (its `vector has 12 bytes, expected 16 (dims * 4)` message), `normalize_text` | (used by the implementation) | base |
| `pharma_agent.domain.corpus.bundle.read_bundle`, `write_bundle` | test_bundle_io | named |
| file names `manifest.json`, `documents.jsonl`, `sections.jsonl`, `glossary.json`, `colloquial_mappings.json`, `embeddings/fake_embedding_4d.jsonl` | test_bundle_io | named (layout, `model_slug`) |
| recomputed `document_count`, `section_count`, `files` (sha256 + bytes of the written file), `embeddings`; placeholder manifest values replaced | test_bundle_io | named |
| no `embeddings` folder and no embedding entry without embeddings; deterministic output | test_bundle_io | named |
| `write_bundle` problems: duplicate document key with line, `vectors must share one non-zero length, got [3, 4]`; nothing written | test_bundle_io | named |
| `manifest.json: file is missing`; manifest validation `schema_version: Input should be 'knowledge-bundle/v1'` | test_bundle_io | named (pydantic message + location rule) |
| size/sha256 mismatch, `glossary.json: file is missing`, `files.notes.txt: not part of knowledge-bundle/v1`, `document_count: 5 does not match documents.jsonl (2 records)`, in that order | test_bundle_io | named |
| `documents.jsonl:2: kind: Input should be ...`, `sections.jsonl:3: document_key: unknown document '...'` | test_bundle_io | named |
| section problems (duplicate key, duplicate ordinal, `start_page ... is after end_page ...`, `blocks[0].markdown: must not be empty`, `blocks[0].start_page: must be >= 1, got 0`, `blocks: must contain at least one block`) and `colloquial_mappings.json: [0].section_keys[0]: unknown section '...'`, in that order | test_bundle_io | named |
| `glossary.json: [3].term: Field required`; duplicate term (case-insensitive, first at [0]); empty term | test_bundle_io | named |
| `colloquial_mappings.json: [1].section_keys[0]: section '...' is already mapped by [0]` | test_bundle_io | named |
| embedding line problems: dims mismatch, `vector: <decode_vector message>`, `embedding_text_sha256: duplicate of line 2`, `String should match pattern '^[0-9a-f]{64}$'` | test_bundle_io | named |
| `manifest.json: embeddings[0].dims: must be >= 1, got 0`, `embeddings[0].file: expected '...', got '...'` | test_bundle_io | named |
| `pharma_agent.domain.corpus.identity.CORPUS_NAMESPACE`, `canonical_json`, `sha256_hex`, `section_revision_id`, `chunk_version_id` and their formulas | test_identity | named |

GAPs: 0.

Residual ambiguities:

1. Moderate: 23 graded tests compare whole problem lists, so every template and the report order
   must be exact. The prompt lists all of them in order, but it is the densest prompt of the tier
   (12 long sentences) and a misreading of one rule fails a test. Both arms get the same text.
2. Problems the tests never trigger (for example `file is not valid UTF-8`,
   `model slug collides with another model`, an empty key) are given for completeness; their exact
   wording is unchecked. Minor.
3. The byte layout of the written files (indentation of the JSON lists, key order of an embedding
   line) is free as long as it is deterministic and one record sits on one line. Minor.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (EXTRA_REVIEW_fable.md)

---

## 2. m02: conversation queries, rolling summary, Postgres checkpointer, service container (application)

- range: `a133d4cd1cbaf8926aeb90d7e2d0eed5f7c6668e..68edeac53e8e8fe94c8d8952130448397ad9c40b`
- commits (oldest first):
  - `2541825` feat(application): add rolling conversation summary and conversation queries
  - `68edeac` feat(infra): add Postgres checkpointer and service container
- plan: 2026-09-12-pharma-agent-platform (F03, first-parent 44-45); no overlap with any task. Its base
  is the first commit of the old draft's m01 (`a133d4c`, ChatService), which is not a task.
- selection: pass 1, layer application (173 of 335 src lines; infrastructure 162); 5 required
  names, fewest among eligible application windows (tie with F06_80-81 broken by src lines)
- size: backend/src 10 files, +331/-4 (335 lines); backend/tests 5 files, +266/-2
- hidden tests (5 files, 6 graded tests, all fail at base):
  - `backend/tests/application/test_queries.py` (A)
  - `backend/tests/application/test_summarize.py` (A)
  - `backend/tests/infrastructure/test_checkpointer.py` (A, integration)
  - `backend/tests/infrastructure/test_container.py` (A, integration)
  - `backend/tests/infrastructure/test_migrations.py` (M, integration)
- support files: none (`tests/memory_repository.py` exists at base)
- grading: the original patch grades clean; integration-only share 32% (the container,
  checkpointer, `include_name` and migrations-env lines).
- The queries and summary sentences are the approved wording of the old draft's m01 (F03_43-44),
  unchanged; the hidden `test_queries.py` and `test_summarize.py` are byte-identical to that draft's.

Final prompt (the draft with every edit of `EXTRA_REVIEW_fable.md` applied; identical to `data/tasks/<id>/prompt.md`):

```text
Add the use cases that read, rename and delete a user's conversations, a background job that folds finished turns into a rolling conversation summary, a LangGraph checkpointer stored in Postgres, and a service container that owns the long-lived resources of the HTTP service and wires these use cases with the existing chat service.
`ConversationQueries(conversations, clock)` in `pharma_agent.application.conversation.queries` has `list_conversations(user_id, *, limit, before=None)`, `get_conversation(user_id, conversation_id)`, `list_messages(user_id, conversation_id, *, limit, before=None)`, `rename(user_id, conversation_id, title)` and `delete(user_id, conversation_id)`, which return `ConversationView` (`id`, `title`, `turn_count`, `created_at`, `updated_at`) and `MessageView` (`id`, `role`, `content`, `status`, `citations`, `phases`, `created_at`) models in the order the repository gives.
All of these except `list_conversations` raise the existing `ConversationNotFound` for a conversation the user does not own, and `rename` renames through the domain model at the clock's time and turns an invalid title into the existing `InvalidInput`.
`SummarizeConversation(llm, conversations, clock, *, every, max_chars)` in `pharma_agent.application.memory.summarize` has `run_if_needed(*, user_id, conversation_id) -> bool`, which returns False without calling the LLM when the conversation does not exist or its `needs_summary(every)` is false.
Otherwise it reads the turns since the last summary: if none of them is usable (every status is in `EXCLUDED_STATUSES`) it only advances the summarized turn count past the turns read and returns False, and if some are it asks the `SUMMARIZER` LLM role for a `ConversationSummary` from `summary_messages(previous summary, usable turns, max_chars=max_chars)`, stores that summary cut to `max_chars` characters and advances the summarized turn count past every turn read, usable or not, and returns True, while an `LlmError` keeps the previous summary and count and returns False.
In `pharma_agent.infrastructure.langgraph.checkpointer`, `open_postgres_checkpointer(conninfo, *, max_size=10)` is an async context manager that opens a psycopg connection pool for the libpq connection string (autocommit, `prepare_threshold` 0, dict rows, at most `max_size` connections), yields a LangGraph `AsyncPostgresSaver` that uses the existing `checkpoint_serializer()` and has created its tables, and closes the pool on exit, and `build_application(settings, *, checkpointer=None)` passes the checkpointer on to `build_chat_graph`.
Alembic does not manage the checkpointer's tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`, `checkpoint_migrations`), so add `include_name(name, type_, parent_names)` to `pharma_agent.infrastructure.persistence.postgres.tables`, returning False exactly for a table with one of those names, and pass it as `include_name` to both `context.configure` calls of the migrations environment.
In `pharma_agent.infrastructure.container`, add a dataclass `Container` with `settings`, `sessions`, `queries`, `chat` (default None), `summarizer` (default None) and `health_checks` (a dict from check name to an async function returning bool), and `open_container(settings)`, an async context manager that opens the existing `Database` from the `postgres` settings, builds a `PostgresConversationRepository` with an `AuditContext` from the retrieval settings, and yields a container whose `queries` are `ConversationQueries` over that repository and the system clock and whose `health_checks` has `"postgres"` (the database ping).
When `settings.llm.configured`, the container also enters `open_postgres_checkpointer(settings.postgres.conninfo)`, builds the application with that checkpointer, and sets `chat` to a `ChatService` with a `MemoryPolicy` from the `memory` settings, `summarizer` to a `SummarizeConversation` over the application's LLM with `every` and `max_chars` from `memory.summary_every_turns` and `memory.summary_max_chars`, and `health_checks["qdrant"]` to a check that is False when the retriever's `verify_collection` with the embedding dimension raises `RetrievalError`, and on exit it closes everything it opened and disposes the database.

Required interfaces:
- `pharma_agent.application.conversation.queries`: `ConversationQueries` (`list_conversations`, `get_conversation`, `list_messages`, `rename`, `delete`), `ConversationView`, `MessageView`
- `pharma_agent.application.memory.summarize`: `SummarizeConversation` (keywords `every`, `max_chars`; `run_if_needed`)
- `pharma_agent.infrastructure.langgraph.checkpointer`: `open_postgres_checkpointer` (keyword `max_size`)
- `pharma_agent.infrastructure.persistence.postgres.tables`: `include_name`
- `pharma_agent.infrastructure.container`: `Container` (`settings`, `sessions`, `queries`, `chat`, `summarizer`, `health_checks`), `open_container`
- Health check names: `postgres`, `qdrant`
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `ConversationNotFound`, `InvalidInput` (`pharma_agent.application.errors`) | test_queries | base |
| `Conversation.start`, `.record_turn`, `build_turn_messages(...)`, `Message.model_copy(status=)`, `FixedClock`, `make_run`, `NOW`, `FakeLlm`, `InMemoryConversationRepository` | test_queries, test_summarize | base |
| `ConversationSummary`, `LlmError`, `LlmRole.SUMMARIZER`, `needs_summary`, `apply_summary`, `summary_messages`, `EXCLUDED_STATUSES` | test_summarize | base |
| `pharma_agent.application.conversation.queries.ConversationQueries(repo, clock)`; `list_conversations(user, limit=)`, `get_conversation`, `list_messages(user, id, limit=)`, `rename`, `delete` | test_queries | named |
| view fields `title`, `turn_count`, `role`, `content`, `phases`, `updated_at`; title cleaning and blank title -> `InvalidInput`; foreign id -> `ConversationNotFound` | test_queries | named |
| `pharma_agent.application.memory.summarize.SummarizeConversation(llm, repo, clock, every=, max_chars=)`, `run_if_needed(user_id=, conversation_id=)` | test_summarize | named |
| no LLM call when not due; excluded statuses only advance `summarized_turns`; summary cut to `max_chars`; `LlmError` keeps the count | test_summarize | named |
| `pharma_agent.infrastructure.langgraph.checkpointer.open_postgres_checkpointer(conninfo, max_size=2)`; `build_chat_graph(checkpointer=saver)`; state readable with `aget_state`; no warning raised | test_checkpointer | integration (named; `build_chat_graph(checkpointer=)` and `checkpoint_serializer` at base) |
| `pharma_agent.infrastructure.container.open_container(Settings(...))`; `container.chat`, `.summarizer` None without an LLM key; `health_checks["postgres"]()`; `queries.list_conversations`; check names `{"postgres", "qdrant"}` with an LLM key | test_container | integration (named; settings fields at base) |
| `pharma_agent.infrastructure.persistence.postgres.tables.include_name`; no autogenerate diff with the checkpointer tables present | test_migrations | integration (named) |

GAPs: 0.

Residual ambiguities:

1. The order of `list_conversations` comes from the fake repository; the prompt says "in the order
   the repository gives" (as in the old m01). Minor.
2. Moderate (grading coverage, not wording): the checkpointer and the container are checked only by
   integration tests, so an agent can leave them unfinished without losing `task_pass`. They are
   32% of the exercised src lines, under the 50% limit.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (EXTRA_REVIEW_fable.md)

---

## 3. m03: AI SDK UI message stream for chat, message citations table (infrastructure)

- range: `a24bd490804c90b6c5d007d534606ef9527ec973..95d69130cd22b4a08738a5ab49e19c61dfe2ae49`
- commits (oldest first):
  - `3c9cdb1` feat(api): encode chat progress as AI SDK UI message stream chunks
  - `fb7e693` feat(api): stream chat turns as AI SDK UI message stream v1
  - `95d6913` feat(persistence): store citations in message_citations referencing corpus chunk versions
- plan: 2026-09-13-web-chat-stream (F09, first-parent 107-109); no overlap with any task
- selection: pass 1, layer infrastructure (247 of 413 src lines; api 166); 3 required names,
  fewest among eligible infrastructure windows
- size: backend/src 7 files, +381/-32 (413 lines); backend/tests 10 files, +863/-43
- hidden tests (5 files, 17 graded tests, 14 fail at base):
  - `backend/tests/api/test_chat_api.py` (M)
  - `backend/tests/api/test_e2e_postgres.py` (M, integration)
  - `backend/tests/api/test_ui_stream.py` (A)
  - `backend/tests/infrastructure/test_conversation_repository.py` (M, integration)
  - `backend/tests/infrastructure/test_migrations.py` (M, integration)
- support files restored from `end`: `backend/tests/api/harness.py` (M: `parse_sse` returns data
  payloads, new `ui_chunks`), `backend/tests/contract/__init__.py`, `backend/tests/contract/invariants.py`,
  `backend/tests/contract/ui_chunks.py` (A: chunk schemas and stream invariants),
  `backend/tests/corpus_rows.py` (M, used by the integration repository test)
- grading: the original patch grades clean; integration-only share 44% (the `message_citations`
  persistence).
- note: the old draft rejected this window on a coupling estimate of 32 that counted the methods
  of restored fakes. Those fakes implement ports that already exist at base, so under the
  amended rule's name count they add no name.

Final prompt (the draft with every edit of `EXTRA_REVIEW_fable.md` applied; identical to `data/tasks/<id>/prompt.md`):

```text
Make `POST /api/v1/chat/stream` speak the AI SDK UI Message Stream v1 instead of named server-sent events, and store the citations of assistant messages in a new `message_citations` table that references corpus chunk versions and releases instead of a JSON column on `messages`.
In a new module `pharma_agent.api.ui_stream`, `UIMessageStreamEncoder()` is created once per turn and its `encode(event)` maps one `ProgressEvent` to a list of chunk dicts with the existing models and helpers of `pharma_agent.application.conversation.ui_message`: `conversation` gives `{"type": "start", "messageId": <message_id>}` and `{"type": "data-conversation", "transient": true, "data": {"id": <conversation_id>, "title": <title>}}`, `phase` gives `{"type": "data-phase", "id": "phase", "data": {"phase": <phase>}}` with `"round"` added when the event has one, `skills_selected` gives `{"type": "data-skills", "data": {"skills": [{"name", "title"} of each skill]}}`, and `evidence` gives `{"type": "data-evidence", "id": "evidence", "data": {"items": <each item as an EvidenceItem JSON dump>}}`.
A non-empty `token` gives `{"type": "text-delta", "id": "text", "delta": <text>}`, preceded by `{"type": "text-start", "id": "text"}` when no text part is open, an empty token gives nothing, and an open text part is closed with `{"type": "text-end", "id": "text"}` before the chunks of `citations` (the `source_document_parts_from_event` parts as JSON dumps) and before the chunk of `done`.
`done` gives `{"type": "finish", "finishReason": ..., "messageMetadata": ...}` with the reason `error` for the statuses `error` and `timeout` and `stop` for every other status, and as metadata the JSON dump, without `feedback`, of a `MessageMetadata` built from the done data's `status`, `created_at`, `error_code`, `usage`, `run_id` and `persisted`.
`ui_message_stream(events)` is an async generator that sends every chunk of one encoder as an sse-starlette `JSONServerSentEvent` (a single `data:` line of compact JSON, non-ASCII characters unescaped, no event name) and then `ServerSentEvent(data="[DONE]")`, and the stream route returns it in its `EventSourceResponse` with the headers `x-vercel-ai-ui-message-stream: v1`, `Cache-Control: no-cache` and `X-Accel-Buffering: no`, keeping the ping, the background summary and the problem responses for errors raised before streaming starts, while the old `pharma_agent.api.sse` module goes away.
Add `MessageCitationTable` (table `message_citations`) to `pharma_agent.infrastructure.persistence.postgres.tables`, with the primary key `message_id` (foreign key to `messages.id`, on delete cascade) and `index`, `chunk_version_id` and `release_id` (foreign keys to `corpus.chunk_versions.id` and `corpus.releases.id`, on delete restrict, indexed as `ix_message_citations_chunk_version_id` and `ix_message_citations_release_id`), `strategy` (16 characters, check constraint named `strategy` allowing `search_only`, `chunk_window` and `full_section`) and `block_chunk_version_ids` (a Postgres array of UUIDs), remove the `citations` column of `MessageTable`, and add the Alembic migration `0008` (down revision `0007`) that brings the database to these models.
`PostgresConversationRepository.append_turn` stores one `message_citations` row per citation of the assistant message in the same transaction as the turn, and `messages` and `get_message` rebuild each message's citations ordered by `index` in one query joining the chunk version, section revision, section and document, with `source` from the document's `source_title`, `title` from the document title, `section` from the section heading, the pages from the chunk version and `snippet` equal to `make_snippet(chunk_text, SNIPPET_CHARS)`, while `recent_turns` returns messages without citations.

Required interfaces:
- `pharma_agent.api.ui_stream`: `UIMessageStreamEncoder` (`encode`), `ui_message_stream`
- `pharma_agent.infrastructure.persistence.postgres.tables`: `MessageCitationTable` (table `message_citations`)
- Alembic revision `0008`
- Chunk types: `start`, `data-conversation`, `data-phase`, `data-skills`, `data-evidence`, `text-start`, `text-delta`, `text-end`, `source-document`, `finish`; SSE end marker `[DONE]`
- Response header `x-vercel-ai-ui-message-stream: v1`
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `ProgressEvent` (`phase`, `token`), `EventType`, `Phase`, `build_citation`, `SNIPPET`, `SOURCE_TITLE`, `OWNER`, `build_harness`, `FakeLlm` | test_ui_stream, test_chat_api | base |
| `source_document_part(citation, is_current=)`, `MessageMetadata`, `MessageStatus`, `EvidenceItem` (camelCase dumps), `source_document_parts_from_event`, `evidence_items_from_event` | test_ui_stream (and the implementation) | base |
| `assert_stream_invariants`, `validate_chunk`, chunk schemas | contract/invariants.py, contract/ui_chunks.py | support |
| `ui_chunks`, `parse_sse` (data payloads, `[DONE]` last) | harness.py | support |
| `pharma_agent.api.ui_stream.UIMessageStreamEncoder().encode(event)` | test_ui_stream | named |
| every chunk dict of the completed-turn test (`start`/`messageId`, `data-conversation` with `transient`, `data-phase` id `phase` and `round`, `data-skills`, `data-evidence` id `evidence`, `text-start`/`text-delta`/`text-end` id `text`, source parts, `finish` with `finishReason` and camelCase `messageMetadata`) | test_ui_stream | named |
| finish reason `error` for `error`/`timeout`, `stop` otherwise; empty token adds nothing; no text part without tokens; `persisted` false only in the metadata | test_ui_stream | named |
| `pharma_agent.api.ui_stream.ui_message_stream(events)`: `data: ` only frames, compact JSON, last frame `data: [DONE]` | test_ui_stream | named (`JSONServerSentEvent`, `ServerSentEvent(data="[DONE]")`) |
| `POST /api/v1/chat/stream`: 200, `text/event-stream`, headers `x-vercel-ai-ui-message-stream: v1`, `cache-control: no-cache`, `x-accel-buffering: no`, no `event:` lines; `start.messageId` = stored assistant message id; source indexes = stored citations; `runId` | test_chat_api | named (route at base; ids and citations from the existing chat service) |
| 404 `application/problem+json` with `CONVERSATION_NOT_FOUND` before streaming | test_chat_api | base (problem responses and opening the turn before streaming exist at base; the prompt says to keep them) |
| `pharma_agent.infrastructure.persistence.postgres.tables.MessageCitationTable`, table `message_citations`, rollback on a dangling citation, restrict/cascade foreign keys, citations round trip | test_conversation_repository, test_migrations, test_e2e_postgres | integration (named) |
| corpus row helpers | corpus_rows.py | support (integration only) |

GAPs: 0.

Residual ambiguities:

1. The exact SSE byte framing comes from sse-starlette (`\r\n` line ends, `data: ` prefix). The
   prompt names `JSONServerSentEvent` and `ServerSentEvent`, which produce exactly the framing the
   test checks; hand-written frames may differ. Minor.
2. Moderate (grading coverage): the `message_citations` persistence (44% of the exercised src
   lines) is checked only by integration tests.
3. `createdAt` is serialized by the existing `MessageMetadata` (`...Z`); building the metadata any
   other way could change the format. The prompt says to build a `MessageMetadata`. Minor.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (EXTRA_REVIEW_fable.md)

---

## 4. m04: FastAPI app, SSE chat, conversation and health endpoints, serve/migrate (api)

- range: `44466f373da672594dbf8a4d419505f662c712f1..4ba674d359882c639724ee413fd87044c66597b5`
- commits (oldest first):
  - `3af531a` feat(api): add FastAPI app with SSE chat, conversations and health endpoints
  - `4ba674d` feat(backend): add serve/migrate commands, Postgres end-to-end test and API docs
- plan: 2026-09-12-pharma-agent-platform (F03, first-parent 47-48). The base is t10's commit; the range
  contains no task commit.
- selection: pass 1, layer api (331 of 362 src lines; `cli.py` 31); 11 required names (8 routes,
  2 CLI commands, `create_app`), the only eligible api window
- size: backend/src 11 files, +362/-0 (362 lines); backend/tests 7 files, +457/-0
- hidden tests (5 files, 9 graded tests; 7 fail at base, the 2 others are existing CLI tests):
  - `backend/tests/api/test_chat_api.py` (A)
  - `backend/tests/api/test_conversations_api.py` (A)
  - `backend/tests/api/test_e2e_postgres.py` (A, integration)
  - `backend/tests/api/test_health_api.py` (A)
  - `backend/tests/test_cli.py` (M)
- support files restored from `end`: `backend/tests/api/__init__.py` (A, empty), `backend/tests/api/harness.py` (A)
- grading: the original patch grades clean; integration-only share 4%.
- **harness note**: the range also edits `backend/docs/superpowers/plans/2026-09-12-pharma-agent-platform.md`.
  `prepare_workspace` strips `superpowers` directories, so the old `original_patch_errors` failed at
  `git apply` before grading; it was graded with the diff limited to
  `':(exclude,glob)**/superpowers/**'`. Harness commit `6b5bbf9` (drop stripped-contaminant hunks
  when applying the original range patch) addresses this; `tasks validate --original-patch` re-run on
  2026-11-15 with the task directory and the unmodified diff: clean.
- Unchanged from the old draft's m02 (draft prompt and audit).

Final prompt (the draft with every edit of `EXTRA_REVIEW_fable.md` applied; identical to `data/tasks/<id>/prompt.md`):

```text
Expose the chat and conversation use cases over HTTP with a FastAPI application under `/api/v1`, stream chat turns as server-sent events, report service health, and add `serve` and `migrate` commands to the `pharma-agent` CLI.
Add `create_app(settings=None, *, container_factory=open_container)` in `pharma_agent.api.app`, usable as the uvicorn factory `pharma_agent.api.app:create_app`, which builds the fastapi-users auth with `build_auth` and stores it as `app.state.auth`, opens the `Container` from `container_factory(settings)` for the lifetime of the application, allows the configured CORS origins, includes the auth routes under `/api/v1`, and answers application errors with the JSON body `{"code": ..., "message": ...}` and status 404 for `ConversationNotFound`, 422 for `InvalidInput`, 503 for `AgentUnavailable` and 400 for any other `ApplicationError`.
Every chat and conversation route needs an active user (`auth.current_active_user`) and works on that user's id as 32 lowercase hex characters, a route called before the container is open answers 503, and the chat routes raise `AgentUnavailable` when the container has no chat service.
`POST /api/v1/chat` takes `{"message", "conversation_id"}` (the message 1 to 4000 characters, the optional conversation id 32 lowercase hex characters, anything else 422), returns the `ChatTurnResult` of `ChatService.ask`, and afterwards runs the container's summarizer (`run_if_needed`) for that conversation as a background task whose errors are only logged.
`POST /api/v1/chat/stream` takes the same body, opens the turn before it starts the response (so an unknown conversation is a 404 and a missing agent a 503), sends every event of the session as a server-sent event whose event name is the event type and whose data is the event data as JSON, and then runs the same background summary.
`GET /api/v1/conversations` (query `limit` 1 to 100, default 20, and an optional `before` time), `GET /api/v1/conversations/{conversation_id}`, `GET /api/v1/conversations/{conversation_id}/messages` (`limit` 1 to 200, default 50, optional `before`), `PATCH /api/v1/conversations/{conversation_id}` with `{"title"}` (1 to 80 characters) and `DELETE /api/v1/conversations/{conversation_id}` (status 204) call the matching `ConversationQueries` methods and return their results as JSON (a bare array of views for the two list routes), and every route with a conversation id that is not 32 lowercase hex characters answers 422.
`GET /api/v1/health` needs no user, runs every check in `container.health_checks`, and answers `{"status": "ok" or "degraded", "agent": <whether the container has a chat service>, "checks": {<check name>: <result>}}` with status 200 when every check passes and 503 otherwise.
`pharma-agent serve` with the options `--host`, `--port` and `--reload` calls `uvicorn.run("pharma_agent.api.app:create_app", factory=True, host=..., port=..., reload=...)` with the host and port defaulting to the `api` settings, and `pharma-agent migrate [REVISION]` (default `head`) runs `alembic.command.upgrade` with the existing `alembic_config()`.

Required interfaces:
- `pharma_agent.api.app.create_app` (keyword `container_factory`); `app.state.auth`
- Routes: `POST /api/v1/chat`, `POST /api/v1/chat/stream`, `GET /api/v1/conversations`, `GET`, `PATCH` and `DELETE /api/v1/conversations/{conversation_id}`, `GET /api/v1/conversations/{conversation_id}/messages`, `GET /api/v1/health`
- JSON fields: requests `message`, `conversation_id`, `title`; error body `code`, `message`; health `status`, `agent`, `checks`
- CLI commands: `pharma-agent serve --host --port --reload`, `pharma-agent migrate [REVISION]`
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `ChatService`, `MemoryPolicy`, `ConversationQueries`, `SummarizeConversation`, `build_chat_graph`, `ChatTurnRunner`, `BudgetLimits`, `SystemClock`, `make_hit`, `FakeLlm`, `FakeRetriever`, `build_deps`, `InMemoryConversationRepository` | harness | base |
| `Container(settings=, sessions=, queries=, chat=, summarizer=, health_checks=)`, `ContainerFactory`, `open_container` | harness | base |
| `Settings(_env_file=None, auth={"jwt_secret": ...})`, `UserTable(...)`, `Auth.current_active_user`, `build_auth` | harness | base |
| `pharma_agent.api.app.create_app(settings, container_factory=)` | harness, test_cli | named |
| `app.state.auth`, dependency override on `auth.current_active_user` | harness | named |
| container opened in the lifespan (`with TestClient(app)`) | harness | named |
| `POST /api/v1/chat/stream`, 200, `text/event-stream`, `event:` = event type, `data:` = JSON | test_chat_api | named |
| first event `conversation`, last `done`; `phase`, `evidence`, `token`, `citations` in between; done `status`, `message_id`, `conversation_id` | test_chat_api | base (session events from m01's service) |
| stored `user_id == OWNER.hex` | test_chat_api | named (32 lowercase hex) |
| `POST /api/v1/chat` returning `persisted`, `citations`, `conversation_id`; summary stored after the second turn | test_chat_api | named (`ChatTurnResult`, background `run_if_needed`) |
| 404 `{"code": "CONVERSATION_NOT_FOUND"}`, 422 for id `"nope"` and empty message, 503 `{"code": "AGENT_UNAVAILABLE"}` on the stream route | test_chat_api | named |
| `GET /api/v1/conversations` (JSON list), `GET .../{id}` `turn_count`, `GET .../{id}/messages` roles, `PATCH .../{id}` title and 422 for `""`, 404 for a foreign id, `DELETE` 204 then 404 | test_conversations_api | named |
| `GET /api/v1/health` without a user: exactly `{"status", "agent", "checks"}`, 200 `ok` / 503 `degraded` | test_health_api | named |
| `cli.app` `migrate`: `alembic.command.upgrade(config, "head")`, `script_location` ending in `:migrations` | test_cli | named (`alembic_config()` at base) |
| `cli.app` `serve --host`: `uvicorn.run("pharma_agent.api.app:create_app", factory=True, host=, port=)`, port from `PHARMA_API__PORT` | test_cli | named (`api` settings at base) |
| Postgres end-to-end flow | test_e2e_postgres | integration |

GAPs: 0.

Residual ambiguities:

1. The CLI tests monkeypatch `alembic.command.upgrade` and `uvicorn.run` before invoking the command,
   and set `PHARMA_API__PORT` the same way. An implementation that binds those functions with
   `from ... import` at module import time, or reads `Settings()` at import time, fails. The prompt
   says "calls `uvicorn.run(...)`" and "runs `alembic.command.upgrade`", and the existing CLI already
   builds settings inside each command. Minor.
2. The error body also has `message`, but only `code` is checked. Minor.
3. The background summary after a streamed turn is not checked. Minor.

An's verdict: approved in bulk 2026-11-15 with the Fable edits (EXTRA_REVIEW_fable.md)

---

## 5. m05: bundle import into resumable releases, release service (application)

- range: `067e562740912786b77a7ee3d22de65e536f0a65..adf89a7b629a06a5d864c7b3f78d8f4f5c149b01`
- commits (oldest first):
  - `fce6d9d` feat(corpus): import knowledge bundles into resumable releases
  - `adf89a7` feat(corpus): add release publish, rollback, gc and reindex service
- plan: 2026-09-13-corpus-store-import (F06, first-parent 80-81); no overlap with any task
- selection: pass 2 (layer application, 515 of 515 src lines); 5 required names, fewest among the
  eligible windows left
- size: backend/src 4 files, +515/-0 (515 lines); backend/tests 3 files, +819/-0
- hidden tests (2 files, 13 graded tests, all fail at base):
  - `backend/tests/application/test_import_bundle.py` (A)
  - `backend/tests/application/test_release_service.py` (A)
- support files restored from `end`: `backend/tests/corpus_memory.py` (A): in-memory
  `CorpusRepository`, `EmbeddingCache` and `VectorIndex` implementing the ports at base,
  `SteppingClock`, and `build_importer`/`build_release_service`, which construct the agent's
  classes positionally plus `embed_batch_size=`/`embed_max_concurrent=`.
- grading: the original patch grades clean; integration-only share 0%.
- note: the old draft rejected this window on a coupling estimate of 33 (28 methods of the
  restored fakes). The ports those fakes implement are all in `domain/corpus/ports.py` at base,
  with docstrings, so they add no name the prompt has to give.

Final prompt (the draft with every edit of `EXTRA_REVIEW_fable.md` applied; identical to `data/tasks/<id>/prompt.md`):

```text
Add the application services that import a knowledge bundle into a new corpus release and manage releases (list, publish, rollback, garbage collection, reindex), built only on the existing corpus ports `CorpusRepository`, `EmbeddingCache`, `Embedder` and `VectorIndex` and the existing corpus domain models.
In `pharma_agent.application.corpus.indexing`, `EmbeddingResolver(cache, embedder, *, batch_size, max_concurrent)` raises `ValueError` mentioning `batch_size` when either value is below 1, and `ensure(texts, bundled)` (embedding-text hash to text, and hash to a precomputed vector) asks the cache which hashes are missing for the embedder's model, stores the missing ones found in `bundled` with `put_many(model, dimension, ...)`, embeds the rest in batches of at most `batch_size` texts keeping `max_concurrent` `embed` calls in flight whenever that many batches are left, and never more, and returns `EmbeddingCounts(cached, from_bundle, computed)`.
Each embedded batch is stored in the cache as soon as it returns, an embedder error propagates as the same exception with the earlier batches kept and no further batch started, and a result with another number of vectors or another vector length raises `CorpusImportError`.
`ImportKnowledgeBundle(repository, cache, index, embedder, clock, *, embed_batch_size, embed_max_concurrent)` in `pharma_agent.application.corpus.import_bundle` is awaited as `importer(bundle, *, publish)` and returns an `ImportReport` with `outcome` (an `ImportOutcome`: `IMPORTED` "imported", `REUSED` "reused" or `NO_CHANGE` "no_change"), `collection_key`, `release` and `published`.
It builds the snapshot with `build_snapshot` and, before calling any port, takes the bundle's vectors for the embedder's model only when the manifest declares that model with the embedder's dimension, raising `CorpusImportError` mentioning `dims` when one of those vectors has another length.
If the collection's current release has the snapshot's bundle digest and chunker version and the embedder's model, the import returns `NO_CHANGE` with that release and `published` true without any other port call; otherwise it ensures the index collection, looks up `find_release` for the same digest, chunker version and model, takes that release as `REUSED` when it is `READY` (nothing is staged or built), and otherwise calls `stage_release` (with the found release's id or a new `uuid4`, the embedder's model and the clock's time) and builds the release as `IMPORTED`.
Building resolves every embedding text of the snapshot (cache first, then the bundle vectors, then the embedder), takes the release's `index_items`, upserts in batches the items whose `chunk_version_id` the index does not have yet (vectors read from the cache by `embedding_text_sha256`, `CorpusImportError` if one is not cached) and rewrites the release ids of the others with `set_release_ids`, then requires `count_release` to equal the number of the snapshot's `release_chunks` (otherwise it raises `CorpusImportError` containing `expected` and the release stays `BUILDING`) and calls `mark_ready` with the snapshot's `stats()` plus `embeddings_cached`, `embeddings_from_bundle`, `embeddings_computed`, `points_upserted` and `points_updated`.
With `publish` true the reused or built release is then published at the clock's time, and the report carries the release as the repository returns it afterwards.
`ReleaseService` in `pharma_agent.application.corpus.releases`, constructed like the importer, has `list_releases(collection_key=None)` returning the repository's summaries, `publish(release_id)`, which raises `ReleaseNotFound` for an unknown id and `ReleaseNotPublishable` naming the status (for example `building`) unless the release is `READY` and returns the published release, and `rollback(collection_key)`, which publishes again and returns the `READY` release with the latest `published_at` (then the highest number) before that of the current release, raising `CollectionNotFound` for an unknown collection and `NoEarlierRelease` when the current release is missing or unpublished or there is no such release.
`gc(collection_key, keep)` retires the releases chosen by the existing `releases_to_retire(releases, current_release_id, keep)`, then for every retired release that still has chunks takes their `index_items` and, among the points present in the index, rewrites with `set_release_ids` those still in some release and deletes those in none, calls `purge_retired` for the collection and returns `GcReport(retired, points_updated, points_deleted, purge)`, where `retired` lists the ids retired by this call in the order `releases_to_retire` gave.
`reindex(collection_key)` (raising `CollectionNotFound`) takes the collection's releases that are not `RETIRED`, skips those whose `embedding_model` is not the embedder's model, ensures the index collection, takes the `index_items` of the usable releases with their `release_ids` limited to usable releases, resolves their embeddings without bundle vectors, upserts all of them, and returns `ReindexReport(points_upserted, release_points, skipped)` with each usable release's `count_release` and the ids of the skipped releases.

Required interfaces:
- `pharma_agent.application.corpus.indexing`: `EmbeddingResolver` (keywords `batch_size`, `max_concurrent`; `ensure`), `EmbeddingCounts` (`cached`, `from_bundle`, `computed`)
- `pharma_agent.application.corpus.import_bundle`: `ImportKnowledgeBundle` (keywords `embed_batch_size`, `embed_max_concurrent`; called with keyword `publish`), `ImportReport` (`outcome`, `collection_key`, `release`, `published`), `ImportOutcome` (`IMPORTED`, `REUSED`, `NO_CHANGE`)
- `pharma_agent.application.corpus.releases`: `ReleaseService` (`list_releases`, `publish`, `rollback`, `gc`, `reindex`), `GcReport` (`retired`, `points_updated`, `points_deleted`, `purge`), `ReindexReport` (`points_upserted`, `release_points`, `skipped`)
```

Name audit:

| name used by hidden tests / restored support | where | status |
| --- | --- | --- |
| `KnowledgeBundle`, `CorpusImportError`, `ReleaseStatus`, `build_snapshot` (`embedding_texts`, `release_chunks`, `chunks`, `stats`), `CollectionNotFound`, `NoEarlierRelease`, `Release`, `ReleaseNotFound`, `ReleaseNotPublishable`, `RetrievalError`, `releases_to_retire` | both | base |
| `small_bundle`, `with_section_text`, `DOSAGE_SECTION`, `LEAFLET_SECTION`, `FakeEmbedder(fail_on_batch=)`, `FAKE_EMBEDDING_MODEL`, `fake_vector`, `NOW` | both | base |
| `CorpusAdapters`, `InMemoryEmbeddingCache`, `InMemoryVectorIndex(drop_ids=)`, `SteppingClock`, `build_importer`, `build_release_service`, fake counters `stage_calls`, `ensure_calls`, `protected_chunk_ids` | both | support |
| port methods the fakes implement (`get_collection`, `find_release`, `stage_release`, `index_items`, `mark_ready`, `publish`, `retire`, `purge_retired`, `missing`, `get_many`, `put_many`, `ensure_collection`, `existing_ids`, `upsert`, `set_release_ids`, `delete`, `count_release`, `list_releases`, `get_release`) | support | base (ports in `domain/corpus/ports.py`) |
| `pharma_agent.application.corpus.import_bundle.ImportKnowledgeBundle(repository, cache, index, embedder, clock, embed_batch_size=, embed_max_concurrent=)`, `importer(bundle, publish=)` | support, both | named |
| `ImportOutcome.IMPORTED/REUSED/NO_CHANGE`; report `outcome`, `published`, `collection_key`, `release` | test_import_bundle | named |
| cache then bundle then embedder, counts in `stats`; batches of at most `batch_size`; no stage/ensure call on `NO_CHANGE` or on a wrong vector length (`match="dims"`); bundle vectors ignored when declared with other dims | test_import_bundle | named |
| failure keeps a `BUILDING` release and the first batch in the cache, rerun resumes; missing points -> `CorpusImportError` (`match="expected"`), release stays `BUILDING` | test_import_bundle | named |
| changed bundle: release 2, `points_upserted` = new chunks, `points_updated` = shared chunks, release ids rewritten | test_import_bundle | named |
| `pharma_agent.application.corpus.indexing.EmbeddingResolver(cache, embedder, batch_size=, max_concurrent=)`, `ensure(texts, {})`, `EmbeddingCounts(cached=, from_bundle=, computed=)`, peak concurrency 2, `ValueError` matching `batch_size` | test_import_bundle | named |
| `pharma_agent.application.corpus.releases.ReleaseService`; `list_releases`, `publish` (`ReleaseNotPublishable` matching `building`, `ReleaseNotFound`), `rollback` (`NoEarlierRelease`, `CollectionNotFound`) | test_release_service | named |
| `gc(key, keep=1)`: `retired` order, points deleted/updated, `purge` passed through, second run is a no-op | test_release_service | named |
| `reindex(key)`: `points_upserted`, `release_points`, `skipped` (other embedding model), only the dropped vector re-embedded | test_release_service | named |

GAPs: 0.

Residual ambiguities:

1. `stats()` and the counts it is updated with: the test reads `embeddings_cached`,
   `embeddings_from_bundle`, `embeddings_computed`, `points_upserted`, `points_updated` and `chunks`;
   `ReleaseStats` at base has these fields and the prompt names them. Minor.
2. The rollback rule ("latest `published_at` before that of the current release") relies on the
   fake keeping the first `published_at` when a release is published again, which the base port
   docstring states. Minor.
3. Moderate: two services and a resolver with concurrency and resume rules in 11 sentences; the
   behaviour is fully stated, but it is the largest graded surface of the tier (515 lines, all
   graded).

An's verdict: approved in bulk 2026-11-15 with the Fable edits (EXTRA_REVIEW_fable.md)
