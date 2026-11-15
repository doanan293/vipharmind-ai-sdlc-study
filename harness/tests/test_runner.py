"""The parallel runner, driven by tests/fakes/fake_agent.py on a toy repo."""

import json
import os
from pathlib import Path

import pytest
from conftest import BASE_FILES, ToyRepo

from sdlc_harness.cli import main
from sdlc_harness.runner import (
    Cohort,
    RunConfig,
    RunUnit,
    load_cohorts,
    plan_units,
    run_all,
    run_unit,
    select_tasks,
    unit_dir,
)

FAKE = Path(__file__).parent / "fakes" / "fake_agent.py"
CALC = "backend/src/pharma_agent/domain/calc.py"
OLD_TEST = "backend/tests/test_calc.py"
HIDDEN = "backend/tests/test_mul.py"
CALC_PARENT = "def add(a, b):\n    return a + b\n"
CALC_COMMIT = CALC_PARENT + "\n\ndef mul(a, b):\n    return a * b\n"
PROMPT = (
    "Add a mul function to the calc module. It multiplies two numbers. Keep add as it is. "
    "Write it in plain Python. Do not add dependencies.\n"
)


def _task_dir(root: Path, task_id: str, commit: str, parent: str, pilot: bool) -> Path:
    d = root / task_id
    d.mkdir(parents=True)
    (d / "task.toml").write_text(
        f'id = "{task_id}"\ncommit = "{commit}"\nparent = "{parent}"\nlayer = "domain"\n'
        f'src_lines = 3\nhidden_tests = ["{HIDDEN}"]\npilot = {"true" if pilot else "false"}\n'
    )
    (d / "prompt.md").write_text(PROMPT)
    return d


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    root = tmp_path_factory.mktemp("runner")
    repo = ToyRepo(root / "toy")
    repo.path.mkdir()
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    parent = repo.commit(
        "chore: base",
        {
            CALC: CALC_PARENT,
            OLD_TEST: "from pharma_agent.domain.calc import add\n\n\n"
            "def test_add():\n    assert add(2, 3) == 5\n",
        },
    )
    commit = repo.commit(
        "feat: mul",
        {
            CALC: CALC_COMMIT,
            HIDDEN: "from pharma_agent.domain.calc import mul\n\n\n"
            "def test_mul():\n    assert mul(2, 3) == 6\n",
        },
    )
    tasks = root / "tasks"
    _task_dir(tasks, "t01", commit, parent, pilot=False)
    _task_dir(tasks, "p01", commit, parent, pilot=True)
    # hidden test does not pass at the "commit": a task-data problem
    _task_dir(tasks, "t02", parent, parent, pilot=False)
    creds = root / "creds"
    for n in (1, 2):
        (creds / str(n)).mkdir(parents=True)
        (creds / str(n) / ".credentials.json").write_text("{}")
    accounts = root / "accounts.toml"
    accounts.write_text(f'[claude]\n1 = "{creds / "1"}"\n2 = "{creds / "2"}"\n')
    return repo.path, tasks, accounts, root / "cache"


@pytest.fixture
def fake(monkeypatch, tmp_path):
    monkeypatch.setenv("SDLC_FAKE_AGENT", str(FAKE))
    monkeypatch.setenv("FAKE_AGENT_STATE", str(tmp_path / "quota-state"))
    monkeypatch.setenv("FAKE_AGENT_WRITE", json.dumps({CALC: CALC_COMMIT}))
    return monkeypatch


def _cfg(world, tmp_path, accounts=(1, 2), timeout_s=60) -> RunConfig:
    repo, tasks, accounts_file, cache = world
    cohort = Cohort("claude-sonnet", "claude", "claude-sonnet-5-5", "medium", tuple(accounts))
    return RunConfig(
        repo=repo,
        tasks_dir=tasks,
        cohorts={"claude-sonnet": cohort},
        timeout_s=timeout_s,
        grade_timeout_s=120,
        cache_dir=cache,
        work_root=tmp_path / "work",
        accounts_file=accounts_file,
        quota_backoff_s=0.0,
    )


UNIT = RunUnit("claude-sonnet", "t01", "vibe", 1)


def _meta(out: Path, unit: RunUnit = UNIT) -> dict:
    return json.loads((unit_dir(out, unit) / "meta.json").read_text())


def test_plan_units_is_deterministic_and_complete():
    units = plan_units(["claude-sonnet", "claude-opus"], ["t01", "t02"], reps=3)
    assert len(units) == 24
    assert len({(u.cohort, u.task_id, u.arm, u.rep) for u in units}) == 24
    assert {u.arm for u in units} == {"spec", "vibe"}
    assert {u.rep for u in units} == {1, 2, 3}
    assert units == plan_units(["claude-sonnet", "claude-opus"], ["t01", "t02"], reps=3)
    assert units != plan_units(["claude-sonnet", "claude-opus"], ["t01", "t02"], reps=3, seed=1)


def test_unit_dir_layout(tmp_path):
    assert unit_dir(tmp_path, UNIT) == tmp_path / "claude-sonnet" / "t01" / "vibe-r1"


def test_runner_requeues_quota_without_counting(world, fake, tmp_path):
    fake.setenv("FAKE_AGENT_MODE", "quota_once")
    out = tmp_path / "raw"
    summary = run_all([UNIT], _cfg(world, tmp_path), out, jobs=2)
    assert summary == {"done": 1, "skipped": 0, "error": 0, "quota": 1}
    assert len(list(out.rglob("grade.json"))) == 1
    d = unit_dir(out, UNIT)
    for name in ("prompt.txt", "transcript.jsonl", "patch.diff", "grade.json", "meta.json"):
        assert (d / name).is_file(), name
    meta = _meta(out)
    assert meta["account"] == 2
    assert meta["status"] == "done"
    assert meta["timed_out"] is False
    assert meta["model"] == "claude-sonnet-5-5"
    assert meta["model_served"] == "fake-model-served"
    assert meta["effort"] == "medium"
    assert meta["tool_version"] == "fake-agent 0.0.1"
    assert meta["usage"] == {
        "input_tokens": 130,
        "output_tokens": 7,
        "turns": 3,
        "model_served": "fake-model-served",
    }
    assert {"started_at", "wall_s"} <= meta.keys()
    assert json.loads((d / "grade.json").read_text())["task_pass"] is True
    assert "mul" in (d / "patch.diff").read_text()
    assert (out / "quota.log").read_text().count("\n") == 1
    # the credentials copy never stays behind
    assert not list((tmp_path / "work").rglob(".credentials.json"))


def test_runner_waits_and_retries_when_every_account_hit_quota(world, fake, tmp_path):
    fake.setenv("FAKE_AGENT_MODE", "quota_once")
    out = tmp_path / "raw"
    summary = run_all([UNIT], _cfg(world, tmp_path, accounts=(1,)), out, jobs=1)
    assert summary["done"] == 1 and summary["quota"] == 1
    assert _meta(out)["account"] == 1


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    stat = Path(f"/proc/{pid}/stat")
    return not (stat.exists() and stat.read_text().split(")")[-1].split()[0] == "Z")


def test_runner_kills_on_timeout_and_still_grades(world, fake, tmp_path):
    fake.setenv("FAKE_AGENT_MODE", "sleep")
    fake.setenv("FAKE_AGENT_PIDFILE", str(tmp_path / "child.pid"))
    out = tmp_path / "raw"
    assert run_unit(UNIT, _cfg(world, tmp_path, timeout_s=2), out) == "done"
    meta = _meta(out)
    assert meta["timed_out"] is True
    assert meta["wall_s"] < 30
    grade = json.loads((unit_dir(out, UNIT) / "grade.json").read_text())
    assert grade["task_pass"] is True  # the file it wrote before hanging is graded
    assert not _alive(int((tmp_path / "child.pid").read_text()))


def test_runner_skips_done_units(world, fake, tmp_path):
    out = tmp_path / "raw"
    cfg = _cfg(world, tmp_path)
    assert run_all([UNIT], cfg, out, jobs=1)["done"] == 1
    grade_file = unit_dir(out, UNIT) / "grade.json"
    before = grade_file.stat().st_mtime_ns
    fake.setenv("FAKE_AGENT_MODE", "sleep")  # would hang if it ran again
    fake.setenv("FAKE_AGENT_PIDFILE", str(tmp_path / "child.pid"))
    assert run_all([UNIT], cfg, out, jobs=1) == {"done": 0, "skipped": 1, "error": 0, "quota": 0}
    assert grade_file.stat().st_mtime_ns == before


def test_grading_error_is_an_error_not_a_fail(world, fake, tmp_path):
    out = tmp_path / "raw"
    unit = RunUnit("claude-sonnet", "t02", "spec", 1)
    assert run_unit(unit, _cfg(world, tmp_path), out) == "error"
    meta = _meta(out, unit)
    assert meta["status"] == "error"
    assert "hidden tests do not pass" in meta["error"]
    assert not (unit_dir(out, unit) / "grade.json").exists()


def test_select_tasks(world):
    _, tasks, _, _ = world
    assert select_tasks(tasks, "pilot") == ["p01"]
    assert select_tasks(tasks, "main") == ["t01", "t02"]
    assert select_tasks(tasks, "t02,t01") == ["t02", "t01"]
    with pytest.raises(ValueError):
        select_tasks(tasks, "t09")


def test_load_cohorts_from_repo_file():
    cohorts = load_cohorts(Path(__file__).parents[1] / "cohorts.toml")
    assert set(cohorts) == {"claude-sonnet", "claude-opus", "agy-gemini", "codex-luna"}
    assert cohorts["claude-opus"].model == "claude-opus-5-5"
    assert cohorts["agy-gemini"].agent == "agy"
    assert cohorts["codex-luna"].model == "gpt-6-luna"
    assert all(c.effort == "medium" and c.accounts for c in cohorts.values())


def test_cli_run_pilot(world, fake, tmp_path):
    repo, tasks, accounts, cache = world
    cohorts = tmp_path / "cohorts.toml"
    cohorts.write_text(
        '[cohort.claude-sonnet]\nagent = "claude"\nmodel = "claude-sonnet-5-5"\n'
        'effort = "medium"\naccounts = [1]\n'
    )
    out = tmp_path / "raw"
    argv = ["run", "--repo", str(repo), "--tasks-dir", str(tasks), "--cohorts-file", str(cohorts)]
    argv += ["--cohorts", "claude-sonnet", "--tasks", "pilot", "--reps", "1", "--jobs", "2"]
    argv += ["--timeout-s", "60", "--out", str(out), "--work-root", str(tmp_path / "work")]
    argv += ["--accounts-file", str(accounts), "--cache-dir", str(cache)]
    assert main(argv) == 0
    assert sorted(p.parent.name for p in out.rglob("grade.json")) == ["spec-r1", "vibe-r1"]
    assert {p.parts[-3] for p in out.rglob("grade.json")} == {"p01"}
