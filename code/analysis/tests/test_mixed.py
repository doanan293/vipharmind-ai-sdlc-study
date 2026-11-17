import os
import warnings

import numpy as np
import pandas as pd
import pytest
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from sdlc_analysis import mixed
from sdlc_analysis.simulate import MAIN_TIER, main_design, simulate


def test_mixed_model_recovers_known_interaction():
    # slope SD 1.0: clearly above the calibrated singular threshold, so level 1 is kept
    res = mixed.fit_h5_model(simulate(n_tasks=40, sd1=1.0), ["a", "b", "c"], B=4, jobs=1)
    assert res["model_level"] == 1  # statsmodels has no correlated random effects (level 0)
    assert res["attempts"][0]["level"] == 0 and "not available" in res["attempts"][0]["reason"]
    inter = res["interaction"]
    assert inter["scale"] == "logit"
    assert inter["coef"] == pytest.approx(1.0, abs=0.6)
    assert inter["ci_low"] < inter["coef"] < inter["ci_high"]
    assert inter["bootstrap"]["B"] == 4 and inter["bootstrap"]["n_failed"] == 0


def test_fit_is_reproducible():
    runs = simulate(n_tasks=20, seed=5)
    a = mixed.fit_h5_model(runs, ["a", "b", "c"], B=3)
    b = mixed.fit_h5_model(runs, ["a", "b", "c"], B=3)
    assert a["interaction"] == b["interaction"]


def test_negative_interaction_is_recovered_with_its_sign():
    res = mixed.fit_h5_model(simulate(n_tasks=40, beta_int=-1.2, seed=3), ["a", "b", "c"], B=2)
    assert res["interaction"]["coef"] < -0.5


def test_resampling_is_within_tier_and_reproducible():
    runs = main_design(seed=1)
    df = mixed._prepare(runs)
    draws = mixed.resample_tasks(df, 50, seed=7)
    tiers = df.groupby("task_id")["tier"].first()
    for d in draws:
        assert [tiers[t] for t in d] == MAIN_TIER  # 15 small, then 5 medium, then 3 large
    assert draws == mixed.resample_tasks(df, 50, seed=7)


def test_a_task_drawn_twice_enters_as_two_tasks():
    df = mixed._prepare(main_design(seed=1))
    out = mixed.stack_draw(df, ["x000", "x000", "x001"])
    assert out["task_id"].nunique() == 3
    assert len(out) == 3 * len(df[df["task_id"] == "x000"])


def test_bootstrap_matches_parallel_and_serial():
    runs = simulate(n_tasks=20, seed=2)
    df = mixed._prepare(runs)
    f = mixed._formula(df)
    serial = mixed.bootstrap_interaction(df, 2, f, B=6, seed=3, jobs=1)
    parallel = mixed.bootstrap_interaction(df, 2, f, B=6, seed=3, jobs=3)
    assert serial == parallel


def test_non_convergence_steps_down_the_ladder(monkeypatch):
    runs = simulate(n_tasks=30, seed=1)
    real = mixed._fit_glmm

    def flaky(df, vc, formula, seed=0):
        if "task_arm" in vc:
            warnings.warn("VB fitting did not converge", ConvergenceWarning)
        return real(df, vc, formula, seed)

    monkeypatch.setattr(mixed, "_fit_glmm", flaky)
    res = mixed.fit_h5_model(runs, ["a", "b", "c"], B=3)
    assert res["model_level"] == 2
    assert "did not converge" in res["attempts"][1]["reason"]


def test_any_fitting_error_steps_down_to_level_3(monkeypatch):
    def broken(df, vc, formula, seed=0):
        raise RuntimeError("boom")

    monkeypatch.setattr(mixed, "_fit_glmm", broken)
    res = mixed.fit_h5_model(simulate(n_tasks=20, seed=2), ["a", "b", "c"], B=50)
    assert res["model_level"] == 3
    assert "RuntimeError" in res["attempts"][1]["reason"]
    inter = res["interaction"]
    assert inter["scale"] == "difference"
    assert inter["ci_low"] < inter["coef"] < inter["ci_high"]
    assert [a["level"] for a in res["attempts"]] == [0, 1, 2, 3]


def test_singular_reason():
    assert mixed.singular_reason({"task": 0.9, "task_arm": 0.12}) is not None
    assert mixed.singular_reason({"task": 0.9, "task_arm": 0.6}) is None
    assert mixed.singular_reason({"task": float("nan")}) is not None


def test_no_slope_variation_reaches_the_singular_branch():
    # true random-slope SD 0 on the 23-task design: data set 0 of calibration/singular_sd.py
    # (fitted slope SD 0.232; the criterion fires in 70% of such data sets) steps down to (1 | task)
    data = main_design(seed=0, beta_int=0.0, sd0=0.8, sd1=0.0)
    res = mixed.fit_h5_model(data, ["a", "b", "c", "d"], B=2, seed=0)
    assert res["attempts"][1]["ok"] is False
    assert "singular" in res["attempts"][1]["reason"]
    assert res["model_level"] == 2


def test_level_3_ols_on_task_differences_is_exact_on_a_line():
    rows = []
    for i, src in enumerate([50, 100, 200, 400, 800, 1600]):
        d = 0.1 + 0.2 * np.log(src)
        for c in ("a", "b"):
            rows.append(
                {
                    "cohort": c,
                    "task_id": f"x{i}",
                    "src_lines": src,
                    "log_src_lines": np.log(src),
                    "tier": "small",
                    "diff": d,
                }
            )
    res = mixed.ols_task_diffs(pd.DataFrame(rows))
    assert res["coef"] == pytest.approx(0.2) and res["se"] == pytest.approx(0, abs=1e-9)


def test_size_column_is_selectable_and_missing_sizes_are_listed():
    runs = simulate(n_tasks=20, seed=4)
    # a second size variable with the opposite relation to the effect
    runs["log_graded_src_lines"] = -runs["log_src_lines"]
    runs.loc[runs["task_id"] == "x000", "log_graded_src_lines"] = None
    a = mixed.fit_h5_model(runs, ["a", "b", "c"], B=3)
    b = mixed.fit_h5_model(runs, ["a", "b", "c"], x_col="log_graded_src_lines", B=3)
    assert a["interaction"]["coef"] > 0 > b["interaction"]["coef"]
    assert b["tasks_without_size"] == ["x000"] and b["n_tasks"] == 19


@pytest.mark.skipif(not os.environ.get("SDLC_SLOW_TESTS"), reason="slow: set SDLC_SLOW_TESTS=1")
def test_interval_coverage_on_the_23_task_design():
    """Regression guard (reviews B2, N1): on the real design (23 tasks, real src_lines and
    tiers, 4 cohorts, 2 arms, 3 reps) the bootstrap interval must cover the true interaction in
    at least 80% of 40 data sets, against the 65-87% of the old variational +/- 1.96 SD interval.
    It is not a calibration: the within-tier percentile bootstrap is expected to cover about
    88-90% on this design (nominal 95%)."""
    n = int(os.environ.get("SDLC_COVERAGE_SETS", "40"))
    B = int(os.environ.get("SDLC_COVERAGE_B", "99"))
    jobs = int(os.environ.get("SDLC_COVERAGE_JOBS", "1"))
    hits, rows = 0, []
    for s in range(n):
        res = mixed.fit_h5_model(
            main_design(seed=1000 + s, beta_int=0.5), ["a", "b", "c", "d"], B=B, seed=s, jobs=jobs
        )
        i = res["interaction"]
        hit = i["ci_low"] <= 0.5 <= i["ci_high"]
        hits += hit
        rows.append(
            (
                s,
                res["model_level"],
                i["coef"],
                i["ci_low"],
                i["ci_high"],
                i.get("vb_posterior_sd"),
                hit,
            )
        )
        print(*rows[-1], flush=True)
    print("coverage", hits / n)
    assert hits / n >= 0.80
