from pathlib import Path

from sdlc_harness.cli import main
from sdlc_harness.tasks import Task, count_sentences, load_task, validate_task, write_task

GOOD = (
    "Add a dosage calculator to the domain layer. "
    "Expose it as `calculate_dose(weight_kg: float, mg_per_kg: float) -> float` in "
    "`pharma_agent.domain.dosage`. "
    "The result must be the weight multiplied by the per-kilogram dose. "
    "Reject a non-positive weight with a `ValueError`. "
    "Keep the existing public modules unchanged."
)


def _task(prompt: str = GOOD, **kw) -> Task:
    base = {
        "id": "t01",
        "commit": "a" * 40,
        "parent": "b" * 40,
        "layer": "domain",
        "src_lines": 42,
        "hidden_tests": ("backend/tests/domain/test_dosage.py",),
        "pilot": False,
        "prompt": prompt,
        "test_names": ("test_rejects_zero_weight",),
    }
    base.update(kw)
    return Task(**base)


def test_validate_accepts_good_prompt():
    assert validate_task(_task()) == []


def test_validate_rejects_prompt_naming_hidden_test():
    errors = validate_task(_task(GOOD + " Make test_dosage.py pass."))
    assert any("test_dosage" in e for e in errors)
    errors = validate_task(
        _task(GOOD.replace("unchanged.", "unchanged for test_rejects_zero_weight."))
    )
    assert any("test_rejects_zero_weight" in e for e in errors)


def test_validate_rejects_four_sentences():
    four = ". ".join(GOOD.split(". ")[:4]) + "."
    assert count_sentences(four) == 4
    assert any("sentences" in e for e in validate_task(_task(four)))


def test_validate_rejects_eleven_sentences():
    eleven = GOOD + " Also log it." * 6
    assert any("sentences" in e for e in validate_task(_task(eleven)))


def test_validate_rejects_todo():
    assert any("TODO" in e for e in validate_task(_task(GOOD + " TODO: finish.")))


def test_count_sentences_ignores_dots_inside_code_and_paths():
    text = "Call `a.b.c()` on version 1.5 of /api/v1/x.json. Then stop! Why? Done."
    assert count_sentences(text) == 4


def test_load_task_round_trip_and_missing_keys(tmp_path: Path):
    write_task(tmp_path / "t01", _task())
    loaded = load_task(tmp_path / "t01")
    assert loaded.prompt.strip() == GOOD
    assert loaded.hidden_tests == ("backend/tests/domain/test_dosage.py",)
    assert loaded.missing_keys == ()
    toml = (tmp_path / "t01" / "task.toml").read_text()
    (tmp_path / "t01" / "task.toml").write_text(
        "\n".join(line for line in toml.splitlines() if not line.startswith("parent"))
    )
    errors = validate_task(load_task(tmp_path / "t01"))
    assert any("parent" in e for e in errors)


def test_load_task_reads_test_names_from_repo(toy_repo, tmp_path: Path):
    sha = toy_repo.commit(
        "feat: dosage",
        {"backend/tests/domain/test_dosage.py": "def test_rejects_zero_weight():\n    pass\n"},
    )
    write_task(tmp_path / "t01", _task(commit=sha, test_names=()))
    loaded = load_task(tmp_path / "t01", repo=toy_repo.path)
    assert loaded.test_names == ("test_rejects_zero_weight",)


def _write_set(root: Path, bad: str | None = None) -> None:
    for i in range(1, 16):
        tid = f"t{i:02d}"
        write_task(root / tid, _task(GOOD + (" TODO" if tid == bad else ""), id=tid))
    for i in (1, 2):
        write_task(root / f"p{i:02d}", _task(id=f"p{i:02d}", pilot=True))


def test_cli_tasks_validate(tmp_path: Path):
    _write_set(tmp_path)
    assert main(["tasks", "validate", "--dir", str(tmp_path)]) == 0
    _write_set(tmp_path, bad="t03")
    assert main(["tasks", "validate", "--dir", str(tmp_path)]) == 1


def test_cli_tasks_validate_requires_17_tasks(tmp_path: Path):
    _write_set(tmp_path)
    (tmp_path / "t15" / "task.toml").unlink()
    (tmp_path / "t15" / "prompt.md").unlink()
    (tmp_path / "t15").rmdir()
    assert main(["tasks", "validate", "--dir", str(tmp_path)]) == 1
