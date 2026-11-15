"""Shared fixtures: a tiny git repo shaped like ViPharmind's backend."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

BACKEND_PYPROJECT = """[project]
name = "pkg-backend"
version = "0.0.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["integration: needs Docker (run with -m integration)"]
addopts = ["-m", "not integration"]
"""

BASE_FILES = {
    "backend/pyproject.toml": BACKEND_PYPROJECT,
    "backend/src/pharma_agent/__init__.py": "",
    "backend/src/pharma_agent/api/__init__.py": "",
    "backend/src/pharma_agent/application/__init__.py": "",
    "backend/src/pharma_agent/domain/__init__.py": "",
    "backend/src/pharma_agent/infrastructure/__init__.py": "",
    "backend/tests/__init__.py": "",
}


@dataclass
class ToyRepo:
    path: Path

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(self.path), *args], check=True, text=True, capture_output=True
        )
        return result.stdout.strip()

    def commit(self, message: str, files: dict[str, str | None]) -> str:
        """Write (or delete, when the value is None) files and commit; return the sha."""
        for rel, content in files.items():
            target = self.path / rel
            if content is None:
                target.unlink()
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def toy_repo(tmp_path: Path) -> ToyRepo:
    path = tmp_path / "toy"
    path.mkdir()
    repo = ToyRepo(path)
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    return repo
