from datetime import datetime

import pytest

from retro import CAMERA_READY_SHA, DEFAULT_REPO, MAIN_SHA
from retro.gitlog import Commit, FileChange, load_commits
from retro.stages import STAGES, classify_file, commit_stage, lifecycle_tables


@pytest.mark.parametrize(
    "path,stage",
    [
        ("backend/tests/unit/test_x.py", "test"),
        ("frontend/src/app/page.test.tsx", "test"),
        ("frontend/e2e/login.ts", "test"),
        ("backend/src/a_test.py", "test"),
        ("frontend/src/x.spec.ts", "test"),
        ("pharma-lab/eval/run.py", "research_eval"),
        ("docs/report/main.tex", "research_eval"),
        ("docs/paper/main.tex", "research_eval"),
        ("docs/presentation/slides.tex", "research_eval"),
        ("seed-pipeline/src/a.py", "data"),
        ("corpus-pipeline/x.py", "data"),
        ("backend/src/pharma_agent/api/x.py", "backend"),
        ("backend/docs/superpowers/plans/p.md", "backend"),
        ("frontend/src/app/page.tsx", "frontend"),
        ("devops/k8s/a.yaml", "deploy"),
        (".github/workflows/ci.yml", "deploy"),
        ("compose.gemini-proxy.yaml", "deploy"),
        ("backend/Dockerfile", "backend"),
        ("Dockerfile.dev", "deploy"),
        (".env.example", "deploy"),
        ("README.md", "docs"),
        ("docs/superpowers/specs/s.md", "docs"),
        ("uv.lock", "other"),
    ],
)
def test_classify_file(path, stage):
    assert classify_file(path) == stage


def _commit(files, date="2026-08-03T10:00:00+00:00", sha="c"):
    return Commit(
        sha,
        datetime.fromisoformat(date),
        "feat: x",
        "feat",
        tuple(FileChange(p, a, d) for p, a, d in files),
    )


def test_commit_stage_majority():
    c = _commit([("backend/src/a.py", 6, 4), ("backend/tests/test_a.py", 3, 0)])
    assert commit_stage(c) == "backend"


def test_commit_stage_tie_takes_earlier_stage():
    c = _commit([("backend/src/a.py", 5, 0), ("seed-pipeline/a.py", 0, 5)])
    assert commit_stage(c) == "data"


def test_commit_stage_zero_lines_uses_file_count():
    c = _commit([("frontend/logo.png", 0, 0)])
    assert commit_stage(c) == "frontend"


def test_commit_stage_empty_commit_is_other():
    assert commit_stage(_commit([])) == "other"


def test_lifecycle_tables():
    commits = [
        _commit([("backend/src/a.py", 10, 0)], "2026-08-03T10:00:00+00:00", "a"),
        _commit([("backend/src/b.py", 2, 1)], "2026-08-04T10:00:00+00:00", "b"),
        _commit([("README.md", 1, 0)], "2026-08-11T10:00:00+00:00", "c"),
    ]
    tables = lifecycle_tables(commits)
    by_stage = {r["stage"]: r for r in tables["by_stage"]}
    assert [r["stage"] for r in tables["by_stage"]] == list(STAGES)
    assert by_stage["backend"] == {"stage": "backend", "commits": 2, "lines_changed": 13}
    assert by_stage["docs"]["commits"] == 1
    assert by_stage["frontend"]["commits"] == 0
    assert tables["by_week"] == [
        {"week": "2026-W32", "stage": "backend", "commits": 2, "lines_changed": 13},
        {"week": "2026-W33", "stage": "docs", "commits": 1, "lines_changed": 1},
    ]


@pytest.mark.real
def test_real_repo_has_little_other():
    commits = load_commits(DEFAULT_REPO, [MAIN_SHA, CAMERA_READY_SHA])
    other = sum(commit_stage(c) == "other" for c in commits)
    assert other / len(commits) < 0.05
