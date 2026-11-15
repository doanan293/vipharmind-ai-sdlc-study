"""Spec/plan files from history and the rule that links feat commits to plans (RQ1)."""

from __future__ import annotations

import csv
import random
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from retro.gitlog import Commit, git

_DOC_RE = re.compile(r"(^|/)docs/superpowers/(specs|plans)/[^/]+\.md$")
_BACKTICK_RE = re.compile(r"`([^`\n]+)`")
_LINE_SUFFIX_RE = re.compile(r"(::[\w.]+|:\d+(-\d+)?)$")
_CODE_EXTS = (".py", ".ts", ".tsx", ".js", ".toml", ".yaml", ".yml", ".sql", ".sh", ".tex")
_SUBPROJECTS = ("backend", "frontend", "seed-pipeline")
_RECORD = "\x1e"
_FIELD = "\x1f"


@dataclass(frozen=True)
class DocFile:
    path: str
    kind: Literal["spec", "plan"]
    added_sha: str
    added_date: datetime
    text: str


def load_spec_plan_files(repo: Path, revs: Sequence[str]) -> list[DocFile]:
    """Every spec/plan file ever added in ``revs``; the earliest addition wins.

    Renames are detected (``-M``), so a moved file is not counted as a new document.
    """
    out = git(
        repo,
        "log",
        "-M",
        "--diff-filter=A",
        "--name-only",
        f"--format={_RECORD}%H{_FIELD}%aI",
        *revs,
        "--",
    )
    first: dict[str, tuple[datetime, str]] = {}
    for record in out.split(_RECORD)[1:]:
        header, _, body = record.partition("\n")
        sha, date = header.split(_FIELD)
        when = datetime.fromisoformat(date)
        for path in body.splitlines():
            m = _DOC_RE.search(path.strip())
            if not m:
                continue
            path = path.strip()
            if path not in first or when < first[path][0]:
                first[path] = (when, sha)
    docs = [
        DocFile(
            path=path,
            kind="spec" if _DOC_RE.search(path).group(2) == "specs" else "plan",
            added_sha=sha,
            added_date=when,
            text=git(repo, "show", f"{sha}:{path}"),
        )
        for path, (when, sha) in first.items()
    ]
    return sorted(docs, key=lambda d: (d.added_date, d.path))


def referenced_code_paths(plan_text: str) -> set[str]:
    """Backtick-quoted strings that look like code file paths."""
    paths = set()
    for raw in _BACKTICK_RE.findall(plan_text):
        s = raw.strip()
        if s.startswith("./"):
            s = s[2:]
        s = _LINE_SUFFIX_RE.sub("", s)
        if " " in s or "/" not in s or s.startswith("..."):
            continue
        if s.endswith(_CODE_EXTS):
            paths.add(s)
    return paths


def _subproject(doc_path: str) -> str | None:
    top = doc_path.split("/", 1)[0]
    return top if top in _SUBPROJECTS else None


def plan_names_file(doc: DocFile, refs: set[str], file_path: str) -> bool:
    if file_path in refs:
        return True
    sub = _subproject(doc.path)
    return bool(sub) and file_path.startswith(sub + "/") and file_path[len(sub) + 1 :] in refs


def _links(commit: Commit, doc: DocFile, refs: set[str], window: timedelta) -> bool:
    if not (commit.date - window <= doc.added_date < commit.date):
        return False
    return any(plan_names_file(doc, refs, f.path) for f in commit.files)


def has_preceding_plan(
    commit: Commit, plans: list[DocFile], window_days: int = 14
) -> DocFile | None:
    window = timedelta(days=window_days)
    hits = [
        p
        for p in plans
        if p.kind == "plan" and _links(commit, p, referenced_code_paths(p.text), window)
    ]
    return max(hits, key=lambda p: p.added_date) if hits else None


def spec_trace_rows(
    commits: list[Commit], docs: list[DocFile], window_days: int = 14
) -> list[dict]:
    window = timedelta(days=window_days)
    feats = [c for c in commits if c.type == "feat"]
    rows = []
    for doc in docs:
        refs = referenced_code_paths(doc.text)
        linked = sorted(c.date for c in feats if _links(c, doc, refs, window))
        rows.append(
            {
                "path": doc.path,
                "kind": doc.kind,
                "added_sha": doc.added_sha,
                "added_date": doc.added_date.date().isoformat(),
                "n_feat_linked": len(linked),
                "first_linked_date": linked[0].date().isoformat() if linked else "",
                "last_linked_date": linked[-1].date().isoformat() if linked else "",
            }
        )
    return rows


def sample_for_manual_check(feats: list[Commit], n: int = 20, seed: int = 20261115) -> list[Commit]:
    ordered = sorted(feats, key=lambda c: (c.date, c.sha))
    picked = random.Random(seed).sample(ordered, min(n, len(ordered)))
    return sorted(picked, key=lambda c: (c.date, c.sha))


def link_accuracy(sheet: Path) -> tuple[int, int]:
    with sheet.open(newline="") as fh:
        verdicts = [row.get("an_verdict", "").strip().lower() for row in csv.DictReader(fh)]
    graded = [v for v in verdicts if v in ("correct", "wrong")]
    return sum(v == "correct" for v in graded), len(graded)
