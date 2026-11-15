"""Per range: non-integration hidden tests collected at `end`, by layer (api/application/domain/infrastructure/other),
and hidden files fully deselected (integration-only)."""
import json, sys, os
rs = {r["id"]: r for r in json.load(open("ranges.json"))["sub_ranges"]}
res_dir = sys.argv[1] if len(sys.argv) > 1 else "results"
out = {}
for rid, r in rs.items():
    p = f"{res_dir}/{rid}.json"
    if not os.path.exists(p): continue
    end = json.load(open(p))["raw"]["end"]["outcomes"]
    hidden = {h.removeprefix("backend/") for h in r["hidden_tests"]}
    by, files_seen = {}, set()
    for k in end:
        f = k.split("::")[0]
        if f in hidden:
            files_seen.add(f)
            layer = f.split("/")[1] if f.count("/") > 1 else "top"
            by[layer] = by.get(layer, 0) + 1
    out[rid] = dict(hidden_collected=sum(by.values()), by_layer=by, integration_only_files=sorted(hidden - files_seen))
    print(rid, out[rid]["hidden_collected"], by, "integration-only:", len(out[rid]["integration_only_files"]))
json.dump(out, open(f"{res_dir}_layers.json", "w"), indent=1)
