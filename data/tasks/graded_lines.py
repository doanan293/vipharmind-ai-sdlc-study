"""graded_src_lines of each main task (prereg-v1.1, "Phân tích độ nhạy thêm cho H5: số dòng được chấm").

graded_src_lines = the backend/src/**.py lines that the original patch (parent..commit for a small
task, base..end for a range task) adds or changes, that are coverage.py statements, and that run
inside at least one graded hidden test (a test in one of the task's hidden test files, not marked
`integration`) when the graded run is made at the original commit with pytest-cov and
`--cov-context=test`. Lines that only run at import or collection time (empty context) are left
out. This is G of medium-tier criterion 8 (tasks/feature-feasibility/medium_coverage.py),
restricted to the contexts of the task's own hidden tests.

Original code only: `git archive` of the commit, `uv sync --frozen`, then pytest on the hidden test
files with `-m "not integration"`. No AI run is read.

Usage (from the repo root; one task at a time, low priority):
  nice -n 19 python3 tasks/graded_lines.py [--repo /home/andv/personal/vipharmind] [--only t01,m02]
Writes tasks/graded_lines.json (merged with existing entries) and logs to .work/graded-lines/.
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "graded_lines.json"
MAIN = [f"t{i:02d}" for i in range(1, 16)] + [f"m{i:02d}" for i in range(1, 6)] + ["f08", "f14", "f15"]
COVRC = "[run]\nsource = src\n[json]\nshow_contexts = True\n"


def git(repo, *args, **kw):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, check=True,
                          **kw).stdout


def changed_lines(repo, base, end):
    """New-side line numbers each backend/src file gains or changes (git diff -U0)."""
    d = git(repo, "diff", "-U0", base, end, "--", "backend/src")
    res, cur = {}, None
    for ln in d.splitlines():
        if ln.startswith("+++ "):
            cur = None if ln.endswith("/dev/null") else ln[6:]
        elif ln.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", ln)
            s, n = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
            res.setdefault(cur, set()).update(range(s, s + n))
    return res


def ast_stmts(repo, end, path):
    src = git(repo, "show", f"{end}:{path}")
    return {n.lineno for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.stmt) and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))}


def run_coverage(repo, task, work: Path, log) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    tree = Path(tempfile.mkdtemp(prefix=task["id"] + "-", dir=work))
    try:
        p = subprocess.Popen(["git", "-C", repo, "archive", task["commit"]], stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", str(tree)], stdin=p.stdout, check=True)
        p.wait()
        lock_dir = tree / "backend" if (tree / "backend/uv.lock").exists() else tree
        subprocess.run(["uv", "sync", "--frozen"], cwd=lock_dir, env=env, check=True, stdout=log,
                       stderr=log, timeout=1800)
        rc = work / "covrc"
        rc.write_text(COVRC)
        report = work / f"{task['id']}.json"
        tests = [t.removeprefix("backend/") for t in task["hidden_tests"]
                 if (tree / t).is_file() and Path(t).name.startswith("test_")]
        r = subprocess.run(
            ["uv", "run", "--frozen", "--with", "pytest-cov", "pytest", "-p", "no:cacheprovider", "-q",
             "-m", "not integration", "--cov=src", f"--cov-config={rc}", "--cov-context=test",
             f"--cov-report=json:{report}", *tests],
            cwd=tree / "backend", env=env, stdout=log, stderr=log, timeout=3600)
        print(task["id"], "pytest rc", r.returncode, file=log, flush=True)
        data = json.loads(report.read_text())
        return {"files": data["files"], "pytest_rc": r.returncode, "test_files": tests}
    finally:
        shutil.rmtree(tree, ignore_errors=True)


def measure(repo, task, cov) -> dict:
    hidden = {t.removeprefix("backend/") for t in task["hidden_tests"]}
    base = task.get("base") or task["parent"]
    total = dict(changed_stmts=0, graded=0, import_only=0, not_run_by_hidden=0)
    per = {}
    for path, lines in changed_lines(repo, base, task["commit"]).items():
        if not path.endswith(".py"):
            continue
        f = cov["files"].get(path.removeprefix("backend/"))
        if f:
            stm = set(f["executed_lines"]) | set(f["missing_lines"])
            ctx = {int(n): [c for c in cs if c] for n, cs in f.get("contexts", {}).items()}
        else:
            stm, ctx = ast_stmts(repo, task["commit"], path), {}
        s = lines & stm
        # a context is "tests/x/test_y.py::test_z|run"; keep those of the task's hidden test files
        g = {n for n in s if any(c.split("::", 1)[0] in hidden for c in ctx.get(n, []))}
        imp = {n for n in s if n in ctx and not ctx[n]}
        row = dict(changed_stmts=len(s), graded=len(g), import_only=len(imp - g),
                   not_run_by_hidden=len(s - g - imp))
        for k in total:
            total[k] += row[k]
        if s:
            per[path.removeprefix("backend/src/pharma_agent/")] = row
    return {"graded_src_lines": total["graded"], "totals": total, "files": per,
            "pytest_rc": cov["pytest_rc"], "test_files": cov["test_files"],
            "base": base, "end": task["commit"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", default=os.environ.get("VIPHARMIND_REPO", "/home/andv/personal/vipharmind"))
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    ids = a.only.split(",") if a.only else MAIN
    res = json.loads(OUT.read_text()) if OUT.exists() else {}
    logs = HERE.parent / ".work" / "graded-lines"
    logs.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="graded-lines-"))
    for tid in ids:
        task = tomllib.loads((HERE / tid / "task.toml").read_text())
        with open(logs / f"{tid}.log", "w") as log:
            try:
                res[tid] = measure(a.repo, task, run_coverage(a.repo, task, work, log))
            except Exception as e:  # recorded: the task is left out of this analysis
                res[tid] = {"graded_src_lines": None, "error": f"{type(e).__name__}: {e}"}
        print(tid, res[tid].get("graded_src_lines"), res[tid].get("totals") or res[tid].get("error"),
              flush=True)
        OUT.write_text(json.dumps(dict(sorted(res.items())), indent=1) + "\n")
    shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
