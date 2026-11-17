"""Support files (fakes/harness) changed in a range: new public class methods + module functions
they define at `end` that did not exist at `base`. Fakes implementing ports means the agent's port
method names/signatures must match these for the restored support files to work."""
import ast, json, subprocess
REPO = "/home/andv/personal/vipharmind-camera-ready"
def show(sha, p):
    r = subprocess.run(["git", "-C", REPO, "show", f"{sha}:{p}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None
def defs(src):
    s = set()
    if src is None: return s
    for n in ast.parse(src).body:
        if isinstance(n, ast.ClassDef):
            for m in n.body:
                if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and not m.name.startswith("_"):
                    s.add(f"{n.name}.{m.name}")
            s.add(n.name)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            s.add(n.name)
    return s
out = {}
for r in json.load(open("ranges.json"))["sub_ranges"]:
    new = {}
    for p in r["support_files"]:
        if not p.endswith(".py"): continue
        d = sorted(defs(show(r["end"], p)) - defs(show(r["base"], p)))
        if d: new[p.removeprefix("backend/tests/")] = d
    out[r["id"]] = dict(n=sum(map(len, new.values())), by_file={k: len(v) for k, v in new.items()}, names=new)
    print(r["id"], out[r["id"]]["n"], out[r["id"]]["by_file"])
json.dump(out, open("fakes_contract.json", "w"), indent=1)
