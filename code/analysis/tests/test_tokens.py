import json

import pytest

from sdlc_analysis.prices import PRICES, cost_usd, is_off_table, table_model
from sdlc_analysis.tokens import ModelTokens, commands, parse_tokens, pytest_ran


def jl(*events):
    return "\n".join(json.dumps(e) for e in events) + "\n"


CLAUDE_RESULT = {
    "type": "result",
    "usage": {
        "input_tokens": 22,
        "cache_creation_input_tokens": 24333,
        "cache_read_input_tokens": 319558,
        "output_tokens": 9836,
        "cache_creation": {"ephemeral_1h_input_tokens": 24333, "ephemeral_5m_input_tokens": 0},
    },
    "modelUsage": {
        "claude-sonnet-5-5": {
            "inputTokens": 22,
            "outputTokens": 9836,
            "cacheReadInputTokens": 319558,
            "cacheCreationInputTokens": 24333,
            "thinkingTokens": 1096,
            "cacheCreationEphemeral5mInputTokens": 0,
            "cacheCreationEphemeral1hInputTokens": 24333,
            "costUSD": 0.2276918,
        }
    },
}


def test_claude_split_from_model_usage_matches_reported_list_cost():
    toks = parse_tokens("claude", jl({"type": "system", "model": "claude-sonnet-5-5"}, CLAUDE_RESULT))
    assert toks == [
        ModelTokens(
            model="claude-sonnet-5-5",
            input_uncached=22,
            cache_read=319558,
            cache_write_5m=0,
            cache_write_1h=24333,
            output=9836,
            reasoning=1096,
            split=True,
            source="result",
        )
    ]
    # the pilot transcript's own costUSD (list prices) equals our table for this run
    assert cost_usd(toks, "claude-sonnet-5-5") == pytest.approx(0.2276918)


def test_claude_without_result_sums_assistant_messages_once_per_message_id():
    def msg(mid, out):
        usage = {
            "input_tokens": 2,
            "cache_creation_input_tokens": 100,
            "cache_read_input_tokens": 1000,
            "output_tokens": out,
            "cache_creation": {"ephemeral_5m_input_tokens": 40, "ephemeral_1h_input_tokens": 60},
        }
        return {"type": "assistant", "message": {"id": mid, "model": "claude-opus-5-5", "usage": usage}}

    # a message streamed twice (two content blocks) carries the same usage: count it once
    toks = parse_tokens("claude", jl(msg("a", 5), msg("a", 5), msg("b", 7)))
    assert toks == [
        ModelTokens("claude-opus-5-5", 4, 2000, 80, 120, 12, None, True, "messages")
    ]


def test_agy_result_adds_cache_reads_and_keeps_thinking_inside_output():
    result = {
        "event": "result",
        "result": {
            "usage": {
                "input_tokens": 426354,
                "output_tokens": 102429,
                "thinking_tokens": 89910,
                "cache_read_tokens": 5645791,
            }
        },
    }
    init = {"event": "init", "init": {"model": "gemini-3.8-flash-medium"}}
    toks = parse_tokens("agy", jl(init, result))
    assert toks == [
        ModelTokens("gemini-3.8-flash-medium", 426354, 5645791, 0, 0, 102429, 89910, True, "result")
    ]
    expected = (426354 * 0.75 + 5645791 * 0.075 + 102429 * 3.75) / 1e6
    assert cost_usd(toks, "gemini-3.8-flash-medium") == pytest.approx(expected)


def test_agy_without_result_sums_finished_response_steps():
    def step(i, inp, out):
        return {
            "event": "step_update",
            "step_update": {
                "step_index": i,
                "state": "DONE",
                "step_type": "agent_response",
                "usage": {"input_tokens": inp, "output_tokens": out, "cache_read_tokens": 10},
            },
        }

    active = {"event": "step_update", "step_update": {"state": "ACTIVE", "step_type": "agent_response",
                                                       "usage": {"input_tokens": 999}}}
    toks = parse_tokens("agy", jl(step(1, 100, 5), active, step(2, 200, 6)))
    assert toks[0].input_uncached == 300 and toks[0].cache_read == 20 and toks[0].output == 11
    assert toks[0].source == "steps"


def test_codex_input_includes_cached_and_is_split():
    done = {
        "type": "turn.completed",
        "usage": {
            "input_tokens": 428199,
            "cached_input_tokens": 380672,
            "cache_write_input_tokens": 0,
            "output_tokens": 6434,
            "reasoning_output_tokens": 890,
        },
    }
    toks = parse_tokens("codex", jl({"type": "turn.started"}, done))
    assert toks == [ModelTokens(None, 428199 - 380672, 380672, 0, 0, 6434, 890, True, "turns")]
    base = ((428199 - 380672) * 0.10 + 380672 * 0.01 + 6434 * 0.50) / 1e6
    assert cost_usd(toks, "gpt-6-luna") == pytest.approx(base)
    long = ((428199 - 380672) * 0.20 + 380672 * 0.02 + 6434 * 0.75) / 1e6
    assert cost_usd(toks, "gpt-6-luna", long_context=True) == pytest.approx(long)


def test_unsplit_tokens_are_priced_as_plain_input_upper_bound():
    toks = [ModelTokens.unsplit("claude-opus-5-5", total_input=1_000_000, output=1_000_000)]
    assert cost_usd(toks, "claude-opus-5-5") == pytest.approx(4.0 + 20.0)


def test_unknown_model_tokens_use_the_cohort_model_price_and_are_flagged():
    toks = [ModelTokens("claude-haiku-9", 1_000_000, 0, 0, 0, 0, None, True, "result")]
    assert cost_usd(toks, "claude-sonnet-5-5") == pytest.approx(2.0)
    assert is_off_table("claude-haiku-9") and not is_off_table(None)


def test_suffixed_model_ids_match_their_table_row_by_prefix():
    # a Sonnet sub-agent inside an Opus run is priced as Sonnet, not as Opus
    toks = [ModelTokens("claude-sonnet-5-5-20261101", 1_000_000, 0, 0, 0, 0, None, True, "result")]
    assert cost_usd(toks, "claude-opus-5-5") == pytest.approx(2.0)
    assert table_model("claude-opus-5-5[1m]") == "claude-opus-5-5"
    assert not is_off_table("claude-opus-5-5[1m]")
    assert table_model("gpt-6-luna-2026") == "gpt-6-luna"  # never the >272k row
    assert table_model("claude-opus-5-5@20261101") == "claude-opus-5-5"
    # a different model whose id extends a table id is off-table, not that row
    assert table_model("gpt-6-luna-mini") is None and is_off_table("gpt-6-luna-mini")
    assert table_model("") is None and not is_off_table("")


def test_no_tokens_means_unknown_cost():
    assert parse_tokens("codex", "") == []
    assert cost_usd([], "gpt-6-luna") is None


def test_price_table_is_the_frozen_prereg_table():
    assert PRICES["claude-sonnet-5-5"].input == 2.00
    assert PRICES["claude-sonnet-5-5"].cache_write_1h == 4.00
    assert PRICES["claude-opus-5-5"].cache_write_5m == 5.00
    assert PRICES["gemini-3.8-flash-medium"].output == 3.75
    assert PRICES["gpt-6-luna"].cache_read == 0.01
    assert PRICES["gpt-6-luna>272k"].output == 0.75


def test_commands_and_pytest_detection_per_agent():
    claude = jl(
        {"type": "assistant", "message": {"id": "m", "content": [
            {"type": "tool_use", "name": "Bash", "input": {"command": "cd backend && uv run pytest -q"}},
            {"type": "text", "text": "pytest"},
        ]}},
        # tool output that mentions pytest is not a command
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "pytest ok"}]}},
    )
    assert commands("claude", claude) == ["cd backend && uv run pytest -q"]
    assert pytest_ran("claude", claude) is True
    codex = jl({"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}})
    assert pytest_ran("codex", codex) is False
    agy = jl({"event": "step_update", "step_update": {"state": "DONE", "step_type": "tool",
              "tool_info": {"parameters": {"CommandLine": "python -m pytest tests"}}}})
    assert pytest_ran("agy", agy) is True
