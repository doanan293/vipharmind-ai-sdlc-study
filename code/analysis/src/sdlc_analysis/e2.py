"""sdlc-e2: exploratory experiment E2 of prereg-v1.2 (brief prompt, 2 x 2 detail x arm).

    uv run sdlc-e2 --detailed MAIN MAIN_TIERS HAIKU --brief BRIEF [--out DIR]

Everything here is exploratory ("thăm dò, thêm sau khi thấy kết quả chính"): estimates with 95%
task-bootstrap intervals, read by sign and magnitude, no significance thresholds and no verdicts.

Analysis unit and bootstrap are those of prereg-v1 section 9 (and the locked estimators are
reused): a (detail, cohort, task, arm) cell's value is the mean of a metric over its valid reps
that have a value; a task's difference is spec minus vibe; a cohort's estimate is the mean over
tasks, each task one weight; pooling averages the cohorts' per-task values, each cohort one
weight. Tasks are resampled with replacement, keeping every rep of a chosen task; percentile
interval 2.5-97.5; seed 20261115; B = 9999 (prereg-v1.2). Every estimate starts its own generator
from the seed. The 23 tasks of all three tiers form one task set (E2 compares arms within a
condition, not tiers); per-tier estimates are reported as well.

Checklist score: `score` (met / items) from judge.json; `score_core` (without [exact] items) is
the sensitivity analysis. A valid unit without a usable judge.json has no score: it is left out
of every score estimate and counted, never imputed.
"""

import argparse
import hashlib
import json
import logging
import sys
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from sdlc_analysis.bootstrap import CI_TYPE, SEED_DEFAULT, Estimate, boot_ratio, boot_stat
from sdlc_analysis.e1 import REPO, unpriced_cohort_cost_unknown
from sdlc_analysis.estimators import paired_diff, pooled_diff
from sdlc_analysis.labels import cohen_kappa
from sdlc_analysis.load import ARMS, TIERS, expected_units, load_runs, load_tasks, unit_status
from sdlc_analysis.report import _round_floats

log = logging.getLogger("sdlc_analysis.e2")

B_E2 = 9999  # prereg-v1.2, "Phân tích của E2"
E2_COHORTS = ("claude-sonnet", "claude-opus", "claude-haiku", "codex-luna")
DETAILS = ("detailed", "brief")
JUDGE_MODEL = "claude-fable-5-2"
E2_OUT = REPO / "data" / "results" / "analysis" / "e2"
EXPLORATORY_NOTE = "thăm dò, thêm sau khi thấy kết quả chính (exploratory, added after the main " \
    "results were seen); no significance thresholds, read by sign and magnitude"
SCORE_METRICS = ("score", "score_core")
# automatic metrics of the 2 x 2 (prereg-v1.2): the four the analysis names, then the rest of
# the automatic metrics (descriptive), then the hidden-test metrics (flagged, see NOTES)
AUTO_METRICS = ("regression_any", "regressions_n", "ai_tests_added", "ai_changed_line_coverage",
                "tokens_total")
AUTO_EXTRA = ("static_errors", "architecture_pass", "patch_lines", "wall_s")
HIDDEN_METRICS = ("hidden_pass_rate", "task_pass")
NOTES = {
    "hidden_pass_rate": "not a correctness measure under the brief prompt: hidden tests call names "
                        "the brief does not give (prereg-v1.2, E2 metric 1)",
    "task_pass": "not a correctness measure under the brief prompt (same reason)",
    "score": "detailed-prompt cells use only judged detailed units",
    "score_core": "sensitivity: items tagged [exact] left out",
}
SIGN = {
    "diff": "spec minus vibe",
    "interaction": "(spec - vibe | brief) - (spec - vibe | detailed)",
    "detail_effect": "brief minus detailed, within one arm",
}


# --------------------------------------------------------------------------- loading


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return None


def _checklist_sha(tasks_dir: Path) -> dict[str, str]:
    out = {}
    for p in Path(tasks_dir).glob("*/checklist.md"):
        out[p.parent.name] = hashlib.sha256(p.read_text().encode()).hexdigest()
    return out


def judge_fields(unit_dir: Path, checklist_sha: dict[str, str]) -> dict:
    """Judge columns of one unit. `judge_status`: none (no judge.json), unreadable, rejected
    (other judge model or a checklist other than the frozen one) or ok. Only ok carries a score."""
    j = _read_json(unit_dir / "judge.json")
    meta = _read_json(unit_dir / "meta.json") or {}
    row = {"prompt_file": meta.get("prompt_file") or "prompt.md",
           "judge_status": "none", "score": None, "score_core": None, "judge_n_items": None,
           "judge_n_met": None, "judge_n_unclear": None, "judge_all_met": None,
           "judge_reject_reason": None}
    if j is None:
        if (unit_dir / "judge.json").exists():
            row["judge_status"] = "unreadable"
        return row
    if not isinstance(j, dict) or not isinstance(j.get("score"), (int, float)):
        row["judge_status"] = "unreadable"
        return row
    want = checklist_sha.get(unit_dir.parent.name)
    reasons = []
    if j.get("judge_model") != JUDGE_MODEL:
        reasons.append(f"judge_model={j.get('judge_model')}")
    if want is not None and j.get("checklist_sha256") not in (None, want):
        reasons.append("checklist_sha256 differs from data/tasks/<id>/checklist.md")
    if reasons:
        row.update(judge_status="rejected", judge_reject_reason="; ".join(reasons))
        return row
    n, met = j.get("n_items"), j.get("n_met")
    row.update(judge_status="ok", score=float(j["score"]),
               score_core=float(j["score_core"]) if isinstance(j.get("score_core"), (int, float))
               else None,
               judge_n_items=n, judge_n_met=met, judge_n_unclear=j.get("n_unclear"),
               judge_all_met=bool(n and met == n))
    return row


def _load_condition(roots: list[Path], tasks: pd.DataFrame, detail: str,
                    checklist_sha: dict[str, str]) -> pd.DataFrame:
    if not roots:
        return pd.DataFrame()
    with unpriced_cohort_cost_unknown():
        runs = load_runs(roots, tasks)
    if runs.empty:
        return runs
    unit_root, extra = [], []
    for u in runs["unit"]:
        hits = [r for r in roots if (Path(r) / u / "meta.json").is_file()]
        root = Path(hits[0])
        unit_root.append(str(root))
        extra.append(judge_fields(root / u, checklist_sha))
    runs = pd.concat([runs, pd.DataFrame(extra, index=runs.index)], axis=1)
    runs["root"] = unit_root
    runs["detail"] = detail
    return runs


def load_e2(detailed_roots: list[Path], brief_roots: list[Path], tasks_dir: Path,
            task_ids: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(tasks, runs): one row per unit directory of either condition, with `detail`, the judge
    columns (`score` is NaN unless judge_status is ok and the unit is valid) and `root`."""
    tasks = load_tasks(tasks_dir, task_ids)
    sha = _checklist_sha(tasks_dir)
    parts = [_load_condition(list(detailed_roots), tasks, "detailed", sha),
             _load_condition(list(brief_roots), tasks, "brief", sha)]
    runs = pd.concat([p for p in parts if not p.empty], ignore_index=True) if any(
        not p.empty for p in parts) else pd.DataFrame()
    if runs.empty:
        return tasks, runs
    runs["prompt_file_mismatch"] = (
        (runs["detail"] == "brief") != (runs["prompt_file"] == "brief.md"))
    for m in SCORE_METRICS:  # a score counts only on a valid unit with an accepted judgement
        runs[m] = pd.to_numeric(runs[m], errors="coerce").where(
            runs["valid"].astype(bool) & (runs["judge_status"] == "ok"))
    runs["judged"] = runs["valid"].astype(bool) & runs["score"].notna()
    for c in ("hidden_total", "hidden_passed", "hidden_pass_rate", "task_pass"):
        if c not in runs:
            runs[c] = None
    ht = pd.to_numeric(runs["hidden_total"], errors="coerce")
    hp = pd.to_numeric(runs["hidden_passed"], errors="coerce")
    runs["hidden_all_pass"] = ((hp == ht) & (ht > 0)).where(ht.notna())
    return tasks, runs


# --------------------------------------------------------------------------- coverage


def coverage(runs: pd.DataFrame, tasks: pd.DataFrame, cohorts: list[str], reps: int
             ) -> pd.DataFrame:
    """Per (detail, cohort, tier, arm): units the design calls for, present, graded (valid),
    excluded system errors, not yet finished, judged, graded but without an accepted judgement."""
    keys = ["cohort", "task_id", "arm", "rep"]
    rows = []
    for detail in DETAILS:
        exp = expected_units(tasks, cohorts, reps)
        sub = runs[runs["detail"] == detail] if not runs.empty else pd.DataFrame(
            columns=keys + ["status", "judged", "judge_status", "valid"])
        st = unit_status(exp, sub)
        extra = sub[keys + ["judged", "judge_status"]] if len(sub) else pd.DataFrame(
            columns=keys + ["judged", "judge_status"])
        st = st.merge(extra, on=keys, how="left")
        for (c, tier, arm), g in st.groupby(["cohort", "tier", "arm"], sort=False):
            graded = g["status"] == "done"
            judged = g["judged"].fillna(False).astype(bool)
            js = g["judge_status"].fillna("none")
            rows.append({
                "detail": detail, "cohort": c, "tier": tier, "arm": arm,
                "expected": len(g),
                "present": int((g["status"] != "missing").sum()),
                "graded": int(graded.sum()),
                "excluded_error": int((g["status"] == "excluded").sum()),
                "not_finished": int((~g["status"].isin(["done", "excluded"])).sum()),
                "judged": int(judged.sum()),
                "graded_not_judged": int((graded & ~judged).sum()),
                "judge_rejected": int((graded & (js == "rejected")).sum()),
                "judge_unreadable": int((graded & (js == "unreadable")).sum()),
            })
    return pd.DataFrame(rows)


def coverage_totals(cov: pd.DataFrame) -> list[dict]:
    num = [c for c in cov.columns if c not in ("detail", "cohort", "tier", "arm")]
    return cov.groupby(["detail", "cohort"], sort=False)[num].sum().reset_index().to_dict(
        "records")


# --------------------------------------------------------------------------- estimators


def _all_tiers(runs: pd.DataFrame) -> pd.DataFrame:
    return runs.assign(tier="all")


def brief_arm_diffs(valid: pd.DataFrame, metric: str, cohorts: list[str], tiers: list[str], *,
                    B: int, seed: int) -> dict[str, Estimate]:
    """E2 primary form: within the brief condition, spec minus vibe of `metric`, per cohort and
    pooled, over all tasks (and per tier). Reuses the locked prereg-v1 estimators."""
    b = valid[valid["detail"] == "brief"]
    out = {}
    allt = _all_tiers(b)
    for c in cohorts:
        out[f"{c}.all"] = paired_diff(allt, c, "all", metric, B=B, seed=seed)
        for t in tiers:
            out[f"{c}.{t}"] = paired_diff(b, c, t, metric, B=B, seed=seed)
    out["pooled.all"] = pooled_diff(allt, metric, cohorts, "all", B=B, seed=seed)
    for t in tiers:
        out[f"pooled.{t}"] = pooled_diff(b, metric, cohorts, t, B=B, seed=seed)
    return out


COLS4 = ("detailed_spec", "detailed_vibe", "brief_spec", "brief_vibe")


def detail_arm_table(valid: pd.DataFrame, metric: str, cohort: str) -> pd.DataFrame:
    """Per task: the four cell means (detail x arm) of one cohort; tasks with all four only."""
    sub = valid[valid["cohort"] == cohort][["detail", "task_id", "arm", metric]].copy()
    sub[metric] = pd.to_numeric(sub[metric].astype("float64"), errors="coerce")
    sub = sub.dropna(subset=[metric])
    if sub.empty:
        return pd.DataFrame(columns=list(COLS4))
    m = sub.groupby(["task_id", "detail", "arm"])[metric].mean().unstack(["detail", "arm"])
    m.columns = [f"{d}_{a}" for d, a in m.columns]
    for c in COLS4:
        if c not in m:
            m[c] = np.nan
    return m[list(COLS4)].dropna()


def pooled_detail_arm_table(valid: pd.DataFrame, metric: str, cohorts: list[str]
                            ) -> pd.DataFrame:
    """Per task: each of the four columns averaged over the cohorts that have all four cells for
    that task (each cohort one weight), so the pooled interaction is the mean of the cohorts'
    interactions in every task."""
    tabs = [detail_arm_table(valid, metric, c) for c in cohorts]
    tabs = [t for t in tabs if len(t)]
    if not tabs:
        return pd.DataFrame(columns=list(COLS4))
    allt = pd.concat(tabs, keys=range(len(tabs)), names=["cohort_i", "task_id"])
    return allt.groupby(level="task_id").mean()[list(COLS4)]


def _col(i):
    return lambda x: x[..., i].mean(-1)


def _diff(i, j):
    return lambda x: (x[..., i] - x[..., j]).mean(-1)


def interaction(table: pd.DataFrame, *, B: int, seed: int) -> dict[str, Estimate]:
    """The 2 x 2 on one per-task table (columns COLS4); every resample uses the same tasks for
    all four cells (prereg-v1 9.1, 2 x 2 rule)."""
    data = table[list(COLS4)].to_numpy(float) if len(table) else np.empty((0, 4))
    d, b = 0, 2  # detailed_spec, brief_spec column offsets
    out = {f"mean.{c}": boot_stat(data, _col(i), B=B, seed=seed) for i, c in enumerate(COLS4)}
    out["diff.detailed"] = boot_stat(data, _diff(d, d + 1), B=B, seed=seed)
    out["diff.brief"] = boot_stat(data, _diff(b, b + 1), B=B, seed=seed)
    out["detail_effect.spec"] = boot_stat(data, _diff(b, d), B=B, seed=seed)
    out["detail_effect.vibe"] = boot_stat(data, _diff(b + 1, d + 1), B=B, seed=seed)
    out["interaction"] = boot_stat(
        data, lambda x: ((x[..., b] - x[..., b + 1]) - (x[..., d] - x[..., d + 1])).mean(-1),
        B=B, seed=seed)
    for e in out.values():
        e.extra["reference_only"] = len(table) < 6
    return out


def interaction_all(valid: pd.DataFrame, metric: str, cohorts: list[str], *, B: int, seed: int
                    ) -> dict[str, Estimate]:
    out = {}
    for c in cohorts:
        for k, e in interaction(detail_arm_table(valid, metric, c), B=B, seed=seed).items():
            out[f"{c}.{k}"] = e
    for k, e in interaction(pooled_detail_arm_table(valid, metric, cohorts), B=B,
                            seed=seed).items():
        e.extra["cohorts"] = list(cohorts)
        out[f"pooled.{k}"] = e
    return out


# --------------------------------------------------------------------------- judge validity


def judge_validity(valid: pd.DataFrame, *, B: int, seed: int,
                   reference: str = "hidden_all_pass") -> dict:
    """prereg-v1.2 (b): on judged detailed-prompt units, agreement between "every checklist item
    met" and passing every hidden test (`reference`). Counts, raw agreement with a task-bootstrap
    interval, Cohen's kappa, and the two conditional rates."""
    d = valid[(valid["detail"] == "detailed") & valid["judged"].astype(bool)].copy()
    d = d[d[reference].notna()]
    out: dict = {"reference": reference, "n_units": len(d)}
    if d.empty:
        return out
    j = d["judge_all_met"].astype(bool)
    r = d[reference].astype(bool)
    agree = (j == r).astype(float)
    per_task = d.assign(_a=agree).groupby("task_id")["_a"].agg(["sum", "size"])
    k = cohen_kappa(j.map(str), r.map(str))
    out.update({
        "n_tasks": len(per_task),
        "both_pass": int((j & r).sum()), "judge_only": int((j & ~r).sum()),
        "tests_only": int((~j & r).sum()), "neither": int((~j & ~r).sum()),
        "agreement": boot_ratio(per_task["sum"].to_numpy(), per_task["size"].to_numpy(),
                                B=B, seed=seed).to_dict(),
        "kappa": k["kappa"], "pe": k["pe"],
        "p_all_met_given_pass": float(j[r].mean()) if r.any() else None,
        "p_not_all_met_given_fail": float((~j[~r]).mean()) if (~r).any() else None,
        "spearman_score_vs_hidden_pass_rate": _spearman(d["score"], d["hidden_pass_rate"]),
    })
    out["by_cohort"] = {}
    for c, g in d.groupby("cohort"):
        jj, rr = g["judge_all_met"].astype(bool), g[reference].astype(bool)
        kk = cohen_kappa(jj.map(str), rr.map(str))
        out["by_cohort"][c] = {"n_units": len(g), "agreement": float((jj == rr).mean()),
                               "kappa": kk["kappa"], "both_pass": int((jj & rr).sum()),
                               "judge_only": int((jj & ~rr).sum()),
                               "tests_only": int((~jj & rr).sum()),
                               "neither": int((~jj & ~rr).sum())}
    return out


def _spearman(a: pd.Series, b: pd.Series):
    x = pd.DataFrame({"a": pd.to_numeric(a, errors="coerce"),
                      "b": pd.to_numeric(b, errors="coerce")}).dropna()
    if len(x) < 3 or x["a"].nunique() < 2 or x["b"].nunique() < 2:
        return None
    return float(x["a"].rank().corr(x["b"].rank()))


# --------------------------------------------------------------------------- summary


def task_cells(valid: pd.DataFrame, metrics: list[str]) -> pd.DataFrame:
    keys = ["detail", "cohort", "tier", "task_id", "arm"]
    v = valid.copy()
    for m in metrics:
        v[m] = pd.to_numeric(v[m].astype("float64"), errors="coerce")
    g = v.groupby(keys)
    out = g.size().rename("n_valid").to_frame()
    out["n_judged"] = g["judged"].sum()
    for m in metrics:
        out[m] = g[m].mean()
    return out.reset_index()


def estimates_table(est: dict) -> pd.DataFrame:
    rows = []
    for k, e in est.items():
        if isinstance(e, dict) and "estimate" in e:
            rows.append({"key": k, "estimate": e["estimate"], "ci_low": e["ci_low"],
                         "ci_high": e["ci_high"], "n_tasks": e["n_tasks"],
                         "n_undefined": e.get("n_undefined"),
                         "reference_only": e.get("reference_only")})
    return pd.DataFrame(rows, columns=["key", "estimate", "ci_low", "ci_high", "n_tasks",
                                       "n_undefined", "reference_only"])


def build_e2(runs: pd.DataFrame, tasks: pd.DataFrame, cohorts: list[str], reps: int, *,
             B: int = B_E2, seed: int = SEED_DEFAULT) -> tuple[dict, dict[str, pd.DataFrame]]:
    in_design = (runs["task_id"].isin(tasks["task_id"]) & runs["cohort"].isin(cohorts)
                 & (runs["rep"] <= reps))
    ignored = runs.loc[~in_design, "unit"].tolist()
    runs = runs[in_design].copy()
    valid = runs[runs["valid"].astype(bool)].copy()
    tiers = [t for t in TIERS if t in set(tasks["tier"])]
    cov = coverage(runs, tasks, cohorts, reps)
    est: dict[str, dict | None] = {}

    for m in SCORE_METRICS:
        for k, e in brief_arm_diffs(valid, m, cohorts, tiers, B=B, seed=seed).items():
            est[f"primary.{m}.{k}"] = e.to_dict()
    detailed_judged = int(valid[(valid["detail"] == "detailed")]["judged"].sum())
    x_metrics = list(AUTO_METRICS) + list(AUTO_EXTRA) + list(HIDDEN_METRICS)
    if detailed_judged:
        x_metrics += list(SCORE_METRICS)
    for m in x_metrics:
        for k, e in interaction_all(valid, m, cohorts, B=B, seed=seed).items():
            est[f"x2.{m}.{k}"] = e.to_dict()

    validity = {"hidden_all_pass": judge_validity(valid, B=B, seed=seed),
                "task_pass": judge_validity(valid, B=B, seed=seed, reference="task_pass")}
    unjudged = runs[runs["valid"].astype(bool) & ~runs["judged"].astype(bool)][
        ["unit", "detail", "cohort", "task_id", "arm", "rep", "judge_status",
         "judge_reject_reason", "root"]]
    metrics = list(dict.fromkeys(list(SCORE_METRICS) + x_metrics))
    summary = {
        "meta": {
            "analysis": "E2 of prereg-v1.2 (brief prompt; detail x arm)",
            "exploratory": EXPLORATORY_NOTE,
            "bootstrap": {"B": B, "seed": seed, "ci": CI_TYPE,
                          "task_set": "all tasks of the three tiers together (key suffix .all); "
                                      "per tier under .<tier>"},
            "sign": SIGN,
            "notes": NOTES,
            "cohorts": cohorts, "reps": reps,
            "tasks": tasks[["task_id", "tier"]].to_dict("records"),
            "judge_model": JUDGE_MODEL,
            "score_on_detailed": bool(detailed_judged),
            "ignored_units_outside_design": ignored,
            "versions": {p: version(p) for p in ("numpy", "pandas")},
        },
        "coverage_totals": coverage_totals(cov),
        "coverage": cov.to_dict("records"),
        "unjudged_valid_units": len(unjudged),
        "prompt_file_mismatch": runs.loc[runs["prompt_file_mismatch"].astype(bool), "unit"]
        .tolist(),
        "estimates": est,
        "judge_validity": validity,
    }
    tables = {
        "coverage": cov,
        "unjudged_units": unjudged,
        "task_cells": task_cells(valid, metrics),
        "estimates": estimates_table(est),
    }
    return _round_floats(summary), tables


# --------------------------------------------------------------------------- figures


def fig_score_diff(est: dict, cohorts: list[str], out: Path) -> list[str]:
    from sdlc_analysis.figures import COHORT_MARK, GRID, INK, MUTED, SERIES, _save, _style, plt

    rows = []
    for name in list(cohorts) + ["pooled"]:
        for j, m in enumerate(SCORE_METRICS):
            e = est.get(f"primary.{m}.{name}.all")
            if e and e.get("estimate") is not None:
                rows.append((name, m, j, e))
    if not rows:
        return []
    fig, ax = plt.subplots(figsize=(6.4, 0.35 * len(rows) + 1.0))
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.axvline(0, color=MUTED, linewidth=1)
    for i, (name, m, j, e) in enumerate(rows):
        y = len(rows) - 1 - i
        ax.plot([e["ci_low"], e["ci_high"]], [y, y], color=SERIES[j], linewidth=2,
                solid_capstyle="round")
        ax.scatter([e["estimate"]], [y], color=SERIES[j], marker=COHORT_MARK.get(name, "o"),
                   s=40, zorder=3, edgecolors="white", linewidths=1)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{n} / {m} (n={e['n_tasks']})" for n, m, _, e in reversed(rows)],
                       fontsize=8)
    ax.set_xlim(-1.05, 1.05)
    ax.set_xlabel("checklist score, spec minus vibe, brief prompt (95% bootstrap CI)",
                  color=INK, fontsize=9)
    ax.set_title("E2 (exploratory): checklist score difference", fontsize=10, color=INK,
                 loc="left")
    return _save(fig, out, "e2_score_diff")


def fig_detail_by_arm(est: dict, cohorts: list[str], metric: str, out: Path) -> list[str]:
    from sdlc_analysis.figures import INK, SERIES, _save, _style, plt

    names = [n for n in list(cohorts) + ["pooled"]
             if all(est.get(f"x2.{metric}.{n}.mean.{c}", {}) and
                    est[f"x2.{metric}.{n}.mean.{c}"].get("estimate") is not None for c in COLS4)]
    if not names:
        return []
    fig, axes = plt.subplots(1, len(names), figsize=(2.2 * len(names) + 0.6, 3.0), sharey=True,
                             squeeze=False)
    for ax, n in zip(axes[0], names):
        _style(ax)
        for j, arm in enumerate(ARMS):
            vals = [est[f"x2.{metric}.{n}.mean.{d}_{arm}"] for d in DETAILS]
            ax.plot([0, 1], [v["estimate"] for v in vals], color=SERIES[j], linewidth=2,
                    marker="os"[j], markersize=6, label=arm)
            for x, v in zip((0, 1), vals):
                ax.plot([x, x], [v["ci_low"], v["ci_high"]], color=SERIES[j], linewidth=1,
                        alpha=0.6)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(list(DETAILS), fontsize=8)
        ax.set_xlim(-0.4, 1.4)
        n_t = est[f"x2.{metric}.{n}.interaction"]["n_tasks"]
        ax.set_title(f"{n} (n={n_t})", fontsize=9, color=INK, loc="left")
    axes[0][0].set_ylabel(f"{metric} (mean over tasks)", fontsize=9, color=INK)
    axes[0][0].legend(frameon=False, fontsize=8)
    fig.suptitle(f"E2 (exploratory): prompt detail x arm, {metric}", fontsize=10, color=INK,
                 x=0.02, ha="left")
    return _save(fig, out, f"e2_detail_x_arm_{metric}")


# --------------------------------------------------------------------------- CLI


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sdlc-e2", description=__doc__.splitlines()[0])
    p.add_argument("--detailed", type=Path, nargs="*", default=[],
                   help="detailed-prompt roots (main, main-tiers, E1 haiku)")
    p.add_argument("--brief", type=Path, nargs="+", required=True, help="brief-prompt root(s)")
    p.add_argument("--tasks", type=Path, default=REPO / "data" / "tasks")
    p.add_argument("--out", type=Path, default=E2_OUT)
    p.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p.add_argument("--bootstrap", type=int, default=B_E2, help="resamples B (prereg-v1.2: 9999)")
    p.add_argument("--task-ids", default=None, help="default: every non-pilot task")
    p.add_argument("--cohorts", default=",".join(E2_COHORTS))
    p.add_argument("--reps", type=int, default=3)
    return p.parse_args(argv)


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    a = parse_args(sys.argv[1:] if argv is None else argv)
    cohorts = [c for c in a.cohorts.split(",") if c]
    tasks, runs = load_e2(a.detailed, a.brief, a.tasks,
                          a.task_ids.split(",") if a.task_ids else None)
    if runs.empty:
        raise SystemExit("no run units found")
    summary, tables = build_e2(runs, tasks, cohorts, a.reps, B=a.bootstrap, seed=a.seed)
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    runs.drop(columns=[c for c in ("error",) if c in runs]).to_csv(out / "runs.csv", index=False)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
    figs = fig_score_diff(summary["estimates"], cohorts, out / "figures")
    for m in ("score", "regression_any", "ai_tests_added"):
        figs += fig_detail_by_arm(summary["estimates"], cohorts, m, out / "figures")
    summary["figures"] = figs
    summary["meta"]["roots"] = {"detailed": [str(p) for p in a.detailed],
                                "brief": [str(p) for p in a.brief]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    tot = summary["coverage_totals"]
    log.info("E2: %d units loaded (%d graded, %d judged) -> %s", len(runs),
             sum(r["graded"] for r in tot), sum(r["judged"] for r in tot), out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
