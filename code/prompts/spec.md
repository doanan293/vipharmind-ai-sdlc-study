Implement the following change in this repository, working in three stages in this order.

1. Design. Before changing any code, write `docs/design.md` covering:
   - Goal: what the change must achieve.
   - Scope: what is included, and what must stay unchanged.
   - Interfaces: the functions, classes, endpoints or schemas that are added or changed, with their signatures.
   - Approach: where the change fits in the existing modules and layers, and the main decisions.
   - Testing: how the change will be shown to work.
2. Plan. From the design, write `docs/plan.md`. Begin with the constraints every part of the work must respect. Then split the work into tasks, each a complete unit that leaves the code working; let the change decide how many tasks there are and how large each one is. For each task, state:
   - Files: the files to create or modify, and the test file.
   - Interfaces: what it uses from earlier tasks and what it provides to later ones.
   - The test that proves the task is done.
3. Implement. Work through the plan one task at a time. For each task, write its test first and run it to see it fail, then write the code until it passes. When all tasks are done, run the backend test suite (from `backend/`, `uv run pytest`) and fix any failures.

Leave `docs/design.md` and `docs/plan.md` in place when you finish.
