"""Synthetic E2 study (prereg-v1.2): the synthetic tasks of `synthetic.py`, two cohorts, both
prompt conditions, with judge.json written so every checklist estimand has a known value.

Checklist: 4 items per task, item 4 tagged [exact]. Items met per (detail, cohort, arm):
"""

import json
from pathlib import Path

import synthetic as syn

COHORTS = ("claude-sonnet", "codex-luna")
# met items (out of 1..4) -> score = len/4, score_core = len(met & {1,2,3})/3
MET = {
    ("brief", "claude-sonnet", "spec"): (1, 2, 3),  # 0.75 / 1.0
    ("brief", "claude-sonnet", "vibe"): (1,),  # 0.25 / 1/3
    ("brief", "codex-luna", "spec"): (1, 4),  # 0.5 / 1/3
    ("brief", "codex-luna", "vibe"): (1, 2),  # 0.5 / 2/3
    ("detailed", "claude-sonnet", "spec"): (1, 2, 3, 4),  # 1.0 / 1.0
    ("detailed", "claude-sonnet", "vibe"): (1, 2, 4),  # 0.75 / 2/3
    ("detailed", "codex-luna", "spec"): (1, 2, 3),  # 0.75 / 1.0
    ("detailed", "codex-luna", "vibe"): (1, 2, 3),  # 0.75 / 1.0
}
EXACT = (4,)
NO_JUDGE = [("brief", "claude-sonnet", "t01", "vibe", 1), ("brief", "claude-sonnet", "t01",
                                                            "vibe", 2)]
# every rep of one cell unjudged: the task drops out of codex's brief score estimate
NO_JUDGE_CELL = ("brief", "codex-luna", "t02", "spec")
REJECTED = ("brief", "claude-sonnet", "t03", "spec", 1)  # judged by another model
DEFERRED = ("brief", "codex-luna", "t04", "vibe", 3)  # not finished yet
BRIEF_SPEC_TESTS = 6  # brief sonnet spec runs add 6 tests (detailed: 4) -> interaction 2


def checklist(tid: str) -> str:
    return (f"# Checklist {tid}\nSource: hidden tests\n\n1. Does a.\n2. Does b.\n3. Does c.\n"
            "4. Returns the literal \"x\". [exact]\n")


def judge_json(met: tuple[int, ...], model: str = "claude-fable-5-2") -> dict:
    items = [{"n": n, "verdict": "met" if n in met else ("unclear" if n == 2 else "not_met"),
              "reason": "r"} for n in range(1, 5)]
    core = [n for n in range(1, 5) if n not in EXACT]
    return {"judge_model": model, "items": items, "n_items": 4, "n_met": len(met),
            "n_unclear": sum(i["verdict"] == "unclear" for i in items),
            "score": len(met) / 4, "exact_items": list(EXACT),
            "score_core": sum(n in met for n in core) / len(core)}


def write_e2(root: Path) -> tuple[Path, Path, Path]:
    tasks_dir = root / "tasks"
    syn.write_tasks(tasks_dir)
    for tier, tasks in syn.TIERS.items():
        for tid in tasks:
            (tasks_dir / tid / "checklist.md").write_text(checklist(tid))
            (tasks_dir / tid / "brief.md").write_text(f"Do the thing for {tid}.\n")
    roots = {"detailed": root / "main", "brief": root / "brief"}
    for detail, res in roots.items():
        for cohort in COHORTS:
            for tier, tasks in syn.TIERS.items():
                for i, tid in enumerate(tasks):
                    for arm in ("spec", "vibe"):
                        k = syn.passes(cohort, tier, arm, i, False)
                        for rep in (1, 2, 3):
                            key = (detail, cohort, tid, arm, rep)
                            status = "deferred" if key == DEFERRED else "done"
                            syn.write_unit(res, cohort, tid, tier, arm, rep, rep <= k, status)
                            d = res / cohort / tid / f"{arm}-r{rep}"
                            meta = json.loads((d / "meta.json").read_text())
                            meta["prompt_file"] = "brief.md" if detail == "brief" else "prompt.md"
                            (d / "meta.json").write_text(json.dumps(meta))
                            if status != "done":
                                continue
                            if (detail == "brief" and cohort == "claude-sonnet"
                                    and arm == "spec"):
                                g = json.loads((d / "grade.json").read_text())
                                g["ai_tests_added"] = BRIEF_SPEC_TESTS
                                (d / "grade.json").write_text(json.dumps(g))
                            if key in NO_JUDGE or key[:4] == NO_JUDGE_CELL:
                                continue
                            model = "gpt-6-luna" if key == REJECTED else "claude-fable-5-2"
                            j = judge_json(MET[(detail, cohort, arm)], model)
                            (d / "judge.json").write_text(json.dumps(j))
    return tasks_dir, roots["detailed"], roots["brief"]
