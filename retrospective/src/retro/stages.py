"""Map files and commits to lifecycle stages (RQ1)."""

from __future__ import annotations

import fnmatch
from collections import defaultdict

from retro.gitlog import Commit

STAGES = ("research_eval", "data", "backend", "frontend", "test", "deploy", "docs", "other")

_TEST_DIRS = {"tests", "test", "e2e"}
_TEST_NAMES = ("test_*.py", "*_test.py", "*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx")
_RESEARCH_PREFIXES = ("docs/report/", "docs/presentation/", "docs/paper/", "pharma-lab/")
_DATA_PREFIXES = ("seed-pipeline/", "corpus-pipeline/")
_DEPLOY_PREFIXES = ("devops/", ".github/")
_DEPLOY_NAMES = ("compose*.yaml", "Dockerfile*", ".env.example")


def classify_file(path: str) -> str:
    """Rules applied in order, first match wins (see the plan's rule table)."""
    parts = path.split("/")
    name = parts[-1]
    if _TEST_DIRS.intersection(parts[:-1]) or any(fnmatch.fnmatch(name, p) for p in _TEST_NAMES):
        return "test"
    if path.startswith(_RESEARCH_PREFIXES):
        return "research_eval"
    if path.startswith(_DATA_PREFIXES):
        return "data"
    if path.startswith("backend/"):
        return "backend"
    if path.startswith("frontend/"):
        return "frontend"
    if path.startswith(_DEPLOY_PREFIXES) or any(fnmatch.fnmatch(name, p) for p in _DEPLOY_NAMES):
        return "deploy"
    if name.endswith(".md"):
        return "docs"
    return "other"


def commit_stage(commit: Commit) -> str:
    """Stage with the most changed lines; ties go to the earlier stage in STAGES.

    A commit with no changed lines (binary files only) is classified by file count.
    """
    if not commit.files:
        return "other"
    lines: dict[str, int] = defaultdict(int)
    counts: dict[str, int] = defaultdict(int)
    for f in commit.files:
        stage = classify_file(f.path)
        lines[stage] += f.added + f.deleted
        counts[stage] += 1
    weights = lines if any(lines.values()) else counts
    return max(STAGES, key=lambda s: (weights.get(s, 0), -STAGES.index(s)))


def _week(commit: Commit) -> str:
    year, week, _ = commit.date.isocalendar()
    return f"{year}-W{week:02d}"


def lifecycle_tables(commits: list[Commit]) -> dict[str, list[dict]]:
    by_stage = {s: {"stage": s, "commits": 0, "lines_changed": 0} for s in STAGES}
    by_week: dict[tuple[str, str], dict] = {}
    for c in commits:
        stage = commit_stage(c)
        by_stage[stage]["commits"] += 1
        by_stage[stage]["lines_changed"] += c.lines_changed
        key = (_week(c), stage)
        row = by_week.setdefault(
            key, {"week": key[0], "stage": stage, "commits": 0, "lines_changed": 0}
        )
        row["commits"] += 1
        row["lines_changed"] += c.lines_changed
    weekly = sorted(by_week.values(), key=lambda r: (r["week"], STAGES.index(r["stage"])))
    return {"by_stage": list(by_stage.values()), "by_week": weekly}
