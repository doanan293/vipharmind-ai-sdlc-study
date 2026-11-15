"""Step 3 (static): what hidden tests import, and which of those names do not exist at base.
new_src_symbols = (module, name) imported from pharma_agent by hidden tests that is absent at base
 -> the agent must create exactly this module path + name; a prose prompt has to name it.
support_missing = names imported from tests.* helper modules that are absent at base
 -> hidden tests cannot run without the support files from `end`."""
import ast, json, subprocess, sys
REPO = "/home/andv/personal/vipharmind-camera-ready"
def show(sha, path):
    p = subprocess.run(["git", "-C", REPO, "show", f"{sha}:{path}"], capture_output=True, text=True)
    return p.stdout if p.returncode == 0 else None
def mod_path(mod):
    rel = mod.replace(".", "/")
    if mod.startswith("pharma_agent"): return [f"backend/src/{rel}.py", f"backend/src/{rel}/__init__.py"]
    return [f"backend/{rel}.py", f"backend/{rel}/__init__.py"]
_cache = {}
def defined(sha, mod):
    key = (sha, mod)
    if key in _cache: return _cache[key]
    names = None
    for p in mod_path(mod):
        src = show(sha, p)
        if src is None: continue
        names = set()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): names.add(node.name)
            elif isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name): names.add(t.id)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name): names.add(node.target.id)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for a in node.names: names.add((a.asname or a.name).split(".")[0])
        break
    _cache[key] = names
    return names
def is_pkg(sha, mod):
    return any(show(sha, f"backend/src/{mod.replace('.', '/')}/__init__.py" if mod.startswith("pharma_agent") else f"backend/{mod.replace('.', '/')}/__init__.py") is not None for _ in [0])
def analyse(r, files_key="hidden_tests"):
    base, end = r["base"], r["end"]
    imports = set()
    for f in r[files_key]:
        if not f.endswith(".py"): continue
        src = show(end, f)
        if src is None: continue
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                for a in node.names: imports.add((node.module, a.name))
            elif isinstance(node, ast.Import):
                for a in node.names: imports.add((a.name, None))
    new_src, old_src, support_missing, new_modules = set(), set(), set(), set()
    for mod, name in imports:
        top = mod.split(".")[0]
        if top not in ("pharma_agent", "tests"): continue
        names = defined(base, mod)
        if names is None:
            # maybe `from pkg import submodule`
            if top == "pharma_agent": new_modules.add(mod)
            target = new_src if top == "pharma_agent" else support_missing
            target.add(f"{mod}:{name}")
            continue
        if name is None: continue
        if name in names or defined(base, f"{mod}.{name}") is not None:
            if top == "pharma_agent": old_src.add(f"{mod}:{name}")
            continue
        (new_src if top == "pharma_agent" else support_missing).add(f"{mod}:{name}")
    priv = sorted(s for s in new_src if s.split(":")[1].startswith("_"))
    return dict(id=r["id"], n_new_src_symbols=len(new_src), n_new_src_modules=len(new_modules), n_private=len(priv),
                n_old_src_symbols=len(old_src), n_support_missing=len(support_missing),
                new_src_symbols=sorted(new_src), new_src_modules=sorted(new_modules), private=priv, support_missing=sorted(support_missing))
rs = json.load(open("ranges.json"))["sub_ranges"]
out = []
for r in rs:
    o = analyse(r); s2 = analyse(r, "support_files")
    o["support_new_src_symbols"] = sorted(set(s2["new_src_symbols"]) - set(o["new_src_symbols"]))
    o["n_support_new_src_symbols"] = len(o["support_new_src_symbols"])
    o["n_union_new_src_symbols"] = o["n_new_src_symbols"] + o["n_support_new_src_symbols"]
    out.append(o)
json.dump(out, open("coupling.json", "w"), indent=1)
for o in out:
    print(o["id"], "new_src_syms", o["n_new_src_symbols"], "new_modules", o["n_new_src_modules"], "private", o["n_private"], "old_syms", o["n_old_src_symbols"], "support_missing", o["n_support_missing"], o["support_missing"][:3], "support_src_new", o["n_support_new_src_symbols"], "union", o["n_union_new_src_symbols"])
