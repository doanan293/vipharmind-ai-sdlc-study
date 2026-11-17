"""Write a readable pytest log (hidden tests, --tb=short) into each rater unit dir of a packet.

usage (harness venv): python test_logs.py PACKET_DIR KEY_CSV TASKS_DIR REPO RESULTS_ROOT [...]
Rebuilds the graded copy exactly as the grader does (saved patch.diff on a fresh start tree, process
docs removed, the commit's hidden tests copied in) and runs only the hidden test files.
"""

import csv
import shutil
import subprocess
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sdlc_harness.grade import grade
from sdlc_harness.runner import RunConfig, _patched_workspace
from sdlc_harness.tasks import load_task

packet, key, tasks, repo = map(Path, sys.argv[1:5])
roots = [Path(p) for p in sys.argv[5:]]
work_root = Path("/tmp/sdlc-testlogs")
work_root.mkdir(exist_ok=True)
cfg = RunConfig(
    repo=repo, tasks_dir=tasks, cohorts={}, work_root=work_root, cache_dir=Path(".work/reference")
)


def one(row: dict) -> str:
    src = next(r / row["unit"] for r in roots if (r / row["unit"] / "grade.json").is_file())
    task = load_task(tasks / row["task_id"])
    scratch = work_root / uuid.uuid4().hex
    try:
        work = _patched_workspace(cfg, task, src / "patch.diff", scratch)
        grade(repo, task, work, cfg.cache_dir, 900)
        backend = work.parent / "graded" / "backend"
        files = [p.removeprefix("backend/") for p in task.hidden_tests]
        proc = subprocess.run(
            [
                "uv",
                "run",
                "--frozen",
                "pytest",
                "-p",
                "no:cacheprovider",
                "-q",
                "--tb=short",
                "-o",
                "console_output_style=classic",
                *files,
            ],
            check=False,
            cwd=backend,
            capture_output=True,
            text=True,
            timeout=900,
        )
        out = (proc.stdout + proc.stderr).splitlines()
        text = "\n".join(out if len(out) <= 400 else out[:60] + ["... (cut) ..."] + out[-330:])
        for rater in ("loi", "bao"):
            log = packet / rater / row["unit_id"] / "test-log.txt"
            log.write_text(
                log.read_text() + "\n===== pytest output of the hidden tests =====\n" + text + "\n"
            )
        return f"ok {row['unit_id']}"
    except Exception as e:  # noqa: BLE001
        return f"FAIL {row['unit_id']} {type(e).__name__}: {e}"
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


rows = list(csv.DictReader(key.open()))
with ThreadPoolExecutor(4) as pool:
    for r in pool.map(one, rows):
        print(r, flush=True)
