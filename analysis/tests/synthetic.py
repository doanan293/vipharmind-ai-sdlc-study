"""Synthetic study shaped like the main design (4 cohorts, 3 tiers, 3 reps) with known effects.

Pass counts are fixed per (cohort, tier, arm): the first k of the 3 reps pass. Every other
metric is a fixed function of (arm, pass), so every estimand has an exact known value.
"""

import json
from pathlib import Path

COHORTS = {
    "claude-sonnet": ("claude", "claude-sonnet-5-5"),
    "claude-opus": ("claude", "claude-opus-5-5"),
    "agy-gemini": ("agy", "gemini-3.8-flash-medium"),
    "codex-luna": ("codex", "gpt-6-luna"),
}
TIERS = {
    "small": {f"t{i:02d}": n for i, n in enumerate(
        [40, 45, 60, 70, 80, 100, 120, 130, 150, 170, 180, 200, 220, 250, 310], start=1)},
    "medium": {f"m{i:02d}": n for i, n in enumerate([320, 380, 450, 520, 650], start=1)},
    "large": {f"f{i:02d}": n for i, n in enumerate([760, 900, 1300], start=1)},
}
BASE_MI = 60.0
# passing reps out of 3: (vibe, spec)
PASSES = {
    "claude-sonnet": {"small": (1, 2), "medium": (1, 3), "large": (0, 3)},
    "claude-opus": {"small": (2, 2), "medium": (1, 2), "large": (1, 3)},
    "agy-gemini": {"small": (1, 1), "medium": (0, 1), "large": (0, 2)},
    "codex-luna": {"small": (1, 2), "medium": (1, 2), "large": (0, 1)},
}
JITTER_CYCLE = (0, 1, 2)  # with jitter, sonnet small spec passes = 1 + cycle[task index % 3]

# token counts of a vibe run (spec runs: double)
CLAUDE_TOK = {"input": 1000, "cache_read": 100_000, "cache_write_1h": 10_000, "output": 5000}
CODEX_TOK = {"input": 200_000, "cached": 150_000, "output": 4000}
AGY_TOK = {"input": 50_000, "cache_read": 150_000, "output": 4000}

NONCOMPLIANT = ("claude-sonnet", "t01", "spec", 3)
CONFIG_TOUCHED = ("claude-sonnet", "t02", "spec", 1)
UPSTREAM = ("claude-sonnet", "t03", "vibe", 1)
EXCLUDED_ERROR = ("claude-sonnet", "f01", "vibe", 3)  # vibe never passes there: rate unchanged
DEFERRED = ("codex-luna", "f02", "spec", 2)  # makes (codex-luna, large) incomplete


def passes(cohort: str, tier: str, arm: str, task_index: int, jitter: bool) -> int:
    v, s = PASSES[cohort][tier]
    if jitter and cohort == "claude-sonnet" and tier == "small" and arm == "spec":
        return 1 + JITTER_CYCLE[task_index % 3]
    return s if arm == "spec" else v


def write_tasks(tasks_dir: Path) -> None:
    for tier, tasks in TIERS.items():
        for tid, lines in tasks.items():
            d = tasks_dir / tid
            d.mkdir(parents=True, exist_ok=True)
            kind = '' if tier == "small" else 'kind = "range"\nbase = "b' + tid + '"\n'
            parent = f'parent = "p{tid}"\n' if tier == "small" else ""
            (d / "task.toml").write_text(
                f'id = "{tid}"\ncommit = "c{tid}"\n{kind}{parent}layer = "domain"\n'
                f"src_lines = {lines}\nhidden_tests = [\"backend/tests/test_{tid}.py\"]\n"
                f'pilot = false\ntier = "{tier}"\n'
                f"baseline_radon_cc = 2.0\nbaseline_radon_mi = {BASE_MI}\n"
            )


def _claude_transcript(model: str, mult: int, arm: str) -> str:
    t = {k: v * mult for k, v in CLAUDE_TOK.items()}
    cmd = "cd backend && uv run pytest -q" if arm == "spec" else "ls"
    ev = [
        {"type": "system", "model": model},
        {"type": "assistant", "message": {"id": "m1", "model": model, "content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": cmd}}]}},
        {"type": "result", "num_turns": 5, "usage": {}, "modelUsage": {model: {
            "inputTokens": t["input"], "cacheReadInputTokens": t["cache_read"],
            "cacheCreationInputTokens": t["cache_write_1h"],
            "cacheCreationEphemeral5mInputTokens": 0,
            "cacheCreationEphemeral1hInputTokens": t["cache_write_1h"],
            "outputTokens": t["output"], "thinkingTokens": 10}}},
    ]
    return "\n".join(json.dumps(e) for e in ev) + "\n"


def _codex_transcript(mult: int, arm: str) -> str:
    t = {k: v * mult for k, v in CODEX_TOK.items()}
    cmd = "uv run pytest" if arm == "spec" else "ls"
    ev = [
        {"type": "item.completed", "item": {"type": "command_execution", "command": cmd}},
        {"type": "turn.completed", "usage": {"input_tokens": t["input"],
         "cached_input_tokens": t["cached"], "output_tokens": t["output"]}},
    ]
    return "\n".join(json.dumps(e) for e in ev) + "\n"


def _agy_transcript(model: str, mult: int, arm: str) -> str:
    t = {k: v * mult for k, v in AGY_TOK.items()}
    cmd = "uv run pytest" if arm == "spec" else "ls"
    ev = [
        {"event": "init", "init": {"model": model}},
        {"event": "step_update", "step_update": {"state": "DONE", "step_type": "tool",
         "tool_info": {"parameters": {"CommandLine": cmd}}}},
        {"event": "result", "result": {"usage": {"input_tokens": t["input"],
         "cache_read_tokens": t["cache_read"], "output_tokens": t["output"]}}},
    ]
    return "\n".join(json.dumps(e) for e in ev) + "\n"


def run_cost(cohort: str, arm: str) -> float:
    """The known converted cost of one synthetic run (prereg 7 table)."""
    m = 2 if arm == "spec" else 1
    if cohort == "claude-sonnet":
        t = CLAUDE_TOK
        return m * (t["input"] * 2 + t["cache_read"] * 0.1 + t["cache_write_1h"] * 4
                    + t["output"] * 10) / 1e6
    if cohort == "claude-opus":
        t = CLAUDE_TOK
        return m * (t["input"] * 4 + t["cache_read"] * 0.2 + t["cache_write_1h"] * 8
                    + t["output"] * 20) / 1e6
    if cohort == "agy-gemini":
        t = AGY_TOK
        return m * (t["input"] * 0.75 + t["cache_read"] * 0.075 + t["output"] * 3.75) / 1e6
    t = CODEX_TOK
    return m * ((t["input"] - t["cached"]) * 0.1 + t["cached"] * 0.01 + t["output"] * 0.5) / 1e6


def run_tokens(cohort: str, arm: str) -> int:
    m = 2 if arm == "spec" else 1
    if cohort.startswith("claude"):
        return m * sum(CLAUDE_TOK.values())
    if cohort == "agy-gemini":
        return m * sum(AGY_TOK.values())
    return m * (CODEX_TOK["input"] + CODEX_TOK["output"])


def write_unit(results: Path, cohort: str, tid: str, tier: str, arm: str, rep: int,
               passed: bool, status: str = "done") -> None:
    agent, model = COHORTS[cohort]
    d = results / cohort / tid / f"{arm}-r{rep}"
    d.mkdir(parents=True, exist_ok=True)
    key = (cohort, tid, arm, rep)
    mult = 2 if arm == "spec" else 1
    meta = {
        "cohort": cohort, "task_id": tid, "arm": arm, "rep": rep, "agent": agent,
        "tool_version": "1.0", "model": model, "model_served": model, "effort": "medium",
        "wall_s": 900.0 if arm == "spec" else 600.0, "timed_out": False, "returncode": 0,
        "agent_exit": "ok", "error_attempts": 0, "tier": tier,
        "usage": {"input_tokens": 1, "output_tokens": 1, "turns": 10 * mult},
        "status": status, "prompt_sha256": f"sha-{tid}-{arm}",
        "upstream_urls": ["https://github.com/x/vipharmind"] if key == UPSTREAM else [],
    }
    if status == "error":
        meta["error_attempts"] = 3
        meta["error"] = "RuntimeError: synthetic"
    (d / "meta.json").write_text(json.dumps(meta))
    if agent == "claude":
        tr = _claude_transcript(model, mult, arm)
    elif agent == "codex":
        tr = _codex_transcript(mult, arm)
    else:
        tr = _agy_transcript(model, mult, arm)
    (d / "transcript.jsonl").write_text(tr)
    if status != "done":
        return
    compliant = arm == "spec" and key != NONCOMPLIANT
    patch = ""
    if compliant:
        patch += "diff --git a/docs/design.md b/docs/design.md\n+x\n"
        patch += "diff --git a/docs/plan.md b/docs/plan.md\n+x\n"
    patch += "diff --git a/backend/src/a.py b/backend/src/a.py\n+y\n"
    (d / "patch.diff").write_text(patch)
    grade = {
        "task_pass": passed,
        "hidden_passed": 10 if passed else 7,
        "hidden_total": 10,
        # a failing vibe run breaks one old test
        "regressions": ["tests/test_old.py::test_x"] if (arm == "vibe" and not passed) else [],
        "ruff_errors": 1 if arm == "spec" else 3,
        "pyrefly_errors": 0 if arm == "spec" else 2,
        "architecture_pass": True,
        "radon_cc_mean": 2.5,
        "radon_mi_mean": BASE_MI - 2.0 if arm == "spec" else BASE_MI,
        "ai_tests_added": 4 if arm == "spec" else 0,
        "ai_changed_line_coverage": 0.9 if arm == "spec" else None,
        "lines_added": 100 * mult,
        "lines_deleted": 10,
        "process_artifacts": compliant,
        "pytest_config_touched": key == CONFIG_TOUCHED,
        "grading_notes": [],
    }
    (d / "grade.json").write_text(json.dumps(grade))


def write_study(root: Path, *, jitter: bool = False, statuses: bool = True) -> tuple[Path, Path]:
    tasks_dir, results = root / "tasks", root / "results"
    write_tasks(tasks_dir)
    for cohort in COHORTS:
        for tier, tasks in TIERS.items():
            for i, tid in enumerate(tasks):
                for arm in ("spec", "vibe"):
                    k = passes(cohort, tier, arm, i, jitter)
                    for rep in (1, 2, 3):
                        key = (cohort, tid, arm, rep)
                        status = "done"
                        if statuses and key == EXCLUDED_ERROR:
                            status = "error"
                        if statuses and key == DEFERRED:
                            status = "deferred"
                        write_unit(results, cohort, tid, tier, arm, rep, rep <= k, status)
    return tasks_dir, results
