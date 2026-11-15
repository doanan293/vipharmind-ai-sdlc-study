"""Token counts by billing type, and the shell commands an agent ran, from transcript.jsonl.

Four billed types (prereg-v1 section 6): uncached input, cache write, cache read, output.
Cache writes are split by retention (5 min / 1 h) where Claude Code reports it. Reasoning
tokens are part of `output` for every tool (that is how each provider bills them); `reasoning`
is kept only for description.
"""

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ModelTokens:
    model: str | None
    input_uncached: int
    cache_read: int
    cache_write_5m: int
    cache_write_1h: int
    output: int
    reasoning: int | None
    split: bool  # False: the tool gave only a total input count (priced as plain input)
    source: str  # where the counts came from: result | messages | steps | turns | meta

    @classmethod
    def unsplit(cls, model: str | None, total_input: int, output: int) -> "ModelTokens":
        return cls(model, total_input, 0, 0, 0, output, None, False, "meta")

    @property
    def total_input(self) -> int:
        return self.input_uncached + self.cache_read + self.cache_write_5m + self.cache_write_1h

    @property
    def total(self) -> int:
        return self.total_input + self.output


def events(transcript: str) -> list[dict]:
    out = []
    for line in transcript.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict):
            out.append(e)
    return out


def _i(d: dict, key: str) -> int:
    v = d.get(key)
    return v if isinstance(v, int) else 0


def _claude_write_split(total: int, five: int | None, hour: int | None) -> tuple[int, int]:
    """(5m, 1h) cache-write tokens. Without a split, all writes are priced at the 1 h rate
    (Claude Code writes 1 h cache entries; this is the upper bound)."""
    if five is None and hour is None:
        return 0, total
    return five or 0, hour or 0


def _claude(evs: list[dict]) -> list[ModelTokens]:
    result = next((e for e in reversed(evs) if e.get("type") == "result"), None)
    if result is not None and isinstance(result.get("modelUsage"), dict) and result["modelUsage"]:
        out = []
        for model, u in result["modelUsage"].items():
            five, hour = _claude_write_split(
                _i(u, "cacheCreationInputTokens"),
                u.get("cacheCreationEphemeral5mInputTokens"),
                u.get("cacheCreationEphemeral1hInputTokens"),
            )
            thinking = u.get("thinkingTokens")
            out.append(
                ModelTokens(
                    model,
                    _i(u, "inputTokens"),
                    _i(u, "cacheReadInputTokens"),
                    five,
                    hour,
                    _i(u, "outputTokens"),
                    thinking if isinstance(thinking, int) else None,
                    True,
                    "result",
                )
            )
        return out
    if result is not None and isinstance(result.get("usage"), dict):
        u = result["usage"]
        cc = u.get("cache_creation") or {}
        five, hour = _claude_write_split(
            _i(u, "cache_creation_input_tokens"),
            cc.get("ephemeral_5m_input_tokens"),
            cc.get("ephemeral_1h_input_tokens"),
        )
        model = next(
            (e["model"] for e in evs if e.get("type") == "system" and e.get("model")), None
        )
        thinking = (u.get("output_tokens_details") or {}).get("thinking_tokens")
        return [
            ModelTokens(
                model,
                _i(u, "input_tokens"),
                _i(u, "cache_read_input_tokens"),
                five,
                hour,
                _i(u, "output_tokens"),
                thinking if isinstance(thinking, int) else None,
                True,
                "result",
            )
        ]
    # no result event (the run was stopped): sum the assistant messages, each message id once
    per_msg: dict[str, tuple[str | None, dict]] = {}
    for e in evs:
        msg = e.get("message")
        if e.get("type") == "assistant" and isinstance(msg, dict) and isinstance(
            msg.get("usage"), dict
        ):
            per_msg[str(msg.get("id"))] = (msg.get("model"), msg["usage"])
    by_model: dict[str | None, list[int]] = {}
    for model, u in per_msg.values():
        cc = u.get("cache_creation") or {}
        five, hour = _claude_write_split(
            _i(u, "cache_creation_input_tokens"),
            cc.get("ephemeral_5m_input_tokens"),
            cc.get("ephemeral_1h_input_tokens"),
        )
        acc = by_model.setdefault(model, [0, 0, 0, 0, 0])
        for k, v in enumerate(
            (_i(u, "input_tokens"), _i(u, "cache_read_input_tokens"), five, hour,
             _i(u, "output_tokens"))
        ):
            acc[k] += v
    return [ModelTokens(m, *acc, None, True, "messages") for m, acc in by_model.items()]


def _agy(evs: list[dict]) -> list[ModelTokens]:
    model = next(
        (e["init"].get("model") for e in evs if e.get("event") == "init" and e.get("init")), None
    )
    result = next((e for e in reversed(evs) if e.get("event") == "result"), None)
    usage = ((result or {}).get("result") or {}).get("usage") if result else None
    if isinstance(usage, dict):
        thinking = usage.get("thinking_tokens")
        return [
            ModelTokens(
                model,
                _i(usage, "input_tokens"),
                _i(usage, "cache_read_tokens"),
                0,
                0,
                _i(usage, "output_tokens"),
                thinking if isinstance(thinking, int) else None,
                True,
                "result",
            )
        ]
    steps = [
        s["usage"]
        for e in evs
        if e.get("event") == "step_update"
        and (s := e.get("step_update") or {}).get("step_type") == "agent_response"
        and s.get("state") == "DONE"
        and isinstance(s.get("usage"), dict)
    ]
    if not steps:
        return []
    return [
        ModelTokens(
            model,
            sum(_i(u, "input_tokens") for u in steps),
            sum(_i(u, "cache_read_tokens") for u in steps),
            0,
            0,
            sum(_i(u, "output_tokens") for u in steps),
            sum(_i(u, "thinking_tokens") for u in steps),
            True,
            "steps",
        )
    ]


def _codex(evs: list[dict]) -> list[ModelTokens]:
    """OpenAI semantics: input_tokens includes cached_input_tokens; output includes reasoning."""
    done = [e.get("usage") or {} for e in evs if e.get("type") == "turn.completed"]
    if not done:
        return []
    inp = sum(_i(u, "input_tokens") for u in done)
    cached = sum(_i(u, "cached_input_tokens") for u in done)
    reasoning = [u["reasoning_output_tokens"] for u in done
                 if isinstance(u.get("reasoning_output_tokens"), int)]
    model = next((e["model"] for e in evs if isinstance(e.get("model"), str)), None)
    return [
        ModelTokens(
            model,
            inp - cached,
            cached,
            0,
            0,
            sum(_i(u, "output_tokens") for u in done),
            sum(reasoning) if reasoning else None,
            True,
            "turns",
        )
    ]


def parse_tokens(agent: str, transcript: str) -> list[ModelTokens]:
    """Token counts per model; [] when the transcript has none."""
    evs = events(transcript)
    if agent == "claude":
        return _claude(evs)
    if agent == "agy":
        return _agy(evs)
    if agent == "codex":
        return _codex(evs)
    raise ValueError(f"unknown agent {agent!r}")


def commands(agent: str, transcript: str) -> list[str]:
    """Shell command lines the agent ran (tool calls only, never tool output)."""
    out: list[str] = []
    for e in events(transcript):
        if agent == "claude" and e.get("type") == "assistant":
            content = (e.get("message") or {}).get("content")
            for block in content if isinstance(content, list) else []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    cmd = (block.get("input") or {}).get("command")
                    if isinstance(cmd, str):
                        out.append(cmd)
        elif agent == "codex" and e.get("type") == "item.completed":
            item = e.get("item") or {}
            if item.get("type") == "command_execution" and isinstance(item.get("command"), str):
                out.append(item["command"])
        elif agent == "agy" and e.get("event") == "step_update":
            s = e.get("step_update") or {}
            if s.get("step_type") == "tool" and s.get("state") == "DONE":
                cmd = ((s.get("tool_info") or {}).get("parameters") or {}).get("CommandLine")
                if isinstance(cmd, str):
                    out.append(cmd)
    return out


PYTEST_RE = re.compile(r"\bpytest\b")


def pytest_ran(agent: str, transcript: str) -> bool:
    return any(PYTEST_RE.search(c) for c in commands(agent, transcript))
