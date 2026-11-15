"""Per-run isolation: a history-free workspace and a clean agent config dir."""

import functools
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
# Files that would steer or inform the agent: the project's historical design specs and plans
# (written before the commit, they can describe the very feature), agent instruction files and
# agent config/skill dirs. Removed from the exported tree before the baseline commit.
CONTAMINANT_DIRS = frozenset({"superpowers", ".claude", ".agents", ".codex", ".gemini"})
CONTAMINANT_FILES = frozenset({"AGENTS.md", "CLAUDE.md", "GEMINI.md", "skills-lock.json"})
SCAN_SKIP = frozenset({".git", ".venv", "node_modules"})


class ContaminatedTreeError(RuntimeError):
    """The agent's tree still holds design docs, plans or agent instruction/config files."""


def find_contaminants(root: Path) -> list[str]:
    """Top-most contaminant paths under root (relative, sorted); .git/.venv are not scanned."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        for d in sorted(dirnames):
            if d in CONTAMINANT_DIRS:
                found.append((here / d).relative_to(root).as_posix())
        dirnames[:] = sorted(d for d in dirnames if d not in CONTAMINANT_DIRS | SCAN_SKIP)
        for f in filenames:
            if f in CONTAMINANT_FILES:
                found.append((here / f).relative_to(root).as_posix())
    return sorted(found)


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
    """Export the parent tree to run_dir/work, strip contaminants, sync deps, commit `baseline`.

    Hidden tests added by the task do not exist at the parent commit, so the export
    already lacks them; hidden tests the task only modifies stay at their parent version.
    Paths stripped by strip_contaminants are appended to `removed` when given.
    """
    work = run_dir / "work"
    work.mkdir(parents=True)
    export_tree(repo, task.parent, work)
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


def _account_source(agent: str, account: int, accounts_file: Path) -> str | dict:
    data = tomllib.loads(accounts_file.read_text())
    try:
        return data[agent][str(account)]
    except KeyError:
        raise KeyError(f"no {agent} account {account} in {accounts_file}") from None


PROXY_KEY_ENV = "SDLC_PROXY_API_KEY"  # codex reads the proxy key from here (never written to disk)
CREDENTIALS = {
    "claude": ".credentials.json",
    "codex": "auth.json",
    "agy": "antigravity-oauth-token",
}
# where each CLI keeps its state under HOME; HOME is the per-attempt config/home for every agent
TOOL_DIR = {"claude": ".claude", "codex": ".codex", "agy": ".gemini/antigravity-cli"}
CODEX_CONFIG = """# written by sdlc-harness: clean, equal conditions (see docs/pilot-report.md)
web_search = "disabled"
project_doc_max_bytes = 0

[skills]
bundled = {{ enabled = false }}
include_instructions = false

[features]
browser_use = false
browser_use_external = false
computer_use = false
in_app_browser = false
apps = false
plugins = false
remote_plugin = false
memories = false
hooks = false
image_generation = false
{provider}"""
CODEX_PROVIDER = """
[model_providers.sdlc-proxy]
name = "cli-proxy-api (local)"
base_url = "{base_url}"
env_key = "{env_key}"
wire_api = "responses"
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


def _proxy_key(proxy_config: Path) -> str:
    """First entry of `api-keys:` in the proxy's config.yaml (read at run time, never copied)."""
    lines = proxy_config.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "api-keys:":
            for item in lines[i + 1 :]:
                item = item.strip()
                if item.startswith("- "):
                    return item[2:].strip().strip("'\"")
                if item and not item.startswith("#"):
                    break
    raise KeyError(f"no api-keys entry in {proxy_config}")


def _agy_agent() -> str:
    from sdlc_harness.agents import AGY_AGENT, AGY_TOOLS

    return (
        f"---\nname: {AGY_AGENT}\n"
        "description: Coding agent.\n"
        f"tools: [{', '.join(AGY_TOOLS)}]\n"
        "mainAgent: true\nsubagent: false\n---\n"
    )


def prepare_config(
    agent: Agent, run_dir: Path, account: int, accounts_file: Path | None = None
) -> dict[str, str]:
    """Create run_dir/config/home, a fresh HOME holding only one account's login; return the env.

    Every agent gets the same layout: HOME is the fresh dir (so nothing under the real ~ is
    found: memories, skills, plugins, instructions), uv uses the host cache read-only-in-spirit.
    """
    src = _account_source(agent, account, accounts_file or ACCOUNTS_FILE)
    home = run_dir / "config" / "home"
    tool = home / TOOL_DIR[agent]
    tool.mkdir(parents=True, exist_ok=True)
    env = {"HOME": str(home), **host_uv_dirs()}
    if agent == "codex" and isinstance(src, dict):
        provider = CODEX_PROVIDER.format(base_url=src["base_url"], env_key=PROXY_KEY_ENV)
        (tool / "config.toml").write_text(
            'model_provider = "sdlc-proxy"\n' + CODEX_CONFIG.format(provider=provider)
        )
        env[PROXY_KEY_ENV] = _proxy_key(Path(src["proxy_config"]).expanduser())
        return {**env, "CODEX_HOME": str(tool)}
    if not isinstance(src, str):
        raise TypeError(f"{agent} account {account}: expected a path")
    path = Path(src).expanduser()
    shutil.copy2(path / CREDENTIALS[agent] if path.is_dir() else path, tool / CREDENTIALS[agent])
    if agent == "claude":
        return {**env, "CLAUDE_CONFIG_DIR": str(tool)}
    if agent == "codex":
        (tool / "config.toml").write_text(CODEX_CONFIG.format(provider=""))
        return {**env, "CODEX_HOME": str(tool)}
    agents_dir = home / ".gemini" / "config" / "agents"
    agents_dir.mkdir(parents=True)
    from sdlc_harness.agents import AGY_AGENT

    (agents_dir / f"{AGY_AGENT}.md").write_text(_agy_agent())
    return env


def config_manifest(config: Path) -> list[str]:
    """Relative paths of every file in a config dir (names only, never contents)."""
    return sorted(p.relative_to(config).as_posix() for p in config.rglob("*") if p.is_file())


def collect_patch(work: Path) -> str:
    """Everything the agent changed since baseline, as a unified diff."""
    _git(work, "add", "-A")
    return _git(work, "diff", "--cached", BASELINE)
