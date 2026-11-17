"""Medium-tier criterion 8 (prereg-v1.1 draft): share of a window's backend/src lines that only
integration-marked tests exercise.

  run      export `end` of each window, `uv sync --frozen`, then run pytest twice with pytest-cov and
           `--cov-context=test`: the graded run (project default, -m "not integration") and the
           integration run (-m integration, needs Docker). Writes <out>/<id>.{graded,integration}.json.
  analyse  S = coverage.py statements on lines the window's diff adds or changes in backend/src/**.py,
           minus lines that only ran at import/collection time (empty context) in both runs (an ast
           statement set is used for files coverage never saw). G = S run inside a graded test,
           I = S run inside an integration test. share_int_only = |I - G| / |S|. Writes <out>/analysis.json.

Usage: python medium_coverage.py run <out> <id,id,...> [--jobs N]
       python medium_coverage.py analyse <out> <id> [<id> ...]"""
import ast, json, os, re, shutil, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = os.environ.get("VIPHARMIND_REPO", "/home/andv/personal/vipharmind")
CANDS = {c["id"]: c for c in json.load(open(HERE / "medium_candidates.json"))["candidates"]}
COVRC = "[run]\nsource = src\n[json]\nshow_contexts = True\n"


def run_one(wid, out: Path, work: Path, rc: Path):
    c = CANDS[wid]
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    tree = Path(tempfile.mkdtemp(prefix=wid + "-", dir=work))
    log = open(out / f"{wid}.log", "w")
    try:
        p = subprocess.Popen(["git", "-C", REPO, "archive", c["end"]], stdout=subprocess.PIPE)
        subprocess.run(["tar", "-x", "-C", str(tree)], stdin=p.stdout, check=True)
        p.wait()
        lock = tree / "backend" if (tree / "backend/uv.lock").exists() else tree
        subprocess.run(["uv", "sync", "--frozen"], cwd=lock, env=env, check=True, stdout=log, stderr=log, timeout=900)
        for name, marker in (("graded", []), ("integration", ["-m", "integration"])):
            # pytest-cov switches the context per test phase through pytest hooks, so code run inside
            # async tests is attributed to the test (coverage's own test_function context is not)
            r = subprocess.run(["uv", "run", "--frozen", "--with", "pytest-cov", "pytest", "-p", "no:cacheprovider",
                                "-q", "--cov=src", f"--cov-config={rc}", "--cov-context=test",
                                f"--cov-report=json:{out / f'{wid}.{name}.json'}", *marker],
                               cwd=tree / "backend", env=env, stdout=log, stderr=log, timeout=1800)
            print(wid, name, "pytest rc", r.returncode, file=log, flush=True)
        return wid, "ok"
    except Exception as e:  # infra
        return wid, f"ERR {e}"
    finally:
        log.close()
        shutil.rmtree(tree, ignore_errors=True)


def added_lines(base, end):
    d = subprocess.run(["git", "-C", REPO, "diff", "-U0", base, end, "--", "backend/src"],
                       capture_output=True, text=True, check=True).stdout
    res, cur = {}, None
    for ln in d.splitlines():
        if ln.startswith("+++ "):
            cur = None if ln.endswith("/dev/null") else ln[6:]
        elif ln.startswith("@@") and cur:
            m = re.search(r"\+(\d+)(?:,(\d+))?", ln)
            s, n = int(m.group(1)), int(m.group(2) or 1)
            res.setdefault(cur, set()).update(range(s, s + n))
    return res


def ast_stmts(end, path):
    src = subprocess.run(["git", "-C", REPO, "show", f"{end}:{path}"], capture_output=True, text=True).stdout
    return {n.lineno for n in ast.walk(ast.parse(src))
            if isinstance(n, ast.stmt) and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))}


def analyse(out: Path, ids):
    res = json.load(open(out / "analysis.json")) if (out / "analysis.json").exists() else {}
    for wid in ids:
        c = CANDS[wid]
        runs = {k: json.load(open(out / f"{wid}.{k}.json"))["files"] for k in ("graded", "integration")}
        tot = dict(S_all=0, import_only=0, S=0, G=0, I=0, int_only=0, none=0)
        per = {}
        for path, lines in added_lines(c["base"], c["end"]).items():
            if not path.endswith(".py"):
                continue
            key = path.removeprefix("backend/")
            stm, ex, imp = set(), {}, set()
            for k, files in runs.items():
                f = files.get(key)
                ex[k] = set()
                if f:
                    stm |= set(f["executed_lines"]) | set(f["missing_lines"])
                    ex[k] = {int(n) for n, ctxs in f.get("contexts", {}).items() if any(ctxs)}
                    imp |= {int(n) for n, ctxs in f.get("contexts", {}).items() if not any(ctxs)}
            if not stm:
                stm = ast_stmts(c["end"], path)
            s0 = lines & stm
            s = s0 - (imp - ex["graded"] - ex["integration"])
            g, i = s & ex["graded"], s & ex["integration"]
            row = dict(S_all=len(s0), import_only=len(s0) - len(s), S=len(s), G=len(g), I=len(i),
                       int_only=len(i - g), none=len(s - g - i))
            for k in tot:
                tot[k] += row[k]
            if row["S"]:
                per[key.removeprefix("src/pharma_agent/")] = row
        tot["share_int_only"] = round(tot["int_only"] / tot["S"], 3) if tot["S"] else None
        tot["share_not_graded"] = round((tot["S"] - tot["G"]) / tot["S"], 3) if tot["S"] else None
        res[wid] = dict(total=tot, files=per)
        print(wid, tot)
    json.dump(res, open(out / "analysis.json", "w"), indent=1)


if __name__ == "__main__":
    cmd, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    if cmd == "run":
        jobs = int(sys.argv[sys.argv.index("--jobs") + 1]) if "--jobs" in sys.argv else 3
        work = Path(tempfile.mkdtemp(prefix="medium-cov-"))
        rc = work / "covrc"
        rc.write_text(COVRC)
        with ThreadPoolExecutor(jobs) as ex:
            for r in ex.map(lambda w: run_one(w, out, work, rc), sys.argv[3].split(",")):
                print(*r, flush=True)
    elif cmd == "analyse":
        analyse(out, sys.argv[3:])
    else:
        raise SystemExit(__doc__)
