from collections import Counter

import pytest

from retro import CAMERA_READY_SHA, DEFAULT_REPO, MAIN_SHA
from retro.gitlog import load_commits

pytestmark = pytest.mark.real


def test_reference_values():
    commits = load_commits(DEFAULT_REPO, [MAIN_SHA, CAMERA_READY_SHA])
    assert len(commits) == 505
    assert commits[0].date.date().isoformat() == "2026-07-23"
    assert commits[-1].date.date().isoformat() == "2026-11-10"
    counts = Counter(c.type for c in commits)
    assert {k: counts[k] for k in ["feat", "docs", "fix", "refactor", "chore", "test"]} == {
        "feat": 221,
        "docs": 115,
        "fix": 50,
        "refactor": 47,
        "chore": 34,
        "test": 20,
    }
