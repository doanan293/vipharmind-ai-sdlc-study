"""Stand-in for an agent CLI in tests; the runner uses it when SDLC_FAKE_AGENT points here.

It ignores the real CLI flags it receives and acts on environment variables:
  FAKE_AGENT_MODE    ok (default) | quota_once | sleep
  FAKE_AGENT_STATE   marker file: quota_once fails while it is absent, then creates it
  FAKE_AGENT_WRITE   JSON {relative path: content} written into the work tree (cwd)
  FAKE_AGENT_PIDFILE sleep mode: where to record the pid of a child that also sleeps
  FAKE_AGENT_CWDLOG  file to append the agent's working directory to
  FAKE_AGENT_DELAY   seconds to sleep before finishing (ok mode)
  FAKE_AGENT_TIMELOG file to append "<start> <end>" to (CLOCK_MONOTONIC, system-wide on Linux)
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def emit(event: dict) -> None:
    print(json.dumps(event), flush=True)


def main() -> int:
    if "--version" in sys.argv:
        print("fake-agent 0.0.1")
        return 0
    started = time.monotonic()
    sys.stdin.read()
    if os.environ.get("FAKE_AGENT_CWDLOG"):
        with open(os.environ["FAKE_AGENT_CWDLOG"], "a") as f:
            f.write(os.getcwd() + "\n")
    mode = os.environ.get("FAKE_AGENT_MODE", "ok")
    emit({"type": "system", "subtype": "init", "model": "fake-model-served"})
    if mode == "quota_once":
        state = Path(os.environ["FAKE_AGENT_STATE"])
        if not state.exists():
            state.write_text("failed once\n")
            emit({"type": "result", "is_error": True, "result": "You've hit your usage limit"})
            return 1
    if mode == "sleep":
        child = subprocess.Popen(["sleep", "300"])
        Path(os.environ["FAKE_AGENT_PIDFILE"]).write_text(str(child.pid))
    for rel, content in json.loads(os.environ.get("FAKE_AGENT_WRITE", "{}")).items():
        target = Path(rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    if mode == "sleep":
        time.sleep(300)
    time.sleep(float(os.environ.get("FAKE_AGENT_DELAY", "0")))
    if os.environ.get("FAKE_AGENT_TIMELOG"):
        with open(os.environ["FAKE_AGENT_TIMELOG"], "a") as f:
            f.write(f"{started} {time.monotonic()}\n")
    emit(
        {
            "type": "result",
            "is_error": False,
            "num_turns": 3,
            "usage": {
                "input_tokens": 10,
                "cache_creation_input_tokens": 20,
                "cache_read_input_tokens": 100,
                "output_tokens": 7,
            },
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
