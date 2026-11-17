# sdlc-analysis

The preregistered analysis of the spec-vs-vibe experiment: `docs/prereg/prereg-v1.md` sections 6, 7, 9
and 10, with tiers and the graded-lines sensitivity analysis as in `docs/prereg/prereg-v1.1.md`. It reads the harness's raw results and
writes the numbers the report reads (`summary.json`, see
`docs/superpowers/specs/2026-11-15-report-and-presentation-design.md` §5.5). The report scripts only
format these numbers. They do not compute statistics.

```
cd analysis
uv sync
uv run pytest -q
uv run sdlc-analysis --results ../results/raw/main ../results/raw/main-tiers --tasks ../tasks \
    --out ../results/analysis --seed 20261115 --repo /home/andv/personal/vipharmind \
    --model-bootstrap 999 --jobs 4 [--labels sheet-loi.csv sheet-bao.csv]
```

Pilot run (committed under `out/pilot/`). Pilot tasks are left out unless named:

```
uv run sdlc-analysis --results ../results/raw/pilot --tasks ../tasks --task-ids p01,p02 \
    --out out/pilot --seed 20261115
```

`--results` takes several roots: the small tier runs into `data/results/raw/main`, the medium and large
tiers into `data/results/raw/main-tiers` (prereg-v1.1); a unit found in two roots is an error.

Options: `--bootstrap B` (default 10000), `--model-bootstrap` (cluster-bootstrap refits of the H5
mixed model, default 999; each refit takes 1-5 s, so use `--jobs`), `--jobs` (processes for those
refits), `--force` (redraw an existing `passing_sample.csv`), `--cohorts` (default: the four prereg cohorts),
`--reps` (default 3), `--task-ids` (default: every task with `pilot = false`), `--repo` (the
ViPharmind git repo, needed for the H5 overlap sensitivity analysis), `--labels A B` (two filled
labeling sheets, for Cohen's kappa).

## Outputs (`--out`)

| File | Content |
| --- | --- |
| `summary.json` | Every estimate with its 95% CI, keyed by stable names, plus verdicts, completeness, the H5 model and descriptives |
| `runs.csv`, `runs.parquet` | Tidy table, one row per unit directory: status, grade metrics, the four token types, converted cost, flags |
| `task_diffs.csv` | Per (cohort, tier, task) pass-rate difference. This is the per-task table the prereg asks for when a tier has fewer than 6 tasks |
| `pooled_task_diffs.csv` | Per task: the mean difference over the cohorts complete in that tier |
| `task_cells.csv` | Per (cohort, tier, task, arm): valid reps, pass rate, hidden-test pass rate |
| `passing_sample.csv` | The 20 passing runs for An's "passes tests but wrong" check (9.10). Drawn once, after the collection deadline: an existing file is kept unless `--force` is given |
| `labeling/sheet-template.csv` | Blank labeling sheet: every valid failing run of the two Claude cohorts, under random ids, in shuffled order |
| `labeling/key-PRIVATE.csv` | Maps ids to units. Do not give it to the raters |

The rater packages of 9.8 (prompt, patch without `docs/design.md` and `docs/plan.md`, test log,
per id) are not built by this package, and no tool in the repo builds them yet. They are built
from `labeling/key-PRIVATE.csv` and the unit directories it names.
| `figures/*.pdf, *.png` | `effect_vs_size`, `pass_diff_by_cohort`, `two_by_two_<tier>`, `cost_per_pass` |

### Keys in `summary.json` → `estimates`

Each estimate has `estimate`, `ci_low`, `ci_high`, `n_tasks`, `B`, `seed`, `ci_type` and
`n_undefined`, plus extra fields where relevant (`mean_spec`, `mean_vibe`, `n_null_runs`,
`reference_only` when a tier has fewer than 6 tasks).

| Key | Prereg |
| --- | --- |
| `h1.primary` | 9 H1: `claude-sonnet`, small tier (`null` if that cell is incomplete) |
| `pass_diff.<cohort>.<tier>` | 9.1, 9.2: H1 format for every complete (cohort, tier) |
| `descriptive_incomplete.<cohort>.<tier>` | 10: incomplete cells, descriptive only |
| `pooled.pass_diff.<tier>` | Cohorts pooled per task (summary figure) |
| `h4.<tier>.rate.<cohort>.<arm>`, `h4.<tier>.diff.<cohort>`, `h4.<tier>.diff_of_diffs`, `h4.<tier>.sonnet_spec_minus_opus_vibe.{pass,cost_usd}`, `h4.<tier>.sonnet_spec_over_opus_vibe.cost_ratio` | 9.3 |
| `h5.primary`, `h5.hidden_pass_rate` | 9.4 (the model is under `h5.mixed_model`; the `graded_src_lines` sensitivity of prereg-v1.1 under `h5.mixed_model_graded`) |
| `secondary.<metric>.<cohort>.<tier>` | 9.5 and the section 6 metrics |
| `cost_eff.<cohort>.<tier>.<arm or diff>.{passes_per_usd,cost_per_pass}` | 9.6 |
| `cost_eff_upper.codex-luna.<tier>.…` | 9.6 for codex with every call at the > 272k price (upper bound; note 11) |
| `sensitivity.{upstream_urls,pytest_config_touched,spec_noncompliant}.{h1,h5}`, `sensitivity.overlap.h5` | 9.7 |
| `exploratory.size_group.<cohort>.<group>` | 9.4: size groups inside the small tier (exploratory) |
| `variability.<cohort>.<tier>`, `variability.all_complete` | 9.1: share of cells whose reps disagree |

Outside `estimates`: `case_study` (9.9: the task and the two runs picked by the design's rule),
`descriptives` (timeouts, exits, compliance, tool versions, prompt hash check, off-table model
tokens, codex runs with several usage records, runs started in the shared-CPU window of the
prereg-v1.1 operational note), `completeness`, `not_run_units`.

`verdicts` uses the prereg reading rule: `supported`, `contrary`, `inconclusive`, or
`not_estimable` / `no_confirmatory_test`. The keys are `H1`, `pass_diff.*`, `H2.*`, `H3a.*`,
`H3b.*`, `H3c.*`, `H4.<tier>` and `H5`. `meta.n_secondary_comparisons` counts every verdict
except H1 and its own copy `pass_diff.claude-sonnet.small`: the per-cohort pass differences, the
H2/H3 tests, H4 per tier and H5. Estimates without a direction (descriptive secondary metrics,
`h5.hidden_pass_rate`, sensitivity re-runs, cost-effectiveness, exploratory size groups) are not
counted as comparisons. `labels` holds the kappa report when `--labels` is given.

## Interpretation notes

These are places where the prereg text left a choice open, or where the implementation could
not follow it word for word. Each note says what the code does.

1. **Mixed model engine and interval (9.4; prereg section 11).** The prereg names
   `lme4::glmer` in R. R is not installed here, so the model uses statsmodels
   `BinomialBayesMixedGLM`, fitted by variational Bayes (fixed-effect prior N(0, 10²), close to a
   likelihood fit; statsmodels' default N(0, 1) prior on each log random-effect SD; the random
   starting values are seeded, so fits are reproducible). statsmodels fits only independent
   variance components, so level 0 (`(1 + arm | task)` with correlated effects) is recorded as
   "not available" and the ladder starts at level 1 (`(1 | task) + (0 + arm | task)`, prereg
   fallback 1), then level 2 (`(1 | task)`), then level 3 (OLS of each task's cohort-mean
   difference on the log size). The point estimate is the posterior mean of the interaction.
   **The interval is a cluster bootstrap of the whole fit**: tasks are resampled with replacement
   inside each tier (all runs of a drawn task kept; a task drawn twice enters as two tasks), the
   level chosen on the full data is refitted on each resample (default 999 resamples, seed
   20261115, resample b fitted with seed 20261116 + b), the interval is the 2.5–97.5 percentile,
   and "SE" is the SD of the resampled coefficients. Failed and non-converged refits are counted
   (`bootstrap.n_failed`, `n_not_converged`); failed ones are left out. The variational posterior
   SD is kept as `vb_posterior_sd` for reference only: on the 23-task design it understated the
   spread of the estimate by about a third (review B2: 65–87% coverage of the old ±1.96 SD
   interval). The slow test `test_interval_coverage_on_the_23_task_design`
   (`SDLC_SLOW_TESTS=1`) checks coverage of the bootstrap interval; see note 2a for its status.
2. **Non-convergence and degeneracy.** A level fails if statsmodels raises a
   `ConvergenceWarning`, if fitting throws any exception (the type is recorded), if an estimate is
   non-finite, or if it is singular: a variance component's posterior-mean SD below **0.30**. The
   old criterion (SD < 1e-3) could never fire, because the N(0, 1) prior on the log-SD keeps a
   variational SD near 0.2–0.3 when the true SD is 0. The threshold comes from
   `calibration/singular_sd.py` (output `calibration/singular_sd.csv`): on the 23-task design,
   20 simulated data sets per true random-slope SD, the fitted slope SD is below 0.30 in most
   data sets with true SD 0 and in few with true SD 0.8 (the exact rates are printed by the
   script and listed in note 2a). The design cannot tell a slope SD of 0 from 0.4, so the
   criterion behaves like lme4's `isSingular` would: a small slope variance is often reported as
   singular. Two other criteria were tried and rejected: the variational ELBO of level 2 was
   higher than level 1's in every simulated data set, whatever the true slope SD (the
   mean-field penalty for 23 extra effects dominates), and the posterior mode (`fit_map`)
   collapses the slope SD to about 1e-10 in every data set.
2a. **Calibration results** (`calibration/singular_sd.py`, 20 data sets per row, the 23-task
   design with its real sizes and tiers, interaction 0, intercept SD 0.8). Share of data sets in
   which level 1 is declared singular:

   | Threshold on the fitted slope SD | True slope SD 0 | 0.4 | 0.8 |
   | --- | --- | --- | --- |
   | 0.25 | 30% | 10% | 0% |
   | **0.30 (used)** | **70%** | **45%** | **10%** |
   | 0.35 | 90% | 80% | 20% |
   | 0.40 | 90% | 85% | 40% |

   Fitted slope SD, median (min–max): 0.27 (0.23–0.44) at true SD 0; 0.31 (0.23–0.71) at 0.4;
   0.51 (0.25–1.00) at 0.8. 0.30 fires in most data sets without slope variation while keeping
   level 1 in 90% of data sets with a clear slope SD (0.8). ELBO(level 2) ≥ ELBO(level 1) in
   60 of 60 data sets, which is why the ELBO is not used.

   **Coverage of the bootstrap interval was not measured in this session.** The slow test
   `test_interval_coverage_on_the_23_task_design` (40 data sets × 99 refits; a level-1 refit takes
   3–15 s on this machine while the main runs share the CPU) needs several CPU-hours. Run it
   before relying on the interval: `SDLC_SLOW_TESTS=1 SDLC_COVERAGE_JOBS=8 uv run pytest
   tests/test_mixed.py -k coverage -s`.
3. **Model details.** `arm` is coded spec = 1. The log size is centred on its mean over tasks;
   this does not change the interaction coefficient. `cohort` is a fixed effect. The data are the
   valid runs of the cohorts used by the H5 primary test (complete in all three tiers), not every
   valid run regardless of completeness, so that both H5 tests use the same cohorts (prereg
   section 11). The `graded_src_lines` sensitivity analysis (prereg-v1.1) fits the same ladder,
   bootstrap included, with `log(graded_src_lines)` (`data/tasks/graded_lines.json`, measured by
   `data/tasks/graded_lines.py`); tasks without a value are dropped and listed in
   `tasks_without_size`.
4. **H5 verdict.** "Supported" requires the primary CI to lie entirely above 0 and the logit-scale
   interaction point estimate to be positive ("cùng hướng" read as the sign of the point
   estimate). If the ladder falls to level 3, the slope is on the difference scale and cannot
   provide the logit-scale guard against the ceiling effect, so H5 cannot be "supported" (it
   reads "inconclusive"). "Contrary" follows the general rule of section 9: the primary CI lies
   entirely below 0, with no condition on the interaction.
5. **Reading rule bounds.** "Entirely on one side" is read strictly. A CI with a bound exactly
   at 0 (or at the −5 MI margin) is "inconclusive". This matters at small n: in the pilot,
   Sonnet's CI is [−1/3, 0].
6. **Non-inferiority (H3c).** The verdict is "supported" when the CI's lower bound is above −5
   MI points, "contrary" when its upper bound is below −5, and "inconclusive" otherwise.
7. **Random number generation.** Every estimate starts its own `numpy.random.default_rng(seed)`,
   so no result depends on the order in which estimates are computed. Joint resampling (2 × 2,
   cost-effectiveness arms, cohort pooling) uses one task-index matrix for all columns. For
   tier comparisons, one generator first draws the higher tier's resamples, then the lower
   tier's. The interval is `numpy.percentile` at 2.5 and 97.5 with linear interpolation.
8. **Null metric values (9.5).** A run with an empty value is dropped from that metric only. A
   task enters a metric when each arm has at least one valid run with a value. Each estimate
   reports the number of dropped runs as `n_null_runs`.
9. **Completeness (10).** The design is cohorts × tasks × 2 arms × reps. A missing unit
   directory counts as not run. `quota`, `auth`, `deferred` and `error` with reruns left all count
   as pending. A cell is complete when every unit is `done` or `error` with
   `error_attempts >= 3` (the harness's `excluded`). Completeness is fixed on the full data and
   is not re-evaluated inside sensitivity analyses. Incomplete cells are reported only
   descriptively, with run-level pass rates per arm and the number of runs not yet run.
10. **Variability (9.1).** The denominator is the cells with at least 2 valid reps, since a
    single rep cannot disagree. Cells with only one valid rep are counted separately.
11. **Token types and cost (6, 7).**
    - Claude: counts come per model from the `modelUsage` of the `result` event, with cache
      writes split 5 m / 1 h. The computed cost equals Claude Code's own list-price `costUSD` on
      all 24 pilot Claude runs (`tests/test_pilot.py`). If there is no `result` event (a stopped
      run), the code sums assistant messages, counting each message id once. Cache writes
      without a 5 m / 1 h split are priced at the 1 h rate, the upper bound.
    - A served model id is matched to the price table exactly, else by the longest table id it
      starts with (dated or suffixed ids such as `claude-sonnet-5-5-20261101` or
      `claude-opus-5-5[1m]`), so a Sonnet sub-agent inside an Opus run is priced as Sonnet. Tokens
      of a named model that matches no row are priced at the cohort model's rate and flagged:
      `tok_offtable`, `cost_has_offtable_model` and `offtable_models` per run, counted per cohort
      and arm in `descriptives.offtable_model_cost`. Unnamed models (codex) are the cohort model.
    - agy: `input_tokens` excludes cache reads, which are reported separately. `output_tokens`
      is read as including thinking tokens. In the pilot, thinking ≤ output on every one of 229
      steps, and `total_tokens` = input + output.
    - Gemini and OpenAI charge no cache-write fee, so cache-write tokens are priced as plain
      input. Both tools report 0 cache writes anyway.
    - codex: `input_tokens` includes `cached_input_tokens`. codex reports one aggregated usage
      per run, so the per-call 272,000-token threshold cannot be applied call by call.
      `cost_usd` uses the ≤ 272k price, so it is a lower bound for codex. `cost_usd_upper` prices
      every call at the > 272k rate, the upper bound, and `cost_eff_upper.codex-luna.*` repeats
      the cost-effectiveness analysis on it (prereg section 11). Codex runs with more than one
      usage record (summed; a cumulative report would double count) are counted in
      `descriptives.codex_runs_with_several_usage_records`; the pilot has one per run.
    - A run without parseable token counts falls back to `meta.usage`. Those tokens are
      unsplit, all input is priced as plain input, and the run is flagged as an upper bound
      (`tokens_split = false`). A run with no counts at all has no cost and is counted
      (`runs_without_cost`).
12. **H2 total tokens** is input (uncached + cache read + cache write) plus output, where output
    includes reasoning tokens.
13. **Cost-effectiveness (9.6).** Both measures are ratios of sums over the valid runs with a
    known cost in a (cohort, tier, arm). Both arms share the resampled tasks, which allows the
    spec − vibe difference to be reported as well. Cost per pass with 0 passes is `null`.
    Resamples where it is undefined are left out of the interval and counted in `n_undefined`.
    Only complete cells get CIs.
14. **2 × 2 (9.3).** It is computed for every tier where both Claude cohorts are complete,
    using the tasks present in both. Sonnet-spec vs Opus-vibe cost is the mean over tasks of the
    per-run cost, reported both as a difference and as a ratio.
15. **Overlap sensitivity (constraint 7, 9.7; prereg section 11).** A range task's commits are
    `git rev-list base..end`, so its `base` commit is not part of it. Two tasks of different
    tiers overlap when their commit sets intersect, and both are dropped: the relation is
    symmetric, since each has a commit lying in the other. Overlap in hidden-test files does not
    cause a drop. With the current `data/tasks/` and the ViPharmind repo, the only overlap is
    f08–t03 (commit `c3a88b2659`). F14's `base` is t01's commit, so t01's change is not inside
    F14, and m04's `base` is t10's commit in the same way, so neither is dropped. The parenthesis
    "f08 và f14" in prereg-v1.1 is corrected to f08 in section 11. The analysis needs `--repo`; without it, `sensitivity.overlap.h5` is absent and
    `overlap` is `null`.
16. **Spec compliance (2)** is the grader's `process_artifacts` (design and plan both present).
    "Vibe runs that wrote a design or plan file" is read from `patch.diff`: either file counts.
    The both-files `process_artifacts` is reported for vibe runs too.
17. **pytest in the transcript (2)** means `\bpytest\b` appears in a shell command the agent ran
    (tool-call inputs only, never tool output).
18. **Sensitivity scope (9.7).** Each exclusion re-runs H1's primary test and H5's primary test
    and nothing else. The overlap exclusion is H5 only.
19. **Labeling (9.8).** Each id is `u` + the first 8 hex digits of `sha256("<seed>:<unit>")`, so
    a unit keeps its id when more runs finish and filled sheets stay decodable; the row order is
    a seeded shuffle. The key can be rebuilt from code and seed, so keep it private. Runs that
    hit the time limit start with `het_gio` in `note`, as the labeling guide requires. Kappa uses
    units labeled by both raters. The "arm revealed" rate is the case-insensitive substring
    `lộ cách làm` in either rater's note. Labels outside the locked set of 9 are listed in
    `invalid_labels`.
20. **Passing-run sample (9.10).** Within each arm, the 10 runs are allocated to tiers in
    proportion to that arm's passing runs per tier, by largest remainder, with ties going to the
    smaller tier first. One generator draws spec then vibe, small to large, from the list sorted
    by (cohort, task, arm, rep). The sample depends on the set of passing runs, so it is drawn
    once, after the collection deadline; the CLI keeps an existing file unless `--force`.
21. **Exploratory size groups** (≤ 82, 83–173, ≥ 174 lines) are computed for each cohort
    complete in the small tier.
22. **Cohort pooling with a missing cohort.** A task's pooled difference is the mean over the
    cohorts that have a difference for it (a cohort without a valid run in one arm of that task
    is left out of that task's mean), each present cohort one weight.
23. **Design filter.** Units of a cohort or task outside the design, or with a rep above
    `--reps`, are not analysed and are listed in `meta.ignored_units_outside_design`.
24. **Case study (9.9)** follows the design's rule (spec-vs-vibe design 7.5): `claude-sonnet`,
    large tier, the task with the largest |pass-rate difference| (ties: larger original patch;
    all 0: largest patch); in it, the lowest-rep run of each arm, or, when the arms differ, the
    lowest-rep passing run of the better arm and the lowest-rep failing run of the other.
25. **Shared-CPU window.** The prereg-v1.1 operational note asks for a check of runs started
    19:16–19:52 local time (UTC+7) on 2026-11-15: `descriptives.shared_cpu_window` counts runs
    started then and their timeouts, per cohort. The prereg section 11 entry of 19:58 (medium
    and large tiers run alongside the small tier) asks for timeouts inside vs outside that
    window: `descriptives.concurrent_tiers_window`, from 19:58 local until the last small-tier
    run ended (its `started_at` plus `wall_s`), by tier and arm.
26. **Pilot data** comes from the older harness. Its `meta.json` has no `upstream_urls`, which
    is treated as empty and counted under `descriptives.upstream_urls_field_missing`. Pilot
    tasks have `pilot = true`, so the pilot run names them with `--task-ids p01,p02`.
