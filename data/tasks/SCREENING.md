# Screening funnel

Source: ViPharmind `main` at `3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe`.
Command: `uv run sdlc-harness screen --repo <ViPharmind> --ref 3baae61d... --out ../tasks/screening.json --jobs 8`
(about 7 minutes). Per-commit records are in `screening.json`.

| After criterion | Remaining | Rejected |
|---|---|---|
| candidates (feat commits touching backend/src and backend/tests) | 110 | 0 |
| 1. no shared test files | 64 | 46 |
| 4. 30-400 changed src lines | 47 | 17 |
| 5. not rename-only | 47 | 0 |
| 2. fail-to-pass | 43 | 4 |

43 commits remain, above the 30 needed. By layer: infrastructure 18, domain 15, application 6, api 3,
no layer 1 (`4ba674d3`, its src changes are outside `api/application/domain/infrastructure`, recorded with `layer: null`).

## Deviation: criterion 1 rejects 46, not 39

The design-time survey counted 39 because it used a narrower file match. The spec defines a shared test
file as every file under `backend/tests/` whose basename is not `test_*.py` (conftest.py, fakes,
fixtures, data files, `__init__.py`). That definition rejects 46, and the harness follows the spec.
Cost: 7 more commits are excluded from the pool than the design assumed.

## Criterion 2: reasons for the 4 rejections

1. 3 commits (`fa1be07f`, `68edeac5`, `d8cc08ee`): no hidden test is collected at the original commit.
   Their new tests are all marked `integration`, which `addopts` deselects (they need Docker).
2. 1 commit (`e9da8134`): existing tests break once the hidden tests are overlaid
   (`test_tracing.py`, `test_checkpoint_cleanup.py`, `test_checkpointer.py`).

No commit was rejected because a hidden test already passed at the parent.

## Method notes

- Each commit is exported twice (parent, original). The original commit's hidden test files are
  copied over the parent tree. Tests run as `uv sync --frozen` then `uv run --frozen pytest` in `backend/`.
- The lockfile moved: at `3baae61d` `uv.lock` is at the repo root (uv workspace, members backend and
  pharma-lab). `backend/uv.lock` existed only from `1c67209` until `73720d1` (2026-09-14), which
  renamed it to the root `uv.lock`. 34 of the 47 parents that reached criterion 2 predate `73720d1`,
  so the runner looks for `uv.lock` in the tree root first and then `backend/`. Trees with neither
  fall back to the harness interpreter.
- Infrastructure failures (uv sync error, timeout, export error, pytest producing no results) are
  recorded as `failed_criterion: "infra"`, separate from criterion 2 rejections. The run had 0.
