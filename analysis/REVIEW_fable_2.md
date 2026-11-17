# Scoped re-review of `analysis/` before tag `prereg-v1-analysis`

Reviewer: Fable 5.2, 2026-11-16. Scope: the fixes to `analysis/REVIEW_fable.md` in commits
`3701bf3`, `f1451b5`, `6ea3b81`, `7cdf1b1` (`analysis/`, `tasks/graded_lines.py`,
`tasks/graded_lines.json`, `prereg/prereg-v1.md` section 11). Only pilot and simulated data were
read. No main result and no `-run*` directory was opened.

## Verdict: FREEZE AFTER FIXES

0 Blocking, 3 Important, 8 Minor.

Both earlier Blocking findings and all six Important findings are fixed, and I found no
regression in the estimators. The three new Important findings are small: two are text and test
changes around the model interval, one is a five-line change in `cli.py`.

Not verified: the fast test suite. I started `pytest -q` twice at `nice 19`; the first run was
killed by the session restart and the second had not finished when this file was written (the
main runs hold the CPU, load average 22–33). Run `uv run pytest -q` once before tagging.

## Earlier findings

| Finding | Status | Evidence |
| --- | --- | --- |
| B1 `graded_src_lines` sensitivity | Fixed | `tasks/graded_lines.py:41-114`, `load.py:63-68, 193`, `mixed.py:254-269`, `report.py:279-280` |
| B2 model interval and singular test | Fixed in mechanism; coverage not yet measured (N1) | `mixed.py:141-236`, `mixed.py:90-98`, `calibration/singular_sd.csv` |
| I1 contrary rule, level-3 cap | Fixed | `estimators.py:238-241`, `tests/test_estimators.py:153, 161-163` |
| I2 overlap reading | Fixed | `prereg-v1.md:450-458` |
| I3 deviations in section 11 | Fixed | `prereg-v1.md:419-449`; `cost_eff_upper` at `report.py:215-219` |
| I4 off-table models | Fixed | `prices.py:29-54`, `load.py:139-141`, `report.py:126-128` |
| I5 stable label ids, sample drawn once | Ids fixed; sample only partly (N2) | `labels.py:18-21, 32-34`, `cli.py:79-83` |
| I6 tests | Fixed, except the coverage criterion (N1) | `tests/test_mixed.py:98-105, 130-149`, `tests/test_estimators.py:166-176` |

Details of what I checked:

- **Cluster bootstrap.** Tasks are drawn with replacement inside each tier in a fixed order from
  one seeded generator (`mixed.py:141-155`). All runs of a drawn task are kept and a repeat
  becomes its own task (`mixed.py:158-169`). The chosen level is refitted per draw, the interval
  is the 2.5–97.5 percentile, and the default is 999 (`mixed.py:41, 207-236`). Replicate `b`
  uses seed `seed + 1 + b` whatever `--jobs` is, and the serial and parallel results are
  compared in a test. The installed statsmodels 0.15.0 accepts `fit_vb(rng=...)`, so the seeded
  fit does not fall through to the exception branch.
- **Singular threshold.** I recomputed the firing rates from `calibration/singular_sd.csv`: 14
  of 20, 9 of 20 and 2 of 20 below 0.30 at true slope SD 0, 0.4 and 0.8. They equal the 70%,
  45% and 10% of README note 2a. The threshold separates 0 from 0.8 and does not separate 0 from
  0.4; the README says so. This is acceptable because the interval no longer depends on the
  random-effects structure being right.
- **`graded_src_lines`.** The script matches the `prereg-v1.1` text clause by clause: lines added
  or changed in `backend/src/**.py` by `base..end` (or `parent..commit`), coverage.py statements,
  run inside a test of the task's hidden test files, `-m "not integration"`, measured at the
  original commit with `--cov-context=test`, empty (import-time) contexts dropped. The grader
  deselects `integration` through the project's `addopts`, so the two runs select the same
  tests. All 23 tasks have a value and `pytest_rc` 0. The values are plausible against v1.1
  (m02 46, m03 46). The second fit uses the same ladder, including level 3 on the graded size.
- **Pooled cohorts.** The rule (mean over the cohorts that have the task) is in README note 22
  and pinned by `test_pooling_with_a_cohort_missing_a_task_averages_the_cohorts_present`. H5 and
  the model use the cohorts complete in all three tiers (`report.py:265-273`).
- **Section 11.** Five entries: engine, interval, threshold and level-3 cap; cohorts of the
  model; codex 272k threshold; Claude cache writes; overlap reading. Each states what had been
  seen. Two rules are still only in the README (N1 and Minor 1).

## Important

### N1. The coverage criterion cannot confirm or reject a 95% interval, and the method's expected coverage is about 88–89%

`tests/test_mixed.py:130-149`, README notes 1 and 2a, `prereg-v1.md:419-434`.

The test passes at 36 or more hits out of 40. Chance of passing, by true coverage:

| True coverage | P(pass, ≥ 36/40) | P(≤ 31/40) |
| --- | --- | --- |
| 95% | 0.95 | 0.00 |
| 89% | 0.55 | 0.03 |
| 85% | 0.26 | 0.14 |
| 80% | 0.08 | 0.41 |
| 75% | 0.02 | 0.70 |

A percentile bootstrap that resamples inside tiers of 15, 5 and 3 tasks undercovers by
construction, because the three large tasks carry most of the leverage on the slope. I simulated
an ordinary linear slope on the real 23 sizes with normal noise (no mixed model involved): the
within-tier percentile interval covered 87.9% at B = 99 (4,000 data sets) and 89.4% at B = 999
(1,500 data sets). So a correct implementation is expected to land near the 88% line, and the
running test is close to a coin flip. A pass would not show 95%, and a fail would not show a bug.

B = 99 in the test against 999 in production is not a problem: fewer resamples lower coverage
by about 1.5 points, so the test is slightly conservative.

This does not block the freeze because the H5 verdict uses only the sign of the coefficient
(`estimators.py:240`), and the primary H5 bootstrap of prereg 9.1 has the same property by
design. The interval is descriptive.

Fix, before the tag:
1. Section 11, engine entry (`prereg-v1.md:419-434`): add one sentence. "Khoảng này là khoảng
   95% danh nghĩa: với 15, 5 và 3 nhiệm vụ mỗi tầng, mô phỏng cho độ phủ thực khoảng 88–90%
   (đo được: k/40). Kết luận H5 chỉ dùng dấu của hệ số, không dùng khoảng này."
2. README note 2a (`README.md:141-145`): replace "was not measured in this session" with the
   observed count, its Wilson interval, and the levels chosen.
3. `tests/test_mixed.py:149`: change the assertion to `hits / n >= 0.80` and keep the printed
   table. At 40 data sets this is a guard against a return to the 65–80% of the old interval,
   not a calibration. For a real measurement, run 120 data sets with seeds 2000–2119 and require
   100 hits (passes 98% of the time at 89% coverage and 2% at 75%).

What to do with the running test, decided here before its result is known:
- **36 or more hits:** record the count as in (1) and (2). Do not claim 95%.
- **32 to 35 hits:** this is the expected range. Record the count, apply (1) to (3), freeze. Do
  not change the method, the seeds or B to obtain a pass.
- **31 or fewer hits:** stop. That happens 3% of the time at 89% coverage. Read the printed rows
  for the level chosen and the misses, check `n_not_converged` and `n_failed`, then re-measure
  on new seeds (2000 onwards). Any change to the method after that goes into section 11 with
  the words "đã xem: kết quả mô phỏng độ phủ".

### N2. `passing_sample.csv` is drawn by the first run of the CLI, whenever that is, and then kept silently

`cli.py:79-83`. README table line 44 and note 20.

The README says the sample is drawn once, after the collection deadline. The code draws it on
the first run that finds no file. An interim run (for example the small tier alone, for H1)
writes a sample without medium or large runs, and every later run keeps it with one INFO line.
The final sample would then break the tier-proportional allocation of prereg 9.10.

Fix: draw only when asked. Add `--draw-passing-sample` and replace `cli.py:79-83` with:

```python
sample_path = out / "passing_sample.csv"
if a.draw_passing_sample:
    if sample_path.exists() and not a.force:
        raise SystemExit(f"{sample_path} exists; --force to redraw")
    passing_sample(valid, a.seed).to_csv(sample_path, index=False)
summary["passing_sample"] = {"drawn": sample_path.exists()}
```

(move the `summary` line after `build_summary`'s result is available; it already is at that
point). Update `test_passing_sample_is_not_redrawn` and `test_outputs_exist` to pass the flag.
Delete `analysis/out/pilot/passing_sample.csv` if it is not meant as the final sample.

### N3. The end-to-end test no longer reaches the "supported" H5 path

`tests/test_end_to_end.py:66-84`.

After the threshold change the synthetic study ends at level 3, so the test now asserts
"inconclusive". No test runs `build_summary` with a logit-scale model and a "supported"
verdict; the pieces are covered only separately (`h5_verdict` unit cases, `fit_h5_model` on
simulated data). A wiring slip at `report.py:275-277`, such as passing the wrong key for
`scale`, would go unnoticed, and this is the line that decides H5.

Fix: add a test that calls `build_summary` on `simulate.main_design(seed=..., beta_int=1.5,
sd1=1.0)` (add the columns the report needs, or monkeypatch `mixed.fit_h5_model` to return
`{"interaction": {"coef": 0.4, "scale": "logit"}, ...}`) and asserts `verdicts["H5"] ==
"supported"` when the primary CI is above 0, and "inconclusive" when the same stub returns
`scale: "difference"`.

## Minor

1. `prereg-v1.md` section 11 has no line for off-table model pricing (`prices.py:47-54`): tokens
   of a named model outside the table are priced at the cohort model's rate and flagged. Add one
   line; seen before the change: nothing.
2. `prices.py:37`: `startswith` accepts any continuation, so a different model whose id extends
   a table id (for example `gpt-6-luna-mini`) is priced as the table row with no flag. Accept a
   prefix match only when the remainder matches `^(-20\d{2,6}|\[.*\]|@.*)$`.
3. `prices.py:41-44`: an empty model string counts as off-table but adds no name to
   `offtable_models`. Treat `""` as `None` in `table_model` and `is_off_table`.
4. `mixed.py:90-98`: the 0.30 threshold was calibrated on the slope SD only, with intercept SD
   0.8, yet it is applied to the intercept SD too (level 2 to level 3). Say so in README note 2.
5. `mixed.py:223-233`: refits that did not converge enter the interval, while on the full data
   non-convergence steps down the ladder. Keep it, and add
   `"share_not_converged": n_not_converged / B` so the report can state it.
6. `cli.py:36-37`: the help says ">= 999" but any value is accepted. Write
   `"reportable": B >= 999` into `h5.mixed_model.interaction.bootstrap`.
7. `labels.py:33-34`: an id collision raises and stops the whole analysis. The chance is about
   1 in 100,000 at 300 failing runs. Acceptable; mention it in README note 19.
8. Cost: README note 2a gives 3–15 s per level-1 refit under load. Two models × 999 refits is
   2 to 8 CPU-hours per analysis run. Run the final analysis with `--jobs` after the main runs
   end, and use a small `--model-bootstrap` for interim runs (flagged by Minor 6).

The ten Minor findings of the first review are all addressed (count of comparisons, README
path, broad exception, rep filter, codex usage records, 2 × 2 cost columns, case study, CPU
window, rater package pointer).
