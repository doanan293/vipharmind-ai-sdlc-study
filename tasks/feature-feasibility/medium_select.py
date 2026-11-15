"""Apply the amended medium-tier rule (prereg-v1.1 draft, 2026-11-15) to every window of
medium_candidates.json: eligibility (criteria 1-9), layer, then the greedy two-pass selection.

Inputs: <names.json> from medium_names.py and <analysis.json> from medium_coverage.py analyse.
Without --write it prints one line per window; with --write it records commit_types, layer_lines,
layer, required_names, integration_coverage, eligible, reason, selected, selection_pass and selected_as
in medium_candidates.json (the first run moves the earlier curated verdict to previous_selection).

Usage: python medium_select.py <names.json> <analysis.json> [--write]"""
import collections, json, os, re, subprocess, sys, tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE.parent
REPO = os.environ.get("VIPHARMIND_REPO", "/home/andv/personal/vipharmind")
P = HERE / "medium_candidates.json"
LAYERS = ("domain", "application", "infrastructure", "api")
TYPE = re.compile(r"^(\w+)(\(.+\))?!?:")
EXCLUDED_TYPES = {"test", "refactor", "chore", "docs"}


def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, check=True).stdout


def task_commits():
    out = {}
    for f in sorted(TASKS.glob("*/task.toml")):
        t = tomllib.load(open(f, "rb"))
        if t.get("kind") == "range":
            out[t["id"]] = set(git("rev-list", "--first-parent", f"{t['base']}..{t['commit']}").split())
        else:
            out[t["id"]] = {t["commit"]}
    return out


def static(c, taskc):
    shas = list(reversed(git("rev-list", "--first-parent", f"{c['base']}..{c['end']}").split()))
    types = [TYPE.match(git("log", "-1", "--format=%s", s)).group(1) for s in shas]
    layer, other, src = collections.Counter(), collections.Counter(), 0
    for ln in git("diff", "--numstat", c["base"], c["end"]).splitlines():
        a, b, p = ln.split("\t")
        n = (int(a) if a != "-" else 0) + (int(b) if b != "-" else 0)
        if not p.startswith("backend/"):
            other[p.split("/")[0]] += n
        if p.startswith("backend/src/"):
            src += n
            parts = p.split("/")
            layer[parts[3] if len(parts) > 4 and parts[3] in LAYERS else "other:" + parts[3]] += n
    overlap = sorted(k for k, v in taskc.items() if v & set(shas))
    return dict(shas=shas, types=types, overlap=overlap, layer_lines=dict(layer), other=dict(other), src=src)


def layer_of(layer_lines):
    four = {k: v for k, v in layer_lines.items() if k in LAYERS}
    return max(four, key=lambda k: (four[k], -LAYERS.index(k))) if four else None


def main():
    nm = json.load(open(sys.argv[1]))
    cov = json.load(open(sys.argv[2]))
    write = "--write" in sys.argv
    data = json.load(open(P))
    taskc = task_commits()
    rows = []
    for c in data["candidates"]:
        wid, g = c["id"], c.get("grading") or {}
        s = static(c, taskc)
        fails = []
        if not c["plan_group"].startswith("F"):
            fails.append("not inside one of the 16 sub-ranges of ranges.json (not a prereg candidate)")
        bad = sorted({t for t in s["types"] if t in EXCLUDED_TYPES})
        if bad:
            fails.append("contains a " + "/".join(bad) + " commit")
        if s["overlap"]:
            fails.append("shares a commit with " + ", ".join(s["overlap"]))
        if s["other"]:
            fails.append("changes files outside backend/ (" + ", ".join(sorted(s["other"])) + ")")
        if not 300 <= s["src"] <= 700:
            fails.append(f"src lines {s['src']} outside 300-700")
        if g:
            if not g.get("original_patch_clean"):
                fails.append("original patch does not grade clean")
            nf = g.get("hidden_failing_at_base") or 0
            if nf < 5:
                fails.append(f"only {nf} graded hidden tests fail at base (< 5)")
        elif not fails:
            raise SystemExit(f"{wid}: not graded but passes the static criteria")
        share = None
        if wid in cov:
            share = cov[wid]["total"]["share_int_only"]
            if share is not None and share > 0.5:
                fails.append(f"{share:.0%} of exercised src lines only exercised by integration tests (> 50%)")
        elif not fails:
            raise SystemExit(f"{wid}: passes so far but has no coverage measurement")
        names = nm[wid]["count"]
        if names > 20:
            fails.append(f"{names} required names (> 20)")
        rows.append(dict(c=c, wid=wid, s=s, eligible=not fails, fails=fails, names=names, src=s["src"],
                         end=c["end"], layer=layer_of(s["layer_lines"]), shas=set(s["shas"]), share=share))

    key = lambda r: (r["names"], r["src"], r["end"])
    elig = [r for r in rows if r["eligible"]]
    chosen, used = [], set()
    for layer in LAYERS:  # pass 1: one per layer
        pool = sorted((r for r in elig if r["layer"] == layer and not r["shas"] & used), key=key)
        if pool and len(chosen) < 5:
            r = pool[0]
            r["pass"] = 1
            chosen.append(r)
            used |= r["shas"]
    for r in sorted(elig, key=key):  # pass 2: fill from all eligible windows
        if len(chosen) >= 5:
            break
        if r in chosen or r["shas"] & used:
            continue
        r["pass"] = 2
        chosen.append(r)
        used |= r["shas"]
    for i, r in enumerate(chosen, 1):
        r["mid"] = f"m{i:02d}"

    for r in rows:
        tag = f"SEL {r['mid']} p{r['pass']}" if r in chosen else ("eligible" if r["eligible"] else "")
        print(f"{tag:12} {r['wid']:24} {r['layer'] or '-':14} {r['src']:4} names={r['names']:2} "
              f"int={r['share']}  {'; '.join(r['fails'])}")

    if write:
        for r in rows:
            c = r["c"]
            if "previous_selection" not in c:
                c["previous_selection"] = {k: c.pop(k) for k in ("verdict", "reason", "selected_as") if k in c}
            c["commit_types"] = r["s"]["types"]
            c["layer_lines"] = r["s"]["layer_lines"]
            c["layer"] = r["layer"]
            c["required_names"] = dict(count=nm[r["wid"]]["count"],
                                       **{k: v for k, v in nm[r["wid"]].items() if k != "count"})
            if r["wid"] in cov:
                c["integration_coverage"] = cov[r["wid"]]["total"] | {"files": cov[r["wid"]]["files"]}
            c["eligible"] = r["eligible"]
            c["reason"] = "eligible" if r["eligible"] else "; ".join(r["fails"])
            c["selected"] = r in chosen
            c["selection_pass"] = r.get("pass")
            c["selected_as"] = r.get("mid")
            if r["eligible"] and r not in chosen:
                blockers = [x["mid"] for x in chosen if x["shas"] & r["shas"]]
                c["reason"] = ("eligible; not selected: shares a commit with " + ", ".join(blockers)) if blockers \
                    else "eligible; not selected: ranked after the selected windows"
        json.dump(data, open(P, "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
