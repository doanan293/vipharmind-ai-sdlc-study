"""Step 1: candidate feature ranges per backend-relevant plan (first-parent, pinned)."""
import json, subprocess, sys
from datetime import timedelta
from pathlib import Path
sys.path.insert(0, "/home/andv/personal/vipharmind-ai-sdlc-study/.worktrees/retro/retrospective/src")
from retro.gitlog import load_commits
from retro.specplans import load_spec_plan_files, referenced_code_paths, _links

REPO = Path("/home/andv/personal/vipharmind-camera-ready")
PIN = "3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe"

def git(*a):
    return subprocess.run(["git", "-c", "core.quotePath=false", "-C", str(REPO), *a], check=True, capture_output=True, text=True).stdout

order = git("rev-list", "--first-parent", "--reverse", PIN).split()
idx = {s: i for i, s in enumerate(order)}
commits = {c.sha: c for c in load_commits(REPO, [PIN])}
docs = load_spec_plan_files(REPO, [PIN])
W = timedelta(days=14)

def numstat(base, end):
    out = {}
    for line in git("diff", "--numstat", "-M", base, end).splitlines():
        a, d, p = line.split("\t", 2)
        if " => " in p:
            from retro.gitlog import _new_path; p = _new_path(p)
        out[p] = (0 if a == "-" else int(a)) + (0 if d == "-" else int(d))
    return out

def summarize(plan, base, end, linked_set):
    i0, i1 = idx[base] + 1, idx[end]
    rng = order[i0:i1 + 1]
    ns = numstat(base, end)
    src = sum(v for p, v in ns.items() if p.startswith("backend/src/"))
    tests = [p for p in ns if p.startswith("backend/tests/")]
    other_dirs = {}
    for p, v in ns.items():
        top = p.split("/")[0]
        if p.startswith("backend/src/") or p.startswith("backend/tests/"):
            continue
        key = "backend/migrations" if "migration" in p or "alembic" in p else ("backend/other" if top == "backend" else top)
        other_dirs[key] = other_dirs.get(key, 0) + v
    return dict(plan=plan, base=base, end=end, n_commits=len(rng),
        n_linked=sum(s in linked_set for s in rng), n_unlinked=sum(s not in linked_set for s in rng),
        n_feat_unlinked=sum(s not in linked_set and commits[s].type == "feat" for s in rng),
        src_lines=src, test_files=len(tests), other_dirs=other_dirs,
        subjects=[(s[:9], commits[s].subject[:70], s in linked_set) for s in rng])

out = []
for d in docs:
    if d.kind != "plan":
        continue
    refs = referenced_code_paths(d.text)
    linked = [s for s in order if commits[s].type == "feat" and _links(commits[s], d, refs, W)]
    if not linked:
        continue
    # backend-relevant: some linked commit touches backend/src
    bl = [s for s in linked if any(f.path.startswith("backend/src/") for f in commits[s].files)]
    if not bl:
        continue
    first, last = linked[0], linked[-1]
    base = order[idx[first] - 1]
    r = summarize(d.path, base, last, set(linked))
    r["n_backend_linked"] = len(bl)
    r["kind"] = "whole-plan"
    out.append(r)
json.dump(out, open("whole_ranges.json", "w"), indent=1)
for r in out:
    print(f"{r['plan'].split('/')[-1][:40]:40} {r['base'][:8]}..{r['end'][:8]} n={r['n_commits']:3} linked={r['n_linked']:3} unl={r['n_unlinked']:3} src={r['src_lines']:6} tests={r['test_files']:3} other={r['other_dirs']}")
