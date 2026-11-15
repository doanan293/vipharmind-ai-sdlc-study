from pathlib import Path

from conftest import BASE_FILES

from sdlc_harness.pytest_run import run_backend_tests


def _tree(tmp_path: Path, files: dict[str, str]) -> Path:
    tree = tmp_path / "tree"
    for rel, content in {**BASE_FILES, **files}.items():
        p = tree / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return tree


def test_run_backend_tests_parses_junit(tmp_path):
    tree = _tree(
        tmp_path,
        {
            "backend/tests/test_mix.py": (
                "import pytest\n"
                "def test_ok():\n    assert True\n"
                "def test_bad():\n    assert False\n"
                "@pytest.mark.integration\n"
                "def test_slow():\n    assert True\n"
                "class TestC:\n    def test_in_class(self):\n        assert True\n"
            )
        },
    )
    report = run_backend_tests(tree)
    assert report.outcomes == {
        "tests/test_mix.py::test_ok": "passed",
        "tests/test_mix.py::test_bad": "failed",
        "tests/test_mix.py::TestC::test_in_class": "passed",
    }
    assert not report.collection_error
    assert report.duration_s >= 0


def test_collection_error_is_flagged(tmp_path):
    tree = _tree(tmp_path, {"backend/tests/test_broken.py": "import nonexistent_mod\n"})
    report = run_backend_tests(tree)
    assert report.collection_error
    assert report.outcomes == {"tests/test_broken.py": "error"}


def test_uv_lock_location_selects_uv(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd[:2], kwargs["cwd"]))
        raise RuntimeError("stop")

    monkeypatch.setattr("sdlc_harness.pytest_run.subprocess.run", fake_run)
    tree = _tree(tmp_path, {"backend/uv.lock": ""})
    try:
        run_backend_tests(tree)
    except RuntimeError:
        pass
    assert calls == [(["uv", "sync"], tree / "backend")]
