"""Grading on a toy repo shaped like ViPharmind's backend."""

import json
import subprocess
from dataclasses import asdict, replace
from pathlib import Path

import pytest
from conftest import BASE_FILES, ToyRepo
from radon.metrics import mi_visit

from sdlc_harness.grade import (
    GraderTimeout,
    GradingError,
    ensure_baseline_radon,
    grade,
    grade_to_dict,
    parse_patch,
)
from sdlc_harness.tasks import Task, load_task, write_task
from sdlc_harness.workspace import collect_patch, prepare_workspace

CALC = "backend/src/pharma_agent/domain/calc.py"
API = "backend/src/pharma_agent/api/routes.py"
OLD_TEST = "backend/tests/test_calc.py"
ARCH_TEST = "backend/tests/architecture/test_layering.py"
HIDDEN_NEW = "backend/tests/test_mul.py"
HIDDEN_MOD = "backend/tests/test_mod.py"

CALC_PARENT = "def add(a, b):\n    return a + b\n"
CALC_COMMIT = CALC_PARENT + "\n\ndef mul(a, b):\n    return a * b\n"

PARENT_FILES = {
    # a project ruff config, as in ViPharmind (else ruff falls back to the user's own config)
    "backend/ruff.toml": 'line-length = 88\n[lint]\nselect = ["F"]\n',
    "backend/pyrefly.toml": 'project-includes = ["src", "tests"]\nsearch-path = ["src"]\n',
    CALC: CALC_PARENT,
    API: "from pharma_agent.domain.calc import add\n\nTOTAL = add(1, 2)\n",
    OLD_TEST: (
        "from pharma_agent.domain.calc import add\n\n\n"
        "def test_add():\n    assert add(2, 3) == 5\n\n\n"
        "def test_add_zero():\n    assert add(0, 0) == 0\n"
    ),
    "backend/tests/architecture/__init__.py": "",
    ARCH_TEST: (
        "from pathlib import Path\n\n\n"
        "def test_domain_does_not_import_api():\n"
        "    domain = Path(__file__).parents[2] / 'src/pharma_agent/domain'\n"
        "    for f in domain.rglob('*.py'):\n"
        "        assert 'pharma_agent.api' not in f.read_text(), f\n"
    ),
    HIDDEN_MOD: "def test_mod_old():\n    assert True\n",
}
COMMIT_FILES = {
    CALC: CALC_COMMIT,
    HIDDEN_NEW: (
        "from pharma_agent.domain.calc import mul\n\n\n"
        "def test_mul():\n    assert mul(2, 3) == 6\n\n\n"
        "def test_mul_zero():\n    assert mul(5, 0) == 0\n"
    ),
    HIDDEN_MOD: (
        "from pharma_agent.domain.calc import mul\n\n\n"
        "def test_mod_uses_mul():\n    assert mul(1, 1) == 1\n"
    ),
}


def _make_repo(root: Path) -> ToyRepo:
    root.mkdir(parents=True)
    repo = ToyRepo(root)
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "user.email", "toy@example.com")
    repo.git("config", "user.name", "Toy")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("chore: scaffold", BASE_FILES)
    return repo


@pytest.fixture(scope="module")
def setup(tmp_path_factory):
    """One toy repo + task + a shared reference cache for the whole module."""
    root = tmp_path_factory.mktemp("grade")
    repo = _make_repo(root / "toy")
    parent = repo.commit("chore: base", PARENT_FILES)
    commit = repo.commit("feat: mul", COMMIT_FILES)
    task = Task("t01", commit, parent, "domain", 3, (HIDDEN_NEW, HIDDEN_MOD), False, "p")
    return repo, task, root / "cache"


@pytest.fixture
def ws(setup, tmp_path):
    """A fresh workspace at the parent; returns (repo, task, work, cache)."""
    repo, task, cache = setup
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    return repo, task, work, cache


def _write(work: Path, files: dict[str, str | None]) -> None:
    for rel, content in files.items():
        p = work / rel
        if content is None:
            p.unlink()
            continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)


def _apply_original(repo: ToyRepo, task: Task, work: Path) -> None:
    diff = repo.git("diff", task.parent, task.commit) + "\n"
    subprocess.run(["git", "-C", str(work), "apply"], input=diff, text=True, check=True)


def _grade(ws):
    repo, task, work, cache = ws
    return grade(repo.path, task, work, cache_dir=cache)


# --- pass / fail -------------------------------------------------------------------------


def test_original_patch_passes(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    g = _grade(ws)
    assert g.task_pass is True
    assert g.regressions == []
    assert (g.hidden_passed, g.hidden_total) == (3, 3)
    assert g.hidden_failed == {}
    assert g.architecture_pass is True
    # the original patch: calc.py +4, test_mul.py +9, test_mod.py +5/-2
    assert (g.lines_added, g.lines_deleted) == (4 + 9 + 5, 2)
    assert g.process_artifacts is False
    assert g.ruff_errors == 0
    assert g.pyrefly_errors == 0


def test_breaking_an_old_test_is_a_regression(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {CALC: CALC_COMMIT.replace("a + b", "a - b")})
    g = _grade(ws)
    assert g.task_pass is False
    assert g.regressions == ["tests/test_calc.py::test_add"]
    assert (g.hidden_passed, g.hidden_total) == (3, 3)


def test_no_change_passes_no_hidden_test(ws):
    g = _grade(ws)
    assert len(g.hidden_failed) == 3  # missing from the run counts as not passing
    assert g.hidden_passed == 0
    assert g.hidden_total == 3
    assert g.task_pass is False
    assert g.regressions == []
    assert (g.lines_added, g.lines_deleted) == (0, 0)
    assert g.ai_tests_added == 0
    assert g.ai_changed_line_coverage is None
    assert (g.radon_cc_mean, g.radon_mi_mean) == (0.0, 0.0)


def test_partial_hidden_pass(ws):
    _, _, work, _ = ws
    _write(work, {CALC: CALC_PARENT + "\n\ndef mul(a, b):\n    return a * b if b else 1\n"})
    g = _grade(ws)
    assert (g.hidden_passed, g.hidden_total) == (2, 3)
    assert g.task_pass is False
    # which hidden test did not pass, and how (failure labels need it)
    assert len(g.hidden_failed) == 1
    ((nodeid, outcome),) = g.hidden_failed.items()
    assert nodeid.startswith("tests/") and outcome == "failed"


def test_ai_edits_to_hidden_tests_are_overwritten(ws):
    _, _, work, _ = ws
    # the AI rewrites the modified hidden test and creates the new one, both trivially passing
    _write(
        work,
        {
            HIDDEN_MOD: "def test_mod_uses_mul():\n    assert True\n",
            HIDDEN_NEW: "def test_mul():\n    assert True\n\n\ndef test_mul_zero():\n"
            "    assert True\n",
        },
    )
    g = _grade(ws)
    assert g.hidden_passed == 0
    assert g.task_pass is False
    assert g.ai_tests_added == 0  # edits to hidden files are not AI tests


def test_ai_deleting_hidden_test_is_restored(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {HIDDEN_MOD: None, HIDDEN_NEW: None})
    g = _grade(ws)
    assert (g.hidden_passed, g.hidden_total) == (3, 3)
    assert g.task_pass is True


def test_deleted_old_test_file_is_restored(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {OLD_TEST: None})
    g = _grade(ws)
    assert g.task_pass is True
    assert g.regressions == []
    assert (work.parent / "graded" / OLD_TEST).read_text() == PARENT_FILES[OLD_TEST]


def test_deleting_old_test_and_breaking_code_is_a_regression(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {OLD_TEST: None, CALC: CALC_COMMIT.replace("a + b", "a - b")})
    g = _grade(ws)
    assert g.task_pass is False
    assert g.regressions == ["tests/test_calc.py::test_add"]


def test_skip_marker_in_old_test_file_is_reverted(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    old = (work / OLD_TEST).read_text()
    _write(
        work,
        {
            CALC: CALC_COMMIT.replace("a + b", "a - b"),
            OLD_TEST: "import pytest\n"
            + old.replace("def test_add():", "@pytest.mark.skip\ndef test_add():"),
        },
    )
    g = _grade(ws)
    assert g.regressions == ["tests/test_calc.py::test_add"]
    assert g.task_pass is False


def test_edited_old_test_assertion_is_reverted(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    old = (work / OLD_TEST).read_text()
    _write(
        work,
        {
            CALC: CALC_COMMIT.replace("a + b", "a - b"),
            OLD_TEST: old.replace("add(2, 3) == 5", "add(2, 3) == -1"),
        },
    )
    g = _grade(ws)
    assert g.regressions == ["tests/test_calc.py::test_add"]
    assert g.task_pass is False


SKIP_HOOK = (
    "import pytest\n\n\n"
    "def pytest_collection_modifyitems(items):\n"
    "    for item in items:\n"
    "        if item.name == 'test_add':\n"
    "            item.add_marker(pytest.mark.skip)\n"
)
DESELECT_HOOK = (
    "def pytest_collection_modifyitems(items):\n"
    "    items[:] = [i for i in items if i.name != 'test_add']\n"
)


@pytest.mark.parametrize("where", ["backend/conftest.py", "backend/tests/conftest.py"])
def test_old_test_skipped_by_new_conftest_is_a_regression(ws, where):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {CALC: CALC_COMMIT.replace("a + b", "a - b"), where: SKIP_HOOK})
    g = _grade(ws)
    assert g.regressions == ["tests/test_calc.py::test_add"]
    assert g.task_pass is False
    assert g.pytest_config_touched is True


def test_old_test_deselected_by_conftest_is_a_regression(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {"backend/conftest.py": DESELECT_HOOK})
    g = _grade(ws)
    assert g.regressions == ["tests/test_calc.py::test_add"]
    assert g.task_pass is False


def test_old_test_skipped_at_parent_and_still_skipped_is_fine(tmp_path):
    repo = _make_repo(tmp_path / "toy")
    files = dict(PARENT_FILES)
    files[OLD_TEST] = "import pytest\n\n\n@pytest.mark.skip\ndef test_add():\n    assert False\n"
    parent = repo.commit("chore: base", files)
    commit = repo.commit("feat: mul", COMMIT_FILES)
    task = Task("t04", commit, parent, "domain", 3, (HIDDEN_NEW, HIDDEN_MOD), False, "p")
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    _apply_original(repo, task, work)
    g = grade(repo.path, task, work)
    assert g.regressions == []
    assert g.task_pass is True


def test_pytest_config_untouched_by_original_patch(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    assert _grade(ws).pytest_config_touched is False


@pytest.mark.parametrize(
    ("path", "change"),
    [
        ("backend/pytest.ini", "[pytest]\naddopts = -q\n"),
        ("backend/setup.cfg", "[tool:pytest]\naddopts = -q\n"),
        ("backend/tox.ini", "[pytest]\naddopts = -q\n"),
        ("backend/pyproject.toml", 'addopts = ["-m", "not integration", "-k", "not test_add"]'),
    ],
)
def test_pytest_config_touched(ws, path, change):
    _, _, work, _ = ws
    if path.endswith("pyproject.toml"):
        text = (work / path).read_text()
        change = text.replace('addopts = ["-m", "not integration"]', change)
        assert change != text
    _write(work, {path: change})
    assert _grade(ws).pytest_config_touched is True


def test_pyproject_change_outside_pytest_section_is_not_config_touch(ws):
    _, _, work, _ = ws
    p = work / "backend/pyproject.toml"
    _write(work, {"backend/pyproject.toml": p.read_text().replace('"0.0.0"', '"0.0.1"')})
    assert _grade(ws).pytest_config_touched is False


def test_failing_ai_test_is_not_a_regression(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {"backend/tests/test_ai_extra.py": "def test_wrong():\n    assert False\n"})
    g = _grade(ws)
    assert g.regressions == []
    assert g.task_pass is True
    assert g.ai_tests_added == 1


def test_architecture_violation(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {CALC: "import pharma_agent.api  # noqa: F401\n" + CALC_COMMIT})
    g = _grade(ws)
    assert g.architecture_pass is False
    assert g.task_pass is False
    assert g.regressions == ["tests/architecture/test_layering.py::test_domain_does_not_import_api"]


# --- process artifacts -------------------------------------------------------------------


def test_process_artifacts_need_both_files(ws):
    _, _, work, _ = ws
    _write(work, {"docs/plan.md": "# Plan\n- a\n- b\n"})
    g = _grade(ws)
    assert g.process_artifacts is False
    assert (g.lines_added, g.lines_deleted) == (0, 0)  # docs are not counted in patch size


def test_process_artifacts_and_labeling_copy(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {"docs/plan.md": "# Plan\n", "docs/design.md": "# Design\n"})
    _write(work, {HIDDEN_MOD: "def test_mod_uses_mul():\n    assert True\n"})
    before = collect_patch(work)
    g = _grade(ws)
    assert g.process_artifacts is True
    assert g.task_pass is True
    assert (g.lines_added, g.lines_deleted) == (4 + 9 + 1, 1)
    # the labeling copy lacks the docs and holds the commit's hidden tests
    graded = work.parent / "graded"
    assert not (graded / "docs/plan.md").exists()
    assert not (graded / "docs/design.md").exists()
    assert (graded / HIDDEN_MOD).read_text() == COMMIT_FILES[HIDDEN_MOD]
    assert (graded / CALC).read_text() == CALC_COMMIT
    # the agent's workspace itself is untouched
    assert collect_patch(work) == before
    assert (work / "docs/plan.md").exists()
    assert (work / HIDDEN_MOD).read_text() == "def test_mod_uses_mul():\n    assert True\n"


def test_process_artifacts_under_backend(ws):
    _, _, work, _ = ws
    _write(work, {"backend/docs/plan.md": "# Plan\n", "backend/docs/design.md": "# D\n"})
    g = _grade(ws)
    assert g.process_artifacts is True
    assert not (work.parent / "graded/backend/docs/plan.md").exists()


# --- static quality ----------------------------------------------------------------------


def test_ruff_counts_diagnostics_in_changed_files(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {CALC: "import os\nimport sys\n" + CALC_COMMIT})
    g = _grade(ws)
    assert g.ruff_errors == 2


def test_ruff_ignores_unchanged_files(ws):
    # a pre-existing violation in an untouched file is not counted
    repo, task, work, _ = ws
    _write(work, {API: "import os\n" + PARENT_FILES[API]})
    subprocess.run(["git", "-C", str(work), "commit", "-qam", "pre"], check=True)
    subprocess.run(
        ["git", "-C", str(work), "tag", "-f", "baseline"], check=True, capture_output=True
    )
    _apply_original(repo, task, work)
    g = _grade(ws)
    assert g.ruff_errors == 0


def test_pyrefly_counts_errors(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {CALC: CALC_COMMIT + '\n\nX: int = "a"\nY: str = 1\n'})
    g = _grade(ws)
    assert g.pyrefly_errors == 2


# --- maintainability ---------------------------------------------------------------------


BRANCHY = (
    "def add(a, b):\n    return a + b\n\n\n"
    "def mul(a, b):\n    if b == 0:\n        return 0\n    return a * b\n"
)


def test_radon_on_changed_src_files(ws):
    _, _, work, _ = ws
    _write(work, {CALC: BRANCHY, "backend/tests/test_ai_r.py": "def test_x():\n    pass\n"})
    g = _grade(ws)
    assert g.radon_cc_mean == pytest.approx((1 + 2) / 2)
    assert g.radon_mi_mean == pytest.approx(mi_visit(BRANCHY, multi=True))


def test_radon_means_over_files(ws):
    _, _, work, _ = ws
    other = (
        "def f(x):\n    if x:\n        return 1\n    if x > 2:\n        return 2\n    return 3\n"
    )
    path = "backend/src/pharma_agent/domain/other.py"
    _write(work, {CALC: BRANCHY, path: other})
    g = _grade(ws)
    assert g.radon_cc_mean == pytest.approx((1 + 2 + 3) / 3)  # mean over all blocks
    mis = [mi_visit(BRANCHY, multi=True), mi_visit(other, multi=True)]
    assert g.radon_mi_mean == pytest.approx(sum(mis) / 2)


def test_baseline_radon_written_once(setup, tmp_path, monkeypatch):
    repo, task, _ = setup
    task_dir = tmp_path / "t01"
    write_task(task_dir, task)
    cc, mi = ensure_baseline_radon(task_dir, repo.path, task)
    assert cc == pytest.approx(1.0)
    assert mi == pytest.approx(mi_visit(CALC_COMMIT, multi=True))
    text = (task_dir / "task.toml").read_text()
    assert f"baseline_radon_cc = {cc!r}" in text
    assert f"baseline_radon_mi = {mi!r}" in text
    assert load_task(task_dir).commit == task.commit  # still a valid task file

    def boom(*a, **k):
        raise AssertionError("recomputed")

    monkeypatch.setattr("sdlc_harness.grade.baseline_radon", boom)
    assert ensure_baseline_radon(task_dir, repo.path, task) == (cc, mi)
    assert (task_dir / "task.toml").read_text() == text


# --- AI tests and coverage ---------------------------------------------------------------


AI_CALC = CALC_PARENT + "\n\ndef mul(a, b):\n    return a * b\n\n\ndef unused(x):\n    return x\n"
AI_TEST = (
    "from pharma_agent.domain.calc import mul\n\n\n"
    "def test_mul_basic():\n    assert mul(2, 2) == 4\n\n\n"
    "class TestMul:\n    def test_in_class(self):\n        assert mul(1, 3) == 3\n\n"
    "    async def test_async_counted(self):\n        pass\n\n\n"
    "def helper():\n    return 1\n"
)


def test_ai_tests_and_changed_line_coverage(ws):
    _, _, work, _ = ws
    _write(work, {CALC: AI_CALC, "backend/tests/test_ai_mul.py": AI_TEST})
    g = _grade(ws)
    assert g.ai_tests_added == 3
    # changed executable lines: def mul, return a*b, def unused, return x -> 3 of 4 covered
    assert g.ai_changed_line_coverage == pytest.approx(0.75)


def test_modified_existing_test_file_counts_only_new_tests(ws):
    _, _, work, _ = ws
    old = (work / OLD_TEST).read_text()
    calc = AI_CALC.replace("a + b", "b + a")  # changed line only the old tests exercise
    more = (
        "\n\ndef test_more():\n    from pharma_agent.domain.calc import mul\n\n"
        "    assert mul(2, 2) == 4\n"
    )
    _write(work, {CALC: calc, OLD_TEST: old + more})
    g = _grade(ws)
    assert g.ai_tests_added == 1
    # changed executable lines: return b + a, def mul, return a*b, def unused, return x;
    # only test_more runs, so `return b + a` and `return x` are missed -> 3 of 5
    assert g.ai_changed_line_coverage == pytest.approx(0.6)


def test_new_methods_in_existing_class_count(ws):
    _, _, work, _ = ws
    base = "class TestK:\n    def test_a(self):\n        assert True\n"
    path = "backend/tests/test_k.py"
    _write(work, {path: base})
    subprocess.run(["git", "-C", str(work), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-qm", "pre"], check=True)
    subprocess.run(
        ["git", "-C", str(work), "tag", "-f", "baseline"], check=True, capture_output=True
    )
    _write(
        work,
        {
            path: base + "\n    def test_b(self):\n        assert True\n\n\n"
            "def test_a():\n    assert True\n"
        },
    )
    assert _grade(ws).ai_tests_added == 2  # TestK::test_b and the top-level test_a


def test_coverage_none_without_ai_tests(ws):
    _, _, work, _ = ws
    _write(work, {CALC: AI_CALC})
    g = _grade(ws)
    assert g.ai_tests_added == 0
    assert g.ai_changed_line_coverage is None


def test_coverage_none_without_changed_src(ws):
    _, _, work, _ = ws
    _write(work, {"backend/tests/test_ai_only.py": "def test_x():\n    assert True\n"})
    g = _grade(ws)
    assert g.ai_tests_added == 1
    assert g.ai_changed_line_coverage is None


def test_coverage_zero_when_ai_tests_cannot_import(ws):
    _, _, work, _ = ws
    _write(
        work,
        {
            CALC: AI_CALC,
            "backend/tests/test_ai_bad.py": "import nope\n\n\ndef test_x():\n    pass\n",
        },
    )
    g = _grade(ws)
    assert g.ai_tests_added == 1
    assert g.ai_changed_line_coverage == 0.0


# --- serialization and guards ------------------------------------------------------------


def test_grade_is_json_serializable(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    g = _grade(ws)
    d = grade_to_dict(g)
    assert d == asdict(g)
    assert json.loads(json.dumps(d))["task_pass"] is True


def test_old_test_failing_at_parent_raises(tmp_path):
    repo = _make_repo(tmp_path / "toy")
    files = dict(PARENT_FILES)
    files[OLD_TEST] += "\n\ndef test_broken_already():\n    assert False\n"
    parent = repo.commit("chore: base", files)
    commit = repo.commit("feat: mul", COMMIT_FILES)
    task = Task("t02", commit, parent, "domain", 3, (HIDDEN_NEW, HIDDEN_MOD), False, "p")
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    with pytest.raises(GradingError, match="test_broken_already"):
        grade(repo.path, task, work)


def test_hidden_test_failing_at_commit_raises(tmp_path):
    repo = _make_repo(tmp_path / "toy")
    parent = repo.commit("chore: base", PARENT_FILES)
    files = dict(COMMIT_FILES)
    files[HIDDEN_NEW] += "\n\ndef test_never_passes():\n    assert False\n"
    commit = repo.commit("feat: mul", files)
    task = Task("t03", commit, parent, "domain", 3, (HIDDEN_NEW, HIDDEN_MOD), False, "p")
    work = prepare_workspace(repo.path, task, tmp_path / "run")
    with pytest.raises(GradingError, match="test_never_passes"):
        grade(repo.path, task, work)


def test_reference_cache_is_reused(ws, monkeypatch):
    repo, task, work, cache = ws
    _grade(ws)  # fills the cache (if not already)
    assert (cache / f"{task.parent}.json").is_file()
    assert (cache / f"{task.commit}.json").is_file()

    def no_export(*a, **k):
        raise AssertionError("reference rerun")

    monkeypatch.setattr("sdlc_harness.grade.export_tree", no_export)
    _apply_original(repo, task, work)
    assert _grade(ws).task_pass is True


def test_regrading_replaces_labeling_copy(ws):
    repo, task, work, _ = ws
    _write(work, {"docs/plan.md": "x\n", "docs/design.md": "y\n"})
    _grade(ws)
    _apply_original(repo, task, work)
    assert _grade(ws).task_pass is True
    assert (work.parent / "graded" / CALC).read_text() == CALC_COMMIT


def test_task_replace_keeps_working(setup, tmp_path):
    # hidden test paths given in any order still map to the same nodeids
    repo, task, cache = setup
    t = replace(task, hidden_tests=tuple(reversed(task.hidden_tests)))
    work = prepare_workspace(repo.path, t, tmp_path / "run")
    _apply_original(repo, t, work)
    assert grade(repo.path, t, work, cache_dir=cache).task_pass is True


def test_preexisting_docs_are_not_process_artifacts(ws):
    _, _, work, _ = ws
    _write(work, {"docs/plan.md": "# old\n", "docs/design.md": "# old\n"})
    subprocess.run(["git", "-C", str(work), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(work), "commit", "-qm", "pre"], check=True)
    subprocess.run(
        ["git", "-C", str(work), "tag", "-f", "baseline"], check=True, capture_output=True
    )
    assert _grade(ws).process_artifacts is False


def test_failing_new_architecture_test_fails_architecture_only(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {"backend/tests/architecture/test_ai_arch.py": "def test_a():\n    assert 0\n"})
    g = _grade(ws)
    assert g.architecture_pass is False
    assert g.regressions == []


def test_broken_ai_test_file_next_to_correct_patch_passes(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _write(work, {"backend/tests/test_ai_broken.py": "def test_x(:\n    pass\n"})
    g = _grade(ws)
    assert g.task_pass is True
    assert g.regressions == []


# --- failures in the agent's tree are grades, not crashes --------------------------------


def _fail_final(monkeypatch, exc):
    import sdlc_harness.grade as grade_mod

    real = grade_mod.run_backend_tests

    def fake(tree, timeout_s=900):
        if tree.name == "graded":
            raise exc
        return real(tree, timeout_s)

    monkeypatch.setattr(grade_mod, "run_backend_tests", fake)


def test_final_run_timeout_raises_with_the_fail_grade(ws, monkeypatch):
    """The caller reruns once; if it times out again the carried grade is kept as a fail."""
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _grade(ws)  # fill the reference cache with the real runner
    _fail_final(monkeypatch, subprocess.TimeoutExpired(["pytest"], 1))
    with pytest.raises(GraderTimeout) as info:
        _grade(ws)
    g = info.value.grade
    assert g.task_pass is False and g.hidden_passed == 0
    assert any("final test run timed out" in n for n in g.grading_notes)


def test_final_run_crash_is_a_grading_error(ws, monkeypatch):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _grade(ws)
    _fail_final(monkeypatch, subprocess.CalledProcessError(1, ["uv", "sync"]))
    with pytest.raises(GradingError, match="final test run failed") as info:
        _grade(ws)
    assert not isinstance(info.value, GraderTimeout)


def test_final_run_without_report_is_a_grading_error(ws, monkeypatch):
    import sdlc_harness.grade as grade_mod
    from sdlc_harness.pytest_run import TestReport

    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _grade(ws)
    real = grade_mod.run_backend_tests
    monkeypatch.setattr(
        grade_mod,
        "run_backend_tests",
        lambda t, s=900: TestReport({}, 0.0, True, "boom") if t.name == "graded" else real(t, s),
    )
    with pytest.raises(GradingError, match="no report"):
        _grade(ws)


def test_pyrefly_failure_is_none(ws, monkeypatch):
    import sdlc_harness.grade as grade_mod

    real = grade_mod._tool
    monkeypatch.setattr(grade_mod, "_tool", lambda n: "false" if n == "pyrefly" else real(n))
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    g = _grade(ws)
    assert g.pyrefly_errors is None
    assert g.task_pass is True
    assert any("pyrefly" in n for n in g.grading_notes)


def test_coverage_timeout_is_none(ws, monkeypatch):
    real = subprocess.run

    def fake(cmd, *a, **k):
        if "coverage" in cmd and "run" in cmd:
            raise subprocess.TimeoutExpired(cmd, 1)
        return real(cmd, *a, **k)

    monkeypatch.setattr("sdlc_harness.grade.subprocess.run", fake)
    _, _, work, _ = ws
    _write(work, {CALC: AI_CALC, "backend/tests/test_ai_mul.py": AI_TEST})
    g = _grade(ws)
    assert g.ai_tests_added == 3
    assert g.ai_changed_line_coverage is None
    assert any("coverage" in n for n in g.grading_notes)


def test_clean_grade_has_no_notes(ws):
    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    assert _grade(ws).grading_notes == []


def test_parse_patch_keeps_odd_line_separators():
    patch = (
        "diff --git a/x.py b/x.py\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        "+++ b/x.py\n"
        "@@ -0,0 +1,3 @@\n"
        "+a = 1  #\x0c - form feed\n"
        "+s = 'x\u2028 y'\n"
        "+b = 2\n"
    )
    [f] = parse_patch(patch)
    assert f.path == "x.py"
    assert f.added_lines == [1, 2, 3]
    assert f.removed == 0


def test_coverage_none_when_run_never_starts(ws, monkeypatch):
    # e.g. `uv run --with coverage` fails before coverage starts: no data file at all
    real = subprocess.run

    def fake(cmd, *a, **k):
        if "coverage" in cmd and "run" in cmd:
            return subprocess.CompletedProcess(cmd, 2, b"", b"uv: lock mismatch")
        return real(cmd, *a, **k)

    monkeypatch.setattr("sdlc_harness.grade.subprocess.run", fake)
    _, _, work, _ = ws
    _write(work, {CALC: AI_CALC, "backend/tests/test_ai_mul.py": AI_TEST})
    g = _grade(ws)
    assert g.ai_changed_line_coverage is None
    assert any("no data" in n for n in g.grading_notes)


# --- a patch that breaks the test setup is the patch's fault ------------------------------


@pytest.mark.parametrize(
    "exc",
    [subprocess.CalledProcessError(1, ["uv", "sync"]), None],
    ids=["sync-failed", "no-report"],
)
def test_failure_caused_by_a_config_change_is_a_fail_grade(ws, monkeypatch, exc):
    import sdlc_harness.grade as grade_mod
    from sdlc_harness.pytest_run import TestReport

    repo, task, work, _ = ws
    _apply_original(repo, task, work)
    _grade(ws)
    (work / "backend/tests/conftest.py").write_text("raise SystemExit(4)\n")  # breaks pytest
    real = grade_mod.run_backend_tests

    def broken(tree, timeout_s=900):
        if tree.name != "graded":
            return real(tree, timeout_s)
        if exc is not None:
            raise exc
        return TestReport({}, 0.0, True, "usage error")

    monkeypatch.setattr(grade_mod, "run_backend_tests", broken)
    g = _grade(ws)
    assert g.task_pass is False and g.hidden_passed == 0
    assert g.pytest_config_touched is True
    assert any("caused by the patch" in n for n in g.grading_notes)
