"""Checklist judge (prereg-v1.2, E2): a fixed agent (Claude Fable 5.2) scores a finished unit against data/tasks/<id>/checklist.md.

The unit's saved patch.diff is applied to a fresh export of the task's start tree, docs/design.md and
docs/plan.md are deleted (partial arm blinding), and the judge agent runs in a directory named by a
random id, with code/prompts/judge.md + the checklist on stdin. It writes <unit>/judge.json.
"""

import hashlib
import json
import logging
import re
import shutil
import subprocess
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from sdlc_harness.agents import build_command, is_auth_error, is_quota_error, parse_usage
from sdlc_harness.grade import ARTIFACT_PATHS
from sdlc_harness.prompting import PROMPTS_DIR
from sdlc_harness.runner import (
    Cohort,
    RunConfig,
    _agent_env,
    _agent_prefix,
    _dispose,
    _kill_group,
    _patched_workspace,
)
from sdlc_harness.tasks import load_task
from sdlc_harness.workspace import Agent, write_back_credentials

log = logging.getLogger(__name__)

# Claude Fable 5.2: not one of the tested agents; high effort for careful checking.
JUDGE = Cohort("judge", "claude", "claude-fable-5-2", "high", (1,))
JUDGE_FILE = "judge.json"
VERDICTS = ("met", "not_met", "unclear")
_ITEM = re.compile(r"^\s*(\d+)\.\s+\S", re.MULTILINE)
EXACT_TAG = (
    " [exact]"  # item needs a literal the brief and start code do not determine (sensitivity)
)


def checklist_items(text: str) -> int:
    """Number of `N. ` items in a checklist."""
    return len(_ITEM.findall(text))


def exact_items(text: str) -> list[int]:
    """Numbers of the items tagged [exact]."""
    return [
        int(m.group(1))
        for line in text.splitlines()
        if (m := _ITEM.match(line)) and line.rstrip().endswith(EXACT_TAG.strip())
    ]


def judge_prompt(checklist: str, prompts_dir: Path = PROMPTS_DIR) -> str:
    """code/prompts/judge.md + the checklist without its [exact] tags (the judge never sees them)."""
    shown = "\n".join(
        line.rstrip()[: -len(EXACT_TAG.strip())].rstrip()
        if line.rstrip().endswith(EXACT_TAG.strip())
        else line
        for line in checklist.strip().splitlines()
    )
    return (prompts_dir / "judge.md").read_text().rstrip() + "\n\n" + shown + "\n"


def _final_message(transcript: str) -> str:
    """The judge's final answer: claude's result event text, or codex's last agent_message."""
    text = ""
    for line in transcript.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if not isinstance(e, dict):
            continue
        if e.get("type") == "result" and isinstance(e.get("result"), str):
            text = e["result"]
            continue
        item = e.get("item")
        if (
            e.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
            and isinstance(item.get("text"), str)
        ):
            text = item["text"]
    return text


def parse_verdicts(message: str, n_items: int) -> list[dict]:
    """The {"items": [...]} object in the judge's answer; exactly n_items entries numbered 1..n."""
    start, end = message.find("{"), message.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in the judge answer")
    items = json.loads(message[start : end + 1])["items"]
    by_n = {int(i["n"]): i for i in items}
    if sorted(by_n) != list(range(1, n_items + 1)):
        raise ValueError(f"judge numbered items {sorted(by_n)}, expected 1..{n_items}")
    out = []
    for n in range(1, n_items + 1):
        v = str(by_n[n].get("verdict", "")).strip().lower()
        if v not in VERDICTS:
            raise ValueError(f"item {n}: verdict {v!r}")
        out.append({"n": n, "verdict": v, "reason": str(by_n[n].get("reason", ""))[:500]})
    return out


def score(items: list[dict], exact: list[int] | tuple[int, ...] = ()) -> dict:
    """score: met / all items (primary); score_core: the same without [exact] items."""
    n = len(items)
    met = sum(i["verdict"] == "met" for i in items)
    core = [i for i in items if i["n"] not in set(exact)]
    return {
        "n_items": n,
        "n_met": met,
        "n_unclear": sum(i["verdict"] == "unclear" for i in items),
        "score": met / n if n else None,
        "exact_items": list(exact),
        "score_core": sum(i["verdict"] == "met" for i in core) / len(core) if core else None,
    }


def _blind(work: Path) -> str:
    """Delete the spec arm's process docs; return the change against `baseline` as a diff."""
    for rel in ARTIFACT_PATHS:
        (work / rel).unlink(missing_ok=True)
    subprocess.run(["git", "-C", str(work), "add", "-A"], check=True, capture_output=True)
    diff = subprocess.run(
        ["git", "-C", str(work), "diff", "--cached", "baseline"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return diff


@dataclass
class JudgeConfig:
    run: RunConfig  # repo, tasks_dir, work_root, accounts_file, grade_timeout_s
    timeout_s: int = 1800
    accounts: tuple[int, ...] = JUDGE.accounts


def judge_unit(unit_out: Path, cfg: JudgeConfig, account: int) -> str:
    """Judge one unit; returns "done", "quota", "auth" or "error". Writes judge.json on done."""
    meta = json.loads((unit_out / "meta.json").read_text())
    task_dir = cfg.run.tasks_dir / meta["task_id"]
    task = load_task(task_dir)
    checklist = (task_dir / "checklist.md").read_text()
    n_items = checklist_items(checklist)
    prompt = judge_prompt(checklist, cfg.run.prompts_dir)
    scratch = cfg.run.work_root / uuid.uuid4().hex
    record: dict = {
        "judge_model": JUDGE.model,
        "judge_agent": JUDGE.agent,
        "account": account,
        "checklist_sha256": hashlib.sha256(checklist.encode()).hexdigest(),
        "judge_prompt_sha256": hashlib.sha256(
            (cfg.run.prompts_dir / "judge.md").read_bytes()
        ).hexdigest(),
    }
    try:
        work = _patched_workspace(cfg.run, task, unit_out / "patch.diff", scratch)
        (work / "CHANGE.diff").write_text(_blind(work))
        (scratch / "judge-prompt.txt").write_text(prompt)
        env = _agent_env(JUDGE, scratch, account, cfg.run.accounts_file)
        cmd = _agent_prefix() + build_command(
            JUDGE.agent, JUDGE.model, JUDGE.effort, scratch / "judge-prompt.txt"
        )
        t0 = time.monotonic()
        with (
            (scratch / "judge-prompt.txt").open("rb") as stdin,
            (unit_out / "judge-transcript.jsonl").open("wb") as stdout,
            (unit_out / "judge-stderr.log").open("wb") as stderr,
        ):
            proc = subprocess.Popen(
                cmd,
                cwd=work,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                env=env,
                start_new_session=True,
            )
            timed_out = False
            try:
                proc.wait(timeout=cfg.timeout_s)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                _kill_group(proc.pid)
                rc = proc.wait()
        try:
            write_back_credentials(
                cast(Agent, JUDGE.agent), scratch, account, cfg.run.accounts_file
            )
        except Exception as e:  # noqa: BLE001
            log.warning("credential write-back failed: %s", type(e).__name__)
        transcript = (unit_out / "judge-transcript.jsonl").read_text(errors="replace")
        stderr_text = (unit_out / "judge-stderr.log").read_text(errors="replace")
        if is_quota_error(JUDGE.agent, rc, transcript, stderr_text):
            return "quota"
        if is_auth_error(JUDGE.agent, rc, transcript, stderr_text):
            return "auth"
        if timed_out:
            raise TimeoutError(f"judge timed out after {cfg.timeout_s}s")
        items = parse_verdicts(_final_message(transcript), n_items)
        record.update(
            items=items,
            **score(items, exact_items(checklist)),
            wall_s=round(time.monotonic() - t0, 3),
            usage=parse_usage(JUDGE.agent, transcript).__dict__,
            judged_at=datetime.now(UTC).isoformat(timespec="seconds"),
        )
        tmp = unit_out / (JUDGE_FILE + ".tmp")
        tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        tmp.replace(unit_out / JUDGE_FILE)
        return "done"
    except Exception as e:  # noqa: BLE001 - one bad unit must not stop the batch
        log.warning("judge failed on %s: %s: %s", unit_out, type(e).__name__, e)
        return "error"
    finally:
        shutil.rmtree(scratch / "config", ignore_errors=True)
        _dispose(scratch, False)


def judge_all(units: list[Path], cfg: JudgeConfig, jobs: int = 4, max_tries: int = 4) -> dict:
    """Judge units without judge.json; rotate accounts on quota/auth; up to max_tries per unit."""
    todo = [u for u in units if not (u / JUDGE_FILE).exists()]
    counts = {"done": 0, "skipped": len(units) - len(todo), "failed": 0}
    accounts = list(cfg.accounts)

    def one(i: int, unit: Path) -> str:
        for attempt in range(max_tries):
            acct = accounts[(i + attempt) % len(accounts)]
            status = judge_unit(unit, cfg, acct)
            if status == "done":
                return status
            log.info("judge %s on %s (account %d, try %d)", status, unit, acct, attempt + 1)
        return "failed"

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for status in pool.map(lambda a: one(*a), enumerate(todo)):
            counts["done" if status == "done" else "failed"] += 1
    return counts
