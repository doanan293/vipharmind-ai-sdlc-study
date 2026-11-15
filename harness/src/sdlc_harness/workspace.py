"""Per-run isolation: a history-free workspace and a clean agent config dir."""

import functools
import json
import logging
import os
import shutil
import subprocess
import threading
import tomllib
from pathlib import Path
from typing import Literal

from sdlc_harness.agents import urls_in
from sdlc_harness.pytest_run import find_lock_dir
from sdlc_harness.tasks import Task
from sdlc_harness.vcs import export_tree

log = logging.getLogger(__name__)

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
# Files that would steer or inform the agent: the project's historical design specs and plans
# (written before the commit, they can describe the very feature), agent instruction files and
# agent config/skill dirs. Removed from the exported tree before the baseline commit.
# Names are matched case-insensitively, at any depth.
CONTAMINANT_DIRS = frozenset(
    {"superpowers", ".claude", ".agents", ".codex", ".gemini", ".cursor", ".windsurf"}
)
CONTAMINANT_FILES = frozenset(
    {
        "claude.md",
        "gemini.md",
        "skills-lock.json",
        ".cursorrules",
        ".windsurfrules",
    }
)
COPILOT_FILE = ("copilot-instructions.md", ".github")  # (name, parent dir name)
SCAN_SKIP = frozenset({".git", ".venv", "node_modules"})


class ContaminatedTreeError(RuntimeError):
    """The agent's tree still holds design docs, plans or agent instruction/config files."""


def find_contaminants(root: Path) -> list[str]:
    """Top-most contaminant paths under root (relative, sorted); .git/.venv are not scanned."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        for d in sorted(dirnames):
            if d.lower() in CONTAMINANT_DIRS:
                found.append((here / d).relative_to(root).as_posix())
        dirnames[:] = sorted(
            d for d in dirnames if d.lower() not in CONTAMINANT_DIRS and d not in SCAN_SKIP
        )
        for f in filenames:
            low = f.lower()
            if (
                low in CONTAMINANT_FILES
                or (low, here.name.lower()) == COPILOT_FILE
                or (low == "agents.md" and here == root)  # elsewhere it may be project docs
            ):
                found.append((here / f).relative_to(root).as_posix())
    return sorted(found)


def tree_urls(root: Path) -> set[str]:
    """Upstream-repo URLs already present in the exported tree (read as text; .git/.venv skipped),
    so only URLs the agent introduced count as upstream access."""
    found: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCAN_SKIP]
        for f in filenames:
            try:
                text = (Path(dirpath) / f).read_text(errors="strict")
            except (OSError, UnicodeDecodeError):
                continue
            found.update(urls_in(text))
    return found


def strip_contaminants(root: Path) -> list[str]:
    """Delete every contaminant under root; return what was removed."""
    removed = find_contaminants(root)
    for rel in removed:
        target = root / rel
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target)
        else:
            target.unlink()
    return removed


def assert_clean_tree(root: Path) -> None:
    left = find_contaminants(root)
    if left:
        raise ContaminatedTreeError(f"agent tree {root} holds {', '.join(left)}")


def _git(work: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(work), *args], check=True, text=True, capture_output=True
    ).stdout


def prepare_workspace(
    repo: Path,
    task: Task,
    run_dir: Path,
    timeout_s: int = 900,
    removed: list[str] | None = None,
) -> Path:
    """Export the start tree (parent, or base for a range task) to run_dir/work, strip contaminants, sync deps, commit `baseline`.

    Hidden tests and support files (conftest, fakes, fixtures) added by the task do not exist at
    the start commit, so the export already lacks them; ones the task only modifies stay at
    their start version.
    Paths stripped by strip_contaminants are appended to `removed` when given.
    """
    work = run_dir / "work"
    work.mkdir(parents=True)
    export_tree(repo, task.start, work)
    stripped = strip_contaminants(work)
    if removed is not None:
        removed.extend(stripped)

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

    _git(work, "init", "-q", "--template=", "-b", "main")
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
        src = data[agent][str(account)]
    except KeyError:
        raise KeyError(f"no {agent} account {account} in {accounts_file}") from None
    if not isinstance(src, str):
        raise TypeError(f"{agent} account {account}: expected a path")
    return Path(src).expanduser()


def _credential_source(agent: str, account: int, accounts_file: Path) -> Path:
    """The account's credential file: the path itself, or CREDENTIALS[agent] inside a dir."""
    path = _account_source(agent, account, accounts_file)
    return path / CREDENTIALS[agent] if path.is_dir() else path


CREDENTIALS = {
    "claude": ".credentials.json",
    "codex": "auth.json",
    "agy": "antigravity-oauth-token",
}
# where each CLI keeps its state under HOME; HOME is the per-attempt config/home for every agent
TOOL_DIR = {"claude": ".claude", "codex": ".codex", "agy": ".gemini/antigravity-cli"}
CODEX_CONFIG = """# written by sdlc-harness: user-level extras off, stock tools untouched (ruling R11)
project_doc_max_bytes = 0

[skills]
bundled = { enabled = false }
include_instructions = false

[features]
apps = false
plugins = false
remote_plugin = false
memories = false
hooks = false
"""


@functools.cache
def host_uv_dirs() -> dict[str, str]:
    """The host's uv cache and Python dirs: agents run with a fresh HOME but must not need the
    network to `uv run` the already-synced project."""
    out = {}
    for var, args in (
        ("UV_CACHE_DIR", ("cache", "dir")),
        ("UV_PYTHON_INSTALL_DIR", ("python", "dir")),
    ):
        out[var] = (
            os.environ.get(var)
            or subprocess.run(
                ["uv", *args], check=True, capture_output=True, text=True
            ).stdout.strip()
        )
    return out


def prepare_config(
    agent: Agent, run_dir: Path, account: int, accounts_file: Path | None = None
) -> dict[str, str]:
    """Create run_dir/config/home, a fresh HOME holding only one account's login; return the env.

    Every agent gets the same layout: HOME is the fresh dir (so nothing under the real ~ is
    found: memories, skills, plugins, instructions), uv uses the host cache read-only-in-spirit.
    """
    source = _credential_source(agent, account, accounts_file or ACCOUNTS_FILE)
    home = run_dir / "config" / "home"
    tool = home / TOOL_DIR[agent]
    tool.mkdir(parents=True, exist_ok=True)
    env = {"HOME": str(home), **host_uv_dirs()}
    dest = tool / CREDENTIALS[agent]
    shutil.copy2(source, dest)
    _snapshots[str(dest)] = dest.read_bytes()
    if agent == "claude":
        return {**env, "CLAUDE_CONFIG_DIR": str(tool)}
    if agent == "codex":
        (tool / "config.toml").write_text(CODEX_CONFIG)
        return {**env, "CODEX_HOME": str(tool)}
    return env


_snapshots: dict[str, bytes] = {}  # credential copy path -> bytes as copied from the source
_cred_locks: dict[tuple[str, int], threading.Lock] = {}
_cred_locks_guard = threading.Lock()


def _is_json(data: bytes) -> bool:
    try:
        json.loads(data)
    except ValueError:
        return False
    return True


def write_back_credentials(
    agent: str, run_dir: Path, account: int, accounts_file: Path | None = None
) -> bool:
    """Copy a token the agent refreshed back to the account source (temp file + os.replace, 0600).

    Only when the run's copy differs from what prepare_config copied; serialised per account.
    Returns whether the source was updated.
    """
    dest = run_dir / "config" / "home" / TOOL_DIR[agent] / CREDENTIALS[agent]
    original = _snapshots.get(str(dest))
    if original is None or not dest.is_file():
        return False
    new = dest.read_bytes()
    if new == original or not new.strip() or not _is_json(new):
        return False
    source = _credential_source(agent, account, accounts_file or ACCOUNTS_FILE).resolve()
    with _cred_locks_guard:
        lock = _cred_locks.setdefault((agent, account), threading.Lock())
    with lock:
        # compare-and-swap: only replace the token this unit started from
        if not source.is_file() or source.read_bytes() != original:
            log.warning(
                "%s account %d: source changed during the run, not written back", agent, account
            )
            return False
        tmp = source.with_name(f".{source.name}.{os.getpid()}.{threading.get_ident()}.tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(new)
            os.chmod(tmp, 0o600)
            os.replace(tmp, source)
        finally:
            tmp.unlink(missing_ok=True)
    _snapshots[str(dest)] = new
    return True


def config_manifest(config: Path) -> list[str]:
    """Relative paths of every file in a config dir (names only, never contents)."""
    return sorted(p.relative_to(config).as_posix() for p in config.rglob("*") if p.is_file())


def collect_patch(work: Path) -> str:
    """Everything the agent changed since baseline, as a unified diff."""
    _git(work, "add", "-A")
    return _git(work, "diff", "--binary", "--cached", BASELINE)
