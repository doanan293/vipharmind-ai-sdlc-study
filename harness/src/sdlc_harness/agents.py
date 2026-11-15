"""Agent CLIs: command lines, token usage from transcripts, and quota-error detection."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

AGENTS = ("claude", "agy", "codex")

# Web access (pilot probes, docs/pilot-report.md). claude: --disallowedTools WebFetch WebSearch.
# agy: its stock agent always has search_web and a browser subagent, and search_web is not a
# permission action, so agy runs a custom main agent (AGY_AGENT, written by prepare_config) whose
# tool list has no web tools; the deny rules are a second guard. codex: web_search disabled here
# and in the CODEX_HOME config. Shell network stays on for all three (agy cannot sandbox it).
AGY_AGENT = "sdlc-coder"
AGY_TOOLS = ("read_file", "edit_file", "write_file", "run_command", "manage_task")
AGY_DENY = ("read_url(*)", "execute_url(*)", "download_url(*)", "mcp(*)")
CODEX_WEB_OFF_FLAGS: tuple[str, ...] = ("-c", 'web_search="disabled"')
CLAUDE_SETTINGS = '{"autoMemoryEnabled": false}'
# Messages that mean "out of quota / usage limit / rate limited", matched case-insensitively
# against the tail of the transcript and stderr of a run that exited non-zero. Taken from the
# CLIs' own strings (claude 2.1.325, agy 1.5.9 incl. its QUOTA_RE, codex 0.162.1). Only agy's
# was seen in a real run (pilot, marked below); the others stay provisional.
QUOTA_PATTERNS: dict[str, tuple[str, ...]] = {
    "claude": (
        r"usage limit reached",
        r"hit your (?:\w+ )?limit",
        r"spend limit reached",
        r"out of extra usage",
        r"rate_limit_error",
    ),
    "agy": (
        r"RESOURCE_EXHAUSTED",  # observed: "RESOURCE_EXHAUSTED (code 429): Individual quota reached"
        r"quota reached",
        r"out of quota",
        r"quota (?:exceeded|exhausted)",
        r"exhausted your capacity",
        r"\b429\b",
        r"rate.?limit",
    ),
    "codex": (
        r"usage limit",
        r"usage_limit_reached",
        r"hit your (?:\w+ )?limit",
        r"insufficient_quota",
        r"quota exceeded",
        r"last status: 429",
    ),
}
QUOTA_TAIL_CHARS = 4000  # only the end of the output: the code an agent read may say "quota"


@dataclass(frozen=True)
class Usage:
    input_tokens: int | None  # includes cache reads and cache writes where reported
    output_tokens: int | None
    turns: int | None
    model_served: str | None
    reasoning_tokens: int | None = None  # thinking/reasoning tokens where reported separately


def build_command(agent: str, model: str, effort: str, prompt_file: Path) -> list[str]:
    """The agent's command line. claude and codex read the prompt on stdin (the runner feeds
    prompt_file); agy ignores stdin, so its prompt is the value of -p, as the last argument."""
    if agent == "claude":
        return [
            "claude",
            "-p",
            "--model",
            model,
            "--effort",
            effort,
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
            CLAUDE_SETTINGS,
        ]
    if agent == "agy":
        return [
            "agy",
            "--agent",
            AGY_AGENT,
            "--model",
            model,
            "--effort",
            effort,
            "--output-format",
            "stream-json",
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
            "--settings",
            json.dumps({"permissions": {"deny": list(AGY_DENY)}}),
            f"-p={prompt_file.read_text()}",
        ]
    if agent == "codex":
        # the proxy is selected by config.toml in CODEX_HOME (prepare_config); like claude's
        # bypassPermissions and agy's --dangerously-skip-permissions: no approvals, no sandbox
        return [
            "codex",
            "exec",
            "--strict-config",
            "-m",
            model,
            "-c",
            f'model_reasoning_effort="{effort}"',
            *CODEX_WEB_OFF_FLAGS,
            "--dangerously-bypass-approvals-and-sandbox",
            "--json",
            "-",
        ]
    raise ValueError(f"unknown agent {agent!r}, expected one of {AGENTS}")


def _events(transcript: str) -> list[dict]:
    events = []
    for line in transcript.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def _claude_usage(events: list[dict]) -> Usage:
    """claude stream-json: init event names the model, the result event sums usage."""
    model = None
    for e in events:
        if e.get("type") == "system" and e.get("model"):
            model = model or e["model"]
        msg = e.get("message")
        if e.get("type") == "assistant" and isinstance(msg, dict) and msg.get("model"):
            model = msg["model"]
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    if result is None:
        return Usage(None, None, None, model)
    usage = result.get("usage") or {}
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    inputs = [usage[k] for k in keys if isinstance(usage.get(k), int)]
    out = usage.get("output_tokens")
    turns = result.get("num_turns")
    thinking = (usage.get("output_tokens_details") or {}).get("thinking_tokens")
    return Usage(
        sum(inputs) if inputs else None,
        out if isinstance(out, int) else None,
        turns if isinstance(turns, int) else None,
        model,
        thinking if isinstance(thinking, int) else None,
    )


def _int(d: dict, key: str) -> int | None:
    v = d.get(key)
    return v if isinstance(v, int) else None


def _agy_usage(events: list[dict]) -> Usage:
    """agy stream-json: {"event": init|step_update|result}; the result sums every model call.

    input = input_tokens + cache_read_tokens (agy reports them apart); turns = model calls
    (finished agent_response steps), since agy's num_turns counts user turns (always 1 here).
    """
    model = next(
        (e["init"].get("model") for e in events if e.get("event") == "init" and e.get("init")),
        None,
    )
    calls = sum(
        1
        for e in events
        if e.get("event") == "step_update"
        and (s := e.get("step_update") or {}).get("step_type") == "agent_response"
        and s.get("state") == "DONE"
    )
    result = next((e for e in reversed(events) if e.get("event") == "result"), None)
    if result is None:
        return Usage(None, None, calls or None, model)
    usage = (result.get("result") or {}).get("usage") or {}
    inputs = [v for k in ("input_tokens", "cache_read_tokens") if (v := _int(usage, k)) is not None]
    return Usage(
        sum(inputs) if inputs else None,
        _int(usage, "output_tokens"),
        calls,
        model,
        _int(usage, "thinking_tokens"),
    )


def _codex_usage(events: list[dict]) -> Usage:
    """codex exec --json: one turn.completed per turn, each with that turn's usage.

    input_tokens already includes cached_input_tokens and output_tokens includes
    reasoning_output_tokens (OpenAI usage semantics). No event names the served model.
    """
    done = [e for e in events if e.get("type") == "turn.completed"]
    model = next((e["model"] for e in events if isinstance(e.get("model"), str)), None)
    if not done:
        return Usage(None, None, None, model)
    usages = [e.get("usage") or {} for e in done]
    inp = [u["input_tokens"] for u in usages if isinstance(u.get("input_tokens"), int)]
    out = [u["output_tokens"] for u in usages if isinstance(u.get("output_tokens"), int)]
    rea = [r for u in usages if (r := _int(u, "reasoning_output_tokens")) is not None]
    return Usage(
        sum(inp) if inp else None,
        sum(out) if out else None,
        len(done),
        model,
        sum(rea) if rea else None,
    )


def parse_usage(agent: str, transcript: str) -> Usage:
    events = _events(transcript)
    if agent == "codex":
        return _codex_usage(events)
    if agent == "agy":
        return _agy_usage(events)
    if agent == "claude":
        return _claude_usage(events)
    raise ValueError(f"unknown agent {agent!r}, expected one of {AGENTS}")


def is_quota_error(agent: str, returncode: int, transcript: str) -> bool:
    """A failed run whose last output reports an exhausted quota or usage limit."""
    if returncode == 0:
        return False
    tail = transcript[-QUOTA_TAIL_CHARS:]
    return any(re.search(p, tail, re.IGNORECASE) for p in QUOTA_PATTERNS[agent])
