"""H5 supporting model (prereg-v1 9.4): mixed logistic regression on the valid runs of the three
tiers,

    pass ~ arm x log(src_lines) + cohort + (1 + arm | task),

with the prereg's fallback ladder when a model does not converge or is degenerate:
(1) drop the correlation between the two random effects; (2) (1 | task); (3) linear regression
of each task's difference (mean over cohorts) on log(src_lines).

Engine (logged in prereg-v1 section 11): statsmodels' BinomialBayesMixedGLM, fitted by
variational Bayes, in place of lme4::glmer. It fits independent variance components only, so
level 0 (correlated random intercept and slope) cannot be fitted and the ladder starts at
level 1. The point estimate is the posterior mean of the interaction. Its interval is a cluster
bootstrap of the whole fit: tasks are resampled with replacement inside each tier (all runs of a
drawn task kept, a task drawn twice enters as two tasks), the chosen level is refitted on every
resample, and the interval is the 2.5-97.5 percentile; "SE" is the SD of the resampled
coefficients. The variational posterior SD is kept only as a diagnostic: on the 23-task design
it understates the spread of the estimate by about a third (README, note 1).

A level is degenerate ("suy biến") when one of its variance components is estimated at what the
data give when that component is absent. The N(0, 1) prior on each log-SD keeps a variational
SD near 0.2-0.3 even when the true SD is 0, so the old 1e-3 threshold could never fire. The
threshold is calibrated by simulation on the 23-task design (calibration/singular_sd.py,
README note 2): a component is degenerate when its posterior-mean SD is below SINGULAR_SD.
"""

import multiprocessing
import warnings
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.genmod.bayes_mixed_glm import BinomialBayesMixedGLM
from statsmodels.tools.sm_exceptions import ConvergenceWarning

FE_PRIOR_SD = 10.0  # weak prior on fixed effects, close to glmer's maximum likelihood
VC_PRIOR_SD = 1.0  # statsmodels default prior SD of each log random-effect SD
# singular criterion (calibrated, README note 2, calibration/singular_sd.py)
SINGULAR_SD = 0.30
B_MODEL_DEFAULT = 999
TIER_ORDER = ("small", "medium", "large")
LEVEL_NAMES = {
    0: "pass ~ arm * log_size + cohort + (1 + arm | task)",
    1: "pass ~ arm * log_size + cohort + (1 | task) + (0 + arm | task)",
    2: "pass ~ arm * log_size + cohort + (1 | task)",
    3: "OLS: task diff (mean over cohorts) ~ log_size",
}
VC = {
    1: {"task": "0 + C(task_id)", "task_arm": "0 + C(task_id):arm"},
    2: {"task": "0 + C(task_id)"},
}
INTERACTION = "arm:log_src"


def _prepare(runs: pd.DataFrame, x_col: str = "log_src_lines") -> pd.DataFrame:
    df = runs[["cohort", "task_id", "tier", "arm", "task_pass", x_col]].copy()
    df = df.rename(columns={x_col: "x_raw"})
    df["y"] = df["task_pass"].astype(float)
    df["arm"] = (df["arm"] == "spec").astype(float)
    task_x = df.groupby("task_id")["x_raw"].first()
    df["log_src"] = df["x_raw"].astype(float) - task_x.astype(float).mean()  # centred over tasks
    return df.reset_index(drop=True)


def _formula(df: pd.DataFrame) -> str:
    return "y ~ arm * log_src" + (" + C(cohort)" if df["cohort"].nunique() > 1 else "")


def _fit_glmm(df: pd.DataFrame, vc: dict, formula: str, seed: int = 0):
    """One variational fit; `seed` fixes statsmodels' random starting SDs (reproducible)."""
    model = BinomialBayesMixedGLM.from_formula(formula, vc, df, vcp_p=VC_PRIOR_SD,
                                               fe_p=FE_PRIOR_SD)
    return model.fit_vb(rng=seed)


def elbo(res) -> float:
    """Evidence lower bound of a variational fit (higher is better)."""
    m = res.model
    mean = np.concatenate([res.fe_mean, res.vcp_mean, res.vc_mean])
    sd = np.concatenate([res.fe_sd, res.vcp_sd, res.vc_sd])
    return float(m.vb_elbo(mean, sd))


def is_nonfinite(res) -> bool:
    vals = [res.fe_mean, res.fe_sd, res.vcp_mean]
    return not all(np.all(np.isfinite(v)) for v in vals) or bool(np.any(res.fe_sd <= 0))


def singular_reason(sds: dict[str, float]) -> str | None:
    """Degenerate when any variance component's posterior-mean SD is below SINGULAR_SD (the
    variational analogue of lme4's isSingular: the data do not move that SD away from where it
    sits when the true SD is 0)."""
    low = {k: v for k, v in sds.items() if not v >= SINGULAR_SD}
    if low:
        txt = ", ".join(f"{k} SD {v:.3f}" for k, v in low.items())
        return f"degenerate: {txt} < {SINGULAR_SD} (singular fit)"
    return None


def _fit_level(df: pd.DataFrame, level: int, formula: str, seed: int):
    """(result, reason): reason is None when the fit is usable."""
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            res = _fit_glmm(df, VC[level], formula, seed)
    except Exception as e:  # noqa: BLE001 - any failure steps down the ladder, recorded
        return None, f"failed: {type(e).__name__}: {e}"
    conv = [w for w in caught if issubclass(w.category, ConvergenceWarning)]
    if conv:
        return res, f"did not converge: {conv[0].message}"
    if is_nonfinite(res):
        return res, "degenerate: non-finite estimate"
    return res, singular_reason(random_sds(res))


def random_sds(res) -> dict[str, float]:
    return {n: float(np.exp(v)) for n, v in zip(res.model.vcp_names, res.vcp_mean)}


def ols_slope(per_task: pd.DataFrame) -> tuple[float, float, float, float]:
    """Level 3 on a table with one row per task (`diff`, `x`): slope, SE, t-interval."""
    X = sm.add_constant(per_task["x"].to_numpy(dtype=float))
    fit = sm.OLS(per_task["diff"].to_numpy(dtype=float), X).fit()
    lo, hi = fit.conf_int(0.05)[1]
    return float(fit.params[1]), float(fit.bse[1]), float(lo), float(hi)


def ols_task_diffs(diffs: pd.DataFrame) -> dict:
    """Level 3: OLS of each task's difference (mean over cohorts, one weight per cohort) on the
    log size. `diffs` has one row per (cohort, task) with columns `diff` and `log_src_lines`."""
    per_task = diffs.groupby("task_id").agg(diff=("diff", "mean"), x=("log_src_lines", "first"))
    coef, se, lo, hi = ols_slope(per_task)
    return {"coef": coef, "se": se, "ci_low": lo, "ci_high": hi, "scale": "difference",
            "n_tasks": len(per_task), "ci_type": "t-based 95% OLS interval"}


# --- cluster bootstrap of the whole fit ---------------------------------------------------


def resample_tasks(df: pd.DataFrame, B: int, seed: int) -> list[list[str]]:
    """B lists of drawn task ids: inside each tier (in TIER_ORDER), as many draws with
    replacement as the tier has tasks. One generator from the seed, tiers drawn in order."""
    rng = np.random.default_rng(seed)
    tiers = df.groupby("task_id")["tier"].first()
    by_tier = [sorted(tiers[tiers == t].index) for t in TIER_ORDER if (tiers == t).any()]
    by_tier += [sorted(tiers[~tiers.isin(TIER_ORDER)].index)] if (~tiers.isin(TIER_ORDER)).any() \
        else []
    draws = []
    for _ in range(B):
        d: list[str] = []
        for ids in by_tier:
            d.extend(ids[i] for i in rng.integers(0, len(ids), size=len(ids)))
        draws.append(d)
    return draws


def stack_draw(df: pd.DataFrame, draw: list[str]) -> pd.DataFrame:
    """Runs of the drawn tasks; the k-th copy of a task becomes its own task `<id>#k`."""
    parts = []
    groups = dict(tuple(df.groupby("task_id")))
    for k, tid in enumerate(draw):
        g = groups[tid].copy()
        g["task_id"] = f"{tid}#{k}"
        parts.append(g)
    out = pd.concat(parts, ignore_index=True)
    task_x = out.groupby("task_id")["x_raw"].first()
    out["log_src"] = out["x_raw"].astype(float) - task_x.astype(float).mean()
    return out


def _level3_coef(df: pd.DataFrame) -> float:
    cells = df.groupby(["cohort", "task_id", "arm"])["y"].mean().unstack("arm")
    cells = cells.dropna()
    if cells.empty:
        return float("nan")
    d = (cells[1.0] - cells[0.0]).rename("d").reset_index()
    per_task = d.groupby("task_id")["d"].mean().rename("diff").to_frame()
    per_task["x"] = df.groupby("task_id")["x_raw"].first()
    if per_task["x"].nunique() < 2:
        return float("nan")
    return ols_slope(per_task)[0]


def _refit_chunk(args) -> list[tuple[float, bool]]:
    """Worker: refit `level` on each drawn data set; (coef, converged) per draw, nan on failure."""
    df, level, formula, draws, seeds = args
    out = []
    for draw, s in zip(draws, seeds):
        data = stack_draw(df, draw)
        if level == 3:
            out.append((_level3_coef(data), True))
            continue
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                res = _fit_glmm(data, VC[level], formula, s)
            names = list(res.model.exog_names)
            coef = float(res.fe_mean[names.index(INTERACTION)])
            conv = not any(issubclass(w.category, ConvergenceWarning) for w in caught)
            out.append((coef if np.isfinite(coef) else float("nan"), conv))
        except Exception:  # noqa: BLE001 - counted as a failed resample
            out.append((float("nan"), False))
    return out


def bootstrap_interaction(df: pd.DataFrame, level: int, formula: str, B: int, seed: int,
                          jobs: int = 1) -> dict:
    draws = resample_tasks(df, B, seed)
    seeds = [seed + 1 + b for b in range(B)]
    chunks = max(1, min(jobs, B))
    parts = [(df, level, formula, draws[i::chunks], seeds[i::chunks]) for i in range(chunks)]
    if chunks == 1:
        results = [_refit_chunk(parts[0])]
    else:
        with ProcessPoolExecutor(chunks, mp_context=multiprocessing.get_context("spawn")) as ex:
            results = list(ex.map(_refit_chunk, parts))
    # undo the striping so replicate b is at position b
    flat: list[tuple[float, bool]] = [None] * B  # type: ignore[list-item]
    for i, res in enumerate(results):
        for j, r in enumerate(res):
            flat[i + j * chunks] = r
    coefs = np.array([c for c, _ in flat], dtype=float)
    ok = np.isfinite(coefs)
    lo, hi = (np.percentile(coefs[ok], [2.5, 97.5]) if ok.any() else (np.nan, np.nan))
    return {
        "ci_low": float(lo) if ok.any() else None,
        "ci_high": float(hi) if ok.any() else None,
        "se": float(np.std(coefs[ok], ddof=1)) if ok.sum() > 1 else None,
        "B": B,
        "seed": seed,
        "n_failed": int((~ok).sum()),
        "n_not_converged": int(sum(1 for c, conv in flat if np.isfinite(c) and not conv)),
        "ci_type": "cluster bootstrap of the whole fit: tasks resampled with replacement within "
                   "tier, chosen level refitted, percentile 2.5-97.5",
    }


# --- the ladder ---------------------------------------------------------------------------


def _task_diff_table(runs: pd.DataFrame, cohorts: list[str], x_col: str) -> pd.DataFrame:
    from sdlc_analysis.estimators import task_diffs

    rows = []
    xs = runs.groupby("task_id")[x_col].first()
    for c in cohorts:
        for tier in sorted(set(runs["tier"])):
            for t, d in task_diffs(runs, "task_pass", c, tier).items():
                rows.append({"cohort": c, "task_id": t, "diff": d, "log_src_lines": xs[t]})
    return pd.DataFrame(rows, columns=["cohort", "task_id", "diff", "log_src_lines"])


def fit_h5_model(
    runs: pd.DataFrame,
    cohorts: list[str],
    *,
    x_col: str = "log_src_lines",
    B: int = B_MODEL_DEFAULT,
    seed: int = 20261115,
    jobs: int = 1,
) -> dict:
    """Fit the ladder on valid runs of `cohorts` with size column `x_col`; returns the model
    used, why earlier levels were dropped, and the arm x log(size) interaction with its
    cluster-bootstrap interval. Tasks without a size value are dropped and listed."""
    runs = runs[runs["cohort"].isin(cohorts)]
    no_x = sorted(set(runs.loc[runs[x_col].isna(), "task_id"]))
    runs = runs[runs[x_col].notna()]
    df = _prepare(runs, x_col)
    formula = _formula(df)
    attempts = [{"level": 0, "model": LEVEL_NAMES[0], "ok": False,
                 "reason": "not available: statsmodels BinomialBayesMixedGLM fits independent "
                           "variance components only (no correlated random effects)"}]
    out = {"n_runs": len(df), "n_tasks": int(df["task_id"].nunique()),
           "cohorts": list(cohorts), "size_variable": x_col, "tasks_without_size": no_x,
           "fixed_formula": formula,
           "log_size_centre": float(df.groupby("task_id")["x_raw"].first().mean())
           if len(df) else None}
    if df.empty:
        out.update(model_level=None, attempts=attempts, interaction=None)
        return out
    chosen = None
    for level in (1, 2):
        res, reason = _fit_level(df, level, formula, seed)
        attempts.append({"level": level, "model": LEVEL_NAMES[level], "ok": reason is None,
                         "reason": reason,
                         "random_effect_sd": None if res is None else random_sds(res)})
        if reason is None:
            chosen = (level, res)
            break
    if chosen is not None:
        level, res = chosen
        names = list(res.model.exog_names)
        i = names.index(INTERACTION)
        coef = float(res.fe_mean[i])
        boot = bootstrap_interaction(df, level, formula, B, seed, jobs)
        out.update(
            model_level=level, model=LEVEL_NAMES[level], attempts=attempts,
            interaction={"coef": coef, "se": boot["se"], "ci_low": boot["ci_low"],
                         "ci_high": boot["ci_high"], "scale": "logit",
                         "vb_posterior_sd": float(res.fe_sd[i]), "bootstrap": boot,
                         "ci_type": boot["ci_type"]},
            fixed_effects={n: {"coef": float(m), "vb_posterior_sd": float(s)}
                           for n, m, s in zip(names, res.fe_mean, res.fe_sd)},
            random_effect_sd=random_sds(res),
        )
        return out
    # level 3
    table = _task_diff_table(runs, cohorts, x_col)
    attempts.append({"level": 3, "model": LEVEL_NAMES[3], "ok": True, "reason": None})
    ols = ols_task_diffs(table)
    boot = bootstrap_interaction(df, 3, formula, B, seed, 1)
    out.update(model_level=3, model=LEVEL_NAMES[3], attempts=attempts,
               interaction={**ols, "se": boot["se"], "ci_low": boot["ci_low"],
                            "ci_high": boot["ci_high"], "ols_se": ols["se"],
                            "ols_ci": [ols["ci_low"], ols["ci_high"]], "bootstrap": boot,
                            "ci_type": boot["ci_type"]})
    return out
