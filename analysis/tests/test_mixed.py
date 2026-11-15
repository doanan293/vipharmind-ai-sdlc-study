import warnings

import numpy as np
import pandas as pd
import pytest
from statsmodels.tools.sm_exceptions import ConvergenceWarning

from sdlc_analysis import mixed


def simulate(n_tasks=60, cohorts=("a", "b", "c"), reps=3, beta_int=1.0, seed=0):
    """pass ~ arm x log(src) + cohort + (1 + arm | task), with known coefficients."""
    rng = np.random.default_rng(seed)
    src = np.exp(rng.uniform(np.log(40), np.log(1500), n_tasks)).round().astype(int)
    x = np.log(src) - np.log(src).mean()
    u0 = rng.normal(0, 0.8, n_tasks)
    u1 = rng.normal(0, 0.4, n_tasks)
    coh_eff = dict(zip(cohorts, np.linspace(-0.5, 0.5, len(cohorts))))
    rows = []
    for t in range(n_tasks):
        for c in cohorts:
            for arm in (0, 1):
                eta = -0.2 + 0.5 * arm - 0.8 * x[t] + beta_int * arm * x[t] + coh_eff[c]
                eta += u0[t] + u1[t] * arm
                for r in range(reps):
                    p = 1 / (1 + np.exp(-eta))
                    rows.append({"cohort": c, "task_id": f"x{t:03d}", "arm": "spec" if arm else
                                 "vibe", "rep": r + 1, "src_lines": int(src[t]),
                                 "log_src_lines": float(np.log(src[t])),
                                 "tier": "small", "task_pass": bool(rng.random() < p)})
    return pd.DataFrame(rows)


def test_mixed_model_recovers_known_interaction():
    runs = simulate()
    res = mixed.fit_h5_model(runs, ["a", "b", "c"])
    assert res["model_level"] == 1  # statsmodels has no correlated random effects (level 0)
    assert res["attempts"][0]["level"] == 0 and "not available" in res["attempts"][0]["reason"]
    inter = res["interaction"]
    assert inter["scale"] == "logit"
    assert inter["ci_low"] < 1.0 < inter["ci_high"]
    assert inter["coef"] == pytest.approx(1.0, abs=0.45)
    assert inter["se"] > 0


def test_negative_interaction_is_recovered_with_its_sign():
    res = mixed.fit_h5_model(simulate(beta_int=-1.2, seed=3), ["a", "b", "c"])
    assert res["interaction"]["coef"] < -0.5


def test_non_convergence_steps_down_the_ladder(monkeypatch):
    runs = simulate(n_tasks=30, seed=1)
    real = mixed._fit_glmm

    def flaky(df, vc, formula):
        if "task_arm" in vc:
            warnings.warn("VB fitting did not converge", ConvergenceWarning)
        return real(df, vc, formula)

    monkeypatch.setattr(mixed, "_fit_glmm", flaky)
    res = mixed.fit_h5_model(runs, ["a", "b", "c"])
    assert res["model_level"] == 2
    assert "did not converge" in res["attempts"][1]["reason"]


def test_degenerate_fit_steps_down(monkeypatch):
    def broken(df, vc, formula):
        raise np.linalg.LinAlgError("singular matrix")

    monkeypatch.setattr(mixed, "_fit_glmm", broken)
    runs = simulate(n_tasks=20, seed=2)
    res = mixed.fit_h5_model(runs, ["a", "b", "c"])
    assert res["model_level"] == 3
    assert res["interaction"]["scale"] == "difference"
    assert [a["level"] for a in res["attempts"]] == [0, 1, 2, 3]


def test_singular_random_effect_sd_is_degenerate():
    assert mixed.is_degenerate(np.array([0.1, 0.2]), np.array([0.05, 0.1]), np.array([np.log(1e-5)]))
    assert mixed.is_degenerate(np.array([np.nan]), np.array([0.1]), np.array([0.0]))
    assert not mixed.is_degenerate(np.array([0.1]), np.array([0.1]), np.array([np.log(0.5)]))


def test_level_3_ols_on_task_differences_is_exact_on_a_line():
    # pooled per-task differences exactly 0.1 + 0.2 * log(src): slope 0.2, no residual
    rows = []
    for i, src in enumerate([50, 100, 200, 400, 800, 1600]):
        d = 0.1 + 0.2 * np.log(src)
        for c in ("a", "b"):
            rows.append({"cohort": c, "task_id": f"x{i}", "src_lines": src,
                         "log_src_lines": np.log(src), "tier": "small", "diff": d})
    res = mixed.ols_task_diffs(pd.DataFrame(rows))
    assert res["coef"] == pytest.approx(0.2) and res["se"] == pytest.approx(0, abs=1e-9)
