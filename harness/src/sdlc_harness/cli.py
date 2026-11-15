"""Command line entry point: sdlc-harness screen | tasks validate | run."""

import argparse
import json
import logging
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from sdlc_harness.runner import (
    COHORTS_FILE,
    RunConfig,
    load_cohorts,
    plan_units,
    run_all,
    select_tasks,
)
from sdlc_harness.screen import hidden_tests, layer_of, screen_static, src_lines
from sdlc_harness.tasks import load_task, validate_task
from sdlc_harness.vcs import Candidate, list_candidates
from sdlc_harness.verify import check_fail_to_pass


def _f2p(args: tuple[Path, Candidate, Path]) -> tuple[bool, bool, str]:
    repo, c, workroot = args
    result = check_fail_to_pass(repo, c, workroot)
    return result.passed, result.infra_error, result.reason


def screen(repo: Path, ref: str, out: Path, jobs: int, workroot: Path) -> list[dict]:
    candidates = list_candidates(repo, ref)
    verdicts = {c.sha: screen_static(c) for c in candidates}
    survivors = [c for c in candidates if verdicts[c.sha].passed]
    f2p: dict[str, tuple[bool, bool, str]] = {}
    with ProcessPoolExecutor(max_workers=jobs) as pool:
        for c, res in zip(
            survivors, pool.map(_f2p, [(repo, c, workroot) for c in survivors]), strict=True
        ):
            f2p[c.sha] = res

    records = []
    for c in candidates:
        v = verdicts[c.sha]
        criterion, reason = v.failed_criterion, v.reason
        if v.passed:
            ok, infra, why = f2p[c.sha]
            criterion = None if ok else ("infra" if infra else 2)
            reason = why
        try:
            layer = layer_of(c)
        except ValueError:
            layer = None
        records.append(
            {
                "sha": c.sha,
                "subject": c.subject,
                "layer": layer,
                "src_lines": src_lines(c),
                "hidden_tests": hidden_tests(c),
                "failed_criterion": criterion,
                "reason": reason,
            }
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(records, indent=2, ensure_ascii=False) + "\n")
    return records


def _print_funnel(records: list[dict]) -> None:
    remaining = len(records)
    print(f"candidates: {remaining}")
    rejected = Counter(r["failed_criterion"] for r in records if r["failed_criterion"])
    for crit in (1, 4, 5, 2, "infra"):
        remaining -= rejected[crit]
        if crit == "infra":
            continue
        print(f"after criterion {crit}: {remaining} (rejected {rejected[crit]})")
    print(
        f"infrastructure failures (not criterion rejections): {rejected['infra']}; usable: {remaining}"
    )
    kept = [r for r in records if r["failed_criterion"] is None]
    print(f"no layer: {sum(1 for r in kept if r['layer'] is None)} of {len(kept)} kept")


EXPECTED_TASKS = {f"t{i:02d}" for i in range(1, 16)} | {"p01", "p02"}


def validate_tasks(root: Path, repo: Path | None) -> list[str]:
    if not root.is_dir():
        return [f"{root} is not a directory"]
    dirs = sorted(d for d in root.iterdir() if (d / "task.toml").exists())
    errors = []
    found = {d.name for d in dirs}
    if found != EXPECTED_TASKS:
        missing = sorted(EXPECTED_TASKS - found)
        extra = sorted(found - EXPECTED_TASKS)
        errors.append(f"expected task dirs t01-t15, p01, p02; missing {missing}, extra {extra}")
    for d in dirs:
        task = load_task(d, repo)
        if task.id != d.name:
            errors.append(f"{d.name}: id is '{task.id}'")
        errors.extend(validate_task(task))
    return errors


def run(args: argparse.Namespace) -> int:
    cohorts = load_cohorts(args.cohorts_file)
    names = [c.strip() for c in args.cohorts.split(",") if c.strip()]
    unknown = [n for n in names if n not in cohorts]
    if unknown:
        print(f"unknown cohort(s) {unknown}; known: {sorted(cohorts)}")
        return 2
    try:
        task_ids = select_tasks(args.tasks_dir, args.tasks)
    except ValueError as e:
        print(e)
        return 2
    if not task_ids:
        print(f"no tasks match '{args.tasks}' in {args.tasks_dir}")
        return 2
    cfg = RunConfig(
        repo=args.repo,
        tasks_dir=args.tasks_dir,
        cohorts={n: cohorts[n] for n in names},
        timeout_s=args.timeout_s,
        grade_timeout_s=args.grade_timeout_s,
        cache_dir=args.cache_dir,
        work_root=args.work_root,
        accounts_file=args.accounts_file,
        quota_backoff_s=args.quota_backoff_s,
        keep_work=args.keep_work,
    )
    units = plan_units(names, task_ids, args.reps, args.seed)
    print(
        f"{len(units)} units: {len(names)} cohort(s) x {len(task_ids)} task(s) x 2 arms x {args.reps}"
    )
    summary = run_all(units, cfg, args.out, args.jobs)
    print(
        f"done {summary['done']}, already done {summary['skipped']}, "
        f"errors {summary['error']}, quota requeues {summary['quota']}"
    )
    return 1 if summary["error"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sdlc-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("screen", help="screen candidate commits (criteria 1, 4, 5, then 2)")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--ref", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--workroot", type=Path, default=Path(".work"))
    t = sub.add_parser("tasks", help="task files")
    tsub = t.add_subparsers(dest="tasks_command", required=True)
    v = tsub.add_parser("validate", help="check the 17 task dirs (exit 0 when all are valid)")
    v.add_argument("--dir", type=Path, default=Path("tasks"))
    v.add_argument(
        "--repo", type=Path, default=None, help="ViPharmind repo, to check hidden test names"
    )
    r = sub.add_parser("run", help="run agents on tasks and grade them (resumable)")
    r.add_argument("--repo", type=Path, required=True, help="ViPharmind repo (read only)")
    r.add_argument("--cohorts", required=True, help="comma-separated cohort names")
    r.add_argument("--tasks", required=True, help="pilot | main | comma-separated task ids")
    r.add_argument("--reps", type=int, default=3)
    r.add_argument("--jobs", type=int, default=1)
    r.add_argument("--timeout-s", type=int, default=3600, help="agent wall-clock limit")
    r.add_argument("--grade-timeout-s", type=int, default=900)
    r.add_argument("--quota-backoff-s", type=float, default=600.0)
    r.add_argument("--seed", type=int, default=20261115)
    r.add_argument("--tasks-dir", type=Path, default=Path("tasks"))
    r.add_argument("--cohorts-file", type=Path, default=COHORTS_FILE)
    r.add_argument("--out", type=Path, default=Path("results/raw"))
    r.add_argument("--work-root", type=Path, default=Path(".work/runs"))
    r.add_argument("--cache-dir", type=Path, default=Path(".work/reference"))
    r.add_argument("--accounts-file", type=Path, default=None)
    r.add_argument("--keep-work", action="store_true", help="keep workspaces after grading")
    args = parser.parse_args(argv)
    if args.command == "run":
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
        return run(args)
    if args.command == "screen":
        _print_funnel(screen(args.repo, args.ref, args.out, args.jobs, args.workroot))
    elif args.command == "tasks":
        if args.repo is None:
            print("note: no --repo, hidden test function names not checked")
        errors = validate_tasks(args.dir, args.repo)
        for e in errors:
            print(e)
        print("tasks valid" if not errors else f"{len(errors)} problem(s)")
        return 1 if errors else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
