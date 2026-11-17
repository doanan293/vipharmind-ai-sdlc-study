"""Build the rater packets of prereg-v1 9.8 and An's passing-sample packet (9.10).

usage: python build_packets.py ANALYSIS_DIR TASKS_DIR OUT_DIR RESULTS_ROOT [RESULTS_ROOT ...]

Rater packet, per unit id: prompt.md (task text only, no arm instructions), patch.diff without
docs/design.md and docs/plan.md, test-log.txt (hidden-test result, failures, regressions). Identical
packets go to loi/ and bao/, each with its own blank sheet. An's packet: the 20 passing runs with
the full patch and grade, named by unit (An is not blind; 9.10 needs no blinding).
"""

import csv
import json
import re
import shutil
import sys
from pathlib import Path

PROCESS = ("docs/design.md", "docs/plan.md", "backend/docs/design.md", "backend/docs/plan.md")


def strip_process(diff: str) -> str:
    parts = re.split(r"(?m)^(?=diff --git )", diff)
    keep = [p for p in parts if not any(f" b/{x}" in p.split("\n", 1)[0] for x in PROCESS)]
    return "".join(keep)


def test_log(grade: dict, timed_out: bool) -> str:
    lines = [f"hidden tests passed: {grade['hidden_passed']}/{grade['hidden_total']}"]
    if timed_out:
        lines.append("NOTE: the agent hit the time limit (het_gio)")
    for name, msg in (grade.get("hidden_failed") or {}).items():
        lines += ["", f"FAILED {name}", str(msg).rstrip()]
    regs = grade.get("regressions") or []
    lines += ["", f"old tests broken (regressions): {len(regs)}"] + [f"  {r}" for r in regs]
    if grade.get("grading_notes"):
        lines += ["", "grader notes:"] + [f"  {n}" for n in grade["grading_notes"]]
    return "\n".join(lines) + "\n"


def find(unit: str, roots: list[Path]) -> Path:
    hits = [r / unit for r in roots if (r / unit / "grade.json").is_file()]
    if len(hits) != 1:
        raise SystemExit(f"{unit}: found {len(hits)} copies")
    return hits[0]


def main() -> None:
    analysis, tasks, out = map(Path, sys.argv[1:4])
    roots = [Path(p) for p in sys.argv[4:]]
    if out.exists():
        raise SystemExit(f"{out} exists; remove it first")
    key = list(csv.DictReader((analysis / "labeling/key-PRIVATE.csv").open()))
    for rater in ("loi", "bao"):
        base = out / rater
        for row in key:
            src = find(row["unit"], roots)
            d = base / row["unit_id"]
            d.mkdir(parents=True)
            shutil.copy(tasks / row["task_id"] / "prompt.md", d / "prompt.md")
            (d / "patch.diff").write_text(strip_process((src / "patch.diff").read_text()))
            grade = json.loads((src / "grade.json").read_text())
            (d / "test-log.txt").write_text(test_log(grade, row["timed_out"] == "True"))
        shutil.copy(analysis / "labeling/sheet-template.csv", base / f"sheet-{rater}.csv")
        shutil.copy(tasks.parents[1] / "docs/prereg/labeling-guide.md", base / "HUONG-DAN.md")
    an = out / "an-passing-sample"
    for row in csv.DictReader((analysis / "passing_sample.csv").open()):
        src = find(row["unit"], roots)
        d = an / row["unit"].replace("/", "__")
        d.mkdir(parents=True)
        shutil.copy(tasks / row["task_id"] / "prompt.md", d / "prompt.md")
        shutil.copy(src / "patch.diff", d / "patch.diff")
        shutil.copy(src / "grade.json", d / "grade.json")
    with (an / "sheet-an.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["unit", "really_correct(yes/no)", "note"])
        for row in csv.DictReader((analysis / "passing_sample.csv").open()):
            w.writerow([row["unit"], "", ""])
    print(f"{len(key)} rater units x2, passing sample -> {out}")


if __name__ == "__main__":
    main()
