"""Run units (cohort x task x arm x rep) in parallel: one agent session each, then grade.

A unit is done iff its grade.json exists, so an interrupted run resumes where it stopped.
A unit stopped by a quota error is not a rep: it goes to the back of the queue with the
cohort's next account, and when every account of a cohort ran out the cohort waits.
"""

import json
import logging
import os
import random
import shutil
import signal
import subprocess
import sys
import threading
import time
import tomllib
import uuid
from collections import Counter, deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal, cast

from sdlc_harness.agents import build_command, is_quota_error, parse_usage
from sdlc_harness.grade import Grade, GradingError, grade, grade_to_dict
from sdlc_harness.prompting import ARMS, PROMPTS_DIR, Arm, render_prompt
from sdlc_harness.tasks import Task, load_task
from sdlc_harness.workspace import Agent, collect_patch, prepare_config, prepare_workspace

log = logging.getLogger(__name__)

Status = Literal["done", "quota", "error"]
COHORTS_FILE = Path(__file__).resolve().parents[2] / "cohorts.toml"
FAKE_AGENT_ENV = "SDLC_FAKE_AGENT"  # tests: path of a script that stands in for the agent CLI
SEED = 20261115
GRADE = "grade.json"
META = "meta.json"
QUOTA_LOG = "quota.log"
QUOTA_EXHAUSTED = "quota retries exhausted"
STUDY_ROOT = Path(__file__).resolve().parents[3]
# Agents run with permission checks off, so their work dirs live outside the study repo (results,
# task files, other reps) and outside any tree whose ancestors hold agent instructions or config.
DEFAULT_WORK_ROOT = Path(os.environ.get("SDLC_WORK_ROOT") or "/tmp/sdlc-runs")
AGENT_MARKERS = ("CLAUDE.md", "AGENTS.md", "GEMINI.md", ".claude", ".codex")
# provider and parent-session variables that could override the account's login, endpoint or
# model; prepare_config's own variables are added back after the scrub
ENV_DROP_PREFIXES = {
    "claude": ("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDECODE"),
    "agy": ("GEMINI_", "GOOGLE_"),
    "codex": ("OPENAI_", "CODEX_"),
}


@dataclass(frozen=True)
class Cohort:
    name: str
    agent: str
    model: str
    effort: str
    accounts: tuple[int, ...]


@dataclass(frozen=True)
class RunUnit:
    cohort: str
    task_id: str
    arm: Arm
    rep: int


@dataclass
class RunConfig:
    repo: Path  # ViPharmind repo (read only)
    tasks_dir: Path
    cohorts: dict[str, Cohort]
    timeout_s: int = 3600  # agent wall-clock limit
    grade_timeout_s: int = 900
    cache_dir: Path | None = None  # reference test runs, shared by every unit of a task
    work_root: Path = DEFAULT_WORK_ROOT  # agent work dirs and config dirs; see validate_work_root
    accounts_file: Path | None = None  # None: workspace.ACCOUNTS_FILE
    prompts_dir: Path = PROMPTS_DIR
    quota_backoff_s: float = 600.0
    max_quota_retries: int = 20  # per unit; then the unit is an error
    keep_work: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False, repr=False)
    _task_locks: dict[str, threading.Lock] = field(default_factory=dict, init=False, repr=False)
    _warm: set[str] = field(default_factory=set, init=False, repr=False)

    def task_lock(self, task_id: str) -> threading.Lock:
        with self._lock:
            return self._task_locks.setdefault(task_id, threading.Lock())


def load_cohorts(path: Path = COHORTS_FILE) -> dict[str, Cohort]:
    data = tomllib.loads(path.read_text())["cohort"]
    return {
        name: Cohort(name, c["agent"], c["model"], c["effort"], tuple(c["accounts"]))
        for name, c in data.items()
    }


def select_tasks(tasks_dir: Path, spec: str) -> list[str]:
    """pilot | main | comma-separated ids -> task ids (pilot/main sorted, ids as given)."""
    if spec in ("pilot", "main"):
        ids = []
        for d in sorted(tasks_dir.iterdir()):
            if (d / "task.toml").is_file() and load_task(d).pilot == (spec == "pilot"):
                ids.append(d.name)
        return ids
    ids = [s.strip() for s in spec.split(",") if s.strip()]
    missing = [i for i in ids if not (tasks_dir / i / "task.toml").is_file()]
    if missing:
        raise ValueError(f"no task.toml for {missing} in {tasks_dir}")
    return ids


def plan_units(
    cohorts: list[str], task_ids: list[str], reps: int = 3, seed: int = SEED
) -> list[RunUnit]:
    """Every cohort x task x arm x rep, in a seeded shuffled order."""
    units = [
        RunUnit(c, t, arm, rep)
        for c in cohorts
        for t in task_ids
        for arm in ARMS
        for rep in range(1, reps + 1)
    ]
    random.Random(seed).shuffle(units)
    return units


def validate_work_root(work_root: Path) -> None:
    """Refuse a work root inside the study repo or below agent instructions or config."""
    root = work_root.expanduser().resolve()
    if root.is_relative_to(STUDY_ROOT):
        raise ValueError(f"work root {root} is inside the study repo {STUDY_ROOT}")
    for d in (root, *root.parents):
        for marker in AGENT_MARKERS:
            if (d / marker).exists():
                raise ValueError(f"work root {root} is below {d / marker}, which agents would read")


def unit_dir(out_root: Path, unit: RunUnit) -> Path:
    return out_root / unit.cohort / unit.task_id / f"{unit.arm}-r{unit.rep}"


def is_done(out_root: Path, unit: RunUnit) -> bool:
    return (unit_dir(out_root, unit) / GRADE).is_file()


# --- one unit ----------------------------------------------------------------------------


def _agent_prefix() -> list[str]:
    fake = os.environ.get(FAKE_AGENT_ENV)
    return [sys.executable, fake] if fake else []


_versions: dict[tuple[str, ...], str] = {}
_versions_lock = threading.Lock()


def tool_version(agent: str) -> str | None:
    """`<cli> --version`, once per CLI; with the fake agent, the fake's version."""
    prefix = _agent_prefix()
    cmd = (*prefix, "--version") if prefix else (agent, "--version")
    with _versions_lock:
        if cmd not in _versions:
            try:
                out = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=60)
                _versions[cmd] = (out.stdout.strip() or out.stderr.strip()).splitlines()[0]
            except (OSError, subprocess.SubprocessError, IndexError):
                return None
        return _versions[cmd]


def scrub_env(agent: str, environ: dict[str, str], extra: dict[str, str]) -> dict[str, str]:
    """The agent's env: no provider/session overrides, no harness venv; then `extra` on top."""
    venv_bins = {Path(environ["VIRTUAL_ENV"]) / "bin"} if environ.get("VIRTUAL_ENV") else set()
    if sys.prefix != sys.base_prefix:
        venv_bins.add(Path(sys.prefix) / "bin")
    env = {
        k: v
        for k, v in environ.items()
        if k != "VIRTUAL_ENV" and not k.startswith(ENV_DROP_PREFIXES[agent])
    }
    if "PATH" in env:
        env["PATH"] = os.pathsep.join(
            p for p in env["PATH"].split(os.pathsep) if p and Path(p) not in venv_bins
        )
    env.update(extra)
    return env


def _agent_env(cohort: Cohort, scratch: Path, account: int, accounts_file: Path | None) -> dict:
    agent = cast(Agent, cohort.agent)
    config_env = prepare_config(agent, scratch, account, accounts_file)
    return scrub_env(cohort.agent, dict(os.environ), config_env)


def _kill_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


class RunCancelled(BaseException):
    """Ctrl-C: the unit stops without writing grade.json, so a rerun redoes it."""


_stop = threading.Event()
_live: set[subprocess.Popen] = set()
_live_lock = threading.Lock()


def kill_live_agents() -> None:
    """Stop new agent starts and kill the process group of every agent still running."""
    with _live_lock:
        _stop.set()
        for proc in _live:
            _kill_group(proc.pid)


def _invoke(
    cmd: list[str], work: Path, out: Path, env: dict, timeout_s: int
) -> tuple[int, bool, float]:
    """Run the agent in its own process group; kill the whole group on timeout or exit."""
    with (
        (out / "prompt.txt").open("rb") as stdin,
        (out / "transcript.jsonl").open("wb") as stdout,
        (out / "stderr.log").open("wb") as stderr,
    ):
        t0 = time.monotonic()
        with _live_lock:
            if _stop.is_set():
                raise RunCancelled
            proc = subprocess.Popen(
                cmd,
                cwd=work,
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                env=env,
                start_new_session=True,
            )
            _live.add(proc)
        timed_out = False
        try:
            proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
        finally:
            _kill_group(proc.pid)  # also any background process the agent left behind
            returncode = proc.wait()
            with _live_lock:
                _live.discard(proc)
        if _stop.is_set():
            raise RunCancelled
        return returncode, timed_out, round(time.monotonic() - t0, 3)


def _grade(cfg: RunConfig, task: Task, work: Path) -> Grade:
    """Grade; the first grade of a task holds a lock so its reference runs are cached once."""
    if task.id not in cfg._warm:
        with cfg.task_lock(task.id):
            if task.id not in cfg._warm:
                result = grade(cfg.repo, task, work, cfg.cache_dir, cfg.grade_timeout_s)
                cfg._warm.add(task.id)
                return result
    return grade(cfg.repo, task, work, cfg.cache_dir, cfg.grade_timeout_s)


def _write_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def run_unit(unit: RunUnit, cfg: RunConfig, out_root: Path, account: int | None = None) -> Status:
    """Run one agent session and grade it into results/raw/<cohort>/<task>/<arm>-r<rep>/."""
    out = unit_dir(out_root, unit)
    if (out / GRADE).is_file():
        return "done"
    cohort = cfg.cohorts[unit.cohort]
    account = cohort.accounts[0] if account is None else account
    # opaque: the agent's cwd must not reveal arm, task, cohort or rep
    scratch = cfg.work_root / uuid.uuid4().hex
    if out.exists():
        shutil.rmtree(out)  # a partial or quota-stopped attempt
    out.mkdir(parents=True)
    meta: dict = {
        "cohort": unit.cohort,
        "task_id": unit.task_id,
        "arm": unit.arm,
        "rep": unit.rep,
        "agent": cohort.agent,
        "tool_version": None,
        "model": cohort.model,
        "model_served": None,
        "effort": cohort.effort,
        "account": account,
        "started_at": None,
        "wall_s": None,
        "timed_out": False,
        "returncode": None,
        "usage": None,
        "status": None,
        "work_dir": str(scratch / "work"),
    }
    try:
        task = load_task(cfg.tasks_dir / unit.task_id)
        (out / "prompt.txt").write_text(render_prompt(task, unit.arm, cfg.prompts_dir))
        work = prepare_workspace(cfg.repo, task, scratch, cfg.grade_timeout_s)
        meta["tool_version"] = tool_version(cohort.agent)
        cmd = _agent_prefix() + build_command(
            cohort.agent, cohort.model, cohort.effort, out / "prompt.txt"
        )
        try:
            env = _agent_env(cohort, scratch, account, cfg.accounts_file)
            meta["started_at"] = datetime.now(UTC).isoformat(timespec="seconds")
            rc, timed_out, wall = _invoke(cmd, work, out, env, cfg.timeout_s)
        finally:
            shutil.rmtree(scratch / "config", ignore_errors=True)  # credentials copy
        transcript = (out / "transcript.jsonl").read_text(errors="replace")
        stderr = (out / "stderr.log").read_text(errors="replace")
        usage = parse_usage(cohort.agent, transcript)
        meta.update(
            returncode=rc,
            timed_out=timed_out,
            wall_s=wall,
            usage=asdict(usage),
            model_served=usage.model_served,
        )
        if not timed_out and is_quota_error(cohort.agent, rc, f"{transcript}\n{stderr}"):
            meta["status"] = "quota"
            _write_json(out / META, meta)
            with cfg._lock, (out_root / QUOTA_LOG).open("a") as f:
                f.write(f"{meta['started_at']} {unit.cohort} {unit.task_id} ")
                f.write(f"{unit.arm}-r{unit.rep} account={account}\n")
            shutil.rmtree(scratch, ignore_errors=True)
            return "quota"
        (out / "patch.diff").write_text(collect_patch(work))
        result = _grade(cfg, task, work)
        if _stop.is_set():  # Ctrl-C reaches the grader's test runs too: do not trust this grade
            raise RunCancelled
        meta["status"] = "done"
        _write_json(out / META, meta)
        _write_json(out / GRADE, grade_to_dict(result))  # last: marks the unit done
        if not cfg.keep_work:
            shutil.rmtree(scratch, ignore_errors=True)
        return "done"
    except RunCancelled:
        shutil.rmtree(scratch / "config", ignore_errors=True)
        raise
    except GradingError as e:
        meta.update(status="error", error=f"grading: {e}")
    except Exception as e:  # one broken unit must not stop the whole run
        log.exception("unit %s failed", unit)
        meta.update(status="error", error=f"{type(e).__name__}: {e}")
    _write_json(out / META, meta)
    return "error"


# --- the queue ---------------------------------------------------------------------------


@dataclass
class _Accounts:
    """One cohort's accounts: which is current, which ran out, and when to try again."""

    accounts: tuple[int, ...]
    current: int = 0
    generation: int = 0  # bumped after each wait; older quota reports are stale
    exhausted: set[int] = field(default_factory=set)
    resume_at: float = 0.0

    def account(self) -> int:
        return self.accounts[self.current]

    def hit_quota(self, account: int, generation: int, backoff_s: float) -> None:
        if generation != self.generation:
            return
        self.exhausted.add(account)
        if self.account() == account:
            self.current = (self.current + 1) % len(self.accounts)
        if self.exhausted >= set(self.accounts):
            log.warning("all accounts out of quota; waiting %.0fs", backoff_s)
            self.exhausted.clear()
            self.generation += 1
            self.resume_at = time.monotonic() + backoff_s


def _ids(u: RunUnit) -> tuple[str, str, str, int]:
    return u.cohort, u.task_id, u.arm, u.rep


def run_all(units: list[RunUnit], cfg: RunConfig, out_root: Path, jobs: int = 1) -> dict[str, int]:
    """Run every unit not yet done with `jobs` agent sessions at a time.

    Returns counts: done, skipped (already done), error, quota (attempts stopped by quota).
    On Ctrl-C, kills every running agent's process group and re-raises KeyboardInterrupt.
    """
    validate_work_root(cfg.work_root)
    _stop.clear()
    summary = {"done": 0, "skipped": 0, "error": 0, "quota": 0}
    queue: deque[RunUnit] = deque()
    for u in units:
        if is_done(out_root, u):
            summary["skipped"] += 1
        else:
            queue.append(u)
    pools = {name: _Accounts(c.accounts) for name, c in cfg.cohorts.items()}
    running: dict[Future, tuple[RunUnit, int, int]] = {}
    quota_hits: Counter[RunUnit] = Counter()
    pool = ThreadPoolExecutor(max_workers=jobs)
    try:
        while queue or running:
            now = time.monotonic()
            held: list[RunUnit] = []
            while queue and len(running) < jobs:
                u = queue.popleft()
                accounts = pools[u.cohort]
                if accounts.resume_at > now:
                    held.append(u)
                    continue
                account = accounts.account()
                future = pool.submit(run_unit, u, cfg, out_root, account)
                running[future] = (u, account, accounts.generation)
            queue.extendleft(reversed(held))
            wake = [pools[u.cohort].resume_at - now for u in queue]
            wake = [w for w in wake if w > 0]
            if not running:
                time.sleep(min(wake) if wake else 0)
                continue
            timeout = min(wake) if wake else None
            finished, _ = wait(running, timeout=timeout, return_when=FIRST_COMPLETED)
            for future in finished:
                u, account, generation = running.pop(future)
                try:
                    status = future.result()
                except Exception:  # run_unit already records its own errors
                    log.exception("unit %s crashed", u)
                    status = "error"
                log.info("%s %s %s %s-r%d account=%d", status, *_ids(u), account)
                if status == "quota":
                    summary["quota"] += 1
                    quota_hits[u] += 1
                    pools[u.cohort].hit_quota(account, generation, cfg.quota_backoff_s)
                    if quota_hits[u] > cfg.max_quota_retries:
                        _give_up(out_root, u)
                        summary["error"] += 1
                    else:
                        queue.append(u)
                else:
                    summary[status] += 1
    except KeyboardInterrupt:
        log.warning("interrupted: killing running agents; rerun to resume")
        kill_live_agents()
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
    return summary


def _give_up(out_root: Path, unit: RunUnit) -> None:
    path = unit_dir(out_root, unit) / META
    meta = json.loads(path.read_text()) if path.is_file() else {}
    meta.update(status="error", error=QUOTA_EXHAUSTED)
    _write_json(path, meta)
