"""Command line entry point: sdlc-harness screen | tasks validate."""

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

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
    args = parser.parse_args(argv)
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
