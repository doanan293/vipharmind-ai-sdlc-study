"""Cross-tier overlap (prereg-v1, constraint 7): tasks that share a commit with a task of another
tier. The H5 sensitivity analysis (9.7) drops them.

A one-commit task's commits are {commit}; a range task's are `git rev-list base..commit` in the
ViPharmind repository. Two tasks of different tiers overlap when their commit sets intersect;
both are dropped (the relation is symmetric: each has a commit lying in the other)."""

import subprocess
from pathlib import Path

import pandas as pd


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout


def commit_sets(tasks: pd.DataFrame, repo: Path) -> dict[str, set[str]]:
    out = {}
    for t in tasks.to_dict("records"):
        end = _git(repo, "rev-parse", f"{t['commit']}^{{commit}}").strip()
        if t["kind"] == "range":
            base = _git(repo, "rev-parse", f"{t['base']}^{{commit}}").strip()
            out[t["task_id"]] = set(_git(repo, "rev-list", f"{base}..{end}").split())
        else:
            out[t["task_id"]] = {end}
    return out


def cross_tier_overlaps(tasks: pd.DataFrame, sets: dict[str, set[str]]) -> list[dict]:
    tier = dict(zip(tasks["task_id"], tasks["tier"]))
    ids = sorted(sets)
    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            if tier[a] == tier[b]:
                continue
            shared = sets[a] & sets[b]
            if shared:
                pairs.append(
                    {"a": a, "b": b, "tiers": [tier[a], tier[b]], "shared_commits": sorted(shared)}
                )
    return pairs


def overlap_tasks(pairs: list[dict]) -> set[str]:
    return {p["a"] for p in pairs} | {p["b"] for p in pairs}
