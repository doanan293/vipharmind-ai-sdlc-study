"""Build the agent prompt: the arm's instruction block, a blank line, then the task text verbatim."""

from pathlib import Path
from typing import Literal

from sdlc_harness.tasks import Task

Arm = Literal["spec", "vibe"]
ARMS: tuple[Arm, ...] = ("spec", "vibe")
PROMPTS_DIR = Path(__file__).resolve().parents[3] / "prompts"


def arm_instructions(arm: Arm, prompts_dir: Path = PROMPTS_DIR) -> str:
    """The instruction block for an arm, read from code/prompts/<arm>.md without trailing whitespace."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm {arm!r}, expected one of {ARMS}")
    return (prompts_dir / f"{arm}.md").read_text().rstrip()


def render_prompt(task: Task, arm: Arm, prompts_dir: Path = PROMPTS_DIR) -> str:
    """Same framing for both arms, so only the instruction block differs."""
    return f"{arm_instructions(arm, prompts_dir)}\n\n{task.prompt}"
