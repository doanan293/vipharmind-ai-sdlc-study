# Controller decisions on prereg-v1-review-fable.md (2026-11-15), pending An's final approval

- B1: accept Fable's proposal (primary estimand: claude-sonnet, small tier, three-way CI reading rule).
- B2: accept the 7-point constraint block. Freeze numeric selection thresholds in v1 now: medium = 2–3 consecutive commits, 300–700 backend/src lines, ≤20 prompt names; large = consecutive range, ≥750 lines, ≤35 names; both: same plan, backend only, hidden tests fail at base/pass at end, original patch task_pass with no regressions; prefer no t01–t15 commit. Candidate pool = 16 sub-ranges in tasks/feature-feasibility/ranges.json + all 2–3 commit windows inside them. Inclusion is deterministic by these criteria; NO AI runs on any candidate or main task before its tier is frozen. DROP the planned f08 pilot (feature-tier plan Task 3); timeouts are set by rule instead. Add an overlap sensitivity analysis (drop tasks whose commits overlap another tier).
- B3: intention-to-treat primary; per-protocol (spec runs that left docs/design.md and docs/plan.md) as sensitivity.
- B4: accept; harness will implement: grader timeout → status error (rerun); quota/auth retry cap exhausted → status "deferred" (rerun after quota reset, never excluded silently); system-error reruns capped at 2, then excluded and listed; agent timeout = counted as run (graded as is); non-zero agent exit without quota/auth = counted as run (graded as is).
- I1: timeouts small 3600 s, medium 7200 s, large 10800 s; exact command frozen with --jobs 8 --seed 20261115.
- I2: data-collection deadline 2026-11-29 (owner wants ASAP; can be extended only via a logged deviation). Order: all four cohorts run concurrently (separate quotas). A cohort that does not finish all units of a tier by the deadline is excluded from confirmatory tests and reported descriptively; H5 pooling uses only cohorts complete in all tiers.
- I3, I4, I5: accept Fable's texts.
- I6: H1 confirmatory; H5 key secondary; H2–H4 secondary; MI non-inferiority margin −5 (Fable's suggestion).
- I7: price table frozen as of the tag date (list prices recorded in the prereg); cost computed from raw transcripts with cache reads/writes priced separately.
- I8: lock the labeling guide into prereg/ (copy from report branch team/labeling/guide.md) adding the two pilot-proposed labels; soften blinding claim.
- I9, I10, I11: accept.
- I12: analysis code (analysis/ package) committed and tested on pilot data before any main-run result is analysed; main runs may start before that, but no main result is opened for analysis until the analysis code is tagged (prereg-v1-analysis).
- Minors: accept all. M8: date of An's re-approval of t05/t07/t13 = date An approves this prereg.
