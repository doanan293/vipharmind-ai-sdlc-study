"""sdlc-analysis: run the preregistered analysis on a results directory.

uv run sdlc-analysis --results DIR --tasks DIR --out DIR [--seed 20261115]
"""

import argparse
import json
import logging
from pathlib import Path

from sdlc_analysis import figures
from sdlc_analysis.bootstrap import B_DEFAULT, SEED_DEFAULT
from sdlc_analysis.labels import kappa_report, labeling_template, passing_sample
from sdlc_analysis.load import COHORTS, TIERS, load_runs, load_tasks
from sdlc_analysis.mixed import B_MODEL_DEFAULT
from sdlc_analysis.overlap import commit_sets, cross_tier_overlaps, overlap_tasks
from sdlc_analysis.report import build_summary

log = logging.getLogger("sdlc_analysis")


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="sdlc-analysis", description=__doc__.splitlines()[0])
    p.add_argument(
        "--results",
        type=Path,
        required=True,
        nargs="+",
        help="results root(s): <cohort>/<task>/<arm>-r<rep>/ (main and main-tiers)",
    )
    p.add_argument("--tasks", type=Path, required=True, help="tasks dir with */task.toml")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int, default=SEED_DEFAULT)
    p.add_argument("--bootstrap", type=int, default=B_DEFAULT, help="resamples B (prereg: 10000)")
    p.add_argument(
        "--task-ids",
        default=None,
        help="comma-separated tasks of the design (default: every non-pilot task)",
    )
    p.add_argument("--cohorts", default=",".join(COHORTS))
    p.add_argument("--reps", type=int, default=3)
    p.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="ViPharmind git repo, to find cross-tier commit overlap (H5 sensitivity)",
    )
    p.add_argument(
        "--model-bootstrap",
        type=int,
        default=B_MODEL_DEFAULT,
        help="cluster-bootstrap refits of the H5 mixed model (>= 999)",
    )
    p.add_argument("--jobs", type=int, default=1, help="processes for the model bootstrap")
    p.add_argument(
        "--draw-passing-sample",
        action="store_true",
        help="write passing_sample.csv (prereg 9.10); give once, after the deadline",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="with --draw-passing-sample: overwrite an existing passing_sample.csv",
    )
    p.add_argument(
        "--labels",
        type=Path,
        nargs=2,
        metavar=("RATER_A_CSV", "RATER_B_CSV"),
        default=None,
        help="two filled labeling sheets: compute Cohen's kappa",
    )
    return p.parse_args(argv)


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    a = parse_args(argv)
    task_ids = a.task_ids.split(",") if a.task_ids else None
    cohorts = [c for c in a.cohorts.split(",") if c]
    tasks = load_tasks(a.tasks, task_ids)
    runs = load_runs(a.results, tasks)
    if runs.empty:
        raise SystemExit(f"no run units under {a.results}")
    overlap = None
    if a.repo is not None:
        sets = commit_sets(tasks, a.repo)
        pairs = cross_tier_overlaps(tasks, sets)
        overlap = {"pairs": pairs, "tasks": sorted(overlap_tasks(pairs)), "repo": str(a.repo)}
    labels = kappa_report(*a.labels) if a.labels else None
    summary, tables = build_summary(
        runs,
        tasks,
        cohorts,
        a.reps,
        B=a.bootstrap,
        seed=a.seed,
        overlap=overlap,
        labels=labels,
        model_B=a.model_bootstrap,
        jobs=a.jobs,
    )
    out = a.out
    out.mkdir(parents=True, exist_ok=True)
    runs_out = runs.drop(columns=[c for c in ("error",) if c in runs])
    runs_out.to_csv(out / "runs.csv", index=False)
    runs_out.astype(
        {c: "string" for c in runs_out.columns if runs_out[c].dtype == object}
    ).to_parquet(out / "runs.parquet", index=False)
    for name, df in tables.items():
        df.to_csv(out / f"{name}.csv", index=False)
    valid = runs[
        runs["valid"] & runs["task_id"].isin(tasks["task_id"]) & runs["cohort"].isin(cohorts)
    ]
    lab = out / "labeling"
    lab.mkdir(exist_ok=True)
    sheet, key = labeling_template(valid, a.seed)
    sheet.to_csv(lab / "sheet-template.csv", index=False)
    key.to_csv(lab / "key-PRIVATE.csv", index=False)
    sample_path = out / "passing_sample.csv"
    if a.draw_passing_sample:
        if sample_path.exists() and not a.force:
            raise SystemExit(f"{sample_path} exists; --force to redraw")
        passing_sample(valid, a.seed).to_csv(sample_path, index=False)
    summary["passing_sample"] = {"drawn": sample_path.exists()}
    tiers = [t for t in TIERS if t in set(tasks["tier"])]
    est = summary["estimates"]
    figs = figures.effect_vs_size(
        tables["task_diffs"], tables["pooled_task_diffs"], out / "figures"
    )
    figs += figures.pass_diff_forest(est, cohorts, tiers, out / "figures")
    for t in tiers:
        figs += figures.two_by_two_rates(est, t, out / "figures")
    figs += figures.cost_per_pass(est, cohorts, tiers, out / "figures")
    summary["figures"] = figs
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    v = summary["verdicts"]
    log.info(
        "H1: %s; H5: %s; %d runs (%d valid) -> %s",
        v.get("H1"),
        v.get("H5"),
        len(runs),
        int(runs["valid"].sum()),
        out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
