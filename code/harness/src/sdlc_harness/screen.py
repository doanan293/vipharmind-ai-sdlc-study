"""Static screening of candidate commits (criteria 1, 4, 5) and code-layer classification."""

import fnmatch
import posixpath
from dataclasses import dataclass
from typing import Literal

from sdlc_harness.vcs import SRC_PREFIX, TESTS_PREFIX, Candidate

Layer = Literal["api", "application", "domain", "infrastructure"]
# Tie-break priority, highest first.
_LAYER_PRIORITY: tuple[Layer, ...] = ("domain", "application", "infrastructure", "api")
_PKG_PREFIX = SRC_PREFIX + "pharma_agent/"

MIN_SRC_LINES = 30
MAX_SRC_LINES = 400
RENAME_MAX_LINES = 2


def SHARED_TEST_FILE(path: str) -> bool:
    """True for files under backend/tests/ whose basename is not test_*.py."""
    return path.startswith(TESTS_PREFIX) and not fnmatch.fnmatchcase(
        posixpath.basename(path), "test_*.py"
    )


def _src_changes(c: Candidate):
    return [ch for ch in c.changes if ch.path.startswith(SRC_PREFIX)]


def src_lines(c: Candidate) -> int:
    return sum(ch.added + ch.deleted for ch in _src_changes(c))


def is_rename_only(c: Candidate) -> bool:
    src = _src_changes(c)
    return bool(src) and all(
        ch.status == "R" and ch.added + ch.deleted <= RENAME_MAX_LINES for ch in src
    )


def layer_of(c: Candidate) -> Layer:
    totals: dict[Layer, int] = dict.fromkeys(_LAYER_PRIORITY, 0)
    for ch in c.changes:
        if not ch.path.startswith(_PKG_PREFIX):
            continue
        layer = ch.path[len(_PKG_PREFIX) :].split("/", 1)[0]
        for known in _LAYER_PRIORITY:
            if layer == known:
                totals[known] += ch.added + ch.deleted
    if not any(totals.values()):
        raise ValueError(f"{c.sha}: no changed lines under {_PKG_PREFIX}<layer>/")
    # max() returns the first maximal item, so priority order breaks ties.
    return max(_LAYER_PRIORITY, key=lambda name: totals[name])


@dataclass
class Verdict:
    sha: str
    passed: bool
    failed_criterion: int | None
    reason: str


def screen_static(c: Candidate) -> Verdict:
    shared = [ch.path for ch in c.changes if SHARED_TEST_FILE(ch.path)]
    if shared:
        return Verdict(c.sha, False, 1, f"touches shared test files: {', '.join(shared)}")
    n = src_lines(c)
    if not MIN_SRC_LINES <= n <= MAX_SRC_LINES:
        return Verdict(c.sha, False, 4, f"{n} src lines outside {MIN_SRC_LINES}-{MAX_SRC_LINES}")
    if is_rename_only(c):
        return Verdict(c.sha, False, 5, "src changes are renames only")
    return Verdict(c.sha, True, None, "passed static screening")


def hidden_tests(c: Candidate) -> list[str]:
    return [
        ch.path
        for ch in c.changes
        if ch.status in ("A", "M")
        and ch.path.startswith(TESTS_PREFIX)
        and fnmatch.fnmatchcase(posixpath.basename(ch.path), "test_*.py")
    ]
