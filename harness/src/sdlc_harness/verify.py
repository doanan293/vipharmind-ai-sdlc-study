"""Criterion 2: hidden tests fail at the parent commit and pass at the original commit."""

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from sdlc_harness.pytest_run import TestReport, run_backend_tests
from sdlc_harness.screen import hidden_tests
from sdlc_harness.vcs import Candidate, export_tree, read_file


@dataclass
class F2PResult:
    sha: str
    passed: bool
    reason: str
    hidden_failing_at_parent: list[str] = field(default_factory=list)
    old_failing: list[str] = field(default_factory=list)


def _file_of(nodeid: str) -> str:
    return nodeid.split("::", 1)[0]


def _split(report: TestReport, files: set[str]) -> tuple[dict[str, str], dict[str, str]]:
    hidden = {k: v for k, v in report.outcomes.items() if _file_of(k) in files}
    other = {k: v for k, v in report.outcomes.items() if _file_of(k) not in files}
    return hidden, other


def _bad(outcomes: dict[str, str]) -> list[str]:
    return sorted(k for k, v in outcomes.items() if v in ("failed", "error"))


def _overlay(repo: Path, sha: str, tree: Path, files: list[str]) -> None:
    for path in files:
        target = tree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(read_file(repo, sha, path))


def check_fail_to_pass(repo: Path, c: Candidate, workroot: Path) -> F2PResult:
    files = hidden_tests(c)
    if not files:
        return F2PResult(c.sha, False, "no hidden test files")
    workroot.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f"f2p-{c.sha[:8]}-", dir=workroot))
    try:
        parent_tree, orig_tree = work / "parent", work / "orig"
        parent_tree.mkdir()
        orig_tree.mkdir()
        export_tree(repo, c.parent, parent_tree)
        export_tree(repo, c.sha, orig_tree)
        # New hidden files are absent at the parent; modified ones keep their old content
        # until overwritten. Either way the original commit's version is what runs.
        _overlay(repo, c.sha, parent_tree, files)
        try:
            parent = run_backend_tests(parent_tree)
            orig = run_backend_tests(orig_tree)
        except subprocess.TimeoutExpired:
            return F2PResult(c.sha, False, "test run timed out")
        except subprocess.CalledProcessError as exc:
            return F2PResult(c.sha, False, f"{' '.join(map(str, exc.cmd))} failed")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    fileset = {f.removeprefix("backend/") for f in files}
    p_hidden, p_other = _split(parent, fileset)
    o_hidden, o_other = _split(orig, fileset)
    hidden_failing = _bad(p_hidden)
    old_failing = sorted(set(_bad(p_other)) | set(_bad(o_other)))

    if not o_hidden:
        return F2PResult(c.sha, False, "no hidden tests collected at the original commit")
    if _bad(o_hidden):
        return F2PResult(
            c.sha,
            False,
            f"hidden tests fail at the original commit: {', '.join(_bad(o_hidden)[:3])}",
            hidden_failing,
            old_failing,
        )
    if not hidden_failing:
        return F2PResult(c.sha, False, "no hidden test fails at the parent", [], old_failing)
    if old_failing:
        return F2PResult(
            c.sha,
            False,
            f"existing tests break: {', '.join(old_failing[:3])}",
            hidden_failing,
            old_failing,
        )
    return F2PResult(c.sha, True, "fail-to-pass confirmed", hidden_failing, [])
