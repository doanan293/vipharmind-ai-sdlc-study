import numpy as np
import pytest
import synthetic as syn

from sdlc_analysis.estimators import (
    cell_means,
    cost_effectiveness,
    h5_verdict,
    paired_diff,
    pooled_diff,
    pooled_task_diffs,
    task_diffs,
    tier_diff,
    two_by_two,
    variability,
)

B = 2000


def valid(runs):
    return runs[runs["valid"]]


def test_cell_means_average_valid_reps(study):
    runs = valid(study[3])
    cm = cell_means(runs, "task_pass").set_index(["cohort", "task_id", "arm"])
    assert cm.loc[("claude-sonnet", "t01", "spec"), "mean"] == pytest.approx(2 / 3)
    # the excluded error leaves 2 valid reps, both failing
    row = cm.loc[("claude-sonnet", "f01", "vibe")]
    assert row["mean"] == 0 and row["n"] == 2


def test_h1_estimate_recovers_known_difference(study):
    runs = valid(study[3])
    est = paired_diff(runs, "claude-sonnet", "small", "task_pass", B=B)
    assert est.estimate == pytest.approx(1 / 3)
    assert est.ci_low == pytest.approx(1 / 3) and est.ci_high == pytest.approx(1 / 3)
    assert est.n_tasks == 15
    assert est.extra["mean_spec"] == pytest.approx(2 / 3)
    assert est.extra["mean_vibe"] == pytest.approx(1 / 3)
    assert paired_diff(runs, "claude-opus", "small", "task_pass", B=B).estimate == 0
    assert paired_diff(runs, "claude-sonnet", "large", "task_pass", B=B).estimate == 1.0


def test_varying_task_effects_interval_covers_truth(jitter_study):
    runs = valid(jitter_study[3])
    d = task_diffs(runs, "task_pass", "claude-sonnet", "small")
    assert sorted(set(np.round(d.values, 6))) == [0, round(1 / 3, 6), round(2 / 3, 6)]
    est = paired_diff(runs, "claude-sonnet", "small", "task_pass", B=B)
    assert est.estimate == pytest.approx(1 / 3)
    assert est.ci_low < 1 / 3 < est.ci_high
    assert est.ci_low > 0.1 and est.ci_high < 0.6


def test_task_enters_only_with_a_valid_run_in_each_arm(study):
    runs = valid(study[3])
    drop = ~((runs["cohort"] == "claude-opus") & (runs["task_id"] == "t07")
             & (runs["arm"] == "vibe"))
    d = task_diffs(runs[drop], "task_pass", "claude-opus", "small")
    assert "t07" not in d.index and len(d) == 14


def test_secondary_metrics_recover_known_differences(study):
    runs = valid(study[3])
    get = lambda m: paired_diff(runs, "claude-sonnet", "small", m, B=B).estimate
    assert get("tokens_total") == syn.run_tokens("claude-sonnet", "spec") - syn.run_tokens(
        "claude-sonnet", "vibe")
    assert get("wall_s") == pytest.approx(300)
    assert get("static_errors") == pytest.approx(-4)
    assert get("regression_any") == pytest.approx(-2 / 3)
    assert get("radon_mi_delta") == pytest.approx(-2)
    assert get("hidden_pass_rate") == pytest.approx(0.1)
    assert get("cost_usd") == pytest.approx(syn.run_cost("claude-sonnet", "spec")
                                            - syn.run_cost("claude-sonnet", "vibe"))


def test_null_metric_values_are_dropped_and_counted(study):
    runs = valid(study[3])
    est = paired_diff(runs, "claude-sonnet", "small", "ai_changed_line_coverage", B=B)
    # vibe runs have no coverage value: no task has both arms
    assert est.estimate is None and est.extra["n_null_runs"] == 45


def test_pooled_diff_weights_cohorts_equally_within_task(study):
    runs = valid(study[3])
    cohorts = ["claude-sonnet", "claude-opus", "agy-gemini"]
    p = pooled_task_diffs(runs, "task_pass", cohorts, "small")
    assert len(p) == 15 and np.allclose(p.values, 1 / 9)
    est = pooled_diff(runs, "task_pass", cohorts, "large", B=B)
    assert est.estimate == pytest.approx(7 / 9)


def test_h5_tier_difference_with_independent_resampling(study):
    runs = valid(study[3])
    cohorts = ["claude-sonnet", "claude-opus", "agy-gemini"]
    est = tier_diff(runs, "task_pass", cohorts, "large", "small", B=B)
    assert est.estimate == pytest.approx(2 / 3)
    assert est.n_tasks == {"large": 3, "small": 15}


def test_two_by_two(study):
    runs = valid(study[3])
    r = two_by_two(runs, "small", B=B)
    assert r["rate.claude-sonnet.spec"].estimate == pytest.approx(2 / 3)
    assert r["rate.claude-sonnet.vibe"].estimate == pytest.approx(1 / 3)
    assert r["rate.claude-opus.spec"].estimate == pytest.approx(2 / 3)
    assert r["rate.claude-opus.vibe"].estimate == pytest.approx(2 / 3)
    assert r["diff.claude-sonnet"].estimate == pytest.approx(1 / 3)
    assert r["diff.claude-opus"].estimate == pytest.approx(0)
    assert r["diff_of_diffs"].estimate == pytest.approx(1 / 3)
    assert r["sonnet_spec_minus_opus_vibe.pass"].estimate == pytest.approx(0)
    assert r["sonnet_spec_minus_opus_vibe.cost_usd"].estimate == pytest.approx(
        syn.run_cost("claude-sonnet", "spec") - syn.run_cost("claude-opus", "vibe"))


def test_two_by_two_joint_resampling_cancels_shared_task_noise(jitter_study):
    # opus diff is 0 everywhere; sonnet's varies by task. Both cohorts share the resampled
    # tasks, so the CI of diff-of-diffs equals the CI of sonnet's own diff.
    runs = valid(jitter_study[3])
    r = two_by_two(runs, "small", B=B)
    s = paired_diff(runs, "claude-sonnet", "small", "task_pass", B=B)
    assert (r["diff_of_diffs"].ci_low, r["diff_of_diffs"].ci_high) == pytest.approx(
        (s.ci_low, s.ci_high))


def test_cost_effectiveness(study):
    runs = valid(study[3])
    ce = cost_effectiveness(runs, "claude-sonnet", "small", B=B)
    c_spec = syn.run_cost("claude-sonnet", "spec")
    assert ce["spec.passes_per_usd"].estimate == pytest.approx(30 / (45 * c_spec))
    assert ce["spec.cost_per_pass"].estimate == pytest.approx(45 * c_spec / 30)
    zero = cost_effectiveness(runs, "agy-gemini", "medium", B=B)
    assert zero["vibe.cost_per_pass"].estimate is None  # 0 passes: undefined, not 0
    assert zero["vibe.passes_per_usd"].estimate == 0


def test_variability_share_of_disagreeing_cells(study):
    runs = valid(study[3])
    v = variability(runs[runs["cohort"] == "claude-sonnet"])
    # sonnet: small (1,2) all 30 cells disagree; medium (1,3): 5 of 10; large (0,3): 0 of 6
    assert v["cells"] == 46 and v["disagree"] == 35
    assert v["share"] == pytest.approx(35 / 46)


@pytest.mark.parametrize(
    ("lo", "hi", "coef", "expected"),
    [
        (0.1, 0.5, 0.8, "supported"),
        (0.1, 0.5, -0.2, "inconclusive"),  # logit interaction points the other way
        (-0.1, 0.5, 0.8, "inconclusive"),
        (-0.5, -0.1, -0.3, "contrary"),
        (-0.5, -0.1, 0.3, "contrary"),  # general rule: CI entirely below 0
        (None, None, 0.3, "not_estimable"),
    ],
)
def test_h5_reading_rule(lo, hi, coef, expected):
    assert h5_verdict(lo, hi, coef) == expected


def test_level3_slope_never_makes_h5_supported():
    assert h5_verdict(0.1, 0.5, 0.8, scale="difference") == "inconclusive"
    assert h5_verdict(-0.5, -0.1, 0.8, scale="difference") == "contrary"


def test_pooling_with_a_cohort_missing_a_task_averages_the_cohorts_present(study):
    # rule (README): a task's pooled difference is the mean over the cohorts that have it
    runs = valid(study[3])
    cohorts = ["claude-sonnet", "claude-opus", "agy-gemini"]
    drop = ~((runs["cohort"] == "claude-sonnet") & (runs["task_id"] == "t07")
             & (runs["arm"] == "vibe"))
    p = pooled_task_diffs(runs[drop], "task_pass", cohorts, "small")
    assert len(p) == 15
    assert p["t07"] == pytest.approx(0.0)  # opus 0 and agy 0; sonnet (1/3) has no t07
    assert p["t01"] == pytest.approx(1 / 9)
    est = pooled_diff(runs[drop], "task_pass", cohorts, "small", B=B)
    assert est.estimate == pytest.approx((14 / 9 + 0) / 15)


def test_two_by_two_cost_keeps_tasks_whose_unused_arms_lack_cost(study):
    runs = valid(study[3]).copy()
    # opus spec costs unknown on t03: irrelevant to "sonnet spec vs opus vibe"
    m = (runs["cohort"] == "claude-opus") & (runs["task_id"] == "t03") & (runs["arm"] == "spec")
    runs.loc[m, "cost_usd"] = None
    r = two_by_two(runs, "small", B=B)
    assert r["sonnet_spec_minus_opus_vibe.cost_usd"].n_tasks == 15
