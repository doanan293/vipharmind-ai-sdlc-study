"""Merge metrics, test results, coupling and verdict into ranges.json; print table rows."""
import json, os
d = json.load(open("ranges.json"))
cp = {o["id"]: o for o in json.load(open("coupling.json"))}
fk = json.load(open("fakes_contract.json"))
lay = json.load(open("results_layers.json"))
VERDICT = {
 "F08": "viable", "F14": "viable", "F15": "viable", "F09": "viable", "F04": "viable",
 "F07": "borderline", "F03": "borderline", "F11": "borderline", "F02": "borderline",
 "F01": "not-viable", "F05": "not-viable", "F06": "not-viable", "F10": "not-viable (too small)",
 "F12": "not-viable", "F13": "not-viable", "F16": "not-viable",
}
DEPS = {"F03", "F04", "F10", "F12", "F16"}
for r in d["sub_ranges"]:
    rid = r["id"]
    src = "results_deps" if rid in DEPS else "results"
    a = json.load(open(f"{src}/{rid}.json"))["analysis"]
    r["grading"] = dict(results_from=src, deps_overlaid=rid in DEPS,
        a_end_total=a["end_total"], a_end_failing=len(a["end_bad"]),
        b_hidden_total=a["hs_hidden_total"], b_hidden_failing=a["hs_hidden_bad"], b_hidden_collect_error_files=len(a["hs_hidden_collect_err_files"]),
        b_old_total=a["hs_old_total"], b_old_newly_failing=len(a["hs_old_bad"]),
        c_hidden_total=a["h_hidden_total"], c_hidden_failing=a["h_hidden_bad"], c_hidden_collect_error_files=len(a["h_hidden_collect_err_files"]),
        c_support_import_missing_static=cp[rid]["n_support_missing"],
        hidden_collected_at_end=lay[rid]["hidden_collected"], hidden_by_layer=lay[rid]["by_layer"],
        integration_only_hidden_files=lay[rid]["integration_only_files"], walls_s=a["walls"])
    r["coupling"] = dict(new_src_symbols=cp[rid]["n_new_src_symbols"], new_src_modules=cp[rid]["n_new_src_modules"],
        support_new_src_symbols=cp[rid]["n_support_new_src_symbols"], private_symbols=cp[rid]["n_private"],
        new_fake_methods=fk[rid]["n"], prompt_contract_estimate=cp[rid]["n_union_new_src_symbols"] + fk[rid]["n"])
    r["verdict"] = VERDICT[rid]
json.dump(d, open("ranges.json", "w"), indent=1)
for r in d["sub_ranges"]:
    g, c = r["grading"], r["coupling"]
    print(f"| {r['id']} | `{r['base'][:10]}` | `{r['end'][:10]}` | {r['n_commits']} | {r['n_not_linked']} | {r['src_lines']} | {g['hidden_collected_at_end']} | {g['a_end_total']}/{g['a_end_failing']} | {g['b_hidden_failing']}/{g['b_hidden_total']} | {g['b_old_newly_failing']} | {g['c_support_import_missing_static']} | {c['new_src_symbols']}+{c['support_new_src_symbols']} ({c['new_src_modules']} mod) | {c['new_fake_methods']} | {c['prompt_contract_estimate']} | {r['verdict']} |")
