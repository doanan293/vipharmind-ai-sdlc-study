"""Follow-up fix/refactor commits per feature (RQ2). Observational, not causal."""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import timedelta

from retro.gitlog import Commit
from retro.specplans import DocFile, has_preceding_plan
from retro.stages import STAGES, classify_file, commit_stage

_REWORK_TYPES = ("fix", "refactor")
_IGNORED_STAGES = ("docs", "other")


def _code_files(commit: Commit) -> set[str]:
    return {f.path for f in commit.files if classify_file(f.path) not in _IGNORED_STAGES}


def rework_count(feat: Commit, later: list[Commit], window_days: int = 14) -> int:
    files = _code_files(feat)
    end = feat.date + timedelta(days=window_days)
    return sum(
        1
        for c in later
        if c.type in _REWORK_TYPES
        and feat.date < c.date <= end
        and files.intersection(f.path for f in c.files)
    )


def rework_rows(commits: list[Commit], plans: list[DocFile]) -> list[dict]:
    rows = []
    for c in commits:
        if c.type != "feat":
            continue
        rows.append(
            {
                "sha": c.sha,
                "date": c.date.date().isoformat(),
                "stage": commit_stage(c),
                "lines_changed": c.lines_changed,
                "has_plan": has_preceding_plan(c, plans) is not None,
                "rework": rework_count(c, commits),
            }
        )
    return rows


def _stats(values: list[int]) -> dict:
    return {
        "n_feat": len(values),
        "mean_rework": statistics.fmean(values) if values else 0.0,
        "share_with_rework": sum(v > 0 for v in values) / len(values) if values else 0.0,
    }


def rework_summary(rows: list[dict]) -> list[dict]:
    out = []
    for group, flag in (("with_plan", True), ("without_plan", False)):
        values = [r["rework"] for r in rows if r["has_plan"] is flag]
        s = _stats(values)
        out.append(
            {
                "group": group,
                "n_feat": s["n_feat"],
                "mean_rework": s["mean_rework"],
                "median_rework": statistics.median(values) if values else 0,
                "share_with_rework": s["share_with_rework"],
            }
        )
    return out


def rework_by_stage(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for r in rows:
        grouped[r["stage"]].append(r["rework"])
    return [{"stage": s, **_stats(grouped[s])} for s in STAGES if s in grouped]
