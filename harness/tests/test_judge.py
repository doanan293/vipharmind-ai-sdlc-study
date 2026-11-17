"""Checklist judge (prereg-v1.2, E2)."""

import json

import pytest
from test_runner import UNIT, _cfg, fake, world  # noqa: F401 - fixtures

from sdlc_harness.judge import (
    JudgeConfig,
    _final_message,
    checklist_items,
    exact_items,
    judge_all,
    judge_prompt,
    parse_verdicts,
    score,
)
from sdlc_harness.runner import RunConfig, run_unit, unit_dir

CHECKLIST = "# Checklist t01\nSource: x\n\n1. multiplies two numbers\n2. keeps add working\n"


def test_checklist_items_counts_numbered_lines():
    assert checklist_items(CHECKLIST) == 2
    assert checklist_items("1. a\n  2. b\nnot 3 an item\n10. c") == 3


def test_parse_verdicts_accepts_wrapped_json_and_checks_numbering():
    msg = 'Here: {"items": [{"n": 2, "verdict": "NOT_MET", "reason": "r"}, {"n": 1, "verdict": "met"}]}'
    items = parse_verdicts(msg, 2)
    assert [i["verdict"] for i in items] == ["met", "not_met"]
    assert score(items) == {
        "n_items": 2,
        "n_met": 1,
        "n_unclear": 0,
        "score": 0.5,
        "exact_items": [],
        "score_core": 0.5,
    }
    assert score(items, [2])["score_core"] == 1.0
    with pytest.raises(ValueError):
        parse_verdicts('{"items": [{"n": 1, "verdict": "met"}]}', 2)
    with pytest.raises(ValueError):
        parse_verdicts('{"items": [{"n": 1, "verdict": "maybe"}]}', 1)
    with pytest.raises(ValueError):
        parse_verdicts("no json", 1)


def test_final_message_takes_the_last_agent_message():
    lines = [
        {"type": "item.completed", "item": {"type": "agent_message", "text": "first"}},
        {"type": "item.completed", "item": {"type": "command_execution", "text": "x"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "last"}},
    ]
    assert _final_message("\n".join(json.dumps(e) for e in lines) + "\nnot json") == "last"


def _judge_world(world, fake, tmp_path):  # noqa: F811
    repo, tasks, accounts, cache = world
    (tasks / "t01" / "checklist.md").write_text(CHECKLIST)
    fake.setenv(
        "FAKE_AGENT_WRITE",
        json.dumps(
            {
                "backend/src/pharma_agent/domain/calc.py": "def add(a, b):\n    return a + b\n",
            }
        ),
    )
    out = tmp_path / "out"
    assert run_unit(UNIT, _cfg(world, tmp_path), out) == "done"
    jcfg = JudgeConfig(
        run=RunConfig(
            repo=repo,
            tasks_dir=tasks,
            cohorts={},
            work_root=tmp_path / "judge-work",
            accounts_file=accounts,
            cache_dir=cache,
            grade_timeout_s=120,
        ),
        timeout_s=60,
        accounts=(1,),
    )
    return unit_dir(out, UNIT), jcfg


def test_judge_writes_scored_record_and_blinds_process_docs(world, fake, tmp_path):  # noqa: F811
    unit, jcfg = _judge_world(world, fake, tmp_path)
    # the unit's patch carries the spec arm's process docs; the judge must not see them
    patch = unit / "patch.diff"
    patch.write_text(
        patch.read_text()
        + "diff --git a/docs/plan.md b/docs/plan.md\nnew file mode 100644\n--- /dev/null\n"
        + "+++ b/docs/plan.md\n@@ -0,0 +1 @@\n+the plan\n"
    )
    seen = tmp_path / "seen.txt"
    fake.setenv("FAKE_AGENT_CWDFILES", str(seen))
    fake.setenv(
        "FAKE_AGENT_RESULT",
        '{"items": [{"n": 1, "verdict": "met", "reason": "ok"},'
        ' {"n": 2, "verdict": "unclear", "reason": "?"}]}',
    )
    assert judge_all([unit], jcfg, jobs=1) == {"done": 1, "skipped": 0, "failed": 0}
    rec = json.loads((unit / "judge.json").read_text())
    assert (
        rec["score"] == 0.5 and rec["n_unclear"] == 1 and rec["judge_model"] == "claude-fable-5-2"
    )
    files = seen.read_text().splitlines()
    assert "CHANGE.diff" in files and "docs/plan.md" not in files
    assert not any(x in str(p) for p in files for x in ("claude-sonnet", "vibe", "t01"))
    # already judged: skipped
    assert judge_all([unit], jcfg, jobs=1)["skipped"] == 1


def test_judge_bad_answer_is_a_failure_without_record(world, fake, tmp_path):  # noqa: F811
    unit, jcfg = _judge_world(world, fake, tmp_path)
    fake.setenv("FAKE_AGENT_RESULT", "I could not decide.")
    assert judge_all([unit], jcfg, jobs=1, max_tries=2)["failed"] == 1
    assert not (unit / "judge.json").exists()
    assert not list((tmp_path / "judge-work").iterdir())


def test_exact_tags_are_counted_and_hidden_from_the_judge(tmp_path):
    text = "# C\n\n1. behaves [exact]\n2. other\n3. named x [exact]\n"
    assert exact_items(text) == [1, 3] and checklist_items(text) == 3
    (tmp_path / "judge.md").write_text("PROMPT\n")
    shown = judge_prompt(text, tmp_path)
    assert "[exact]" not in shown and "1. behaves\n" in shown and "3. named x\n" in shown


def test_final_message_reads_claude_result_and_codex_message():
    claude = json.dumps({"type": "result", "result": "answer"})
    assert _final_message("x\n" + claude) == "answer"
    codex = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "c"}})
    assert _final_message(codex) == "c"
