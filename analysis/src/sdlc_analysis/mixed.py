"""H5 supporting model (prereg-v1 9.4): mixed logistic regression on every valid run of the
three tiers,

    pass ~ arm x log(src_lines) + cohort + (1 + arm | task),

with the prereg's fallback ladder when a model does not converge or is degenerate:
(1) drop the correlation between the two random effects; (2) (1 | task); (3) linear regression
of each task's difference (mean over cohorts) on log(src_lines).

The prereg names lme4::glmer (R). This package uses statsmodels' BinomialBayesMixedGLM
(variational Bayes): it fits independent variance components only, so level 0 (correlated
random intercept and slope) cannot be fitted and the ladder starts at level 1. See README,
"Interpretation notes".
"""

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from statsmodels.tools.sm_exceptions import ConvergenceWarning

FE_PRIOR_SD = 10.0  # weak prior on fixed effects, close to glmer's maximum likelihood
VC_PRIOR_SD = 1.0  # statsmodels default prior SD of each log random-effect SD
SINGULAR_SD = 1e-3  # a random-effect SD below this is a singular (degenerate) fit
Z = 1.959963984540054
LEVEL_NAMES = {
    0: "pass ~ arm * log_src + cohort + (1 + arm | task)",
    1: "pass ~ arm * log_src + cohort + (1 | task) + (0 + arm | task)",
    2: "pass ~ arm * log_src + cohort + (1 | task)",
    3: "OLS: task diff (mean over cohorts) ~ log_src",
}
VC = {
    1: {"task": "0 + C(task_id)", "task_arm": "0 + C(task_id):arm"},
    2: {"task": "0 + C(task_id)"},
}


def is_degenerate(fe_mean: np.ndarray, fe_sd: np.ndarray, vcp_mean: np.ndarray) -> bool:
    finite = np.all(np.isfinite(fe_mean)) and np.all(np.isfinite(fe_sd)) and np.all(
        np.isfinite(vcp_mean))
    if not finite or np.any(np.asarray(fe_sd) <= 0):
        return True
    return bool(np.any(np.exp(vcp_mean) < SINGULAR_SD))


def _prepare(runs: pd.DataFrame) -> pd.DataFrame:
    df = runs[["cohort", "task_id", "arm", "task_pass", "log_src_lines"]].copy()
    df["y"] = df["task_pass"].astype(float)
    df["arm"] = (df["arm"] == "spec").astype(float)
    task_x = df.groupby("task_id")["log_src_lines"].first()
    df["log_src"] = df["log_src_lines"] - task_x.mean()  # centred over tasks
    return df


def _formula(df: pd.DataFrame) -> str:
    return "y ~ arm * log_src" + (" + C(cohort)" if df["cohort"].nunique() > 1 else "")


def _fit_glmm(df: pd.DataFrame, vc: dict, formula: str):
    model = BinomialBayesMixedGLM.from_formula(formula, vc, df, vcp_p=VC_PRIOR_SD,
                                               fe_p=FE_PRIOR_SD)
    return model.fit_vb()


def ols_task_diffs(diffs: pd.DataFrame) -> dict:
    """Level 3: OLS of each task's difference (mean over cohorts, one weight per cohort) on
    log(src_lines). `diffs` has one row per (cohort, task) with column `diff`."""
    per_task = diffs.groupby("task_id").agg(diff=("diff", "mean"), x=("log_src_lines", "first"))
    X = sm.add_constant(per_task["x"].to_numpy())
    fit = sm.OLS(per_task["diff"].to_numpy(), X).fit()
    lo, hi = fit.conf_int(0.05)[1]
    return {"coef": float(fit.params[1]), "se": float(fit.bse[1]), "ci_low": float(lo),
            "ci_high": float(hi), "scale": "difference", "n_tasks": len(per_task),
            "ci_type": "t-based 95% OLS interval"}


def fit_h5_model(runs: pd.DataFrame, cohorts: list[str], task_diff_table=None) -> dict:
    """Fit the ladder on valid runs of `cohorts`; returns the model used, why earlier levels
    were dropped, and the arm x log(src_lines) interaction."""
    runs = runs[runs["cohort"].isin(cohorts)]
    df = _prepare(runs)
    formula = _formula(df)
    attempts = [{"level": 0, "model": LEVEL_NAMES[0], "ok": False,
                 "reason": "not available: statsmodels BinomialBayesMixedGLM fits independent "
                           "variance components only (no correlated random effects)"}]
    out = {"n_runs": len(df), "n_tasks": int(df["task_id"].nunique()),
           "cohorts": list(cohorts), "fixed_formula": formula,
           "log_src_centre": float(df.groupby("task_id")["log_src_lines"].first().mean())
           if len(df) else None}
    for level in (1, 2):
        reason = None
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                res = _fit_glmm(df, VC[level], formula)
            conv = [w for w in caught if issubclass(w.category, ConvergenceWarning)]
            if conv:
                reason = f"did not converge: {conv[0].message}"
            elif is_degenerate(res.fe_mean, res.fe_sd, res.vcp_mean):
                reason = "degenerate fit (non-finite estimate or random-effect SD < 1e-3)"
        except (np.linalg.LinAlgError, ValueError, FloatingPointError) as e:
            reason = f"failed: {type(e).__name__}: {e}"
        attempts.append({"level": level, "model": LEVEL_NAMES[level], "ok": reason is None,
                         "reason": reason})
        if reason is None:
            names = list(res.model.exog_names)
            i = names.index("arm:log_src")
            coef, se = float(res.fe_mean[i]), float(res.fe_sd[i])
            out.update(
                model_level=level, model=LEVEL_NAMES[level], attempts=attempts,
                interaction={"coef": coef, "se": se, "ci_low": coef - Z * se,
                             "ci_high": coef + Z * se, "scale": "logit",
                             "ci_type": "posterior mean +/- 1.96 posterior SD (variational "
                                        "Bayes, statsmodels BinomialBayesMixedGLM)"},
                fixed_effects={n: {"coef": float(m), "se": float(s)}
                               for n, m, s in zip(names, res.fe_mean, res.fe_sd)},
                random_effect_sd={n: float(np.exp(v))
                                  for n, v in zip(res.model.vcp_names, res.vcp_mean)},
            )
            return out
    # level 3
    if task_diff_table is None:
        from sdlc_analysis.estimators import task_diffs

        rows = []
        tiers = runs.groupby("task_id")["tier"].first()
        xs = runs.groupby("task_id")["log_src_lines"].first()
        for c in cohorts:
            for tier in sorted(set(tiers)):
                for t, d in task_diffs(runs, "task_pass", c, tier).items():
                    rows.append({"cohort": c, "task_id": t, "diff": d,
                                 "log_src_lines": xs[t]})
        task_diff_table = pd.DataFrame(rows)
    attempts.append({"level": 3, "model": LEVEL_NAMES[3], "ok": True, "reason": None})
    out.update(model_level=3, model=LEVEL_NAMES[3], attempts=attempts,
               interaction=ols_task_diffs(task_diff_table))
    return out
