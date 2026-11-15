import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from retro import CAMERA_READY_SHA, DEFAULT_REPO, MAIN_SHA


def _real_repo_available() -> bool:
    if not (DEFAULT_REPO / ".git").exists():
        return False
    for sha in (MAIN_SHA, CAMERA_READY_SHA):
        r = subprocess.run(
            ["git", "-C", str(DEFAULT_REPO), "cat-file", "-e", f"{sha}^{{commit}}"],
            capture_output=True,
        )
        if r.returncode != 0:
            return False
    return True


def pytest_collection_modifyitems(config, items):
    if _real_repo_available():
        return
    skip = pytest.mark.skip(reason="ViPharmind repo with the pinned commits is not available")
    for item in items:
        if "real" in item.keywords:
            item.add_marker(skip)


def git(repo: Path, *args: str, env: dict | None = None) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    ).stdout.strip()


@pytest.fixture
def make_repo(tmp_path) -> Callable[[list[dict]], Path]:
    """Build a toy git repo from a list of commit specs.

    Each spec: ``message``, ``date`` (ISO), optional ``files`` ({path: str | bytes | None},
    None deletes), optional ``rename`` ({old: new}), optional ``checkout`` (raw args for
    ``git checkout`` run before the commit, e.g. ``"-b side main"``).
    """
    counter = iter(range(1000))

    def build(specs: list[dict]) -> Path:
        repo = tmp_path / f"repo{next(counter)}"
        repo.mkdir()
        git(repo, "init", "-q", "-b", "main")
        git(repo, "config", "user.email", "t@example.com")
        git(repo, "config", "user.name", "T")
        git(repo, "config", "commit.gpgsign", "false")
        for spec in specs:
            if spec.get("checkout"):
                git(repo, "checkout", "-q", *spec["checkout"].split())
            for old, new in spec.get("rename", {}).items():
                (repo / new).parent.mkdir(parents=True, exist_ok=True)
                git(repo, "mv", old, new)
            for path, content in spec.get("files", {}).items():
                target = repo / path
                if content is None:
                    target.unlink()
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                if isinstance(content, bytes):
                    target.write_bytes(content)
                else:
                    target.write_text(content)
            git(repo, "add", "-A")
            env = {"GIT_AUTHOR_DATE": spec["date"], "GIT_COMMITTER_DATE": spec["date"]}
            git(repo, "commit", "-q", "--allow-empty", "-m", spec["message"], env=env)
        return repo

    return build
