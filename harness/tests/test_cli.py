import json

from sdlc_harness.cli import main

SRC = "backend/src/pharma_agent/domain/calc.py"


def test_screen_writes_records(toy_repo, tmp_path):
    body = "".join(f"def f{i}():\n    return {i}\n" for i in range(20))
    toy_repo.commit(
        "feat: calc",
        {SRC: body, "backend/tests/test_calc.py": "def test_x():\n    assert False or __file__\n"},
    )
    toy_repo.commit("feat: tiny", {SRC: body + "x = 1\n", "backend/tests/test_t.py": "x = 1\n"})
    out = tmp_path / "out" / "screening.json"
    code = main(
        ["screen", "--repo", str(toy_repo.path), "--ref", "HEAD", "--out", str(out)]
        + ["--jobs", "2", "--workroot", str(tmp_path / "work")]
    )
    assert code == 0
    first, second = json.loads(out.read_text())
    assert second["failed_criterion"] == 4
    assert first["layer"] == "domain"
    assert first["hidden_tests"] == ["backend/tests/test_calc.py"]
    # the test passes at the parent too, so criterion 2 rejects it
    assert first["failed_criterion"] == 2
