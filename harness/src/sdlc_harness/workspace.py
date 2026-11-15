"""Per-run isolation: a history-free workspace and a clean agent config dir."""

import os
import shutil
import subprocess
import tomllib
from pathlib import Path
from typing import Literal

from sdlc_harness.pytest_run import find_lock_dir
from sdlc_harness.tasks import Task
from sdlc_harness.vcs import export_tree

Agent = Literal["claude", "agy", "codex"]

ACCOUNTS_FILE = Path(__file__).resolve().parents[2] / "accounts.local.toml"
LOCAL_EXCLUDES = (
    ".venv/",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
)
BASELINE = "baseline"


def _git(work: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(work), *args], check=True, text=True, capture_output=True
    ).stdout


def prepare_workspace(repo: Path, task: Task, run_dir: Path, timeout_s: int = 900) -> Path:
    """Export the parent tree to run_dir/work, sync deps, and commit a fresh `baseline`.

    Hidden tests added by the task do not exist at the parent commit, so the export
    already lacks them; hidden tests the task only modifies stay at their parent version.
    """
    work = run_dir / "work"
    work.mkdir(parents=True)
    export_tree(repo, task.parent, work)

    lock_dir = find_lock_dir(work)
    if lock_dir is not None:
        env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
        subprocess.run(
            ["uv", "sync", "--frozen"],
            cwd=lock_dir,
            env=env,
            check=True,
            capture_output=True,
            timeout=timeout_s,
        )

    _git(work, "init", "-q", "-b", "main")
    _git(work, "config", "user.name", "harness")
    _git(work, "config", "user.email", "harness@localhost")
    _git(work, "config", "commit.gpgsign", "false")
    exclude = work / ".git" / "info" / "exclude"
    exclude.parent.mkdir(exist_ok=True)
    with exclude.open("a") as f:
        f.write("\n".join(LOCAL_EXCLUDES) + "\n")
    _git(work, "add", "-A")
    _git(work, "commit", "-q", "--allow-empty", "-m", "baseline")
    _git(work, "tag", BASELINE)
    return work


def _account_source(agent: str, account: int, accounts_file: Path) -> Path:
    data = tomllib.loads(accounts_file.read_text())
    try:
        return Path(data[agent][str(account)]).expanduser()
    except KeyError:
        raise KeyError(f"no {agent} account {account} in {accounts_file}") from None


def _copy(src: Path, dest: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dest, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dest / src.name)


def prepare_config(
    agent: Agent, run_dir: Path, account: int, accounts_file: Path | None = None
) -> dict[str, str]:
    """Create run_dir/config holding only the credentials of one account; return the env."""
    if agent == "agy":
        raise NotImplementedError("agy config is set up in the pilot task")
    src = _account_source(agent, account, accounts_file or ACCOUNTS_FILE)
    config = run_dir / "config"
    config.mkdir(parents=True, exist_ok=True)
    if agent == "codex":
        _copy(src / "auth.json" if src.is_dir() else src, config)
        return {"CODEX_HOME": str(config)}
    _copy(src, config)
    return {"CLAUDE_CONFIG_DIR": str(config)}


def collect_patch(work: Path) -> str:
    """Everything the agent changed since baseline, as a unified diff."""
    _git(work, "add", "-A")
    return _git(work, "diff", "--cached", BASELINE)
