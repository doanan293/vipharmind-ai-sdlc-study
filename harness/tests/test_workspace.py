import subprocess
from pathlib import Path

import pytest

from sdlc_harness.tasks import Task
from sdlc_harness.workspace import collect_patch, prepare_config, prepare_workspace

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
    all_shas = toy.git("rev-list", "--all").split()
    assert not any(sha in log[0] for sha in all_shas)
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


def test_prepare_config_copies_only_credentials(tmp_path):
    src = tmp_path / "src"
    (src / "plugins").mkdir(parents=True)
    (src / ".credentials.json").write_text("{}")
    (src / "settings.json").write_text("{}")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(f'[claude]\n1 = "{src / ".credentials.json"}"\n')
    env = prepare_config("claude", tmp_path / "run", 1, accounts)
    config = tmp_path / "run" / "config"
    assert env == {"CLAUDE_CONFIG_DIR": str(config)}
    assert sorted(p.name for p in config.iterdir()) == [".credentials.json"]


def test_prepare_config_codex_copies_only_auth_json(tmp_path):
    src = tmp_path / "codex"
    (src / "sessions").mkdir(parents=True)
    for name in ("auth.json", "config.toml", "history.jsonl"):
        (src / name).write_text("x")
    accounts = tmp_path / "accounts.toml"
    accounts.write_text(f'[codex]\n2 = "{src}"\n')
    env = prepare_config("codex", tmp_path / "run", 2, accounts)
    assert env == {"CODEX_HOME": str(tmp_path / "run" / "config")}
    assert [p.name for p in (tmp_path / "run" / "config").iterdir()] == ["auth.json"]


def test_prepare_config_agy_not_yet_supported(tmp_path):
    with pytest.raises(NotImplementedError):
        prepare_config("agy", tmp_path, 1)
