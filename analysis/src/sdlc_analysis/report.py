"""Everything of prereg-v1 section 9 computed from the runs table into one JSON-able dict
(summary.json), keyed by stable names."""

from importlib.metadata import version

import numpy as np
import pandas as pd

from sdlc_analysis import mixed
from sdlc_analysis.bootstrap import CI_TYPE, Estimate, verdict
from sdlc_analysis.estimators import (
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
from sdlc_analysis.labels import CLAUDE
from sdlc_analysis.load import TIERS, completeness, expected_units, unit_status

PRIMARY_COHORT, PRIMARY_TIER = "claude-sonnet", "small"
MI_MARGIN = -5.0
# secondary metrics (prereg 6, 9.5): name -> (hypothesis, direction, margin); None = descriptive
SECONDARY = {
    "tokens_total": ("H2", 1, 0.0),
    "wall_s": ("H2", 1, 0.0),
    "static_errors": ("H3a", -1, 0.0),
    "regression_any": ("H3b", -1, 0.0),
    "radon_mi_delta": ("H3c", 1, MI_MARGIN),
    "hidden_pass_rate": None,
    "regressions_n": None,
    "ruff_errors": None,
    "pyrefly_errors": None,
    "architecture_pass": None,
    "radon_cc_delta": None,
    "ai_tests_added": None,
    "ai_changed_line_coverage": None,
    "patch_lines": None,
    "tok_input_uncached": None,
    "tok_cache_read": None,
    "tok_cache_write_5m": None,
    "tok_cache_write_1h": None,
    "tok_output": None,
    "cost_usd": None,
    "turns": None,  # comparable between arms within a cohort only
}
SENSITIVITY = {
    "upstream_urls": lambda r: r["upstream"].astype(bool),
    "pytest_config_touched": lambda r: r["pytest_config_touched"].astype(bool),
    "spec_noncompliant": lambda r: (r["arm"] == "spec") & ~r["process_artifacts"].astype(bool),
}


def _est(e: Estimate | None) -> dict | None:
    return None if e is None else e.to_dict()


def _round_floats(x):
    if isinstance(x, float):
        return None if not np.isfinite(x) else x
    if isinstance(x, dict):
        return {str(k): _round_floats(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_round_floats(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return _round_floats(float(x))
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def _counts(df: pd.DataFrame, by: list[str], col: str | None = None) -> list[dict]:
    if df.empty:
        return []
    if col is None:
        g = df.groupby(by).size().rename("n").reset_index()
    else:
        s = df[col].astype(bool)
        g = df.assign(_v=s).groupby(by)["_v"].agg(["sum", "size"]).reset_index()
        g = g.rename(columns={"sum": "n", "size": "of"})
        g["share"] = g["n"] / g["of"]
    return g.to_dict("records")


def descriptives(runs: pd.DataFrame, valid: pd.DataFrame) -> dict:
    v = valid
    spec, vibe = v[v["arm"] == "spec"], v[v["arm"] == "vibe"]
    vibe_docs = vibe.assign(
        any_doc=vibe["patch_design_doc"].astype(bool) | vibe["patch_plan_doc"].astype(bool))
    sha = runs.dropna(subset=["prompt_sha256"]).groupby(["task_id", "arm"])["prompt_sha256"]
    nuniq = sha.nunique()
    excluded = runs[runs["status"] == "excluded"]
    return {
        "status_counts": _counts(runs, ["cohort", "tier", "status"]),
        "timeouts": _counts(v, ["cohort", "tier", "arm"], "timed_out"),
        "nonzero_exit": _counts(v, ["cohort", "arm"], "nonzero_exit"),
        "grader_timeout_twice": _counts(v, ["cohort", "arm"], "grader_timeout"),
        "excluded_runs": excluded[["unit", "arm", "error", "error_attempts"]].to_dict("records"),
        "excluded_by_arm": excluded.groupby("arm").size().to_dict(),
        "compliance_spec": _counts(spec, ["cohort", "tier"], "process_artifacts"),
        "vibe_wrote_design_or_plan": _counts(vibe_docs, ["cohort", "tier"], "any_doc"),
        "vibe_process_artifacts": _counts(vibe, ["cohort", "tier"], "process_artifacts"),
        "pytest_ran": _counts(v, ["cohort", "arm"], "pytest_ran"),
        "ai_tests_added_mean": v.groupby(["cohort", "arm"])["ai_tests_added"].mean()
        .reset_index().to_dict("records"),
        "upstream_urls": _counts(v, ["cohort", "arm"], "upstream"),
        "upstream_urls_field_missing": int((~v["upstream_urls_known"].astype(bool)).sum()),
        "pytest_config_touched": _counts(v, ["cohort", "arm"], "pytest_config_touched"),
        "tool_versions": _counts(v.fillna({"tool_version": "unknown"}),
                                 ["cohort", "arm", "tool_version"]),
        "tokens_unsplit_upper_bound": _counts(v, ["cohort"], "tokens_unsplit"),
        "runs_without_cost": int(v["cost_usd"].isna().sum()),
        "prompt_sha256_check": {
            "cells": len(nuniq),
            "cells_with_one_value": int((nuniq == 1).sum()),
            "violations": [{"task_id": t, "arm": a, "values": int(n)}
                           for (t, a), n in nuniq.items() if n != 1],
        },
        "served_model_unknown": _counts(v, ["cohort"], "model_served_unknown"),
        "offtable_model_cost": _counts(v, ["cohort", "arm"], "cost_has_offtable_model"),
        "offtable_models": sorted({m for ms in v["offtable_models"].dropna() for m in
                                   str(ms).split(",") if m}),
        "codex_runs_with_several_usage_records": int(
            (pd.to_numeric(v["usage_records"], errors="coerce") > 1).sum()),
        "shared_cpu_window": shared_cpu_window(v),
        "concurrent_tiers_window": concurrent_tiers_window(v),
    }


# prereg-v1.1 operational note: coverage measurements and range-task checks shared the CPU with
# the first small-tier runs, 19:16-19:52 local time (UTC+7) on 2026-11-15
WINDOW_UTC = ("2026-11-15T12:16:00+00:00", "2026-11-15T12:52:00+00:00")


def shared_cpu_window(v: pd.DataFrame) -> dict:
    start = pd.to_datetime(v["started_at"], utc=True, errors="coerce")
    lo, hi = (pd.Timestamp(x) for x in WINDOW_UTC)
    inside = v[(start >= lo) & (start <= hi)]
    return {"window_utc": list(WINDOW_UTC), "runs_started": len(inside),
            "timeouts": int(inside["timed_out"].astype(bool).sum()),
            "by_cohort": _counts(inside, ["cohort"], "timed_out")}


def build_summary(
    runs: pd.DataFrame,
    tasks: pd.DataFrame,
    cohorts: list[str],
    reps: int,
    *,
    B: int,
    seed: int,
    overlap: dict | None = None,
    labels: dict | None = None,
    model_B: int = mixed.B_MODEL_DEFAULT,
    jobs: int = 1,
) -> tuple[dict, dict]:
    """Returns (summary, tables). `tables` holds DataFrames written as CSV next to it."""
    runs = runs.copy()
    runs["tokens_unsplit"] = runs["tokens_split"].map(lambda x: x is False)
    runs["model_served_unknown"] = runs["agent"] == "codex"
    in_design = (runs["task_id"].isin(tasks["task_id"]) & runs["cohort"].isin(cohorts)
                 & (runs["rep"] <= reps))
    ignored = runs[~in_design]["unit"].tolist()
    runs = runs[in_design]
    valid = runs[runs["valid"]].copy()
    exp = expected_units(tasks, cohorts, reps)
    comp = completeness(exp, runs)
    st = unit_status(exp, runs)
    complete = {(r["cohort"], r["tier"]) for r in comp.to_dict("records") if r["complete"]}
    tiers = [t for t in TIERS if t in set(tasks["tier"])]
    est: dict[str, dict | None] = {}
    verdicts: dict[str, str] = {}
    tables: dict[str, pd.DataFrame] = {}
    kw = {"B": B, "seed": seed}

    # --- per (cohort, tier): pass difference in H1 format, secondary metrics, cost-effectiveness
    diff_rows = []
    for c in cohorts:
        for t in tiers:
            key = f"{c}.{t}"
            if (c, t) not in complete:
                sub = valid[(valid["cohort"] == c) & (valid["tier"] == t)]
                cell = comp[(comp["cohort"] == c) & (comp["tier"] == t)]
                est[f"descriptive_incomplete.{key}"] = {
                    "complete": False,
                    "valid_runs": len(sub),
                    "not_run_or_pending": int(cell["pending"].sum() + cell["missing"].sum()),
                    "pass_rate_spec_runs": _mean(sub[sub["arm"] == "spec"]["task_pass"]),
                    "pass_rate_vibe_runs": _mean(sub[sub["arm"] == "vibe"]["task_pass"]),
                }
                continue
            e = paired_diff(valid, c, t, "task_pass", **kw)
            est[f"pass_diff.{key}"] = _est(e)
            verdicts[f"pass_diff.{key}"] = verdict(e.ci_low, e.ci_high, 1)
            sv = valid[(valid["cohort"] == c) & (valid["tier"] == t)]
            for (tid, arm), g in sv.groupby(["task_id", "arm"]):
                diff_rows.append({"cohort": c, "tier": t, "task_id": tid, "arm": arm,
                                  "n_valid": len(g), "pass_rate": g["task_pass"].astype(float)
                                  .mean(), "hidden_pass_rate": g["hidden_pass_rate"].mean()})
            for m, spec_ in SECONDARY.items():
                e2 = paired_diff(valid, c, t, m, **kw)
                est[f"secondary.{m}.{key}"] = _est(e2)
                if spec_ is not None:
                    hyp, direction, margin = spec_
                    verdicts[f"{hyp}.{m}.{key}"] = verdict(e2.ci_low, e2.ci_high, direction,
                                                           margin)
            for k2, e3 in cost_effectiveness(valid, c, t, **kw).items():
                est[f"cost_eff.{key}.{k2}"] = _est(e3)
            if (sv["agent"] == "codex").any():
                # codex: per-call 272k threshold unknown; the same at the > 272k price (bound)
                for k2, e3 in cost_effectiveness(valid, c, t, cost_col="cost_usd_upper",
                                                 **kw).items():
                    est[f"cost_eff_upper.{key}.{k2}"] = _est(e3)
            est[f"variability.{key}"] = variability(sv)
    cells = pd.DataFrame(diff_rows)
    tables["task_cells"] = cells

    # per-task differences (table for tiers with < 6 tasks, and the size figure)
    td_rows = []
    for c in cohorts:
        for t in tiers:
            if (c, t) in complete:
                for tid, d in task_diffs(valid, "task_pass", c, t).items():
                    td_rows.append({"cohort": c, "tier": t, "task_id": tid, "pass_diff": d})
    task_diff_table = pd.DataFrame(td_rows, columns=["cohort", "tier", "task_id", "pass_diff"])
    task_diff_table = task_diff_table.merge(tasks[["task_id", "src_lines"]], on="task_id",
                                            how="left")
    tables["task_diffs"] = task_diff_table

    # pooled per tier (aggregate figure): cohorts complete in that tier
    pooled_rows = []
    for t in tiers:
        cs = [c for c in cohorts if (c, t) in complete]
        if cs:
            est[f"pooled.pass_diff.{t}"] = _est(pooled_diff(valid, "task_pass", cs, t, **kw))
            for tid, d in pooled_task_diffs(valid, "task_pass", cs, t).items():
                pooled_rows.append({"tier": t, "task_id": tid, "pooled_pass_diff": d})
    tables["pooled_task_diffs"] = pd.DataFrame(
        pooled_rows, columns=["tier", "task_id", "pooled_pass_diff"]).merge(
        tasks[["task_id", "src_lines"]], on="task_id", how="left")

    # --- H1 (confirmatory)
    if (PRIMARY_COHORT, PRIMARY_TIER) in complete:
        est["h1.primary"] = est[f"pass_diff.{PRIMARY_COHORT}.{PRIMARY_TIER}"]
        verdicts["H1"] = verdicts[f"pass_diff.{PRIMARY_COHORT}.{PRIMARY_TIER}"]
    else:
        est["h1.primary"] = None
        verdicts["H1"] = "no_confirmatory_test"

    # --- H4 / RQ5: 2 x 2 per tier where both Claude cohorts are complete
    for t in tiers:
        if all((c, t) in complete for c in CLAUDE):
            for k, e in two_by_two(valid, t, *CLAUDE, **kw).items():
                est[f"h4.{t}.{k}"] = _est(e)
            dd = est[f"h4.{t}.diff_of_diffs"]
            verdicts[f"H4.{t}"] = verdict(dd["ci_low"], dd["ci_high"], 1)

    # --- H5
    h5_cohorts = [c for c in cohorts if all((c, t) in complete for t in TIERS)]
    h5 = {"cohorts": h5_cohorts}
    if h5_cohorts and "large" in tiers and "small" in tiers:
        p = tier_diff(valid, "task_pass", h5_cohorts, "large", "small", **kw)
        est["h5.primary"] = _est(p)
        est["h5.hidden_pass_rate"] = _est(
            tier_diff(valid, "hidden_pass_rate", h5_cohorts, "large", "small", **kw))
        h5_runs = valid[valid["cohort"].isin(h5_cohorts)]
        model = mixed.fit_h5_model(h5_runs, h5_cohorts, B=model_B, seed=seed, jobs=jobs)
        h5["mixed_model"] = model
        inter = model["interaction"] or {}
        verdicts["H5"] = h5_verdict(p.ci_low, p.ci_high, inter.get("coef"),
                                    inter.get("scale", "logit"))
        # prereg-v1.1 sensitivity: the same ladder on log(graded_src_lines)
        h5["mixed_model_graded"] = mixed.fit_h5_model(
            h5_runs, h5_cohorts, x_col="log_graded_src_lines", B=model_B, seed=seed, jobs=jobs)
        h5["reference_only_tiers"] = [t for t in TIERS
                                      if len(pooled_task_diffs(valid, "task_pass", h5_cohorts,
                                                               t)) < 6]
    else:
        est["h5.primary"] = None
        h5["reason"] = "no cohort is complete in all three tiers"
        verdicts["H5"] = "not_estimable"

    # --- sensitivity (9.7): H1 primary and H5 primary, one exclusion at a time
    for name, mask_fn in SENSITIVITY.items():
        keep = valid[~mask_fn(valid)]
        dropped = int(mask_fn(valid).sum())
        if (PRIMARY_COHORT, PRIMARY_TIER) in complete:
            e = paired_diff(keep, PRIMARY_COHORT, PRIMARY_TIER, "task_pass", **kw)
            e.extra["runs_dropped_all_cohorts"] = dropped
            est[f"sensitivity.{name}.h1"] = _est(e)
        if h5_cohorts:
            e = tier_diff(keep, "task_pass", h5_cohorts, "large", "small", **kw)
            e.extra["runs_dropped_all_cohorts"] = dropped
            est[f"sensitivity.{name}.h5"] = _est(e)
    if overlap is not None and h5_cohorts:
        drop = set(overlap.get("tasks", []))
        keep = valid[~valid["task_id"].isin(drop)]
        e = tier_diff(keep, "task_pass", h5_cohorts, "large", "small", **kw)
        e.extra["tasks_dropped"] = sorted(drop)
        est["sensitivity.overlap.h5"] = _est(e)

    # --- exploratory: size groups inside the small tier
    for c in cohorts:
        if (c, "small") not in complete:
            continue
        for grp in ("small", "medium", "large"):
            sub = valid[(valid["tier"] == "small") & (valid["size_group"] == grp)]
            est[f"exploratory.size_group.{c}.{grp}"] = _est(
                paired_diff(sub, c, "small", "task_pass", **kw))

    est["variability.all_complete"] = variability(
        valid[[(c, t) in complete for c, t in zip(valid["cohort"], valid["tier"])]])

    # number of secondary comparisons: every verdict except H1 and its own H1-format copy
    h1_copy = f"pass_diff.{PRIMARY_COHORT}.{PRIMARY_TIER}"
    n_secondary = sum(1 for k in verdicts if k not in ("H1", h1_copy))

    pending = st[~st["status"].isin(["done", "excluded"])]
    summary = {
        "meta": {
            "prereg": "prereg-v1 (section 9); tiers from prereg-v1.1",
            "bootstrap": {"B": B, "seed": seed, "ci": CI_TYPE},
            "cohorts": cohorts,
            "reps": reps,
            "tasks": tasks[["task_id", "tier", "src_lines"]].to_dict("records"),
            "n_secondary_comparisons": n_secondary,
            "versions": {p: version(p) for p in ("numpy", "pandas", "scipy", "statsmodels")},
            "ignored_units_outside_design": ignored,
        },
        "completeness": comp.to_dict("records"),
        "not_run_units": pending[["cohort", "task_id", "arm", "rep", "status"]]
        .to_dict("records"),
        "h5": h5,
        "case_study": case_study(valid, tasks, complete),
        "overlap": overlap,
        "estimates": est,
        "verdicts": verdicts,
        "descriptives": descriptives(runs, valid),
        "labels": labels,
    }
    return _round_floats(summary), tables


def _mean(s: pd.Series):
    return float(s.astype(float).mean()) if len(s) else None




def case_study(valid: pd.DataFrame, tasks: pd.DataFrame, complete: set) -> dict | None:
    """Prereg 9.9 with the design's rule (7.5): large tier, claude-sonnet; the task with the
    largest |pass-rate difference| (ties: larger original patch); if every difference is 0, the
    task with the largest original patch. In it, the lowest-rep run of each arm; when the arms'
    pass rates differ, one passing run (arm with the higher rate) and one failing run (the other
    arm), each the lowest rep that qualifies."""
    c, t = PRIMARY_COHORT, "large"
    if (c, t) not in complete:
        return None
    d = task_diffs(valid, "task_pass", c, t)
    if d.empty:
        return None
    size = tasks.set_index("task_id")["src_lines"]
    df = pd.DataFrame({"absdiff": d.abs(), "src_lines": size.reindex(d.index)})
    rule = "largest |difference|, ties to the larger original patch"
    if (df["absdiff"] == 0).all():
        rule = "every difference is 0: largest original patch"
    tid = df.sort_values(["absdiff", "src_lines"], ascending=False).index[0]
    runs = valid[(valid["cohort"] == c) & (valid["task_id"] == tid)].sort_values("rep")
    rate = runs.groupby("arm")["task_pass"].apply(lambda s: s.astype(float).mean())
    picks = {}
    if rate.get("spec") != rate.get("vibe") and len(rate) == 2:
        hi = rate.idxmax()
        lo = "vibe" if hi == "spec" else "spec"
        p = runs[(runs["arm"] == hi) & runs["task_pass"].astype(bool)]
        f = runs[(runs["arm"] == lo) & ~runs["task_pass"].astype(bool)]
        picks = {hi: p["unit"].iloc[0] if len(p) else None,
                 lo: f["unit"].iloc[0] if len(f) else None}
    for arm in ("spec", "vibe"):
        if picks.get(arm) is None:
            r = runs[runs["arm"] == arm]
            picks[arm] = r["unit"].iloc[0] if len(r) else None
    return {"task_id": tid, "rule": rule, "pass_diff": float(d[tid]), "units": picks}


# prereg-v1 section 11, 2026-11-15 19:58: medium and large tiers ran alongside the small tier
CONCURRENT_START_UTC = "2026-11-15T12:58:00+00:00"


def concurrent_tiers_window(v: pd.DataFrame) -> dict:
    """Timeouts of runs started inside vs outside the concurrent-tier window: from 19:58 local
    (UTC+7) until the last small-tier run ended (its start plus wall_s)."""
    start = pd.to_datetime(v["started_at"], utc=True, errors="coerce")
    lo = pd.Timestamp(CONCURRENT_START_UTC)
    small = v["tier"] == "small"
    ends = start[small] + pd.to_timedelta(pd.to_numeric(v.loc[small, "wall_s"], errors="coerce"),
                                          unit="s")
    hi = ends.max() if len(ends) and ends.notna().any() else None
    if hi is None or hi < lo:
        return {"window_utc": [CONCURRENT_START_UTC, None], "note": "no small-tier run after start"}
    inside = (start >= lo) & (start <= hi)
    out = {"window_utc": [CONCURRENT_START_UTC, hi.isoformat()]}
    for name, mask in (("inside", inside), ("outside", ~inside & start.notna())):
        out[name] = _counts(v[mask], ["tier", "arm"], "timed_out")
    return out
