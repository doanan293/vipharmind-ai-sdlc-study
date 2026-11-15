"""Agent command lines, usage parsing and quota detection (no real agent CLI is run)."""

import json
from pathlib import Path

import pytest

from sdlc_harness.agents import (
    AGY_AGENT,
    AGY_DENY,
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
        "--disable-slash-commands",
        "--safe-mode",
        "--settings",
        '{"autoMemoryEnabled": false}',
    ]


def test_build_command_codex_sets_reasoning_medium():
    cmd = build_command("codex", "gpt-6-luna", "medium", PROMPT)
    assert cmd[:2] == ["codex", "exec"]
    assert cmd[cmd.index("-m") + 1] == "gpt-6-luna"
    assert 'model_reasoning_effort="medium"' in cmd
    assert cmd[cmd.index("-c") + 1] == 'model_reasoning_effort="medium"'
    # same autonomy as claude bypassPermissions / agy --dangerously-skip-permissions
    assert "--dangerously-bypass-approvals-and-sandbox" in cmd
    assert "--sandbox" not in cmd
    assert "--json" in cmd
    assert "--strict-config" in cmd
    assert CODEX_WEB_OFF_FLAGS == ("-c", 'web_search="disabled"')
    assert cmd[cmd.index("-c", cmd.index("-c") + 1) + 1] == 'web_search="disabled"'
    assert cmd[-1] == "-"  # prompt on stdin


def test_build_command_agy_passes_prompt_as_print_value_and_uses_no_web_agent(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Add mul.\n-p is not a flag here\n")
    cmd = build_command("agy", "gemini-3.8-flash-medium", "medium", prompt)
    assert cmd[0] == "agy"
    assert cmd[cmd.index("--model") + 1] == "gemini-3.8-flash-medium"
    assert cmd[cmd.index("--effort") + 1] == "medium"
    assert cmd[cmd.index("--output-format") + 1] == "stream-json"
    assert cmd[cmd.index("--agent") + 1] == AGY_AGENT
    assert json.loads(cmd[cmd.index("--settings") + 1]) == {"permissions": {"deny": list(AGY_DENY)}}
    assert "read_url(*)" in AGY_DENY
    assert "--dangerously-skip-permissions" in cmd
    assert "--disable-slash-commands" in cmd
    # agy -p takes the prompt as its value (stdin is ignored): it must be the last argument
    assert cmd[-1] == "-p=Add mul.\n-p is not a flag here\n"


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


def test_parse_usage_claude_reports_thinking_tokens():
    transcript = _jsonl(
        {
            "type": "result",
            "num_turns": 1,
            "usage": {
                "input_tokens": 1,
                "output_tokens": 9,
                "output_tokens_details": {"thinking_tokens": 4},
            },
        },
    )
    assert parse_usage("claude", transcript).reasoning_tokens == 4


def test_parse_usage_agy_stream_json():
    transcript = _jsonl(
        {"event": "init", "init": {"model": "gemini-3.8-flash-medium", "tools": []}},
        {
            "event": "step_update",
            "step_update": {
                "step_type": "agent_response",
                "state": "DONE",
                "usage": {"input_tokens": 8},
            },
        },
        {"event": "step_update", "step_update": {"step_type": "tool", "state": "DONE"}},
        {
            "event": "step_update",
            "step_update": {
                "step_type": "agent_response",
                "state": "DONE",
                "usage": {"input_tokens": 9},
            },
        },
        {
            "event": "step_update",
            "step_update": {"step_type": "agent_response", "state": "ACTIVE", "text_delta": "x"},
        },
        {
            "event": "result",
            "result": {
                "status": "SUCCESS",
                "num_turns": 1,
                "usage": {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "thinking_tokens": 5,
                    "cache_read_tokens": 300,
                    "total_tokens": 120,
                },
            },
        },
    )
    assert parse_usage("agy", transcript) == Usage(400, 20, 2, "gemini-3.8-flash-medium", 5)


def test_parse_usage_codex_sums_turns():
    transcript = _jsonl(
        {"type": "thread.started", "thread_id": "x"},
        {"type": "turn.started"},
        {
            "type": "turn.completed",
            "usage": {"input_tokens": 50, "output_tokens": 5, "reasoning_output_tokens": 2},
        },
        {"type": "turn.started"},
        {"type": "turn.completed", "usage": {"input_tokens": 70, "output_tokens": 6}},
    )
    assert parse_usage("codex", transcript) == Usage(120, 11, 2, None, 2)


def test_parse_usage_empty_transcript_is_unknown():
    assert parse_usage("claude", "") == Usage(None, None, None, None)
    assert parse_usage("codex", "garbage") == Usage(None, None, None, None)
    assert parse_usage("agy", "") == Usage(None, None, None, None)


def test_is_quota_error_needs_failure_and_limit_message():
    limit = _jsonl({"type": "result", "is_error": True, "result": "You've hit your usage limit"})
    assert is_quota_error("claude", 1, limit)
    assert not is_quota_error("claude", 0, limit)
    assert not is_quota_error("claude", 1, _jsonl({"type": "result", "result": "crashed"}))
    assert is_quota_error("codex", 1, "ERROR: You've hit your usage limit. Try again later.")
    assert not is_quota_error("codex", 1, "ERROR: stream disconnected")


@pytest.mark.parametrize(
    ("agent", "message"),
    [
        ("claude", "Usage limit reached"),
        ("claude", "You've hit your session limit · resets 3pm"),
        ("claude", '{"type":"error","error":{"type":"rate_limit_error"}}'),
        ("codex", "You've reached your usage limit. Increase your limits to continue using codex."),
        ("codex", '{"type":"error","message":"usage_limit_reached"}'),
        ("codex", "exceeded retry limit, last status: 429 Too Many Requests"),
        ("agy", 'AGY_ERROR: {"short_error":"x","status":"RESOURCE_EXHAUSTED"}'),
        ("agy", "model gemini-3.8-flash-medium is out of quota until 18:00"),
        ("agy", "You have exhausted your capacity on this model"),
    ],
)
def test_is_quota_error_known_messages(agent, message):
    assert is_quota_error(agent, 1, message)


def test_is_quota_error_ignores_unrelated_limits():
    assert not is_quota_error("claude", 1, "Subagent nesting limit reached (depth 3 of 3)")
    assert not is_quota_error("agy", 1, 'AGY_ERROR: {"short_error":"tool \\"swarm\\" not found"}')
