"""Step 2: gradeability of feature ranges.
Runs per range: end | base | base+hidden+support(from end) | base+hidden only.
Usage: uv run --project <harness> python grade_ranges.py F05 F12 ...  (results -> results/<id>.json)"""
import json, os, re, shutil, subprocess, sys, tempfile, time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sdlc_harness.vcs import export_tree, read_file
from sdlc_harness.pytest_run import find_lock_dir, _nodeid

REPO = Path("/home/andv/personal/vipharmind-camera-ready")
WORK = Path("/tmp/feature-feasibility"); WORK.mkdir(exist_ok=True)
HERE = Path(__file__).parent
R = {r["id"]: r for r in json.load(open(HERE / "ranges.json"))["sub_ranges"]}
DEP_FILES = ("backend/pyproject.toml", "backend/uv.lock", "uv.lock", "pyproject.toml")
for _r in R.values():
    _r["other_dirs_files"] = set(subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", _r["base"], _r["end"], "--", *DEP_FILES], capture_output=True, text=True).stdout.split())
RESULTS = os.environ.get("RESULTS", "results")

def run_suite(tree: Path, timeout_s=900):
    """Like sdlc_harness.pytest_run.run_backend_tests but keeps failure messages."""
    backend = tree / "backend"
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    lock = find_lock_dir(tree)
    subprocess.run(["uv", "sync", "--frozen"], cwd=lock, env=env, check=True, capture_output=True, timeout=timeout_s)
    xml = tree / "junit.xml"
    t0 = time.time()
    proc = subprocess.run(["uv", "run", "--frozen", "pytest", "-p", "no:cacheprovider", f"--junitxml={xml}",
                           "--continue-on-collection-errors", "-q"], cwd=backend, env=env,
                          capture_output=True, text=True, timeout=timeout_s)
    wall = time.time() - t0
    out, msgs = {}, {}
    if not xml.is_file():
        return dict(outcomes={}, msgs={}, wall=wall, rc=proc.returncode, tail=(proc.stdout + proc.stderr)[-800:])
    for case in ET.parse(xml).getroot().iter("testcase"):
        k = _nodeid(backend, case.get("classname", ""), case.get("name", ""))
        o = "passed"
        for tag in ("error", "failure", "skipped"):
            el = case.find(tag)
            if el is not None:
                o = {"error": "error", "failure": "failed", "skipped": "skipped"}[tag]
                if tag != "skipped":
                    msgs[k] = ((el.get("message") or "") + "\n" + (el.text or ""))[-1500:]
                break
        out[k] = o
    return dict(outcomes=out, msgs=msgs, wall=wall, rc=proc.returncode, tail=proc.stdout[-300:])

def overlay(tree, sha, paths, status):
    for p in paths:
        t = tree / p
        if status.get(p) == "D":
            t.unlink(missing_ok=True); continue
        t.parent.mkdir(parents=True, exist_ok=True)
        data = subprocess.run(["git", "-C", str(REPO), "show", f"{sha}:{p}"], check=True, capture_output=True).stdout
        t.write_bytes(data)

def variant(rid, name):
    r = R[rid]
    tree = Path(tempfile.mkdtemp(prefix=f"{rid}-{name}-", dir=WORK))
    try:
        export_tree(REPO, r["end"] if name == "end" else r["base"], tree)
        if name in ("base_hs", "base_h"):
            overlay(tree, r["end"], r["hidden_tests"], {})
        if name == "base_hs":
            overlay(tree, r["end"], r["support_files"], r["support_status"])
        if name in ("base_hs", "base_h") and os.environ.get("DEPS") == "1":
            # dependency manifests changed in the range are given to the agent (not part of the task)
            overlay(tree, r["end"], [p for p in DEP_FILES if p in r["other_dirs_files"]], {})
        return run_suite(tree)
    except Exception as e:  # infra
        return dict(outcomes={}, msgs={}, wall=0, rc=-1, tail=f"INFRA {type(e).__name__}: {str(e)[-500:]} {getattr(e,'stderr',b'')[-500:] if getattr(e,'stderr',None) else ''}")
    finally:
        shutil.rmtree(tree, ignore_errors=True)

SUPPORT_RE = re.compile(r"(from tests[\.\w]* import|No module named 'tests|cannot import name '\w+' from 'tests|fixture '\w+' not found|tests/\w+\.py)")

def analyse(rid, res):
    r = R[rid]
    hidden = {p.removeprefix("backend/") for p in r["hidden_tests"]}
    f = lambda k: k.split("::")[0]
    bad = lambda o: {k for k, v in o.items() if v in ("failed", "error")}
    def split(o): return ({k: v for k, v in o.items() if f(k) in hidden}, {k: v for k, v in o.items() if f(k) not in hidden})
    e_h, e_o = split(res["end"]["outcomes"]); _, b_o = split(res["base"]["outcomes"])
    hs_h, hs_o = split(res["base_hs"]["outcomes"]); h_h, h_o = split(res["base_h"]["outcomes"])
    pre_bad = bad(b_o)
    hidden_files_collect_err_h = sorted(k for k in bad(h_h) if "::" not in k)
    support_dep = sorted(k for k in bad(h_h) if SUPPORT_RE.search(res["base_h"]["msgs"].get(k, "")))
    # hidden tests that fail in base_h but would not be explained by src: compare to hs
    return dict(
        end_total=len(res["end"]["outcomes"]), end_bad=sorted(bad(res["end"]["outcomes"])),
        end_skipped=sum(v == "skipped" for v in res["end"]["outcomes"].values()),
        base_total=len(res["base"]["outcomes"]), base_bad=sorted(pre_bad),
        hs_hidden_total=len(hs_h), hs_hidden_bad=len(bad(hs_h)), hs_hidden_pass=len(hs_h) - len(bad(hs_h)) - sum(v=="skipped" for v in hs_h.values()),
        hs_hidden_collect_err_files=sorted(k for k in bad(hs_h) if "::" not in k),
        hs_old_total=len(hs_o), hs_old_bad=sorted(bad(hs_o) - pre_bad),
        h_hidden_total=len(h_h), h_hidden_bad=len(bad(h_h)),
        h_hidden_collect_err_files=hidden_files_collect_err_h,
        h_support_dependent=support_dep,
        h_support_msgs={k: res["base_h"]["msgs"][k][-400:] for k in support_dep[:8]},
        h_old_bad=sorted(bad(h_o) - pre_bad),
        walls={k: round(v["wall"], 1) for k, v in res.items()},
        tails={k: v["tail"] for k, v in res.items() if not v["outcomes"]},
    )

def main(ids):
    jobs = [(rid, v) for rid in ids for v in ("end", "base", "base_hs", "base_h")]
    with ThreadPoolExecutor(int(os.environ.get("JOBS", "6"))) as ex:
        futs = {j: ex.submit(variant, *j) for j in jobs}
        for rid in ids:
            res = {v: futs[(rid, v)].result() for v in ("end", "base", "base_hs", "base_h")}
            a = analyse(rid, res)
            json.dump(dict(id=rid, analysis=a, raw={k: dict(outcomes=v["outcomes"], msgs={m: t[-600:] for m, t in v["msgs"].items()}) for k, v in res.items()}),
                      open(HERE / RESULTS / f"{rid}.json", "w"), indent=1)
            print(rid, json.dumps({k: (len(v) if isinstance(v, list) and k not in ("end_bad",) else v) for k, v in a.items() if k not in ("h_support_msgs", "tails")}), a["tails"] or "", flush=True)

if __name__ == "__main__":
    main(sys.argv[1:])
