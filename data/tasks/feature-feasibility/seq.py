"""Print first-parent sequence with plan assignment (latest-added linking plan) and src/test lines."""
import sys, json
sys.path.insert(0, "/home/andv/personal/vipharmind-ai-sdlc-study-retro/retrospective/src")
from pathlib import Path
from retro.gitlog import load_commits, git
from retro.specplans import load_spec_plan_files, has_preceding_plan
REPO = Path("/home/andv/personal/vipharmind-camera-ready"); PIN = "3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe"
order = git(REPO, "rev-list", "--first-parent", "--reverse", PIN).split()
cs = {c.sha: c for c in load_commits(REPO, [PIN])}
plans = [d for d in load_spec_plan_files(REPO, [PIN]) if d.kind == "plan"]
rows = []
for i, s in enumerate(order):
    c = cs[s]
    p = has_preceding_plan(c, plans) if c.type == "feat" else None
    src = sum(f.added + f.deleted for f in c.files if f.path.startswith("backend/src/"))
    tst = sum(f.added + f.deleted for f in c.files if f.path.startswith("backend/tests/"))
    oth = sorted({f.path.split("/")[0] if not f.path.startswith("backend/") else "backend/" + f.path.split("/")[1] for f in c.files} - {"backend/src", "backend/tests"})
    rows.append(dict(i=i, sha=s, date=c.date.isoformat()[:16], type=c.type, plan=(p.path.split("/")[-1][:-3] if p else ""), src=src, tst=tst, other=oth, subj=c.subject))
json.dump(rows, open("sequence.json", "w"), indent=0)
for r in rows:
    if r["src"] or r["tst"] or r["plan"]:
        print(f"{r['i']:3} {r['sha'][:8]} {r['date'][5:]} {r['type'][:4]:4} {r['plan'][11:34]:23} s{r['src']:5} t{r['tst']:5} {','.join(r['other'])[:30]:30} {r['subj'][:60]}")
