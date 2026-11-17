"""Medium-tier criterion 9 (prereg-v1.1 draft). Mechanical required-name count of a window (base..end), over its hidden test files and restored
support files at `end` (graded and integration-marked alike). A name counts when the tests need it and
it does not exist at `base`. Usage: python medium_names.py <out.json> [<id> ...]. Fields, keyword arguments, methods of the new classes themselves and
free-text strings are not counted.
 N1 symbols: (module, name) imported from pharma_agent.* (or a pharma_agent module imported whole)
    that is not a top-level definition / submodule at base.
 N3 routes:  (file, router, HTTP method, path) route decorators in backend/src at end not present at base.
 N4 cli:     (file, command) functions decorated with `.command(...)` in backend/src at end not at base.
 N5 codes:   UPPER_SNAKE string literals (>=2 parts) used in test/support files that occur in backend/src
    at end and nowhere in backend/src at base (error codes, audit actions), minus names already in N1.
 N6 members: `X.MEMBER` attribute accesses in test/support files where X is imported from pharma_agent,
    exists at base, and MEMBER (UPPER_SNAKE) is new on X (new enum members such as event types).
 N7 port methods: public method names of classes defined in the test/support files (fakes) that
    backend/src defines (`def name`) at end but not at base: port methods the agent must add and that
    the restored fakes already implement."""
import ast, json, os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = os.environ.get("VIPHARMIND_REPO", "/home/andv/personal/vipharmind")
def git(*a):
    r = subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True); return r.stdout if r.returncode == 0 else None
def mod_src(sha, mod):
    p = "backend/src/" + mod.replace(".", "/")
    for c in (p + ".py", p + "/__init__.py"):
        s = git("show", f"{sha}:{c}")
        if s is not None: return s, c
    return None, None
def toplevel(src):
    names = set()
    for n in ast.parse(src).body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)): names.add(n.name)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for e in ast.walk(t):
                    if isinstance(e, ast.Name): names.add(e.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name): names.add(n.target.id)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names: names.add((a.asname or a.name).split(".")[0])
        elif type(n).__name__ == "TypeAlias": names.add(n.name.id)
        elif isinstance(n, ast.If):  # TYPE_CHECKING blocks etc.
            for m in n.body:
                if isinstance(m, (ast.Import, ast.ImportFrom)):
                    for a in m.names: names.add((a.asname or a.name).split(".")[0])
    return names
def exists(sha, mod, name):
    s, _ = mod_src(sha, mod)
    if s is not None and name in toplevel(s): return True
    return mod_src(sha, f"{mod}.{name}")[0] is not None
def class_members(sha, mod, cls):
    s, _ = mod_src(sha, mod)
    if s is None: return set()
    for n in ast.parse(s).body:
        if isinstance(n, ast.ClassDef) and n.name == cls:
            out = set()
            for b in n.body:
                if isinstance(b, ast.Assign):
                    out |= {t.id for t in b.targets if isinstance(t, ast.Name)}
                elif isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name): out.add(b.target.id)
                elif isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)): out.add(b.name)
            return out
    return set()
def count(base, end, test_files):
    srcs = {f: git("show", f"{end}:{f}") for f in test_files}
    srcs = {f: s for f, s in srcs.items() if s is not None and f.endswith(".py")}
    n1, n6, strings = set(), set(), set()
    for f, s in srcs.items():
        tree = ast.parse(s); imported = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("pharma_agent"):
                for a in node.names:
                    imported[a.asname or a.name] = (node.module, a.name)
                    if not exists(base, node.module, a.name): n1.add(f"{node.module}.{a.name}")
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.startswith("pharma_agent") and mod_src(base, a.name)[0] is None: n1.add(a.name)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings |= set(re.findall(r"\b[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+\b", node.value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in imported \
                    and re.fullmatch(r"[A-Z][A-Z0-9_]*", node.attr):
                mod, cls = imported[node.value.id]
                if exists(base, mod, cls) and f"{mod}.{cls}" not in n1:
                    if node.attr not in class_members(base, mod, cls) and node.attr in class_members(end, mod, cls):
                        n6.add(f"{cls}.{node.attr}")
    diff_files = git("diff", "--name-only", base, end, "--", "backend/src").split()
    def deco(sha, p):
        src = git("show", f"{sha}:{p}")
        if src is None: return set(), set()
        routes = {(p, m.group(1), m.group(2), m.group(3)) for m in re.finditer(r'@(\w+)\.(get|post|put|patch|delete|api_route)\(\s*"([^"]*)"', src)}
        cmds = set()
        for n in ast.walk(ast.parse(src)):
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for d in n.decorator_list:
                    if isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute) and d.func.attr == "command":
                        name = d.args[0].value if d.args and isinstance(d.args[0], ast.Constant) else n.name
                        cmds.add((p, getattr(d.func.value, "id", "?"), name))
        return routes, cmds
    n3, n4 = set(), set()
    for p in diff_files:
        if not p.endswith(".py"): continue
        re_, ce = deco(end, p); rb, cb = deco(base, p)
        n3 |= re_ - rb; n4 |= ce - cb
    n3 = sorted(f"{m.upper()} {path} ({f.split('/')[-1]})" for f, r, m, path in n3)
    n4 = sorted(f"{name} ({f.split('/')[-1]})" for f, g, name in n4)
    def src_has(sha, tok):
        return bool(git("grep", "-q", "-w", tok, sha, "--", "backend/src") is not None and subprocess.run(["git", "-C", REPO, "grep", "-q", "-w", tok, sha, "--", "backend/src"]).returncode == 0)
    n5 = {t for t in strings if src_has(end, t) and not src_has(base, t)} - {x.rsplit('.', 1)[-1] for x in n1}
    meths = set()
    for f, src in srcs.items():
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ClassDef):
                meths |= {b.name for b in node.body if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)) and not b.name.startswith("_") and not b.name.startswith("test")}
    def src_defines(sha, m):
        return subprocess.run(["git", "-C", REPO, "grep", "-q", "-E", rf"def {m}\b", sha, "--", "backend/src"]).returncode == 0
    n7 = {m for m in meths if src_defines(end, m) and not src_defines(base, m)}
    parts = dict(symbols=sorted(n1), routes=n3, cli=n4, codes=sorted(n5), members=sorted(n6), port_methods=sorted(n7))
    return sum(len(v) for v in parts.values()), parts
if __name__ == "__main__":
    C = json.load(open(HERE / "medium_candidates.json"))["candidates"]
    out_path = Path(sys.argv[1])
    want = set(sys.argv[2:])
    out = {}
    for c in C:
        if want and c["id"] not in want: continue
        n, parts = count(c["base"], c["end"], c["hidden_tests"] + c["support_files"])
        out[c["id"]] = dict(count=n, **parts)
        print(c["id"], n, {k: len(v) for k, v in parts.items()})
    json.dump(out, open(out_path, "w"), indent=1)
