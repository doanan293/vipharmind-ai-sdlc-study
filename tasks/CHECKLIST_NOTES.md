# Checklist notes

Method: items come from the hidden test files at each task's `commit`, limited to tests added or changed between `parent`/`base` and `commit` (git diff of the hidden test files). Tests that were already in those files and did not change are regression checks the starting code already passes, so they are left out. Exact error strings, constant names and module paths are rewritten as behaviors. Wire contracts are kept: HTTP routes and status/problem codes, SSE/UI-stream chunk shapes, third-party URLs, and stored enum values.

- t01: 15 items. Nothing left out.
- t02: 14 items. Nothing left out.
- t03: 13 items. Nothing left out. operationIds are kept because they are part of the published OpenAPI contract.
- t04: 5 items. The pre-existing settings tests (unchanged) are left out.
- t05: 8 items. Nothing left out.
- t06: 6 items. Nothing left out.
- t07: 11 items. Nothing left out.
- t08: 11 items. Nothing left out.
- t09: 10 items. The ChatRole enum-values check is merged into the message-format item.
- t10: 6 items. Nothing left out.
- t11: 9 items. Nothing left out.
- t12: 8 items. The fixed skill ids are kept because the prompt fixes them. A brief-only agent would not know them, so this item is uncertain.
- t13: 8 items. The observation/score names ("chat_turn", "user_feedback") are given as reference values, not as requirements.
- t14: 8 items. Nothing left out.
- t15: 9 items. The pre-existing SMTP/Resend/log sender tests (unchanged) are left out.
- m01: 23 items. The exact problem-message strings and the bundle file names are not required. The UUIDv5 formulas are reduced to determinism and sensitivity.
- m02: 15 items. Nothing left out. The migration item covers the include_name filter behaviorally.
- m03: 18 items. test_invariants_reject_split_markers_and_orphan_sources only exercises a test helper; its two rules are folded into items 7 and 8. The unchanged pre-existing chat API tests are left out.
- m04: 18 items. The pre-existing CLI tests (ask, etc.) are left out.
- m05: 22 items. Nothing left out.
- f08: 24 items. The test_feedback_service and test_summarize diffs only pass pre-generated message ids, so they add no behavior and are left out. The test_container diff only reflects the paged result shape (covered by item 9).
- f14: 25 items. Nothing left out. The existing test_account_settings tests are unchanged and left out.
- f15: 20 items. The pre-existing qdrant adapter, CLI release and corpus model tests (unchanged) are left out, except the changed snapshot assertion (item 10).
