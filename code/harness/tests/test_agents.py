"""Agent command lines, usage parsing and quota detection (no real agent CLI is run)."""

import json
from pathlib import Path

import pytest

from sdlc_harness.agents import (
    Usage,
    build_command,
    is_auth_error,
    is_quota_error,
    parse_usage,
    upstream_urls,
)

PROMPT = Path("/runs/x/prompt.txt")


def test_build_command_claude_stock_agent_at_medium():
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
    assert not any("web_search" in a for a in cmd)  # stock tools (ruling R11)
    assert cmd[-1] == "-"  # prompt on stdin


def test_build_command_agy_passes_prompt_as_print_value_and_uses_stock_agent(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Add mul.\n-p is not a flag here\n")
    cmd = build_command("agy", "gemini-3.8-flash-medium", "medium", prompt)
    assert cmd[0] == "agy"
    assert cmd[cmd.index("--model") + 1] == "gemini-3.8-flash-medium"
    assert cmd[cmd.index("--effort") + 1] == "medium"
    assert cmd[cmd.index("--output-format") + 1] == "stream-json"
    assert "--agent" not in cmd and "--settings" not in cmd  # stock agent (ruling R11)
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
        ("claude", "5-hour limit reached - resets 3pm"),
        ("claude", "Weekly limit reached"),
        ("claude", "5 hour limit reached"),
        ("claude", "You've hit your session limit · resets 3pm"),
        ("claude", '{"type":"error","error":{"type":"rate_limit_error"}}'),
        ("codex", "You've reached your usage limit. Increase your limits to continue using codex."),
        ("codex", '{"type":"error","message":"usage_limit_reached"}'),
        ("codex", "exceeded retry limit, last status: 429 Too Many Requests"),
        ("agy", 'AGY_ERROR: {"short_error":"x","status":"RESOURCE_EXHAUSTED"}'),
        ("agy", "model gemini-3.8-flash-medium is out of quota until 18:00"),
        ("agy", "You have exhausted your capacity on this model"),
        # observed in the pilot (agy 1.5.9, 2026-11-15), stderr of a run that exited 3
        (
            "agy",
            (
                "error: Individual quota reached. Please upgrade your subscription to increase "
                "your limits. Resets in 167h3m55s."
            ),
        ),
    ],
)
def test_is_quota_error_known_messages(agent, message):
    assert is_quota_error(agent, 1, message, message)  # as transcript and as stderr
    if agent == "agy":
        assert is_quota_error(agent, 1, "", message)


def test_is_quota_error_ignores_unrelated_limits():
    assert not is_quota_error("claude", 1, "Subagent nesting limit reached (depth 3 of 3)", "")
    assert not is_quota_error("claude", 1, "Subagent nesting limit reached (depth 3 of 3)")
    assert not is_quota_error("agy", 1, 'AGY_ERROR: {"short_error":"tool \\"swarm\\" not found"}')


def test_upstream_urls_finds_repo_links_only():
    transcript = (
        '{"cmd": "git clone https://github.com/doanan293/ViPharmind.git"}\n'
        '{"text": "from vipharmind.domain import X; see https://docs.python.org/3/"}\n'
        '{"url": "https://raw.githubusercontent.com/x/vipharmind/main/a.py"}\n'
        '{"cmd": "git clone https://github.com/doanan293/ViPharmind.git"}\n'
    )
    assert upstream_urls(transcript) == [
        "https://github.com/doanan293/ViPharmind.git",
        "https://raw.githubusercontent.com/x/vipharmind/main/a.py",
    ]
    assert upstream_urls('{"text": "import vipharmind"}') == []


def test_agy_quota_ignores_code_the_agent_read():
    read = _jsonl(
        {
            "event": "step_update",
            "step_update": {"step_type": "tool", "output": "if status == 429: # rate limit"},
        },
        {"event": "result", "result": {"status": "ERROR", "error": "tool crashed"}},
    )
    assert not is_quota_error("agy", 3, read, "error: tool crashed")
    # tool output mentioning quota is not agy's own error either
    noisy = _jsonl({"event": "step_update", "step_update": {"output": "RESOURCE_EXHAUSTED"}})
    assert not is_quota_error("agy", 3, noisy, "")


def test_agy_quota_from_pilot_result_event_and_agy_error_line():
    result = _jsonl(
        {"event": "result", "result": {"status": "ERROR", "error": "Individual quota reached."}}
    )
    assert is_quota_error("agy", 3, result, "")
    line = 'AGY_ERROR: {"short_error":"RESOURCE_EXHAUSTED (code 429): Individual quota reached."}'
    assert is_quota_error("agy", 3, f"some output\n{line}\n", "")
    assert not is_quota_error("agy", 0, result, "")


def test_agy_generic_429_in_stderr_still_counts():
    assert is_quota_error("agy", 1, "", "request failed: 429 Too Many Requests")


def test_agy_quota_ignores_the_final_message_text():
    final = _jsonl(
        {"event": "result", "result": {"status": "DONE", "response": "fixed the 429 rate limit"}}
    )
    assert not is_quota_error("agy", 1, final, "")


@pytest.mark.parametrize(
    ("agent", "transcript", "stderr"),
    [
        (
            "claude",
            _jsonl(
                {
                    "type": "result",
                    "is_error": True,
                    "result": "Failed to authenticate. API Error: 401",
                }
            ),
            "",
        ),
        ("claude", "", "Please run /login"),
        ("codex", _jsonl({"type": "error", "message": "refresh token was already used"}), ""),
        ("codex", "", "ERROR: unexpected status 401 Unauthorized"),
        ("agy", "", 'AGY_ERROR: {"short_error":"invalid_grant"}'),
        (
            "agy",
            _jsonl({"event": "result", "result": {"status": "ERROR", "error": "not logged in"}}),
            "",
        ),
    ],
)
def test_is_auth_error_known_messages(agent, transcript, stderr):
    assert is_auth_error(agent, 1, transcript, stderr)
    assert not is_auth_error(agent, 0, transcript, stderr)


def test_is_auth_error_ignores_tool_output_and_final_text():
    tool = _jsonl(
        {"type": "user", "message": {"content": "grep: 401 Unauthorized, invalid_grant"}},
        {"type": "result", "is_error": False, "result": "handled the 401 case"},
    )
    assert not is_auth_error("claude", 1, tool, "")
    agy = _jsonl({"event": "step_update", "step_update": {"output": "invalid_grant 401"}})
    assert not is_auth_error("agy", 1, agy, "")
    assert not is_auth_error("codex", 1, _jsonl({"type": "item.completed", "text": "401"}), "")
