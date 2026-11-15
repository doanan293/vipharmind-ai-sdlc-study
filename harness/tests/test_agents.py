"""Agent command lines, usage parsing and quota detection (no real agent CLI is run)."""

import json
from pathlib import Path

import pytest

from sdlc_harness.agents import (
    AGY_WEB_OFF_FLAGS,
    CODEX_WEB_OFF_FLAGS,
    Usage,
    build_command,
    is_quota_error,
    parse_usage,
)

PROMPT = Path("/runs/x/prompt.txt")


def test_build_command_claude_disables_web_and_sets_medium():
    cmd = build_command("claude", "claude-sonnet-5-5", "medium", PROMPT)
    assert cmd == [
        "claude",
        "-p",
        "--model",
        "claude-sonnet-5-5",
        "--effort",
        "medium",
        "--output-format",
        "stream-json",
        "--verbose",
        "--permission-mode",
        "bypassPermissions",
        "--disallowedTools",
        "WebFetch",
        "WebSearch",
        "--strict-mcp-config",
        "--setting-sources",
        "",
        "--no-session-persistence",
    ]


def test_build_command_codex_sets_reasoning_medium():
    cmd = build_command("codex", "gpt-6-luna", "medium", PROMPT)
    assert cmd[:2] == ["codex", "exec"]
    assert cmd[cmd.index("-m") + 1] == "gpt-6-luna"
    assert 'model_reasoning_effort="medium"' in cmd
    assert cmd[cmd.index("-c") + 1] == 'model_reasoning_effort="medium"'
    assert cmd[cmd.index("--sandbox") + 1] == "workspace-write"
    assert "--json" in cmd
    assert all(flag in cmd for flag in CODEX_WEB_OFF_FLAGS)
    assert cmd[-1] == "-"  # prompt on stdin


def test_build_command_agy_skips_permissions_and_sets_medium():
    cmd = build_command("agy", "gemini-3.8-flash-medium", "medium", PROMPT)
    assert cmd[:8] == [
        "agy",
        "-p",
        "--model",
        "gemini-3.8-flash-medium",
        "--effort",
        "medium",
        "--output-format",
        "stream-json",
    ]
    assert "--dangerously-skip-permissions" in cmd
    assert "--disable-slash-commands" in cmd
    assert cmd[len(cmd) - len(AGY_WEB_OFF_FLAGS) :] == list(AGY_WEB_OFF_FLAGS)


def test_build_command_rejects_unknown_agent():
    with pytest.raises(ValueError):
        build_command("cursor", "m", "medium", PROMPT)


def _jsonl(*events: dict) -> str:
    return "\n".join(json.dumps(e) for e in events) + "\n"


def test_parse_usage_claude_stream_json():
    transcript = _jsonl(
        {"type": "system", "subtype": "init", "model": "claude-sonnet-5-5"},
        {"type": "assistant", "message": {"model": "claude-sonnet-5-5", "content": []}},
        {
            "type": "result",
            "num_turns": 4,
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": 100,
                "output_tokens": 7,
            },
        },
    )
    assert parse_usage("claude", "not json\n" + transcript) == Usage(130, 7, 4, "claude-sonnet-5-5")


def test_parse_usage_codex_sums_turns():
    transcript = _jsonl(
        {"type": "thread.started", "thread_id": "x"},
        {"type": "turn.started"},
        {"type": "turn.completed", "usage": {"input_tokens": 50, "output_tokens": 5}},
        {"type": "turn.started"},
        {"type": "turn.completed", "usage": {"input_tokens": 70, "output_tokens": 6}},
    )
    assert parse_usage("codex", transcript) == Usage(120, 11, 2, None)


def test_parse_usage_empty_transcript_is_unknown():
    assert parse_usage("claude", "") == Usage(None, None, None, None)
    assert parse_usage("codex", "garbage") == Usage(None, None, None, None)


def test_is_quota_error_needs_failure_and_limit_message():
    limit = _jsonl({"type": "result", "is_error": True, "result": "You've hit your usage limit"})
    assert is_quota_error("claude", 1, limit)
    assert not is_quota_error("claude", 0, limit)
    assert not is_quota_error("claude", 1, _jsonl({"type": "result", "result": "crashed"}))
    assert is_quota_error("codex", 1, "ERROR: You've hit your usage limit. Try again later.")
    assert not is_quota_error("codex", 1, "ERROR: stream disconnected")
