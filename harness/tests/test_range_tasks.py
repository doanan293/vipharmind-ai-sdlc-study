"""Multi-commit range tasks on a toy repo: workspace at base, hidden/support/manifests from end."""

import subprocess

import pytest
from conftest import BASE_FILES, ToyRepo

from sdlc_harness.grade import grade
from sdlc_harness.tasks import Task, load_task, validate_task, write_task
from sdlc_harness.workspace import prepare_workspace

CALC = "backend/src/pharma_agent/domain/calc.py"
OLD_TEST = "backend/tests/test_calc.py"
SUPPORT = "backend/tests/support.py"
CONFTEST = "backend/tests/conftest.py"
NEW_SUPPORT = "backend/tests/fakes.py"
HIDDEN_A = "backend/tests/test_mul.py"
HIDDEN_B = "backend/tests/test_neg.py"
PYPROJECT = "backend/pyproject.toml"

BASE = {
    CALC: "def add(a, b):\n    return a + b\n",
    OLD_TEST: (
        "from pharma_agent.domain.calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"
    ),
    SUPPORT: "def expected(a, b):\n    return a * b\n",
}
C1 = {
    CALC: BASE[CALC] + "\n\ndef mul(a, b):\n    return a * b\n",
    NEW_SUPPORT: "class FakeCalc:\n    result = 6\n",
    HIDDEN_A: (
        "from pharma_agent.domain.calc import mul\n"
        "from tests.fakes import FakeCalc\n\n\n"
        "def test_mul():\n    assert mul(2, 3) == FakeCalc.result\n"
    ),
}
C2 = {
    CALC: C1[CALC] + "\n\ndef neg(a):\n    return -a\n",
    SUPPORT: "def expected(a, b):\n    return a * b\n\n\ndef negated(a):\n    return -a\n",
    CONFTEST: "import pytest\n\n\n@pytest.fixture\ndef five():\n    return 5\n",
    HIDDEN_B: (
        "from pharma_agent.domain.calc import neg\n"
        "from tests.support import negated\n\n\n"
        "def test_neg(five):\n    assert neg(five) == negated(five)\n"
    ),
}


@pytest.fixture(scope="module")
def rng(tmp_path_factory):
    root = tmp_path_factory.mktemp("range")
    repo = ToyRepo(root / "toy")
    repo.path.mkdir()
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    base = repo.commit("chore: base", BASE)
    repo.commit("feat: one", C1)
    repo.commit("feat: two", C2)
    end = repo.commit("feat: three", {PYPROJECT: BASE_FILES[PYPROJECT] + "# dep bump\n"})
    task = Task(
        "f01", end, "", "domain", 5, (HIDDEN_A, HIDDEN_B), False, "p", base=base, kind="range"
    )
    return repo, task, root / "cache"


@pytest.fixture
def ws(rng, tmp_path):
    repo, task, cache = rng
    return repo, task, prepare_workspace(repo.path, task, tmp_path / "run"), cache


def _apply_original(repo, task, work):
    diff = repo.git("diff", task.start, task.commit) + "\n"
    subprocess.run(["git", "-C", str(work), "apply"], input=diff, text=True, check=True)


def test_range_workspace_starts_at_base(ws):
    _, _, work, _ = ws
    assert (work / CALC).read_text() == BASE[CALC]
    assert not (work / HIDDEN_A).exists() and not (work / HIDDEN_B).exists()
    # support files stay at base state; added ones do not exist
    assert (work / SUPPORT).read_text() == BASE[SUPPORT]
    assert not (work / NEW_SUPPORT).exists() and not (work / CONFTEST).exists()
    assert "dep bump" not in (work / PYPROJECT).read_text()
    log = subprocess.run(
        ["git", "-C", str(work), "log", "--format=%s"], check=True, text=True, capture_output=True
    ).stdout.split()
    assert log == ["baseline"]


def test_original_range_patch_passes(ws):
    repo, task, work, cache = ws
    _apply_original(repo, task, work)
    g = grade(repo.path, task, work, cache_dir=cache)
    assert g.task_pass is True, (g.hidden_failed, g.regressions, g.grading_notes)
    assert g.regressions == []
    assert (g.hidden_passed, g.hidden_total) == (2, 2)


def test_range_hidden_and_support_files_restored_from_end(ws):
    repo, task, work, cache = ws
    # code only; the agent also tampers with support files and adds its own fakes
    (work / CALC).write_text(C2[CALC])
    (work / SUPPORT).write_text("def negated(a):\n    return a\n")
    (work / NEW_SUPPORT).write_text("class FakeCalc:\n    result = 99\n")
    (work / CONFTEST).write_text("import pytest\n\n\n@pytest.fixture\ndef five():\n    return 0\n")
    g = grade(repo.path, task, work, cache_dir=cache)
    assert g.task_pass is True, (g.hidden_failed, g.regressions, g.grading_notes)
    assert g.hidden_total == 2


def test_range_manifests_restored_from_end(ws):
    repo, task, work, cache = ws
    _apply_original(repo, task, work)
    (work / PYPROJECT).write_text(BASE_FILES[PYPROJECT] + "# tampered\n")
    g = grade(repo.path, task, work, cache_dir=cache)
    graded = work.parent / "graded"
    assert "dep bump" in (graded / PYPROJECT).read_text()
    assert "tampered" not in (graded / PYPROJECT).read_text()
    assert g.task_pass is True, g.grading_notes


def test_range_without_code_fails(ws):
    repo, task, work, cache = ws
    g = grade(repo.path, task, work, cache_dir=cache)
    assert g.task_pass is False
    assert g.hidden_passed == 0


def test_commit_tasks_unchanged():
    t = Task("t01", "e" * 40, "p" * 40, "domain", 3, (HIDDEN_A,), False, "p")
    assert (t.kind, t.start) == ("commit", "p" * 40)


def test_range_task_toml_roundtrip(rng, tmp_path):
    repo, task, _ = rng
    write_task(tmp_path / "f01", task)
    loaded = load_task(tmp_path / "f01", repo.path)
    assert (loaded.kind, loaded.base, loaded.commit) == ("range", task.base, task.commit)
    assert loaded.start == task.base
    assert loaded.missing_keys == ()
    assert "test_mul" in loaded.test_names
    assert not any("missing key" in e for e in validate_task(loaded))
