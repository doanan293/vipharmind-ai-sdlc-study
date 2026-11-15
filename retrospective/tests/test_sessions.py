import json
from datetime import date

from retro.sessions import (
    CUTOFF,
    SESSION_DIRS,
    collect_sessions,
    session_rows,
    session_stats,
    tool_rows,
)


def _write(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(e if isinstance(e, str) else json.dumps(e) for e in entries))


def test_session_dirs_and_cutoff():
    assert [p.name for p in SESSION_DIRS] == [
        "-home-andv-personal-vipharmind",
        "-home-andv-personal-vipharmind-camera-ready",
    ]
    assert CUTOFF == date(2026, 11, 10)


def test_session_stats_counts_only(tmp_path):
    f = tmp_path / "s.jsonl"
    _write(
        f,
        [
            {"type": "summary"},
            {
                "type": "user",
                "timestamp": "2026-09-01T01:00:00Z",
                "message": {"content": "API_KEY=sk-secret"},
            },
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Bash", "input": {"command": "cat .env"}}
                    ]
                },
            },
            {
                "type": "user",
                "message": {"content": [{"type": "tool_result", "content": "SECRET=1"}]},
            },
            {
                "type": "user",
                "message": {"content": [{"type": "text", "text": "[Request interrupted by user]"}]},
            },
            "not json",
        ],
    )
    s = session_stats(f)
    assert (s.user_messages, s.assistant_turns, s.tool_calls, s.user_interrupts) == (
        2,
        1,
        {"Bash": 1},
        1,
    )
    assert s.first_ts == date(2026, 9, 1)
    assert not s.is_subagent
    for secret in ("sk-secret", "cat .env", "SECRET"):
        assert secret not in repr(s)


def test_assistant_entries_of_one_message_count_once(tmp_path):
    f = tmp_path / "s.jsonl"
    block = {"type": "tool_use", "name": "Read", "input": {}}
    _write(
        f,
        [
            {
                "type": "assistant",
                "timestamp": "2026-09-01T01:00:00Z",
                "message": {"id": "m1", "content": [{"type": "text", "text": "x"}]},
            },
            {"type": "assistant", "message": {"id": "m1", "content": [block]}},
            {"type": "assistant", "message": {"id": "m2", "content": [block, block]}},
        ],
    )
    s = session_stats(f)
    assert (s.assistant_turns, s.tool_calls) == (2, {"Read": 3})


def test_collect_excludes_after_cutoff_and_missing_timestamp(tmp_path):
    user = {"type": "user", "message": {"content": "hi"}}
    _write(tmp_path / "a.jsonl", [{**user, "timestamp": "2026-11-04T10:00:00Z"}])
    _write(tmp_path / "b.jsonl", [{**user, "timestamp": "2026-11-15T10:00:00Z"}])
    _write(tmp_path / "c.jsonl", [user])
    _write(
        tmp_path / "a" / "subagents" / "agent-1.jsonl",
        [{**user, "timestamp": "2026-11-03T10:00:00Z"}],
    )
    stats, dropped = collect_sessions([tmp_path])
    assert dropped == {"after_cutoff": 1, "no_timestamp": 1}
    assert [(s.session_no, s.is_subagent, s.first_ts) for s in stats] == [
        (1, True, date(2026, 11, 3)),
        (2, False, date(2026, 11, 4)),
    ]
    rows = session_rows(stats)
    assert set(rows[0]) == {
        "session_no",
        "is_subagent",
        "first_ts",
        "user_messages",
        "assistant_turns",
        "tool_calls",
        "user_interrupts",
    }
    assert tool_rows(stats) == []


def test_tool_rows_sum_across_sessions(tmp_path):
    a = {"type": "assistant", "timestamp": "2026-09-01T01:00:00Z"}
    _write(
        tmp_path / "x.jsonl",
        [{**a, "message": {"content": [{"type": "tool_use", "name": "Bash"}]}}],
    )
    _write(
        tmp_path / "y.jsonl",
        [
            {
                **a,
                "message": {
                    "content": [
                        {"type": "tool_use", "name": "Bash"},
                        {"type": "tool_use", "name": "Edit"},
                    ]
                },
            }
        ],
    )
    stats, _ = collect_sessions([tmp_path])
    assert tool_rows(stats) == [{"tool": "Bash", "calls": 2}, {"tool": "Edit", "calls": 1}]


def test_collect_skips_missing_dirs(tmp_path):
    assert collect_sessions([tmp_path / "nope"]) == ([], {"after_cutoff": 0, "no_timestamp": 0})


def test_injected_user_entries_are_not_human_messages(tmp_path):
    f = tmp_path / "s.jsonl"
    ts = "2026-09-01T01:00:00Z"
    _write(
        f,
        [
            {"type": "user", "timestamp": ts, "message": {"content": "real question"}},
            {"type": "user", "isMeta": True, "message": {"content": "injected skill body"}},
            {"type": "user", "isCompactSummary": True, "message": {"content": "summary"}},
            {"type": "user", "message": {"content": "<command-name>/clear</command-name>"}},
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "text", "text": "<local-command-stdout>x</local-command-stdout>"}
                    ]
                },
            },
        ],
    )
    assert session_stats(f).user_messages == 1
