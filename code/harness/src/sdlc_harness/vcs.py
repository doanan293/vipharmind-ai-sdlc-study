"""Read-only access to a git repo: list candidate feat commits, export trees, read files."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

FEAT_RE = re.compile(r"^feat(\(.+\))?!?:")
SRC_PREFIX = "backend/src/"
TESTS_PREFIX = "backend/tests/"

Status = Literal["A", "M", "D", "R"]


@dataclass(frozen=True)
class FileChange:
    path: str
    status: Status
    added: int
    deleted: int


@dataclass(frozen=True)
class Candidate:
    sha: str
    parent: str
    subject: str
    changes: tuple[FileChange, ...]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, text=True, capture_output=True
    ).stdout


def _parse_changes(repo: Path, sha: str) -> tuple[FileChange, ...]:
    status_tokens = _git(repo, "show", "--name-status", "-z", "--format=", "-M", sha).split("\0")
    numstat_tokens = _git(repo, "show", "--numstat", "-z", "--format=", "-M", sha).split("\0")

    statuses: list[tuple[Status, str]] = []
    i = 0
    while i < len(status_tokens) and status_tokens[i]:
        code = status_tokens[i][0]
        if code in ("R", "C"):
            statuses.append(("R" if code == "R" else "A", status_tokens[i + 2]))
            i += 3
        else:
            statuses.append((code if code in ("A", "D") else "M", status_tokens[i + 1]))  # type: ignore[arg-type]
            i += 2

    counts: list[tuple[int, int]] = []
    i = 0
    while i < len(numstat_tokens) and numstat_tokens[i]:
        added, deleted, path = numstat_tokens[i].split("\t", 2)
        i += 3 if path == "" else 1  # rename/copy: path is empty, old and new follow
        counts.append((0 if added == "-" else int(added), 0 if deleted == "-" else int(deleted)))

    return tuple(
        FileChange(path=path, status=status, added=a, deleted=d)
        for (status, path), (a, d) in zip(statuses, counts, strict=True)
    )


def list_candidates(repo: Path, ref: str) -> list[Candidate]:
    """Non-merge feat commits on the first-parent line of ref touching src and tests (oldest first)."""
    log = _git(
        repo, "log", "--first-parent", "--no-merges", "--reverse", "--format=%H%x00%P%x00%s", ref
    )
    candidates = []
    for line in log.splitlines():
        sha, parents, subject = line.split("\0", 2)
        if not FEAT_RE.match(subject):
            continue
        changes = _parse_changes(repo, sha)
        if not any(c.path.startswith(SRC_PREFIX) for c in changes):
            continue
        if not any(c.path.startswith(TESTS_PREFIX) for c in changes):
            continue
        candidates.append(
            Candidate(
                sha=sha,
                parent=parents.split()[0] if parents else "",
                subject=subject,
                changes=changes,
            )
        )
    return candidates


def export_tree(repo: Path, sha: str, dest: Path) -> None:
    """Export the tree at sha into dest (no .git)."""
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", sha], check=True, capture_output=True
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)


def read_file(repo: Path, sha: str, path: str) -> str:
    return _git(repo, "show", f"{sha}:{path}")
