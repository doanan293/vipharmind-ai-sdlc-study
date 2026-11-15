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


# --- round 1: hidden-set check, deleted files, original-patch report ----------------------


def test_range_hidden_tests_must_match_git(rng):
    from dataclasses import replace

    from sdlc_harness.grade import range_hidden_errors

    repo, task, _ = rng
    assert range_hidden_errors(repo.path, task) == []
    short = replace(task, hidden_tests=(HIDDEN_A,))
    extra = replace(task, hidden_tests=(*task.hidden_tests, OLD_TEST))
    assert any(HIDDEN_B in e for e in range_hidden_errors(repo.path, short))
    assert any(OLD_TEST in e for e in range_hidden_errors(repo.path, extra))
    assert range_hidden_errors(repo.path, replace(task, kind="commit")) == []


def test_grade_refuses_mismatched_hidden_list(rng, tmp_path):
    from dataclasses import replace

    from sdlc_harness.grade import GradingError

    repo, task, cache = rng
    bad = replace(task, hidden_tests=(HIDDEN_A,))
    work = prepare_workspace(repo.path, bad, tmp_path / "run")
    with pytest.raises(GradingError, match="hidden_tests"):
        grade(repo.path, bad, work, cache_dir=cache)


def test_validate_tasks_checks_range_hidden_set(rng, tmp_path):
    from dataclasses import replace

    from sdlc_harness.cli import validate_tasks

    repo, task, _ = rng
    write_task(tmp_path / "f01", replace(task, hidden_tests=(HIDDEN_A,)))
    errors = validate_tasks(tmp_path, repo.path)
    assert any("hidden_tests" in e and HIDDEN_B in e for e in errors)


def test_original_patch_errors_clean_and_broken(rng, tmp_path):
    from sdlc_harness.grade import original_patch_errors

    repo, task, cache = rng
    assert original_patch_errors(repo.path, task, tmp_path / "ok", cache_dir=cache) == []


@pytest.fixture(scope="module")
def deleting(tmp_path_factory):
    """A range that deletes an old test file (and its tests) and renames another."""
    root = tmp_path_factory.mktemp("range-del")
    repo = ToyRepo(root / "toy")
    repo.path.mkdir()
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    old2 = "backend/tests/test_old2.py"
    moved = "backend/tests/test_moved.py"
    body = "def test_old2():\n    assert True\n"
    base = repo.commit("chore: base", {**BASE, old2: body, "backend/tests/test_ren.py": body})
    repo.commit("feat: one", {**C1, old2: None, "backend/tests/test_ren.py": None, moved: body})
    end = repo.commit("feat: two", C2)
    task = Task(
        "f02",
        end,
        "",
        "domain",
        5,
        (HIDDEN_A, HIDDEN_B, moved),
        False,
        "p",
        base=base,
        kind="range",
    )
    return repo, task, root / "cache"


def test_range_deleted_or_renamed_old_tests_are_not_regressions(deleting, tmp_path):
    repo, task, cache = deleting
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    _apply_original(repo, task, work)
    g = grade(repo.path, task, work, cache_dir=cache)
    assert g.task_pass is True, (g.hidden_failed, g.regressions, g.grading_notes)
    assert g.regressions == []
    assert any("test_old2.py" in n for n in g.grading_notes)


def test_range_old_test_broken_at_end_is_not_gradable(tmp_path):
    from sdlc_harness.grade import GradingError

    repo = ToyRepo(tmp_path / "toy")
    repo.path.mkdir()
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    base = repo.commit("chore: base", {**BASE, CONFTEST: "FIVE = 5\n"})
    # the end support file breaks the old test (fakes shadow calc via conftest)
    end = repo.commit(
        "feat: one",
        {**C1, CONFTEST: "raise RuntimeError('boom')\n"},
    )
    task = Task("f03", end, "", "domain", 1, (HIDDEN_A,), False, "p", base=base, kind="range")
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    with pytest.raises(GradingError):
        grade(repo.path, task, work, cache_dir=tmp_path / "cache")


def test_original_patch_check_passes_with_deleted_and_renamed_tests(deleting, tmp_path):
    from sdlc_harness.grade import original_patch_errors

    repo, task, cache = deleting
    assert original_patch_errors(repo.path, task, tmp_path / "run", cache_dir=cache) == []


def test_range_old_test_failing_only_at_end_is_not_gradable(tmp_path):
    from sdlc_harness.grade import GradingError

    repo = ToyRepo(tmp_path / "toy")
    repo.path.mkdir()
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    base = repo.commit("chore: base", BASE)
    # the end tree imports fine and the hidden test passes, but old test_add fails there
    end = repo.commit("feat: one", {**C1, CALC: C1[CALC].replace("a + b", "a + b + 1")})
    task = Task("f04", end, "", "domain", 1, (HIDDEN_A,), False, "p", base=base, kind="range")
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    with pytest.raises(GradingError, match="old tests do not pass at end"):
        grade(repo.path, task, work, cache_dir=tmp_path / "cache")


def test_original_patch_check_ignores_hunks_for_stripped_contaminants(tmp_path):
    from sdlc_harness.grade import original_patch_errors

    repo = ToyRepo(tmp_path / "toy")
    repo.path.mkdir()
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    spec = "backend/docs/superpowers/plans/p.md"
    base = repo.commit(
        "chore: base", {**BASE, spec: "plan v1\n", "skills-lock.json": "{}\n", "CLAUDE.md": "a\n"}
    )
    end = repo.commit(
        "feat: one", {**C1, spec: "plan v2\n", "skills-lock.json": "{ }\n", "CLAUDE.md": "b\n"}
    )
    task = Task("f09", end, "", "domain", 1, (HIDDEN_A,), False, "p", base=base, kind="range")
    assert original_patch_errors(repo.path, task, tmp_path / "run", cache_dir=tmp_path / "c") == []


def test_is_contaminant_path_matches_the_export_strip():
    from sdlc_harness.workspace import drop_contaminant_hunks, is_contaminant_path

    assert is_contaminant_path("backend/docs/superpowers/x.md")
    assert is_contaminant_path("skills-lock.json") and is_contaminant_path("a/CLAUDE.md")
    assert is_contaminant_path("AGENTS.md") and not is_contaminant_path("docs/AGENTS.md")
    assert not is_contaminant_path("backend/src/superpowers_x.py")
    diff = "diff --git a/x.py b/x.py\n+1\ndiff --git a/superpowers/a b/superpowers/a\n+2\n"
    assert drop_contaminant_hunks(diff) == "diff --git a/x.py b/x.py\n+1\n"
