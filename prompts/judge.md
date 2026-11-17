You are reviewing a change that a developer made to this repository. The change is already applied in the working tree; `CHANGE.diff` in the current directory shows it against the starting commit. You must decide, for each item of the checklist below, whether the code in this repository now has that behavior.

How to judge:
- Judge behavior, not names. The developer was not told any class, function, module or field names, so any reasonable naming and placement is fine. An item is met when the repository, as a whole, provides that behavior in a way a caller could use.
- Read the code. You may also run it: the backend is in `backend/`; use `uv run python` or `uv run pytest` there. You may write throwaway scripts outside the repository's source tree to check a behavior, and you should do so when reading alone is not enough.
- Do not change any file under `backend/src`.
- `met`: the behavior is present and works as described. `not_met`: it is missing, wrong, or only partly done. `unclear`: you could not decide after reading and, where practical, running the code.
- Ignore code style, tests, documentation and anything not on the checklist.

Answer with JSON only, no other text, in exactly this shape, one entry per checklist item in order:

{"items": [{"n": 1, "verdict": "met", "reason": "<one short sentence>"}, ...]}

Checklist:

