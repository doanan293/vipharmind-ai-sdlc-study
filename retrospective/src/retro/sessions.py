"""Statistics from the surviving Claude Code session logs.

Only counts leave this module: no message text, tool output, session ids or paths.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

_PROJECTS = Path.home() / ".claude" / "projects"
SESSION_DIRS = (
    _PROJECTS / "-home-andv-personal-vipharmind",
    _PROJECTS / "-home-andv-personal-vipharmind-camera-ready",
)
CUTOFF = date(2026, 11, 10)
_INTERRUPT = "[Request interrupted by user"
_INJECTED_FLAGS = ("isMeta", "isCompactSummary")
_INJECTED_PREFIXES = ("<command-", "<local-command")


@dataclass(frozen=True)
class SessionStats:
    session_no: int
    is_subagent: bool
    first_ts: date | None
    user_messages: int
    assistant_turns: int
    tool_calls: dict[str, int] = field(default_factory=dict)
    user_interrupts: int = 0


def _blocks(content) -> list[dict]:
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def _user_text(content) -> str | None:
    """Text of a human message, or None if the entry only carries tool results."""
    if isinstance(content, str):
        return content
    blocks = _blocks(content)
    texts = [b.get("text", "") for b in blocks if b.get("type") == "text"]
    if not texts:
        return None
    return "\n".join(t for t in texts if isinstance(t, str))


def session_stats(path: Path) -> SessionStats:
    first_ts: date | None = None
    user_messages = interrupts = 0
    anon_assistant = 0
    message_ids: set[str] = set()
    tools: Counter[str] = Counter()
    with path.open(errors="replace") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            if first_ts is None and isinstance(entry.get("timestamp"), str):
                try:
                    first_ts = datetime.fromisoformat(entry["timestamp"]).date()
                except ValueError:
                    pass
            message = entry.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if entry.get("type") == "user":
                if any(entry.get(flag) for flag in _INJECTED_FLAGS):
                    continue
                text = _user_text(content)
                if text is not None and not text.lstrip().startswith(_INJECTED_PREFIXES):
                    user_messages += 1
                    interrupts += _INTERRUPT in text
            elif entry.get("type") == "assistant":
                mid = message.get("id") if isinstance(message, dict) else None
                if isinstance(mid, str):
                    message_ids.add(mid)
                else:
                    anon_assistant += 1
                for b in _blocks(content):
                    if b.get("type") == "tool_use":
                        tools[str(b.get("name", "unknown"))] += 1
    return SessionStats(
        session_no=0,
        is_subagent="subagents" in path.parts,
        first_ts=first_ts,
        user_messages=user_messages,
        assistant_turns=len(message_ids) + anon_assistant,
        tool_calls=dict(tools),
        user_interrupts=interrupts,
    )


def collect_sessions(
    dirs: Sequence[Path] = SESSION_DIRS, cutoff: date = CUTOFF
) -> tuple[list[SessionStats], dict[str, int]]:
    dropped = {"after_cutoff": 0, "no_timestamp": 0}
    kept: list[tuple[str, SessionStats]] = []
    for d in dirs:
        if not d.is_dir():
            continue
        for path in sorted(d.rglob("*.jsonl")):
            s = session_stats(path)
            if s.first_ts is None:
                dropped["no_timestamp"] += 1
            elif s.first_ts > cutoff:
                dropped["after_cutoff"] += 1
            else:
                kept.append((str(path), s))
    kept.sort(key=lambda item: (item[1].first_ts, item[0]))
    stats = [
        SessionStats(
            session_no=i,
            is_subagent=s.is_subagent,
            first_ts=s.first_ts,
            user_messages=s.user_messages,
            assistant_turns=s.assistant_turns,
            tool_calls=s.tool_calls,
            user_interrupts=s.user_interrupts,
        )
        for i, (_, s) in enumerate(kept, start=1)
    ]
    return stats, dropped


def session_rows(stats: list[SessionStats]) -> list[dict]:
    return [
        {
            "session_no": s.session_no,
            "is_subagent": s.is_subagent,
            "first_ts": s.first_ts.isoformat() if s.first_ts else "",
            "user_messages": s.user_messages,
            "assistant_turns": s.assistant_turns,
            "tool_calls": sum(s.tool_calls.values()),
            "user_interrupts": s.user_interrupts,
        }
        for s in stats
    ]


def tool_rows(stats: list[SessionStats]) -> list[dict]:
    total: Counter[str] = Counter()
    for s in stats:
        total.update(s.tool_calls)
    return [{"tool": t, "calls": n} for t, n in sorted(total.items(), key=lambda x: (-x[1], x[0]))]
