from sdlc_harness.prompting import PROMPTS_DIR, arm_instructions, render_prompt
from sdlc_harness.tasks import Task

TASK_TEXT = (
    "Add a dosage calculator to the domain layer.\n"
    "Expose it as `calculate_dose(weight_kg: float, mg_per_kg: float) -> float`.\n"
)


def _task(prompt: str = TASK_TEXT) -> Task:
    return Task(
        id="t01",
        commit="a" * 40,
        parent="b" * 40,
        layer="domain",
        src_lines=42,
        hidden_tests=("backend/tests/domain/test_dosage.py",),
        pilot=False,
        prompt=prompt,
    )


def test_both_arms_contain_identical_task_text():
    for arm in ("spec", "vibe"):
        assert render_prompt(_task(), arm).endswith(TASK_TEXT)


def test_arms_differ_only_in_instruction_block():
    task = _task()
    spec = render_prompt(task, "spec").removeprefix(arm_instructions("spec"))
    vibe = render_prompt(task, "vibe").removeprefix(arm_instructions("vibe"))
    assert spec == vibe
    assert render_prompt(task, "spec") != render_prompt(task, "vibe")


def test_instruction_block_is_separated_by_a_blank_line():
    rendered = render_prompt(_task(), "vibe")
    assert rendered == arm_instructions("vibe") + "\n\n" + TASK_TEXT


def test_spec_prompt_names_design_and_plan_files():
    spec = arm_instructions("spec")
    assert "docs/design.md" in spec
    assert "docs/plan.md" in spec


def test_prompts_do_not_mention_hidden_or_experiment():
    for arm in ("spec", "vibe"):
        text = (PROMPTS_DIR / f"{arm}.md").read_text().lower()
        for word in ("hidden", "experiment", "grade", "benchmark"):
            assert word not in text, f"{arm}.md mentions {word!r}"


def test_vibe_is_one_sentence_without_process_or_tests():
    vibe = arm_instructions("vibe")
    assert vibe.count(".") == 1 and vibe.endswith(".")
    assert "test" not in vibe.lower()
    assert "plan" not in vibe.lower()


def test_spec_prompt_is_at_most_25_lines():
    assert len((PROMPTS_DIR / "spec.md").read_text().strip().splitlines()) <= 25


def test_unknown_arm_is_rejected():
    try:
        render_prompt(_task(), "other")  # type: ignore[arg-type]
    except ValueError:
        return
    raise AssertionError("expected ValueError")
