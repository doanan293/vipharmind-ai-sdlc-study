# Independent review of `analysis/` before tag `prereg-v1-analysis`

Reviewer: Fable 5.2, 2026-11-15. Scope: `analysis/` (README, `src/sdlc_analysis/`, `tests/`,
`out/pilot/`) against `prereg/prereg-v1.md` sections 6, 7, 9, 10, 11 and `prereg/prereg-v1.1.md`.
Only pilot data and synthetic data were read. No main result was opened.

## Verdict: FREEZE AFTER FIXES

2 Blocking, 6 Important, 10 Minor.

The bootstrap estimators, cohort and tier filters, reading rules, completeness rule, price table,
kappa and the passing-run sample match the prereg. `uv run pytest -q`: 76 passed. The two blockers
are both in H5: one analysis that `prereg-v1.1` requires is missing, and the mixed-model interval
is not a 95% interval.

## What was checked and found correct

| Item | Prereg | Result |
| --- | --- | --- |
| Task-level estimand, one weight per task, spec minus vibe | 9 | `estimators.py:30-50`, correct |
| H1 = `claude-sonnet`, small tier, only if the cell is complete | 9, 10 | `report.py:220-225`, correct |
| B = 10,000, percentile 2.5–97.5, seed 20261115, tasks resampled with all reps | 9.1 | `bootstrap.py:15-18, 54-77`, correct |
| 2 × 2 uses one task-index matrix for both cohorts | 9.1, 9.3 | `estimators.py:128-148`, correct (same seed, same n) |
| Tiers resampled separately for H5 | 9.1, 9.4 | `bootstrap.py:95-116`, correct |
| Cohort pooling: mean over cohorts inside a task, then over tasks | 9 | `estimators.py:79-87`, correct |
| H5 pools only cohorts complete in all three tiers | 10 | `report.py:236`, correct |
| Three-way verdicts, strict bounds, MI margin −5 | 9, 9.5 | `bootstrap.py:119-132`, `report.py:26-33`, correct |
| A task enters only with a valid run in each arm | 10 | `estimators.py:37-44`, correct |
| Completeness: done, or error with 3 attempts | 4, 10 | `load.py:138-143, 269-294`; same rule as `harness/runner.py:256, 798` |
| Price table and the four token types | 7 | `prices.py:19-25` equals the table; Claude 5 m / 1 h split priced separately |
| agy `input_tokens` excludes cache reads | 6 | Confirmed on pilot: cache read > input in 221 of 229 steps |
| codex `input_tokens` includes cached | 6 | `tokens.py:188-210`, correct |
| Cost per pass undefined at 0 passes | 9.6 | `estimators.py:185-189`, correct |
| Sensitivity exclusions, one at a time, H1 and H5 primary | 9.7 | `report.py:51-55, 256-272`, correct |
| Cohen's kappa, cross-table, "lộ cách làm" rate | 9.8 | `labels.py:43-89`, correct |
| Passing sample: 10 per arm, proportional by tier, seed, sorted list | 9.10 | `labels.py:92-124`, correct |

## Blocking

### B1. The `graded_src_lines` sensitivity analysis of `prereg-v1.1` is not implemented

`prereg/prereg-v1.1.md:327-344` requires the mixed model to be re-run with
`log(graded_src_lines)` in place of `log(src_lines)`, with the same fallback ladder. It also
requires the measurement and its code to be committed **before** tag `prereg-v1-analysis`.
`graded_src_lines` appears nowhere in the repo outside that file: not in any `task.toml`, not in
`tasks/feature-feasibility/`, not in `analysis/`.

Fix:
1. Measure `graded_src_lines` for the 23 tasks on the original code only, as the text defines it.
   Commit the script and the values (for example a `graded_src_lines` field in each `task.toml`).
   Record any task that cannot be measured, with the reason.
2. `load.py:36-59`: read the field and add `log_graded_src_lines`.
3. `mixed.py:49-55, 79`: give `fit_h5_model` a parameter for the size column.
4. `report.py:244`: add a second call and store it as `h5.mixed_model_graded`. Tasks without a
   value are dropped from this fit and listed.
5. Add a test with a synthetic study where the two size variables give opposite slopes.

### B2. The mixed-model interval is not a 95% interval, and the fallback for a singular fit cannot trigger

`mixed.py:61-64, 113-116`. README note 1.

I simulated the real design (23 tasks with the real `src_lines`, 4 cohorts, 2 arms, 3 reps, 60
data sets per row) and fitted `fit_h5_model`:

| True interaction | Task SD (intercept, arm) | Coverage of the reported 95% interval | Reported SE (mean) | Actual SD of the estimate |
| --- | --- | --- | --- | --- |
| 0.0 | 0.8, 0.4 | 82% | 0.163 | 0.252 |
| 0.5 | 0.8, 0.4 | 80% | 0.158 | 0.240 |
| 0.0 | 1.5, 1.0 | 65% | 0.176 | 0.321 |
| 0.0 | 0.8, 0.0 | 87% | 0.162 | 0.231 |

The point estimate is close to unbiased (mean −0.01, 0.53, 0.04, −0.03). The reported SE is about
two thirds of the true spread, which is the known behaviour of mean-field variational Bayes. The
prereg asks for the coefficient, its standard error and a 95% interval, so the last two are wrong
as reported.

In the fourth row the true random-slope SD is 0, yet the fitted SD averaged 0.33 and level 1 was
kept in all 60 fits. The N(0, 1) prior on the log SD keeps it away from 0, so the `< 1e-3` test
at `mixed.py:26, 40-45` never fires on a real fit. Fallback 2 of the prereg ("suy biến") is
unreachable except through an exception.

Is note 1 acceptable as a logged deviation? Not as it stands:
- It is logged only in the README. Section 11 of `prereg-v1.md` is the change log and has no line
  for it.
- The sign of the coefficient, which is all the H5 verdict uses, is trustworthy. The interval is
  not.

Fix, in order of preference:
1. Install R and `lme4` and fit `glmer(pass ~ arm * log_src + cohort + (1 + arm | task),
   family = binomial)` through `Rscript` from `mixed.py`. Step down the ladder on a convergence
   message or `isSingular()`. This follows the prereg word for word and removes notes 1 and 2.
   Keep the statsmodels fit as a cross-check.
2. If R cannot be used: add a line to section 11 (seen before the change: nothing). Keep the
   variational point estimate, and replace the interval with a task-level bootstrap of the whole
   fit (resample tasks inside each tier, keep all runs of a task, at least 2,000 resamples, same
   seed, percentile interval). Report "SE" as the bootstrap SD. Replace the singularity test
   with one that can fire, for example a likelihood comparison of level 1 against level 2, or
   state in section 11 that fallback 2 is reached only on a fitting failure.

Either way, add a calibration test on the 23-task design (see I6).

## Important

### I1. H5 "contrary" needs a negative interaction; the prereg does not say so

`estimators.py:235-236`. README note 4.

Prereg 9.4 adds the second condition only to "được ủng hộ". The general rule in section 9 says
"trái với giả thuyết" when the interval lies entirely on the other side. With the code as
written, a primary interval entirely below 0 with a positive coefficient reads "inconclusive",
where the prereg text reads "contrary".

The "supported" half of note 4 is consistent with the prereg: "cùng hướng" as the sign of the
point estimate, plus a primary interval above 0, is the natural reading.

Fix: change line 235 to `if ci_high < 0:` and update the test case
`(-0.5, -0.1, 0.3, "inconclusive")` in `tests/test_estimators.py:153` to `"contrary"`. If the
mirror rule is preferred, it is a change to the reading rule and needs a line in section 11.

Related: when the ladder reaches level 3, the slope is on the difference scale. The prereg's
guard against the ceiling effect needs a logit-scale coefficient, so a level-3 sign cannot
provide it. Fix: at `report.py:246`, if `model["interaction"]["scale"] != "logit"`, cap the
verdict at "inconclusive" for the "supported" branch and say why in `h5`.

### I2. The overlap exclusion disagrees with the text of `prereg-v1.1`

`overlap.py:19-28`, `report.py:267-272`. README note 15.

The code drops f08 and t03 (checked against the ViPharmind repo: the only cross-tier commit
intersection is `c3a88b2659`). `prereg/prereg-v1.1.md:280-281` says "tầng lớn: f08 và f14 thuộc
loại đó". f14 is not dropped, because its `base` is t01's commit and `base..end` excludes it.

The code's reading is the defensible one. m04's `base` is t10's commit in exactly the same way,
and the same sentence of v1.1 says no medium task is in the class. So the v1.1 sentence
contradicts itself. The choice matters: dropping f14 too would leave f15 as the only large task.

Fix: decide before unblinding and write it in section 11: "a task's commits are `base..end`,
`base` excluded; f14 and m04 are therefore not dropped; the parenthesis in v1.1 is corrected to
f08 only". No code change if that reading is kept.

### I3. Forced deviations are recorded only in the README

Section 11 must hold every change after the tag. These need a line each (seen before the change:
nothing), in addition to B2 and I2:
- Note 11, codex: the per-call 272,000-token threshold of section 7 cannot be applied, because
  codex reports one usage record per run (pilot: one `turn.completed` with 428,199 input tokens
  over many calls). `cost_usd` is therefore a lower bound for codex. Also add
  `cost_eff.codex-luna.*` computed on `cost_usd_upper`, so the report can show both bounds.
- Note 3: the mixed model uses the cohorts complete in all three tiers, where 9.4 says "mọi lượt
  hợp lệ của ba tầng". Acceptable given section 10, but it is a narrowing.
- Note 11, Claude cache writes without a 5 m / 1 h split priced at the 1 h rate.

### I4. Tokens of a model outside the price table are priced silently at the cohort's rate

`prices.py:29-35`. README note 11.

Under R11 the tools run their default agents with web tools. Claude Code can use a smaller model
for sub-tasks. Those tokens would be priced at the Sonnet or Opus rate with no flag. The pilot
cannot show this (it ran the older configuration, and only the cohort model appears).

A dated or suffixed id (for example `claude-sonnet-5-5-<date>` or `…[1m]`) also fails the exact
match, so a Sonnet sub-agent inside an Opus run would be priced as Opus.

Fix: in `price_for`, match on prefix (`next(k for k in PRICES if model.startswith(k))`) before
falling back. In `load.py:100-126` add `tok_offtable` (tokens priced by fallback) and a boolean
`cost_has_offtable_model`. Report the count per cohort and arm in `descriptives`.

### I5. Re-running the analysis overwrites the labeling key with new ids

`labels.py:17-40`, `cli.py:66-71`.

Ids come from a generator seeded once and consumed in order over the current set of failing
runs. When more runs finish (the medium and large tiers run later), every id changes and
`key-PRIVATE.csv` is overwritten. Sheets already filled can no longer be decoded. The same holds
for `passing_sample.csv`: it changes whenever the set of passing runs changes.

Fix: derive each id from the unit, for example
`"u" + sha256(f"{seed}:{unit}").hexdigest()[:8]`, and keep the seeded shuffle for the order
only. Then ids are stable across runs. For the passing sample, write in the README that it is
drawn once, after the collection deadline, and refuse to overwrite an existing
`passing_sample.csv` unless `--force` is given.

### I6. The tests do not pin the mixed model or uneven pooling

- `tests/test_mixed.py:34-48`: 60 tasks, one seed, tolerance ±0.45, and "the interval covers the
  truth" once. This would not catch B2. Add a test on the 23-task design with at least 40
  simulated data sets that requires coverage of at least 88%.
- No real fit reaches the singular branch. Add a test with a true random-slope SD of 0 that
  requires the ladder to step down, once the criterion can fire.
- `estimators.py:87` (`skipna=True`): a task with a difference in only some cohorts is averaged
  over those cohorts. No test covers it. Add one, and say in the README that this is the rule.
- The rest is pinned well. Sign flips are caught (H1 = +1/3, H5 = +2/3, H2, H3a, H3b and H3c
  verdicts in `test_end_to_end.py`). Run-level averaging in place of task-level is caught by the
  sensitivity values 16/45 and 29/90. Shared resampling is caught by
  `test_two_by_two_joint_resampling_cancels_shared_task_noise`. Claude pricing is checked
  against Claude Code's own `costUSD` on 24 pilot runs.

## Minor

1. `report.py:287`: `n_secondary_comparisons` counts `pass_diff.claude-sonnet.small`, which is
   H1 itself. Subtract it when H1 is estimable. The count also leaves out `h5.hidden_pass_rate`,
   the sensitivity re-runs and the cost comparisons; say so in the README or count them.
2. `README.md:4`: refers to `prereg/prereg-v1.1-draft.md`, which no longer exists. Change to
   `prereg/prereg-v1.1.md`.
3. `mixed.py:103`: only `LinAlgError`, `ValueError` and `FloatingPointError` are caught. Any
   other error stops the whole analysis. Catch `Exception` and record the type in `reason`.
4. `report.py:144`: a unit with `rep` above `--reps` is outside the design but still analysed.
   Filter on `rep <= reps` and list such units in `ignored_units_outside_design`.
5. `tokens.py:188-210`: several `turn.completed` events are summed. If codex ever reports
   cumulative usage, this double counts. The pilot has one event per run. Add a descriptive
   count of runs with more than one.
6. `estimators.py:126-127, 150`: the Sonnet-spec against Opus-vibe cost comparison drops a task
   when the unused arm has no cost. Build the two columns from `cell_means` directly.
7. Prereg 9.9: the rule that picks the qualitative case (large tier; largest original patch if
   every Sonnet difference is 0) is not computed. Add `case_study.task_id` to `summary.json`.
8. `prereg-v1.1.md` operational note: the report must check timeouts in the 19:16–19:52 window
   of 2026-11-15. `started_at` is loaded but no count is produced. Add it to `descriptives`.
9. Prereg 9.8: the rater package (prompt, patch without `docs/design.md` and `docs/plan.md`,
   test log) is not built by this package. Say in the README which tool builds it.
10. Notes 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 17, 18, 20, 21, 22: acceptable as written.

## Interpretation notes: summary

| Note | Judgment |
| --- | --- |
| 1 | Should change. See B2 |
| 2 | Should change. The singularity test cannot fire. See B2 |
| 3 | Acceptable. Log in section 11 (I3) |
| 4 | "Supported" half is consistent with the prereg. "Contrary" half and the level-3 case should change. See I1 |
| 5–10 | Acceptable |
| 11 | Acceptable after I3 (codex threshold, section 11) and I4 (off-table models) |
| 12–14 | Acceptable |
| 15 | Acceptable reading. It conflicts with one sentence of v1.1, which must be settled in section 11. See I2 |
| 16–18 | Acceptable |
| 19 | Should change: ids must be stable across runs. See I5 |
| 20 | Acceptable. Draw once after the deadline (I5) |
| 21–22 | Acceptable |
