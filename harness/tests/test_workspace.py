import subprocess
import tomllib
from pathlib import Path

import pytest

from sdlc_harness.tasks import Task
from sdlc_harness.workspace import (
    PROXY_KEY_ENV,
    ContaminatedTreeError,
    assert_clean_tree,
    collect_patch,
    config_manifest,
    find_contaminants,
    prepare_config,
    prepare_workspace,
)

HIDDEN_NEW = "backend/tests/test_new.py"
HIDDEN_MOD = "backend/tests/test_old.py"


def _task(parent: str, commit: str) -> Task:
    return Task("t01", commit, parent, "domain", 40, (HIDDEN_NEW, HIDDEN_MOD), False, "p")


@pytest.fixture
def prepared(toy_repo, tmp_path):
    toy_repo.commit("chore: old test", {HIDDEN_MOD: "def test_old():\n    assert True\n"})
    parent = toy_repo.git("rev-parse", "HEAD")
    commit = toy_repo.commit(
        "feat: thing",
        {
            HIDDEN_NEW: "def test_new():\n    assert True\n",
            HIDDEN_MOD: "def test_old():\n    assert False\n",
            "backend/src/pharma_agent/domain/x.py": "X = 1\n",
        },
    )
    work = prepare_workspace(toy_repo.path, _task(parent, commit), tmp_path / "run")
    return toy_repo, parent, commit, work


def _git(work: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(work), *args], check=True, text=True, capture_output=True
    ).stdout.strip()


def test_workspace_has_no_original_history(prepared):
    toy, _, _, work = prepared
    log = _git(work, "log", "--format=%H %s").splitlines()
    assert len(log) == 1 and log[0].endswith(" baseline")
    assert len(_git(work, "rev-list", "--all").splitlines()) == 1
    assert _git(work, "tag").splitlines() == ["baseline"]
    assert _git(work, "branch", "--format=%(refname:short)").splitlines() == ["main"]
    for sha in toy.git("rev-list", "--all").split():
        assert (
            subprocess.run(
                ["git", "-C", str(work), "cat-file", "-e", sha], check=False, capture_output=True
            ).returncode
            != 0
        )
    assert _git(work, "rev-parse", "baseline") == _git(work, "rev-parse", "HEAD")


def test_new_hidden_tests_removed_modified_kept_at_parent_version(prepared):
    _, _, _, work = prepared
    assert not (work / HIDDEN_NEW).exists()
    assert "assert True" in (work / HIDDEN_MOD).read_text()


def test_collect_patch_shows_agent_edits(prepared):
    _, _, _, work = prepared
    assert collect_patch(work) == ""
    (work / "backend/src/pharma_agent/domain/y.py").write_text("Y = 2\n")
    (work / ".venv").mkdir()
    (work / ".venv/junk").write_text("x")
    patch = collect_patch(work)
    assert "domain/y.py" in patch and "+Y = 2" in patch
    assert ".venv" not in patch


def _tree(root: Path) -> list[str]:
    return sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())


@pytest.fixture
def host_uv(monkeypatch):
    monkeypatch.setattr(
        "sdlc_harness.workspace.host_uv_dirs",
        lambda: {"UV_CACHE_DIR": "/uv/cache", "UV_PYTHON_INSTALL_DIR": "/uv/python"},
    )


def test_prepare_config_claude_copies_only_credentials(tmp_path, host_uv):
    src = tmp_path / "src"
    (src / "plugins").mkdir(parents=True)
    (src / ".credentials.json").write_text("{}")
    (src / "settings.json").write_text("{}")
    (src / "CLAUDE.md").write_text("host memory")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(f'[claude]\n1 = "{src}"\n')
    env = prepare_config("claude", tmp_path / "run", 1, accounts)
    home = tmp_path / "run" / "config" / "home"
    assert env == {
        "HOME": str(home),
        "UV_CACHE_DIR": "/uv/cache",
        "UV_PYTHON_INSTALL_DIR": "/uv/python",
        "CLAUDE_CONFIG_DIR": str(home / ".claude"),
    }
    assert _tree(tmp_path / "run" / "config") == ["home/.claude/.credentials.json"]


def test_prepare_config_agy_copies_only_the_token(tmp_path, host_uv):
    src = tmp_path / "antigravity-cli"
    (src / "brain").mkdir(parents=True)
    (src / "antigravity-oauth-token").write_text("tok")
    (src / "settings.json").write_text("{}")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(f'[agy]\n1 = "{src}"\n')
    env = prepare_config("agy", tmp_path / "run", 1, accounts)
    config = tmp_path / "run" / "config"
    assert env["HOME"] == str(config / "home")
    assert _tree(config) == [
        "home/.gemini/antigravity-cli/antigravity-oauth-token",
    ]


def test_prepare_config_codex_proxy_reads_key_at_runtime(tmp_path, host_uv):
    proxy = tmp_path / "proxy.yaml"
    proxy.write_text('port: 8317\napi-keys:\n  - "sk-test-123"\nrouting:\n  strategy: rr\n')
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(
        f'[codex]\n1 = {{ proxy_config = "{proxy}", base_url = "http://localhost:8317/v1" }}\n'
    )
    env = prepare_config("codex", tmp_path / "run", 1, accounts)
    codex_home = tmp_path / "run" / "config" / "home" / ".codex"
    assert env["CODEX_HOME"] == str(codex_home)
    assert env[PROXY_KEY_ENV] == "sk-test-123"
    assert _tree(tmp_path / "run" / "config") == ["home/.codex/config.toml"]
    config = tomllib.loads((codex_home / "config.toml").read_text())
    assert "sk-test" not in (codex_home / "config.toml").read_text()
    assert config["model_provider"] == "sdlc-proxy"
    provider = config["model_providers"]["sdlc-proxy"]
    assert provider["base_url"] == "http://localhost:8317/v1"
    assert provider["env_key"] == PROXY_KEY_ENV
    assert "web_search" not in config  # stock tools (ruling R11)
    assert config["project_doc_max_bytes"] == 0
    assert config["skills"] == {"bundled": {"enabled": False}, "include_instructions": False}
    assert config["features"]["memories"] is False and config["features"]["plugins"] is False
    assert "model_reasoning_effort" not in config  # only the command line sets it


def test_prepare_config_codex_direct_copies_only_auth_json(tmp_path, host_uv):
    src = tmp_path / "codex"
    (src / "sessions").mkdir(parents=True)
    for name in ("auth.json", "config.toml", "history.jsonl", "AGENTS.md"):
        (src / name).write_text("x")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(f'[codex]\n2 = "{src}"\n')
    env = prepare_config("codex", tmp_path / "run", 2, accounts)
    assert PROXY_KEY_ENV not in env
    assert _tree(tmp_path / "run" / "config") == [
        "home/.codex/auth.json",
        "home/.codex/config.toml",
    ]
    config = tomllib.loads((tmp_path / "run/config/home/.codex/config.toml").read_text())
    assert "model_provider" not in config and "web_search" not in config


def test_prepare_config_is_identical_for_two_attempts(tmp_path, host_uv):
    src = tmp_path / "antigravity-cli"
    src.mkdir()
    (src / "antigravity-oauth-token").write_text("tok")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(f'[agy]\n1 = "{src}"\n')
    for agent_runs in ("r1", "r2"):
        prepare_config("agy", tmp_path / agent_runs, 1, accounts)
    one, two = tmp_path / "r1" / "config", tmp_path / "r2" / "config"
    assert _tree(one) == _tree(two)
    assert all((one / f).read_bytes() == (two / f).read_bytes() for f in _tree(one))
    assert config_manifest(one) == config_manifest(two) == _tree(one)


def test_prepare_config_file_sources(tmp_path, host_uv):
    (tmp_path / "creds-acct1.json").write_text("{}")
    (tmp_path / "auth-acct2.json").write_text("{}")
    (tmp_path / "tok").write_text("t")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(
        f'[claude]\n1 = "{tmp_path / "creds-acct1.json"}"\n'
        f'[codex]\n2 = "{tmp_path / "auth-acct2.json"}"\n'
        f'[agy]\n3 = "{tmp_path / "tok"}"\n'
    )
    prepare_config("claude", tmp_path / "r1", 1, accounts)
    prepare_config("codex", tmp_path / "r2", 2, accounts)
    prepare_config("agy", tmp_path / "r3", 3, accounts)
    assert _tree(tmp_path / "r1/config") == ["home/.claude/.credentials.json"]
    assert "home/.codex/auth.json" in _tree(tmp_path / "r2/config")
    assert "home/.gemini/antigravity-cli/antigravity-oauth-token" in _tree(tmp_path / "r3/config")


def test_unknown_account_is_an_error(tmp_path, host_uv):
    accounts = tmp_path / "accounts.toml"
    accounts.write_text("[claude]\n")
    with pytest.raises(KeyError, match="no claude account 7"):
        prepare_config("claude", tmp_path / "run", 7, accounts)


CONTAMINANTS = {
    "docs/superpowers/specs/2026-01-01-thing-design.md": "spec",
    "backend/docs/superpowers/plans/2026-01-02-thing.md": "plan",
    "frontend/docs/superpowers/notes.md": "x",
    "skills-lock.json": "{}",
    "backend/skills-lock.json": "{}",
    "AGENTS.md": "a",
    "backend/CLAUDE.md": "c",
    "frontend/GEMINI.md": "g",
    ".claude/settings.json": "{}",
    ".agents/skills/x/SKILL.md": "s",
    "backend/.codex/config.toml": "",
    ".gemini/settings.json": "{}",
}
KEPT = {
    "docs/specs/keep.md": "k",
    "backend/src/pharma_agent/domain/superpowersish.py": "Z = 1\n",
    "docs/agents.md": "lowercase name is not an instruction file",
}


@pytest.fixture
def contaminated(toy_repo, tmp_path):
    parent = toy_repo.commit("docs: history", {**CONTAMINANTS, **KEPT})
    commit = toy_repo.commit("feat: thing", {HIDDEN_NEW: "def test_new():\n    assert True\n"})
    removed: list[str] = []
    work = prepare_workspace(
        toy_repo.path, _task(parent, commit), tmp_path / "run", removed=removed
    )
    return work, removed


def test_prepare_workspace_strips_agent_files_and_superpowers_docs(contaminated):
    work, removed = contaminated
    assert sorted(removed) == sorted(
        [
            "docs/superpowers",
            "backend/docs/superpowers",
            "frontend/docs/superpowers",
            "skills-lock.json",
            "backend/skills-lock.json",
            "AGENTS.md",
            "backend/CLAUDE.md",
            "frontend/GEMINI.md",
            ".claude",
            ".agents",
            "backend/.codex",
            ".gemini",
        ]
    )
    for rel in CONTAMINANTS:
        assert not (work / rel).exists(), rel
    for rel in KEPT:
        assert (work / rel).exists(), rel
    assert find_contaminants(work) == []
    tracked = _git(work, "ls-files").splitlines()
    assert not any("superpowers/" in t or t.endswith("AGENTS.md") for t in tracked)
    assert collect_patch(work) == ""  # removed before baseline: not part of the patch


def test_find_contaminants_ignores_git_and_venv(tmp_path):
    (tmp_path / ".venv/lib/superpowers").mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git/CLAUDE.md").write_text("x")
    assert find_contaminants(tmp_path) == []
    (tmp_path / "x/superpowers/plans").mkdir(parents=True)
    assert find_contaminants(tmp_path) == ["x/superpowers"]


def test_assert_clean_tree_refuses_contaminated_tree(tmp_path):
    assert_clean_tree(tmp_path)
    (tmp_path / "CLAUDE.md").write_text("x")
    with pytest.raises(ContaminatedTreeError, match="CLAUDE.md"):
        assert_clean_tree(tmp_path)
