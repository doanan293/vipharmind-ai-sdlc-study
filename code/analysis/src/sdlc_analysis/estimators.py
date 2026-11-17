"""Estimators of prereg-v1 section 9. All take the table of valid runs (status done).

The analysis unit is the task: a (cohort, task, arm) cell's value is the mean of a metric over
its valid reps; a task's difference is spec minus vibe; a cohort's estimate is the mean of task
differences, each task weighted equally. A task enters only when each arm has at least one valid
run with a non-null value of the metric (prereg 10; 9.5 for null metric values).
"""

import numpy as np
import pandas as pd

from sdlc_analysis.bootstrap import (
    B_DEFAULT,
    SEED_DEFAULT,
    Estimate,
    boot_independent_diff,
    boot_mean,
    boot_stat,
)

KEYS = ["cohort", "tier", "task_id", "arm"]


def _metric_frame(runs: pd.DataFrame, metric: str) -> pd.DataFrame:
    df = runs[KEYS + [metric]].copy()
    df[metric] = pd.to_numeric(df[metric].astype("float64"), errors="coerce")
    return df


def cell_means(runs: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Mean of `metric` over the valid reps of each (cohort, tier, task, arm) with a value."""
    df = _metric_frame(runs, metric).dropna(subset=[metric])
    g = df.groupby(KEYS, sort=True)[metric]
    return pd.DataFrame({"mean": g.mean(), "n": g.size()}).reset_index()


def _arm_table(runs: pd.DataFrame, metric: str, cohort: str, tier: str) -> pd.DataFrame:
    sub = runs[(runs["cohort"] == cohort) & (runs["tier"] == tier)]
    cm = cell_means(sub, metric)
    wide = cm.pivot(index="task_id", columns="arm", values="mean")
    for a in ("spec", "vibe"):
        if a not in wide:
            wide[a] = np.nan
    return wide[["spec", "vibe"]].dropna()


def task_diffs(runs: pd.DataFrame, metric: str, cohort: str, tier: str) -> pd.Series:
    """Per-task spec minus vibe of the cell means, tasks with both arms only."""
    w = _arm_table(runs, metric, cohort, tier)
    return (w["spec"] - w["vibe"]).rename("diff")


def n_null(
    runs: pd.DataFrame, metric: str, cohort: str | None = None, tier: str | None = None
) -> int:
    sub = runs
    if cohort is not None:
        sub = sub[sub["cohort"] == cohort]
    if tier is not None:
        sub = sub[sub["tier"] == tier]
    return int(pd.to_numeric(sub[metric].astype("float64"), errors="coerce").isna().sum())


def paired_diff(
    runs: pd.DataFrame,
    cohort: str,
    tier: str,
    metric: str = "task_pass",
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
) -> Estimate:
    """Prereg 9.1 / 9.5: mean over tasks of (spec - vibe), task bootstrap."""
    w = _arm_table(runs, metric, cohort, tier)
    est = boot_mean((w["spec"] - w["vibe"]).to_numpy(), B=B, seed=seed)
    est.extra.update(
        mean_spec=float(w["spec"].mean()) if len(w) else None,
        mean_vibe=float(w["vibe"].mean()) if len(w) else None,
        n_null_runs=n_null(runs, metric, cohort, tier),
        reference_only=len(w) < 6,
    )
    return est


def pooled_task_diffs(runs: pd.DataFrame, metric: str, cohorts: list[str], tier: str) -> pd.Series:
    """Per task: the mean of the cohorts' differences (each cohort one weight; prereg 9)."""
    cols = {c: task_diffs(runs, metric, c, tier) for c in cohorts}
    if not cols:
        return pd.Series(dtype=float)
    df = pd.DataFrame(cols)
    return df.mean(axis=1, skipna=True).dropna().rename("pooled_diff")


def pooled_diff(
    runs: pd.DataFrame,
    metric: str,
    cohorts: list[str],
    tier: str,
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
) -> Estimate:
    p = pooled_task_diffs(runs, metric, cohorts, tier)
    est = boot_mean(p.to_numpy(), B=B, seed=seed)
    est.extra.update(cohorts=list(cohorts), reference_only=len(p) < 6)
    return est


def tier_diff(
    runs: pd.DataFrame,
    metric: str,
    cohorts: list[str],
    hi: str = "large",
    lo: str = "small",
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
) -> Estimate:
    """H5 primary (prereg 9.4): pooled difference in tier `hi` minus tier `lo`, each tier's
    tasks resampled on their own."""
    a = pooled_task_diffs(runs, metric, cohorts, hi)
    b = pooled_task_diffs(runs, metric, cohorts, lo)
    est = boot_independent_diff(a.to_numpy(), b.to_numpy(), B=B, seed=seed)
    est.n_tasks = {hi: len(a), lo: len(b)}
    est.extra.update(
        cohorts=list(cohorts),
        **{
            f"pooled_{hi}": float(a.mean()) if len(a) else None,
            f"pooled_{lo}": float(b.mean()) if len(b) else None,
        },
    )
    return est


def two_by_two(
    runs: pd.DataFrame,
    tier: str,
    a: str = "claude-sonnet",
    b: str = "claude-opus",
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
) -> dict[str, Estimate]:
    """Prereg 9.3 (RQ5/H4): arm x model on the tasks both cohorts have; every resample uses the
    same tasks for both cohorts."""
    ta = _arm_table(runs, "task_pass", a, tier)
    tb = _arm_table(runs, "task_pass", b, tier)
    tasks = sorted(set(ta.index) & set(tb.index))
    data = (
        np.column_stack(
            [
                ta.loc[tasks, "spec"],
                ta.loc[tasks, "vibe"],
                tb.loc[tasks, "spec"],
                tb.loc[tasks, "vibe"],
            ]
        )
        if tasks
        else np.empty((0, 4))
    )

    def col(i):
        return lambda x: x[..., i].mean(-1)

    out = {
        f"rate.{a}.spec": boot_stat(data, col(0), B=B, seed=seed),
        f"rate.{a}.vibe": boot_stat(data, col(1), B=B, seed=seed),
        f"rate.{b}.spec": boot_stat(data, col(2), B=B, seed=seed),
        f"rate.{b}.vibe": boot_stat(data, col(3), B=B, seed=seed),
        f"diff.{a}": boot_stat(data, lambda x: (x[..., 0] - x[..., 1]).mean(-1), B=B, seed=seed),
        f"diff.{b}": boot_stat(data, lambda x: (x[..., 2] - x[..., 3]).mean(-1), B=B, seed=seed),
        "diff_of_diffs": boot_stat(
            data,
            lambda x: ((x[..., 0] - x[..., 1]) - (x[..., 2] - x[..., 3])).mean(-1),
            B=B,
            seed=seed,
        ),
        "sonnet_spec_minus_opus_vibe.pass": boot_stat(
            data, lambda x: (x[..., 0] - x[..., 3]).mean(-1), B=B, seed=seed
        ),
    }
    # cost: a's spec runs vs b's vibe runs, on tasks with a cost in both of those cells (the
    # unused arms do not matter)
    cm = cell_means(runs[runs["tier"] == tier], "cost_usd").set_index(["cohort", "task_id", "arm"])
    sa = cm.xs((a, "spec"), level=("cohort", "arm"))["mean"] if len(cm) else pd.Series(dtype=float)
    vb = cm.xs((b, "vibe"), level=("cohort", "arm"))["mean"] if len(cm) else pd.Series(dtype=float)
    ctasks = sorted(set(sa.index) & set(vb.index))
    cdata = np.column_stack([sa.loc[ctasks], vb.loc[ctasks]]) if ctasks else np.empty((0, 2))
    out["sonnet_spec_minus_opus_vibe.cost_usd"] = boot_stat(
        cdata, lambda x: (x[..., 0] - x[..., 1]).mean(-1), B=B, seed=seed
    )
    out["sonnet_spec_over_opus_vibe.cost_ratio"] = boot_stat(
        cdata, lambda x: x[..., 0].mean(-1) / x[..., 1].mean(-1), B=B, seed=seed
    )
    for e in out.values():
        e.extra["cohorts"] = [a, b]
    return out


def cost_effectiveness(
    runs: pd.DataFrame,
    cohort: str,
    tier: str,
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
    cost_col: str = "cost_usd",
) -> dict[str, Estimate]:
    """Prereg 9.6: passes per converted dollar and cost per pass, per arm, over the valid runs
    with a known cost; task bootstrap (both arms share the resampled tasks). Cost per pass with 0
    passes is undefined (None), never 0; resamples where it is undefined are counted and left
    out of the interval."""
    sub = runs[(runs["cohort"] == cohort) & (runs["tier"] == tier)].copy()
    sub["cost_usd"] = pd.to_numeric(sub[cost_col].astype("float64"), errors="coerce")
    n_no_cost = int(sub["cost_usd"].isna().sum())
    sub = sub.dropna(subset=["cost_usd"])
    sub["pass"] = sub["task_pass"].astype(float)
    agg = sub.groupby(["task_id", "arm"]).agg(
        passes=("pass", "sum"), cost=("cost_usd", "sum"), runs=("pass", "size")
    )
    wide = agg.unstack("arm")
    both = [("runs", "spec"), ("runs", "vibe")]
    tasks = list(wide.dropna(subset=both).index) if all(c in wide.columns for c in both) else []
    # columns: spec passes, spec cost, vibe passes, vibe cost
    data = (
        np.column_stack(
            [
                wide.loc[tasks, ("passes", "spec")],
                wide.loc[tasks, ("cost", "spec")],
                wide.loc[tasks, ("passes", "vibe")],
                wide.loc[tasks, ("cost", "vibe")],
            ]
        )
        if tasks
        else np.empty((0, 4))
    )

    def ratio(i, j):
        def f(x):
            num, den = x[..., i].sum(-1), x[..., j].sum(-1)
            return np.where(den > 0, num / np.where(den > 0, den, 1), np.nan)

        return f

    out = {
        "spec.passes_per_usd": boot_stat(data, ratio(0, 1), B=B, seed=seed),
        "spec.cost_per_pass": boot_stat(data, ratio(1, 0), B=B, seed=seed),
        "vibe.passes_per_usd": boot_stat(data, ratio(2, 3), B=B, seed=seed),
        "vibe.cost_per_pass": boot_stat(data, ratio(3, 2), B=B, seed=seed),
        "diff.passes_per_usd": boot_stat(
            data, lambda x: ratio(0, 1)(x) - ratio(2, 3)(x), B=B, seed=seed
        ),
        "diff.cost_per_pass": boot_stat(
            data, lambda x: ratio(1, 0)(x) - ratio(3, 2)(x), B=B, seed=seed
        ),
    }
    for arm, i in (("spec", 0), ("vibe", 2)):
        for k in ("passes_per_usd", "cost_per_pass"):
            out[f"{arm}.{k}"].extra.update(
                passes=float(data[:, i].sum()), cost_usd=float(data[:, i + 1].sum())
            )
    for e in out.values():
        e.extra["n_runs_without_cost"] = n_no_cost
    return out


def variability(runs: pd.DataFrame) -> dict:
    """Prereg 9.1: share of (cohort, task, arm) cells whose valid reps disagree on task_pass.
    Only cells with >= 2 valid reps can disagree; they form the denominator."""
    g = runs.groupby(["cohort", "task_id", "arm"])["task_pass"]
    n = g.size()
    k = g.apply(lambda s: s.astype(bool).sum())
    multi = n >= 2
    disagree = (k[multi] > 0) & (k[multi] < n[multi])
    cells = int(multi.sum())
    return {
        "cells": cells,
        "disagree": int(disagree.sum()),
        "share": float(disagree.sum() / cells) if cells else None,
        "cells_single_rep": int((~multi).sum()),
    }


def h5_verdict(ci_low, ci_high, interaction_coef, scale: str = "logit") -> str:
    """Prereg 9.4 with the section 9 reading rule. "supported" only when the primary test's 95%
    CI lies entirely above 0 AND the logit-scale interaction points the same way (positive point
    estimate). A level-3 fallback slope is on the difference scale and cannot give the logit
    guard against the ceiling effect, so it never makes H5 "supported". "contrary" when the
    primary CI lies entirely below 0 (the general rule; prereg 9.4 adds no condition to it).
    Otherwise "inconclusive"."""
    if ci_low is None or ci_high is None:
        return "not_estimable"
    if ci_high < 0:
        return "contrary"
    if ci_low > 0 and interaction_coef is not None and interaction_coef > 0 and scale == "logit":
        return "supported"
    return "inconclusive"
