# sdlc-analysis

The preregistered analysis of the spec-vs-vibe experiment: `prereg/prereg-v1.md` sections 6, 7, 9
and 10, with tiers as in `prereg/prereg-v1.1-draft.md`. It reads the harness's raw results and
writes the numbers the report reads (`summary.json`, see
`docs/superpowers/specs/2026-11-15-report-and-presentation-design.md` §5.5). The report scripts only
format these numbers. They do not compute statistics.

```
cd analysis
uv sync
uv run pytest -q
uv run sdlc-analysis --results ../results/raw/main --tasks ../tasks --out ../results/analysis \
    --seed 20261115 --repo /home/andv/personal/vipharmind \
    [--labels sheet-loi.csv sheet-bao.csv]
```

Pilot run (committed under `out/pilot/`). Pilot tasks are left out unless named:

```
uv run sdlc-analysis --results ../results/raw/pilot --tasks ../tasks --task-ids p01,p02 \
    --out out/pilot --seed 20261115
```

Options: `--bootstrap B` (default 10000), `--cohorts` (default: the four prereg cohorts),
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
| `passing_sample.csv` | The 20 passing runs for An's "passes tests but wrong" check (9.10) |
| `labeling/sheet-template.csv` | Blank labeling sheet: every valid failing run of the two Claude cohorts, under random ids, in shuffled order |
| `labeling/key-PRIVATE.csv` | Maps ids to units. Do not give it to the raters |
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
| `h5.primary`, `h5.hidden_pass_rate` | 9.4 (the model is under `h5.mixed_model`) |
| `secondary.<metric>.<cohort>.<tier>` | 9.5 and the section 6 metrics |
| `cost_eff.<cohort>.<tier>.<arm or diff>.{passes_per_usd,cost_per_pass}` | 9.6 |
| `sensitivity.{upstream_urls,pytest_config_touched,spec_noncompliant}.{h1,h5}`, `sensitivity.overlap.h5` | 9.7 |
| `exploratory.size_group.<cohort>.<group>` | 9.4: size groups inside the small tier (exploratory) |
| `variability.<cohort>.<tier>`, `variability.all_complete` | 9.1: share of cells whose reps disagree |

`verdicts` uses the prereg reading rule: `supported`, `contrary`, `inconclusive`, or
`not_estimable` / `no_confirmatory_test`. The keys are `H1`, `pass_diff.*`, `H2.*`, `H3a.*`,
`H3b.*`, `H3c.*`, `H4.<tier>` and `H5`. `meta.n_secondary_comparisons` counts every verdict
except H1. `labels` holds the kappa report when `--labels` is given.

## Interpretation notes

These are places where the prereg text left a choice open, or where the implementation could
not follow it word for word. Each note says what the code does.

1. **Mixed model engine (9.4).** The prereg names `lme4::glmer` in R. R is not installed here,
   so the model uses statsmodels `BinomialBayesMixedGLM`, fitted by variational Bayes.
   statsmodels fits only independent variance components. It cannot fit level 0
   (`(1 + arm | task)` with correlated effects). The ladder therefore records level 0 as "not
   available" and starts at level 1 (`(1 | task) + (0 + arm | task)`, prereg fallback 1), then
   level 2 (`(1 | task)`), then level 3 (OLS of each task's cohort-mean difference on
   `log(src_lines)`). The interval is the posterior mean ± 1.96 posterior SD. It is not a Wald
   interval from maximum likelihood. Priors: fixed effects N(0, 10²), which is weak and close to
   glmer's likelihood fit. Each log random-effect SD uses the statsmodels default prior,
   N(0, 1).
2. **Non-convergence and degeneracy.** A level fails if statsmodels raises a
   `ConvergenceWarning`, if fitting throws an exception, if any estimate is non-finite, or if a
   random-effect SD falls below 1e-3 (a singular fit).
3. **Model details.** `arm` is coded spec = 1. `log(src_lines)` is centred on its mean over
   tasks; this does not change the interaction coefficient. `cohort` is a fixed effect. The data
   are the valid runs of the cohorts used by the H5 primary test (complete in all three tiers),
   not every valid run regardless of completeness, so that both H5 tests use the same cohorts.
4. **H5 verdict.** "Supported" requires the primary CI to lie entirely above 0 and the
   interaction point estimate to be positive. "Cùng hướng" is read as the sign of the point
   estimate. "Contrary" is the mirror case: CI entirely below 0 and a negative coefficient.
   Anything else is "inconclusive". If the ladder falls to level 3, the slope is on the
   difference scale, not the logit scale. Its sign is still used, and `interaction.scale` says
   which scale applies.
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
    - Tokens of a model not in the price table (for example a subagent on another model) are
      priced at the cohort model's rate.
    - agy: `input_tokens` excludes cache reads, which are reported separately. `output_tokens`
      is read as including thinking tokens. In the pilot, thinking ≤ output on every one of 229
      steps, and `total_tokens` = input + output.
    - Gemini and OpenAI charge no cache-write fee, so cache-write tokens are priced as plain
      input. Both tools report 0 cache writes anyway.
    - codex: `input_tokens` includes `cached_input_tokens`. codex reports one aggregated usage
      per run, so the per-call 272,000-token threshold cannot be applied call by call.
      `cost_usd` uses the ≤ 272k price. `cost_usd_upper` in the runs table prices every call at
      the > 272k rate as a bound.
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
15. **Overlap sensitivity (constraint 7, 9.7).** A range task's commits are
    `git rev-list base..end`, so its `base` commit is not part of it. Two tasks of different
    tiers overlap when their commit sets intersect, and both are dropped: the relation is
    symmetric, since each has a commit lying in the other. Overlap in hidden-test files does not
    cause a drop. With the current `tasks/` and the ViPharmind repo, the only overlap is
    f08–t03 (commit `c3a88b2659`). F14's `base` is t01's commit, so t01's change is not inside
    F14. The analysis needs `--repo`; without it, `sensitivity.overlap.h5` is absent and
    `overlap` is `null`.
16. **Spec compliance (2)** is the grader's `process_artifacts` (design and plan both present).
    "Vibe runs that wrote a design or plan file" is read from `patch.diff`: either file counts.
    The both-files `process_artifacts` is reported for vibe runs too.
17. **pytest in the transcript (2)** means `\bpytest\b` appears in a shell command the agent ran
    (tool-call inputs only, never tool output).
18. **Sensitivity scope (9.7).** Each exclusion re-runs H1's primary test and H5's primary test
    and nothing else. The overlap exclusion is H5 only.
19. **Labeling (9.8).** Ids and order come from the seeded generator, so the key can be
    regenerated from code and seed. Keep the key private. Runs that hit the time limit start
    with `het_gio` in `note`, as the labeling guide requires. Kappa uses units labeled by both
    raters. The "arm revealed" rate is the case-insensitive substring `lộ cách làm` in either
    rater's note. Labels outside the locked set of 9 are listed in `invalid_labels`.
20. **Passing-run sample (9.10).** Within each arm, the 10 runs are allocated to tiers in
    proportion to that arm's passing runs per tier, by largest remainder, with ties going to the
    smaller tier first. One generator draws spec then vibe, small to large, from the list sorted
    by (cohort, task, arm, rep).
21. **Exploratory size groups** (≤ 82, 83–173, ≥ 174 lines) are computed for each cohort
    complete in the small tier.
22. **Pilot data** comes from the older harness. Its `meta.json` has no `upstream_urls`, which
    is treated as empty and counted under `descriptives.upstream_urls_field_missing`. Pilot
    tasks have `pilot = true`, so the pilot run names them with `--task-ids p01,p02`.
