"""Agent CLIs: command lines, token usage from transcripts, and quota-error detection."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

AGENTS = ("claude", "agy", "codex")

# Stock agents (ruling R11, owner 2026-11-15): each CLI runs its default agent with its default
# tools, web included; only user-level extras are removed (skills, plugins, MCP, memory, custom
# instructions) by the clean HOME (workspace.prepare_config) and the flags below. Any run whose
# transcript reaches the upstream ViPharmind repo is flagged (upstream_urls) for a sensitivity check.
UPSTREAM_RE = re.compile(
    r"(?:https?://|git@)[^\s\"'<>]*(?:vipharmind|doanan293)[^\s\"'<>]*", re.IGNORECASE
)
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
        # "5-hour limit reached", "weekly limit reached"; not e.g. "Subagent nesting limit reached"
        r"\b(?:\d+[- ]?(?:hour|day)|weekly|daily|monthly|session|opus|sonnet|extra usage)\s+limit reached",
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
            "--model",
            model,
            "--effort",
            effort,
            "--output-format",
            "stream-json",
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
            f"-p={prompt_file.read_text()}",
        ]
    if agent == "codex":
        # like claude's bypassPermissions and agy's --dangerously-skip-permissions: no approvals, no sandbox
        return [
            "codex",
            "exec",
            "--strict-config",
            "-m",
            model,
            "-c",
            f'model_reasoning_effort="{effort}"',
            "--dangerously-bypass-approvals-and-sandbox",
            "--json",
            "-",
        ]
    raise ValueError(f"unknown agent {agent!r}, expected one of {AGENTS}")


def urls_in(text: str) -> set[str]:
    return {m.group(0).rstrip(".,);]}\\") for m in UPSTREAM_RE.finditer(text)}


def upstream_urls(transcript: str, exclude: set[str] | frozenset[str] = frozenset()) -> list[str]:
    """Distinct URLs in a transcript that point at the upstream ViPharmind repo or its owner,
    minus `exclude` (URLs already in the task tree)."""
    return sorted(urls_in(transcript) - set(exclude))


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


def _agy_own_errors(transcript: str) -> str:
    """agy's own error text in a transcript: AGY_ERROR lines and the final result/error event,
    never tool output (which can hold code that says "429" or "rate limit")."""
    parts = [ln for ln in transcript.splitlines() if ln.startswith("AGY_ERROR:")]
    for e in _events(transcript):
        if e.get("event") in ("result", "error"):
            r = e.get("result") if e.get("event") == "result" else e
            if isinstance(r, dict):  # error/status fields only, not the agent's final message
                parts.extend(str(r[k]) for k in ("error", "status") if r.get(k))
    return "\n".join(parts)


def is_quota_error(agent: str, returncode: int, transcript: str, stderr: str = "") -> bool:
    """A failed run whose output reports an exhausted quota or usage limit.

    claude and codex: the tail of transcript + stderr. agy: only stderr and agy's own error
    lines/events, so code the agent read cannot look like a quota error.
    """
    if returncode == 0:
        return False
    if agent == "agy":
        tail = (stderr + "\n" + _agy_own_errors(transcript))[-QUOTA_TAIL_CHARS:]
    else:
        tail = f"{transcript}\n{stderr}"[-QUOTA_TAIL_CHARS:]
    return any(re.search(p, tail, re.IGNORECASE) for p in QUOTA_PATTERNS[agent])


AUTH_PATTERNS = (
    r"\b401\b",
    r"invalid_grant",
    r"refresh[ _]token[^\n]{0,60}(?:already|expired|revoked|invalid|reused|used)",
    r"failed to authenticate",
    r"authentication[_ ](?:error|failed)",
    r"not logged in",
    r"please (?:log ?in|run /login|sign in)",
    r"invalid (?:api key|credentials|authentication)",
    r"unauthenticated",
)


def _own_error_text(agent: str, transcript: str, stderr: str) -> str:
    """stderr plus the agent's own error/result fields; never tool output or the final message
    of a successful-looking turn."""
    if agent == "agy":
        return stderr + "\n" + _agy_own_errors(transcript)
    parts = [stderr]
    for e in _events(transcript):
        kind = e.get("type")
        if agent == "claude" and kind == "result" and e.get("is_error"):
            parts.append(str(e.get("result", "")))
        if kind in ("error", "turn.failed"):
            parts.append(json.dumps(e.get("error") or e.get("message") or ""))
    return "\n".join(parts)


def is_auth_error(agent: str, returncode: int, transcript: str, stderr: str = "") -> bool:
    """A failed run whose own error output says the login was rejected (expired, revoked or
    already-rotated token); matched like agy's quota errors, never on tool output."""
    if returncode == 0:
        return False
    text = _own_error_text(agent, transcript, stderr)[-QUOTA_TAIL_CHARS:]
    return any(re.search(p, text, re.IGNORECASE) for p in AUTH_PATTERNS)
