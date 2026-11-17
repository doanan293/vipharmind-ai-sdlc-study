# Independent review of the medium-tier prompts (m01-m05) and of the `prereg-v1.1` draft

Reviewer: Fable (independent of the drafter). Date: 2026-11-15.

Method: for each window I read the hidden tests and restored support files at `end`, the base code at
`base` and the original source diff, without relying on the drafter's audit tables. Test line numbers
refer to the file at the range `end`. For part 2 I re-derived the selection with my own script from
`medium_candidates.json` plus `git` (commit types, sizes, layers and task overlap recomputed, not read
from the JSON), re-ran `medium_names.py` on ten windows, and enumerated all 188 windows of the 16
sub-ranges. I did not open anything under `data/results/` and ran no agent.

## Summary

| task | verdict | blocking-risk issues | minor issues |
| --- | --- | --- | --- |
| m01 | APPROVE WITH EDITS (it is a written design; see below) | 3 | 1 |
| m02 | APPROVE WITH EDITS | 0 | 1 |
| m03 | APPROVE | 0 | 0 (1 optional) |
| m04 | APPROVE WITH EDITS | 0 | 1 |
| m05 | APPROVE WITH EDITS | 2 | 1 |

No REJECT. As in the feature tier, I found no public name (module path, class, function, keyword,
route, CLI command, error code) that a graded test needs, that is missing at base and that a prompt
does not name. Every issue is a behaviour that a graded test pins and the prompt leaves open or words
in a way that points away from what the test accepts. All edits are insertions or replacements inside
existing sentences; no sentence count changes.

`prereg-v1.1` draft: **the selection is reproduced exactly (same five windows, same order, 21
eligible) and the amended rule is acceptable as a logged deviation, but the draft is not ready to
tag.** Four blocking items, all about what the document must record, none about the picks (part 2).

Format, all five: English, 7-12 one-sentence lines, a "Required interfaces" section, no mention of
tests. Words per prompt body: m01 801, m02 495, m03 460, m04 400, m05 656 (longest sentence 108 words,
m01). No prompt refers to a plan, a design document or a process, and I found nothing that helps one
arm only.

Grading facts that apply to every task: hidden ids come from the reference run at `end` under
`-m "not integration"`, so integration-marked tests and anything only they import are ungraded.

---

## m01: APPROVE WITH EDITS

Names: verified. Base `bundle.py` has every model, `BundleValidationError(problems)`, `model_slug`,
`encode_vector`, `decode_vector` (with the exact `vector has 12 bytes, expected 16 (dims * 4)`
message) and `_STRICT`; `normalize_text` exists in `domain/shared/text.py`. Only `read_bundle`,
`write_bundle` and the five `identity` names are new, and all are named. I checked every expected
problem list in `test_bundle_io.py` and every formula in `test_identity.py` against the prompt: the
templates, the prefixes and the stated order agree with the tests everywhere except the three points
below.

### Is it a prompt or a written design?

It is a written design. The body is 801 words and states 34 message templates plus the order in which
they are reported; 24 of the 34 are exercised by a graded test and 10 are not (`model name must
contain letters or digits`, `model slug collides`, `is not a sha256 hex digest`, `.model: must contain
letters or digits`, `duplicate model`, `is not listed in files`, `files.<name>: missing entry`,
`file is not valid UTF-8`, and the two empty-key messages). Several clauses are control flow rather
than behaviour ("which skips the rest of that entry", "the first that applies").

I still approve it, for three reasons. (1) The tests compare whole problem lists with `==`, so the
templates and their order are observable output, not approach; no shorter text can make the task
passable, because the spec the module docstring cites is stripped. (2) Removing the 10 unexercised
templates would make the prompt mirror the test selection, which is worse. (3) Both arms get the same
text. What An should accept knowingly: for m01 the prompt is already the specification, so the
spec-first arm has little to add and can only lose detail when it restates the text. That is the same
tier property I noted for f08/f14/f15, at its extreme here. It belongs in the report's limitations,
and m01 should be named there.

A REJECT would not help under the draft's replacement rule: with F05_69-70 removed, the rule picks
F05_69-71 for the domain layer, which contains the same two commits plus one more (see V-4).

### Issues

**M01-1 (blocking risk). A JSON list file with one invalid entry must contribute nothing to the
content checks.** `test_bundle_io.py:372-390`: the glossary has a duplicate term at `[1]`, a blank
term at `[2]` and a missing `term` at `[3]`, and the expected list is only
`["glossary.json: [3].term: Field required"]`. The prompt says the two JSON files are validated "as
lists" and then that the content checks report duplicates and empty terms. An agent that validates
entry by entry and keeps the valid ones (reasonable under "every problem reported at once") also
reports `[1]` and `[2]` and fails. JSONL files behave the other way (an invalid line drops only that
record, `:311-333`), so the asymmetry has to be stated.

Edit, sentence 7. Replace

> the two JSON files as lists of `GlossaryEntry` and `ColloquialMappingRecord` (where `<file>`), and then

with

> the two JSON files each as one list of `GlossaryEntry` or `ColloquialMappingRecord` (where `<file>`; a list with any validation problem counts as empty in the later checks, while an invalid JSONL line drops only that record), and then

**M01-2 (blocking risk). "Empty" means empty after stripping whitespace.** `:344` and `:360`: block
markdown `"   "` must give `blocks[0].markdown: must not be empty`; `:383`/`:402` and `:410`: term
`" "` must give `[2].term: must not be empty`. The prompt never says a whitespace-only string is
empty; `if not block.markdown` follows the prompt and fails two tests.

Edit, sentence 8. Replace

> The content checks, shared with `write_bundle`, report per document

with

> The content checks, shared with `write_bundle`, treat a string that is blank after stripping whitespace as empty and report per document

**M01-3 (blocking risk). Which line counts as the first occurrence of an embedding hash.**
`:441-476`: line 2 has matching dims but an undecodable vector, line 3 repeats its hash, and the
expected problems are `...:2: vector: ...` and `...:3: embedding_text_sha256: duplicate of line 2`.
So a line registers its hash once its dims match, even when its vector fails to decode. The natural
implementation tests membership in the dict of decoded vectors; line 2 is not in it, line 3 then
decodes cleanly, and the problem is missing.

Edit, sentence 10. Replace

> else `<file>:<line>: embedding_text_sha256: duplicate of line <l>`, else

with

> else `<file>:<line>: embedding_text_sha256: duplicate of line <l>` (the first line with that hash whose dims matched, whether or not its vector decoded), else

**M01-4 (minor). Order of `files` in the written manifest.** The read side reports "for each `files`
entry in manifest order", and `:301-308` expects `documents.jsonl` problems before
`glossary.json: file is missing`. The prompt does not fix the order `write_bundle` uses. Any order
with documents before glossary passes (including alphabetical), so the risk is low. Optional edit,
sentence 2: replace "`files` (each written file name to a `BundleFile`" with "`files` (the four record
files in the order above, then the embedding files, each name to a `BundleFile`".

Drafter's residual ambiguities: #1 is the design question above; #2 and #3 leave.

---

## m02: APPROVE WITH EDITS

Names: verified. Base has the `ConversationRepository` port with `list_for_user`, `messages`,
`update_title`, `update_summary`, `delete -> bool`, `turns_since`; `Conversation.rename`,
`needs_summary`, `apply_summary(summary, covered_turns=, now=)`; `InvalidTitle`, `InvalidInput`,
`ConversationNotFound`, `EXCLUDED_STATUSES`, `summary_messages`, `LlmRole.SUMMARIZER`,
`build_chat_graph(checkpointer=)`, `checkpoint_serializer`, `Database.ping`, `AuditContext`,
`MemoryPolicy`, `settings.postgres.conninfo`, `settings.llm.configured`, the `memory` settings, and
the `langgraph-checkpoint-postgres` and `psycopg[pool]` dependencies. `MessageRole` is a `StrEnum`, so
`m.role == "user"` holds whichever type the view uses.

Graded surface: only `test_queries.py` (1 test) and `test_summarize.py` (5 tests). Sentences 6-9
(checkpointer, `include_name`, container; 162 of 335 src lines) are reached only by integration tests.
The prompt is right to describe them, but see V-5.

### Issues

**M02-1 (minor to moderate). "The covered turn count" can be read as the number of usable turns.**
`test_summarize.py`, due-summary test: two turns are read, one is `blocked`, and
`stored.summarized_turns == 2`. An agent that advances by the usable turns stores 1 and fails. The
excluded-only case has the same reading risk.

Edit, sentence 5. Replace

> it only advances the summarized turn count and returns False

with

> it only advances the summarized turn count past the turns read and returns False

and replace

> stores that summary cut to `max_chars` characters with the covered turn count,

with

> stores that summary cut to `max_chars` characters and advances the summarized turn count past every turn read, usable or not,

Not an issue: sentence 6 gives pool settings (autocommit, `prepare_threshold` 0, dict rows). That is
approach, but it is what `AsyncPostgresSaver` requires, it is ungraded, and both arms get it. Leave.

Drafter's residual ambiguities: #1 leave; #2 is V-5.

---

## m03: APPROVE

Names: verified. Base `application/conversation/ui_message.py` has `CamelModel` with
`serialize_by_alias=True` (so "JSON dump" gives camelCase without further instruction),
`EvidenceItem`, `MessageMetadata`, `MessageUsage`, `MessageStatus`, `source_document_part`,
`source_document_parts_from_event` (sets `is_current=True`) and `evidence_items_from_event`. The base
route already opens the turn before streaming and answers problem responses. `ProgressEvent` has
exactly the seven event types the prompt maps.

I checked the full expected chunk list of `test_ui_stream.py` (start, transient `data-conversation`,
`data-phase` with and without `round`, `data-skills`, `data-evidence`, text start/delta/end, source
parts, `finish` with the six metadata keys and no `feedback`), the seven finish-reason cases, the
empty-token and no-token cases, the SSE framing test and the four `test_chat_api.py` tests. The prompt
states each of them. The framing test needs `\r\n\r\n` separators, compact JSON and unescaped
non-ASCII (`"delta":"Liều [1]"`); naming `JSONServerSentEvent` and `ServerSentEvent` gives all three.
That naming is approach, but it is the only short way to pin the bytes; keep it.

Optional edit (not required), sentence 5: after "a single `data:` line of compact JSON" add
", non-ASCII characters unescaped". It protects an agent that writes frames by hand.

Graded surface: `ui_stream.py` and the route (166 api lines). No graded test reaches the 247
infrastructure lines of sentences 6-7. See V-5; the window's layer label is the ungraded part.

Drafter's residual ambiguities: all leave.

---

## m04: APPROVE WITH EDITS

Names: verified. Base has `ApplicationError.code` with `CONVERSATION_NOT_FOUND`, `INVALID_INPUT`,
`AGENT_UNAVAILABLE`; `build_auth(settings, resolve_sessions)` and `Auth.current_active_user`;
`include_auth_routes`; `Container`, `ContainerFactory`, `open_container`; `ChatService.ask` and
`open_turn`; `api` settings with host, port and `cors_origins`; `alembic_config()`; and the
`fastapi`, `sse-starlette` and `uvicorn` dependencies. The harness builds the app before the lifespan
runs and overrides `app.state.auth.current_active_user`; the prompt names both.

Graded: 9 tests, 7 failing at base (the other two are the pre-existing CLI tests). Every status code,
body key and CLI assertion is stated.

### Issues

**M04-1 (minor). The list routes must return bare JSON arrays.** `test_conversations_api.py` iterates
`listed.json()` and asserts `client.get("/api/v1/conversations").json() == []`, and iterates the
messages response. The routes take `limit` and `before`, which invites a paginated envelope
(`{"items": [...]}`); "return their views as JSON" does not exclude it.

Edit, sentence 6. Replace

> call the matching `ConversationQueries` methods and return their views as JSON,

with

> call the matching `ConversationQueries` methods and return their results as JSON (a bare array of views for the two list routes),

Drafter's residual ambiguity #1 (monkeypatched `alembic.command.upgrade` and `uvicorn.run`): real but
it cannot be fixed without describing approach or tests; a module-level `from alembic.command import
upgrade` is unusual. Leave. #2 and #3 leave.

Before the task directory is accepted: `tasks validate --original-patch` must pass for m04 on the
unmodified harness path (it was graded with a hand-limited diff; harness commit `6b5bbf9` is meant to
cover this but was not re-run).

---

## m05: APPROVE WITH EDITS

Names: verified. Every port method the restored `tests/corpus_memory.py` implements is declared in
`domain/corpus/ports.py` at base with the same signature; `ReleaseStats` has the five counters;
`releases_to_retire` sorts by number itself, so `retired == [r2.id, r1.id]` does not depend on the
order the agent passes; `CorpusImportError`, `ReleaseNotFound`, `ReleaseNotPublishable`,
`NoEarlierRelease`, `CollectionNotFound`, `build_snapshot` and the fixtures exist at base. The only
new imports are the five the prompt names, plus `ImportReport`, `GcReport` and `ReindexReport` (used
through attributes only).

I walked all 13 tests. The port-call observables (`stage_calls`, `ensure_calls`, cache contents after
a failed batch, release ids on points, `skipped`, `release_points`) all follow from the prompt.

### Issues

**M05-1 (blocking risk). A reused release must still be published.** `test_import_bundle.py:112-125`:
the second import with `publish=True` returns `REUSED`, `second.published` is true and
`second.release.published_at == NOW`. Sentence 6 says the import "returns `NO_CHANGE` ... without any
other port call" and, in the same construction, "returns `REUSED` with that release when it is
`READY`". Read in parallel, both are early returns, and sentence 8's "the release is then published"
then applies only to the built release.

Edit, sentence 6. Replace

> returns `REUSED` with that release when it is `READY`, and otherwise calls

with

> takes that release as `REUSED` when it is `READY` (nothing is staged or built), and otherwise calls

Edit, sentence 8. Replace

> With `publish` true the release is then published at the clock's time

with

> With `publish` true the reused or built release is then published at the clock's time

**M05-2 (blocking risk). "At most `max_concurrent`" is satisfied by a sequential loop, which fails.**
`:245-252`: six one-text batches with `max_concurrent=2` must give `embedder.peak == 2`. A sequential
resolver has a peak of 1 and still obeys "at most".

Edit, sentence 2. Replace

> with at most `max_concurrent` `embed` calls in flight

with

> keeping `max_concurrent` `embed` calls in flight whenever that many batches are left, and never more

**M05-3 (minor). The embedder's error must surface as itself.** `:133` and
`test_release_service.py:84` use `pytest.raises(RetrievalError)`. The concurrency requirement makes
`asyncio.TaskGroup` likely, and it raises an `ExceptionGroup`. "Re-raised" probably suffices; to be
safe, in sentence 3 replace "an embedder error is re-raised" with "an embedder error propagates as the
same exception".

Drafter's residual ambiguities: all leave.

---

## Part 2: `prereg-v1.1` draft

### What I verified

1. **Selection reproduced.** My script gives 21 eligible windows and the same five picks in the same
   order: F05_69-70 (domain, pass 1), F03_44-45 (application, pass 1), F09_107-109 (infrastructure,
   pass 1), F03_47-48 (api, pass 1), F06_80-81 (pass 2). Eligibility matches the JSON for all 93
   windows, and the tally by first failed criterion matches the draft (1, 5, 42, 2, 11, 4, 5, 2).
2. **Candidate set complete.** The 16 sub-ranges hold 188 windows of 2-3 consecutive first-parent
   commits. 67 are all-`feat`, `backend/`-only and 300-700 src lines; all 67 are in the JSON. No
   ungraded or unmeasured window passes the static criteria.
3. **Name counts reproduced.** `medium_names.py` returns identical counts and name lists for the five
   picks and five other eligible windows (F02_29-30, F03_43-44, F06_79-80, F09_106-107, F13_391-392).
   For the five picks only N1, N3 and N4 are non-zero; the grep-based N5-N7 play no part.
4. **Overlap table correct.** The shared hidden-test paths listed for m02, m03 and m04 match the
   `hidden_tests` of every `task.toml`; no pick shares a commit with any task.
5. **Sensitivity of the picks to the rule's free parameters** (same data, one parameter changed):

| change | result |
| --- | --- |
| no layer pass (pure ranking) | same five windows, different numbering |
| minimum failing tests 1, 3 or 5 | unchanged |
| minimum failing tests 8 or 10 | m02 and m04 drop out (F03_43-44 and F13_391-392 enter) |
| integration share limit 60%, 75%, 100% | unchanged |
| integration share limit 33% or 40% | m03 drops out (F02_29-30 enters) |
| integration share limit 25% | m02 and m03 drop out |
| `test`/`refactor` windows allowed | unchanged |
| tie-break without src lines (names, then `end`) | unchanged |

### Is the amended rule principled?

Yes, with one reservation. Excluding windows that share a commit with another tier follows directly
from the independence argument and from v1's own sensitivity analysis. Requiring graded signal
(criteria 7 and 8) and feature-only commits (criterion 2) is sound, and the table shows the layer
pass, the commit-type rule, the tie-break and the 5-test minimum do not decide any pick. The rule
discarded four of the drafter's five hand picks, which is evidence it was not tuned to keep them.

The reservation is researcher degrees of freedom in criterion 8. The thresholds were set after the
candidates' metrics were visible (not after any AI result). m03 sits at 44% under a 50% limit, and
its membership depends on both the limit and the metric's definition: the metric drops lines that
only run at import time (declarations, table definitions), and by plain src lines 247 of m03's 413
lines (60%) are in files no graded test reaches. I do not ask for a change, because 50% is the natural
majority threshold and a change now would be a second post-hoc choice. I ask for disclosure (V-5).

### Is the mechanical name count reasonable?

As a selection device, yes: it is reproducible, runs before any prompt exists and is applied to every
window the same way. As a measure of what a prompt must say, no, and the draft should not present it
as one. It does not count methods, fields and keywords of new classes or free-text strings, so it does
not track prompt burden: m01 has 7 names and an 801-word prompt with 34 templates; m04 has 11 names
and the shortest prompt. More important, the cap kept its number but changed its unit. v1's cap was
"the prompt can state every name the hidden tests need with at most 20 names". Counting the entries of
each "Required interfaces" section the way the large tier is still counted (methods, fields and
keywords included) gives about: m01 13, m02 25, m03 18, m04 24, m05 36. Three of the five exceed 20 in
v1's unit, and m05 exceeds the large tier's cap of 35. The large tier keeps the hand count (F04 and
F07 were rejected on about 60 and 70 names that include service and port methods), so the two tiers
now use different units for a criterion with the same name.

This is acceptable only if the deviation record says so in plain words (V-1).

### Blocking items (before the tag)

**V-1. The deviation is not yet logged, and the log line must cover every change.** `prereg-v1.md`
section 11 still reads "(Chưa có thay đổi.)". The draft promises one line; that line (or lines) must
list all of: (a) overlap with t/p tasks changed from "ranked later" to "excluded", and extended to
f08/f14/f15; (b) new criteria 2, 7 and 8 with their thresholds; (c) the name cap's unit changed from
names stated in the prompt to the mechanical N1-N7 count, with the hand counts of the five selected
prompts; (d) new ordering (src-lines tie-break, layer pass); (e) the new replacement rule. The "seen
before the change" field must say: candidate metrics (sizes, grading of the original patch, name
counts, coverage) and a first hand-picked list had been seen; no AI result had.

**V-2. Constraint 1 of v1 is in its fallback case and the draft does not say so.** The draft's own
operational note says the first small-tier main runs started around 19:16 on 2026-11-15, before any
`prereg-v1.1` tag. v1 allows this only if nobody opens `grade.json` or computes small-tier pass rates
until the tag exists, and requires section 11 to record the tag date and the date results are opened.
The draft must state that the fallback applies, confirm the condition, and add those two dates.

**V-3. The data v1.1 exists to add is incomplete.** Missing: the SHA-256 of each final prompt (m01-m05
after the edits above, and f08, f14, f15); the large-tier table (id, `base`, `end`, src lines, names);
the number of names stated in each prompt, which v1 lists as required data (the mechanical count is a
different quantity); the known cross-tier overlaps of the large tier carried over from v1 constraint
7. The m01-m05 task directories do not exist yet, so `tasks validate --original-patch` has not been
run on any of them; it must pass for all five, m04 in particular.

**V-4. The replacement rule is ambiguous in two places.** (a) "a name the tests need cannot be stated
within the 20-name limit" does not say in which unit; in the hand-count unit three approved prompts
already exceed it. Either drop the clause or tie it to the mechanical count. (b) "the next eligible
window in the selection order" does not say whether windows sharing a commit with the dropped task
are skipped. If they are not, dropping m01 selects F05_69-71, which contains the same commits. State
that such windows are skipped, and whether the remaining picks are kept or the whole selection is
re-run. No verdict in this review triggers the rule, so it can be fixed without affecting any pick.

### Non-blocking, to disclose in v1.1 or the report

**V-5. Graded size of m02 and m03 is small-tier size.** m02: 6 graded tests on 173 application lines;
the 162 infrastructure lines are integration-only. m03: the graded tests reach 166 api lines; none of
the 247 infrastructure lines, although the window's layer is "infrastructure". For H5 these two tasks
are medium by diff size but close to small by what `task_pass` measures. Add a "src lines in files a
graded test reaches" column to the task table and name this in the limitations. Also include the
sensitivity table above, or an equivalent, so a reader can see m03's dependence on the 50% limit.

**V-6. m01 is a specification-transcription task** (see m01). Name it in the limitations.

**V-7. Reproducibility of `medium_select.py`.** It needs `names.json` and `analysis.json`, which are
not committed; their content is embedded in `medium_candidates.json`. Commit the two inputs or let the
script read the JSON, so the documented command runs from a clean checkout.

**V-8. Small things.** The name categories are numbered N1, N3-N7 (no N2). N7 matches `def name`
anywhere in `backend/src`, so a new unrelated function with a fake's method name would be counted; it
affects no selected window. The draft's claim that v1's rule, applied verbatim, puts 3 of the top 5
candidates inside f08/f14/f15 cannot be checked from the committed data (those windows were never
graded or counted in v1's unit); either add the supporting numbers or soften the sentence.
