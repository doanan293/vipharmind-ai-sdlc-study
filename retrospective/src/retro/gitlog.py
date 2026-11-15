"""Read a commit history with one ``git log`` call (no checkout)."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

_TYPE_RE = re.compile(r"^([a-z]+)(\([^)]*\))?!?: ")
_BRACE_RENAME_RE = re.compile(r"^(.*)\{(.*) => (.*)\}(.*)$")
_RECORD = "\x1e"
_FIELD = "\x1f"


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int
    deleted: int


@dataclass(frozen=True)
class Commit:
    sha: str
    date: datetime
    subject: str
    type: str
    files: tuple[FileChange, ...]

    @property
    def lines_changed(self) -> int:
        return sum(f.added + f.deleted for f in self.files)


def parse_type(subject: str) -> str:
    m = _TYPE_RE.match(subject)
    return m.group(1) if m else "other"


def _new_path(path: str) -> str:
    """Resolve a numstat rename path (``pre{a => b}post`` or ``a => b``) to the new path."""
    m = _BRACE_RENAME_RE.match(path)
    if m:
        pre, _old, new, post = m.groups()
        joined = pre + new + post
        while "//" in joined:
            joined = joined.replace("//", "/")
        return joined.lstrip("/")
    if " => " in path:
        return path.split(" => ", 1)[1]
    return path


def _count(field: str) -> int:
    return 0 if field == "-" else int(field)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.quotePath=false", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def load_commits(repo: Path, revs: Sequence[str]) -> list[Commit]:
    out = git(
        repo,
        "log",
        "-M",
        "--numstat",
        f"--format={_RECORD}%H{_FIELD}%aI{_FIELD}%s",
        *revs,
        "--",
    )
    commits: list[Commit] = []
    for record in out.split(_RECORD)[1:]:
        header, _, body = record.partition("\n")
        sha, date, subject = header.split(_FIELD)
        files = []
        for line in body.splitlines():
            if not line.strip():
                continue
            added, deleted, path = line.split("\t", 2)
            files.append(FileChange(_new_path(path), _count(added), _count(deleted)))
        commits.append(
            Commit(sha, datetime.fromisoformat(date), subject, parse_type(subject), tuple(files))
        )
    commits.reverse()
    commits.sort(key=lambda c: c.date)
    return commits
