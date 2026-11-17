"""Step 1b: dense cores of each backend plan, split at natural boundaries to 400-2500 src lines.
Also builds ranges.json = whole-plan ranges + sub-ranges with metrics."""
import json, subprocess, sys
sys.path.insert(0, "/home/andv/personal/vipharmind-ai-sdlc-study/.worktrees/retro/retrospective/src")
from retro.gitlog import _new_path
REPO = "/home/andv/personal/vipharmind-camera-ready"
rows = json.load(open("sequence.json"))
def git(*a): return subprocess.run(["git","-c","core.quotePath=false","-C",REPO,*a],check=True,capture_output=True,text=True).stdout
# (id, plan, first_idx, last_idx, note) -- indices into first-parent order of 3baae61
SUB = [
 ("F01","2026-09-11-pharma-agent-core.md",18,25,"domain layer (kernel, guardrail, retrieval models, AgentRun, skills, prompts)"),
 ("F02","2026-09-11-pharma-agent-core.md",26,32,"LangGraph loop + infra adapters + composition root/CLI"),
 ("F03","2026-09-12-pharma-agent-platform.md",37,48,"conversations, Postgres, ChatService, auth, FastAPI SSE"),
 ("F04","2026-09-12-pharma-agent-extras.md",53,59,"skills repo/service, feedback, tracing, checkpoint cleanup, API"),
 ("F05","2026-09-13-corpus-domain.md",67,74,"knowledge bundle models, IO, section/chunk pipeline"),
 ("F06","2026-09-13-corpus-store-import.md (+corpus-retrieval)",75,81,"corpus schema, snapshot/release, PG repo, Qdrant index, import, publish/rollback"),
 ("F07","2026-09-13-corpus-retrieval.md",82,88,"corpus CLI, retrieval over releases, refactor, audit ids, health"),
 ("F08","2026-09-13-web-api-foundation.md (linked as corpus-retrieval)",100,105,"problem details, cursors, paging, op ids, message ids"),
 ("F09","2026-09-13-web-chat-stream.md",106,112,"AI SDK UIMessage stream, citations persisted, history, citation endpoint"),
 ("F10","2026-09-13-web-auth-e2e.md",113,119,"cookie sessions, CSRF, Google OAuth, cleanup CLI, E2E server"),
 ("F11","2026-09-13-web-*.md (F09+F10)",106,119,"chat stream + auth (merged)"),
 ("F12","2026-10-10-account-flows.md",367,375,"account domain, tables, PG adapters, messages, use cases, FastAPI wiring"),
 ("F13","2026-10-10-product-launch.md",391,395,"access policy, organizations domain/db/infra, create/rename/delete"),
 ("F14","2026-10-10-product-launch.md",396,399,"invitations, audit reads, org API, memberships"),
 ("F15","2026-10-10-product-launch.md",400,404,"user collections, scoped search, collection API"),
 ("F16","2026-10-10-product-launch.md",405,409,"authored documents/glossary, bundle build, publish, API"),
]
def metrics(base, end, first, last):
    ns = {}
    for line in git("diff","--numstat","-M",base,end).splitlines():
        a,d,p = line.split("\t",2); p=_new_path(p)
        ns[p] = (0 if a=="-" else int(a)) + (0 if d=="-" else int(d))
    st = {}
    for line in git("diff","--name-status","-M",base,end).splitlines():
        parts=line.split("\t"); st[parts[-1]]=parts[0][0]
    src = sum(v for p,v in ns.items() if p.startswith("backend/src/"))
    tst = sum(v for p,v in ns.items() if p.startswith("backend/tests/"))
    tfiles = [p for p in ns if p.startswith("backend/tests/")]
    hidden = sorted(p for p in tfiles if p.split("/")[-1].startswith("test_") and p.endswith(".py") and st.get(p)!="D")
    support = sorted(p for p in tfiles if p not in hidden)
    other = {}
    for p,v in ns.items():
        if p.startswith(("backend/src/","backend/tests/")): continue
        k = "migrations" if ("migration" in p or "alembic" in p) else ("backend/"+p.split("/")[1] if p.startswith("backend/") else p.split("/")[0])
        other[k]=other.get(k,0)+v
    return dict(src_lines=src, test_lines=tst, hidden_tests=hidden, support_files=support,
        support_status={p:st.get(p,"?") for p in support}, other_dirs=other,
        frontend="frontend" in other, pharma_lab=any(k.startswith(("pharma-lab","seed-pipeline","corpus-pipeline")) for k in other),
        migrations=any(k=="migrations" or "migration" in k for k in other) or any("migration" in p for p in ns if p.startswith("backend/src/")))
PLANS = {"F06":["2026-09-13-corpus-store-import","2026-09-13-corpus-retrieval"],
 "F08":["2026-09-13-web-api-foundation","2026-09-13-corpus-retrieval"],
 "F09":["2026-09-13-web-chat-stream","2026-09-13-corpus-retrieval"],
 "F10":["2026-09-13-web-auth-e2e","2026-09-13-corpus-retrieval"],
 "F11":["2026-09-13-web-chat-stream","2026-09-13-web-auth-e2e","2026-09-13-corpus-retrieval"]}
out=[]
for rid,plan,f,l,note in SUB:
    base, end = rows[f-1]["sha"], rows[l]["sha"]
    rng = rows[f:l+1]
    stems = PLANS.get(rid, [plan.split(" ")[0][:-3]])
    linked = [r for r in rng if r["plan"] and r["plan"] in stems]
    m = metrics(base,end,f,l)
    out.append(dict(id=rid, kind="sub-range", plan=plan, note=note, base=base, end=end, first_idx=f, last_idx=l,
        n_commits=len(rng), n_feat=sum(r["type"]=="feat" for r in rng),
        n_not_linked=len(rng)-len(linked), not_linked=[f"{r['sha'][:8]} {r['subj'][:60]}" for r in rng if r not in linked],
        commits=[f"{r['sha'][:8]} {r['subj'][:70]}" for r in rng], **m))
whole = json.load(open("whole_ranges.json"))
for w in whole:
    w.pop("subjects",None); w["kind"]="whole-plan"
json.dump(dict(pinned="3baae61d764f6d83f7205d0d4d97ee52dd8e0dbe", whole_plan=whole, sub_ranges=out), open("ranges.json","w"), indent=1)
for r in out:
    print(f"{r['id']} {r['base'][:8]}..{r['end'][:8]} n={r['n_commits']:2} unl={r['n_not_linked']} src={r['src_lines']:5} tst={r['test_lines']:5} hid={len(r['hidden_tests']):2} sup={len(r['support_files'])} {r['support_files']} other={r['other_dirs']} mig={r['migrations']}")
