from sdlc_harness.vcs import list_candidates
from sdlc_harness.verify import check_fail_to_pass

SRC = "backend/src/pharma_agent/domain/calc.py"
OLD_TEST = "backend/tests/test_old.py"
NEW_TEST = "backend/tests/test_new.py"
OLD_OK = "def test_old():\n    assert True\n"


def _last(repo):
    return list_candidates(repo.path, "HEAD")[-1]


def test_check_fail_to_pass_accepts_real_f2p(toy_repo, tmp_path):
    toy_repo.commit("chore: old test", {OLD_TEST: OLD_OK})
    toy_repo.commit(
        "feat: add calc",
        {
            SRC: "def double(x):\n    return 2 * x\n",
            NEW_TEST: (
                "import sys, pathlib\n"
                "def test_double():\n"
                "    assert pathlib.Path(__file__).parents[1].joinpath("
                "'src/pharma_agent/domain/calc.py').exists()\n"
            ),
        },
    )
    res = check_fail_to_pass(toy_repo.path, _last(toy_repo), tmp_path / "work")
    assert res.passed, res.reason
    assert res.hidden_failing_at_parent == ["tests/test_new.py::test_double"]
    assert res.old_failing == []


def test_rejects_when_hidden_test_already_passes_at_parent(toy_repo, tmp_path):
    toy_repo.commit(
        "feat: trivial", {SRC: "x = 1\n", NEW_TEST: "def test_always():\n    assert True\n"}
    )
    res = check_fail_to_pass(toy_repo.path, _last(toy_repo), tmp_path / "work")
    assert not res.passed
    assert "parent" in res.reason


def test_rejects_when_old_test_breaks(toy_repo, tmp_path):
    marker = "backend/src/pharma_agent/domain/flag.txt"
    toy_repo.commit(
        "chore: old",
        {
            marker: "on",
            OLD_TEST: (
                "import pathlib\n"
                "def test_old():\n"
                "    p = pathlib.Path(__file__).parents[1] / 'src/pharma_agent/domain/flag.txt'\n"
                "    assert p.read_text() == 'on'\n"
            ),
        },
    )
    toy_repo.commit(
        "feat: breaks old",
        {marker: "off", NEW_TEST: "def test_new():\n    assert False or __file__\n"},
    )
    # test_new passes at the original commit but not at the parent; test_old fails at the original.
    res = check_fail_to_pass(toy_repo.path, _last(toy_repo), tmp_path / "work")
    assert not res.passed
    assert "tests/test_old.py::test_old" in res.old_failing
