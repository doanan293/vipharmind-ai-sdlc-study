from sdlc_harness.screen import (
    SHARED_TEST_FILE,
    hidden_tests,
    is_rename_only,
    layer_of,
    screen_static,
)
from sdlc_harness.vcs import Candidate, FileChange, list_candidates

SRC = "backend/src/pharma_agent"


def _cand(*changes: FileChange) -> Candidate:
    return Candidate(sha="s", parent="p", subject="feat: x", changes=changes)


def _src(layer: str, n: int, status="M", name="m.py") -> FileChange:
    return FileChange(f"{SRC}/{layer}/{name}", status, n, 0)  # type: ignore[arg-type]


TEST = FileChange("backend/tests/test_a.py", "A", 5, 0)


def test_shared_test_file():
    assert SHARED_TEST_FILE("backend/tests/conftest.py")
    assert SHARED_TEST_FILE("backend/tests/fakes.py")
    assert SHARED_TEST_FILE("backend/tests/unit/memory_repository.py")
    assert SHARED_TEST_FILE("backend/tests/fixtures/data.json")
    assert not SHARED_TEST_FILE("backend/tests/unit/test_x.py")
    assert not SHARED_TEST_FILE(f"{SRC}/domain/conftest.py")


def test_shared_test_file_fails_criterion_1():
    v = screen_static(_cand(_src("domain", 50), FileChange("backend/tests/conftest.py", "M", 1, 0)))
    assert not v.passed and v.failed_criterion == 1


def test_size_bounds():
    assert screen_static(_cand(_src("domain", 29), TEST)).failed_criterion == 4
    assert screen_static(_cand(_src("domain", 401), TEST)).failed_criterion == 4
    assert screen_static(_cand(_src("domain", 30), TEST)).passed
    v = screen_static(_cand(_src("domain", 400), TEST))
    assert v.passed and v.failed_criterion is None


def test_size_counts_added_plus_deleted_under_src_only():
    c = _cand(FileChange(f"{SRC}/domain/a.py", "M", 20, 10), TEST)
    assert screen_static(c).passed
    assert (
        screen_static(
            _cand(_src("domain", 10), FileChange("backend/tests/test_b.py", "A", 100, 0))
        ).failed_criterion
        == 4
    )


def test_rename_only_fails_criterion_5():
    c = _cand(FileChange(f"{SRC}/domain/b.py", "R", 1, 1), TEST)
    assert is_rename_only(c)
    # 2 lines is too small for criterion 4 first; use many renames to reach 30+
    many = _cand(*[FileChange(f"{SRC}/domain/f{i}.py", "R", 1, 1) for i in range(15)], TEST)
    assert is_rename_only(many)
    v = screen_static(many)
    assert v.failed_criterion == 5


def test_not_rename_only():
    assert not is_rename_only(_cand(FileChange(f"{SRC}/domain/b.py", "R", 2, 1), TEST))
    assert not is_rename_only(_cand(_src("domain", 40), TEST))


def test_layer_of_most_lines_and_tiebreak():
    assert (
        layer_of(_cand(_src("api", 10), _src("infrastructure", 30, name="n.py")))
        == "infrastructure"
    )
    assert (
        layer_of(
            _cand(_src("api", 10, name="a.py"), _src("api", 10, name="b.py"), _src("domain", 15))
        )
        == "api"
    )
    assert layer_of(_cand(_src("api", 10), _src("domain", 10))) == "domain"
    assert layer_of(_cand(_src("api", 10), _src("application", 10))) == "application"
    assert layer_of(_cand(_src("api", 10), _src("infrastructure", 10))) == "infrastructure"
    assert layer_of(_cand(_src("application", 5), _src("infrastructure", 5))) == "application"


def test_hidden_tests_excludes_deleted_and_non_test_files():
    c = _cand(
        FileChange("backend/tests/unit/test_a.py", "A", 5, 0),
        FileChange("backend/tests/test_b.py", "M", 1, 1),
        FileChange("backend/tests/test_gone.py", "D", 0, 5),
        FileChange("backend/tests/helpers.py", "M", 1, 1),
        FileChange("backend/tests/unit/test_data.json", "A", 1, 0),
        FileChange(f"{SRC}/domain/test_inside_src.py", "A", 1, 0),
    )
    assert hidden_tests(c) == ["backend/tests/unit/test_a.py", "backend/tests/test_b.py"]


def test_real_rename_and_delete_statuses(toy_repo):
    body = "".join(f"line {i}\n" for i in range(20))
    toy_repo.commit(
        "chore: seed", {f"{SRC}/domain/old.py": body, f"{SRC}/domain/gone.py": body + "x\n"}
    )
    toy_repo.git("mv", f"{SRC}/domain/old.py", f"{SRC}/domain/new.py")
    sha = toy_repo.commit(
        "feat: move and delete",
        {f"{SRC}/domain/gone.py": None, "backend/tests/test_t.py": "t\n"},
    )
    cands = list_candidates(toy_repo.path, "main")
    c = next(x for x in cands if x.sha == sha)
    by_path = {ch.path: ch for ch in c.changes}
    assert by_path[f"{SRC}/domain/new.py"].status == "R"
    assert by_path[f"{SRC}/domain/gone.py"].status == "D"
    assert by_path["backend/tests/test_t.py"].status == "A"
    assert not is_rename_only(c)
