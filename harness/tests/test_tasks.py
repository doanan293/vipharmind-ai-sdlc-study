from pathlib import Path

import pytest

from sdlc_harness.cli import main
from sdlc_harness.sample import review_order
from sdlc_harness.tasks import (
    Task,
    count_sentences,
    generate_tasks,
    load_task,
    validate_task,
    write_task,
)

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


# --- baseline keys round trip and generate ------------------------------------------------------


def test_write_task_round_trips_baseline_radon(tmp_path: Path):
    task = _task(baseline_radon_cc=3.5, baseline_radon_mi=71.25)
    write_task(tmp_path / "t01", task)
    loaded = load_task(tmp_path / "t01")
    assert (loaded.baseline_radon_cc, loaded.baseline_radon_mi) == (3.5, 71.25)
    write_task(tmp_path / "t01", loaded)
    assert load_task(tmp_path / "t01").baseline_radon_cc == 3.5
    write_task(tmp_path / "t02", _task())
    assert "baseline" not in (tmp_path / "t02" / "task.toml").read_text()
    assert load_task(tmp_path / "t02").baseline_radon_cc is None


def _screening() -> list[dict]:
    recs = []
    for i in range(8):
        recs.append(
            {
                "sha": f"{i:040x}",
                "subject": f"feat: change {i}",
                "layer": "domain" if i < 5 else "api",
                "src_lines": 10 + i,
                "hidden_tests": [f"backend/tests/test_{i}.py"],
                "failed_criterion": None,
                "reason": "ok",
            }
        )
    recs.append({**recs[0], "sha": "f" * 40, "failed_criterion": 2})
    return recs


def _review(screening, verdicts: dict[str, str], n: int | None = None) -> str:
    order = review_order([r for r in screening if r["failed_criterion"] is None])
    out = ["# Review\n"]
    for i, r in enumerate(order[:n], 1):
        out.append(
            f"## {i}. `{r['sha'][:10]}` {r['subject']}\n\n- sha: `{r['sha']}`\n\n"
            f"Draft prompt:\n\n```text\nPrompt for {r['sha'][:6]}. One. Two.\n```\n\n"
            f"An: {verdicts.get(r['sha'], '')}\n"
        )
    return "\n".join(out)


def _gen(tmp_path, review, screening=None):
    return generate_tasks(
        review,
        screening or _screening(),
        lambda sha: "p" + sha[1:],
        tmp_path,
        k=3,
        pilots=2,
    )


def test_generate_writes_ids_in_selection_order_and_is_deterministic(tmp_path: Path):
    scr = _screening()
    eligible = [r for r in scr if r["failed_criterion"] is None]
    verdicts = {r["sha"]: "pass (ok)" for r in eligible}
    review = _review(scr, verdicts)
    chosen = _gen(tmp_path, review, scr)
    assert [c.id for c in chosen] == ["t01", "t02", "t03", "p01", "p02"]
    t01 = load_task(tmp_path / "t01")
    assert t01.parent == "p" + t01.commit[1:] and not t01.pilot
    assert load_task(tmp_path / "p01").pilot
    assert t01.prompt.startswith("Prompt for ") and "```" not in t01.prompt
    first = {p.name: p.read_text() for p in tmp_path.rglob("*") if p.is_file()}
    _gen(tmp_path, review, scr)
    assert first == {p.name: p.read_text() for p in tmp_path.rglob("*") if p.is_file()}


def test_generate_skips_failed_verdicts(tmp_path: Path):
    scr = _screening()
    eligible = [r for r in scr if r["failed_criterion"] is None]
    order = review_order(eligible)
    verdicts = {r["sha"]: "pass" for r in eligible}
    verdicts[order[0]["sha"]] = "fail (no)"
    chosen = _gen(tmp_path, _review(scr, verdicts), scr)
    assert order[0]["sha"] not in {c.commit for c in chosen}


def test_generate_fails_on_wrong_order(tmp_path: Path):
    scr = _screening()
    verdicts = {r["sha"]: "pass" for r in scr}
    lines = _review(scr, verdicts).split("\n## ")
    swapped = "\n## ".join([lines[0], lines[2], lines[1], *lines[3:]])
    with pytest.raises(ValueError, match="order"):
        _gen(tmp_path, swapped, scr)


def test_generate_fails_on_missing_verdict_among_needed(tmp_path: Path):
    scr = _screening()
    eligible = [r for r in scr if r["failed_criterion"] is None]
    order = review_order(eligible)
    verdicts = {r["sha"]: "pass" for r in eligible}
    del verdicts[order[1]["sha"]]
    with pytest.raises(ValueError, match="verdict"):
        _gen(tmp_path, _review(scr, verdicts), scr)


def test_generate_fails_when_quota_cannot_be_filled(tmp_path: Path):
    scr = _screening()
    eligible = [r for r in scr if r["failed_criterion"] is None]
    verdicts = {r["sha"]: "fail" for r in eligible}
    with pytest.raises(ValueError, match="quota"):
        _gen(tmp_path, _review(scr, verdicts), scr)
