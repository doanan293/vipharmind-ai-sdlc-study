"""Command line entry point: sdlc-harness screen."""

import argparse
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from sdlc_harness.screen import hidden_tests, layer_of, screen_static, src_lines
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sdlc-harness")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("screen", help="screen candidate commits (criteria 1, 4, 5, then 2)")
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--ref", required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--jobs", type=int, default=4)
    p.add_argument("--workroot", type=Path, default=Path(".work"))
    args = parser.parse_args(argv)
    if args.command == "screen":
        _print_funnel(screen(args.repo, args.ref, args.out, args.jobs, args.workroot))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
