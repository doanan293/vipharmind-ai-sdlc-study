"""Agent CLIs: command lines, token usage from transcripts, and quota-error detection."""

import json
import re
from dataclasses import dataclass
from pathlib import Path

AGENTS = ("claude", "agy", "codex")

# Placeholders finalised in Task 9, once the real CLIs have been probed on this machine.
# Flags that switch off web access for agy and codex (claude uses --disallowedTools).
AGY_WEB_OFF_FLAGS: tuple[str, ...] = ()
CODEX_WEB_OFF_FLAGS: tuple[str, ...] = ()
# Messages that mean "out of quota / usage limit", matched case-insensitively against the
# tail of the transcript and stderr of a run that exited non-zero. Provisional: confirm
# against real error output in Task 9.
QUOTA_PATTERNS: dict[str, tuple[str, ...]] = {
    "claude": (
        r"usage limit",
        r"hit your (?:\w+ )?limit",
        r"\blimit reached\b",
        r"out of extra usage",
    ),
    "agy": (
        r"RESOURCE_EXHAUSTED",
        r"quota (?:exceeded|exhausted)",
        r"usage limit",
        r"hit your (?:\w+ )?limit",
    ),
    "codex": (
        r"usage limit",
        r"hit your (?:\w+ )?limit",
        r"insufficient_quota",
        r"quota exceeded",
    ),
}
QUOTA_TAIL_CHARS = 4000  # only the end of the output: the code an agent read may say "quota"


@dataclass(frozen=True)
class Usage:
    input_tokens: int | None  # includes cache reads and cache writes where reported
    output_tokens: int | None
    turns: int | None
    model_served: str | None


def build_command(agent: str, model: str, effort: str, prompt_file: Path) -> list[str]:
    """The agent's command line; the prompt (prompt_file) is fed on stdin by the runner."""
    del prompt_file  # every CLI reads the prompt from stdin; kept for the interface
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
        ]
    if agent == "agy":
        return [
            "agy",
            "-p",
            "--model",
            model,
            "--effort",
            effort,
            "--output-format",
            "stream-json",
            "--dangerously-skip-permissions",
            "--disable-slash-commands",
            *AGY_WEB_OFF_FLAGS,
        ]
    if agent == "codex":
        # the proxy is selected by the profile in CODEX_HOME (prepare_config)
        return [
            "codex",
            "exec",
            "-m",
            model,
            "-c",
            f'model_reasoning_effort="{effort}"',
            "--sandbox",
            "workspace-write",
            "--json",
            *CODEX_WEB_OFF_FLAGS,
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
    """claude and agy stream-json: init event names the model, the result event sums usage."""
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
    return Usage(
        sum(inputs) if inputs else None,
        out if isinstance(out, int) else None,
        turns if isinstance(turns, int) else None,
        model,
    )


def _codex_usage(events: list[dict]) -> Usage:
    """codex exec --json: one turn.completed per turn, each with that turn's usage."""
    done = [e for e in events if e.get("type") == "turn.completed"]
    model = next((e["model"] for e in events if isinstance(e.get("model"), str)), None)
    if not done:
        return Usage(None, None, None, model)
    usages = [e.get("usage") or {} for e in done]
    inp = [u["input_tokens"] for u in usages if isinstance(u.get("input_tokens"), int)]
    out = [u["output_tokens"] for u in usages if isinstance(u.get("output_tokens"), int)]
    return Usage(sum(inp) if inp else None, sum(out) if out else None, len(done), model)


def parse_usage(agent: str, transcript: str) -> Usage:
    events = _events(transcript)
    if agent == "codex":
        return _codex_usage(events)
    if agent in ("claude", "agy"):
        return _claude_usage(events)
    raise ValueError(f"unknown agent {agent!r}, expected one of {AGENTS}")


def is_quota_error(agent: str, returncode: int, transcript: str) -> bool:
    """A failed run whose last output reports an exhausted quota or usage limit."""
    if returncode == 0:
        return False
    tail = transcript[-QUOTA_TAIL_CHARS:]
    return any(re.search(p, tail, re.IGNORECASE) for p in QUOTA_PATTERNS[agent])
