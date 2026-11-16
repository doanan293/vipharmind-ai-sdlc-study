"""prereg-v1.2 E2 judge check (a): draw the 24 brief units Lợi and Bảo grade by hand, build their
blinded packets, and later compute the agreement.

    uv run python scripts/draw_human_check.py draw --brief BRIEF_ROOT [--force --out DIR --key CSV]
    uv run python scripts/draw_human_check.py kappa --loi sheet-loi.csv --bao sheet-bao.csv \
        [--key CSV] [--out JSON]

`draw` refuses unless every one of the 4 x 23 x 2 x 3 = 552 brief units is finished (graded, or
excluded after its system-error reruns). `--force` skips that check for testing only, and then
needs an explicit --out and --key that are not the real locations. An existing packet directory
or key is never overwritten.

Packet, per unit code (identical for loi/ and bao/): brief.md (the task text the agent got),
change.diff (the saved patch without docs/design.md and docs/plan.md), checklist.md (without the
[exact] tags, as the judge sees it); per rater: sheet-<rater>.csv (unit_code, item_n, verdict
met/not_met/unclear, note) and HUONG-DAN.md with the judge's criteria. The private key (unit code
-> unit) goes to results/analysis/e2/, never into the packets.
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_packets import strip_process

from sdlc_analysis import e2, humancheck
from sdlc_analysis.bootstrap import SEED_DEFAULT

REPO = e2.REPO
PACKETS = REPO / "results" / "packets" / "human-check"
KEY = REPO / "results" / "analysis" / "e2" / "human-check-key-PRIVATE.csv"
AGREEMENT = REPO / "results" / "analysis" / "e2" / "human-check-agreement.json"
RATERS = ("loi", "bao")
EXPECTED_BRIEF = 552
ITEM_RE = re.compile(r"^\s*(\d+)\.\s+\S", re.MULTILINE)
EXACT = "[exact]"


def shown_checklist(text: str) -> str:
    """The checklist as the judge sees it (harness judge_prompt): [exact] tags removed."""
    return "\n".join(
        line.rstrip()[: -len(EXACT)].rstrip() if line.rstrip().endswith(EXACT) else line
        for line in text.strip().splitlines()
    ) + "\n"


def readme(judge_md: str) -> str:
    crit = judge_md.split("How to judge:", 1)[-1].split("Answer with JSON", 1)[0].strip()
    return (
        "# Chấm tay danh sách hành vi (E2, prereg-v1.2)\n\n"
        "Mỗi thư mục là một lượt, mang mã ngẫu nhiên. Trong đó: `brief.md` (đề agent nhận), "
        "`change.diff` (thay đổi của agent so với mã khởi đầu, đã bỏ docs/design.md và "
        "docs/plan.md), `checklist.md` (các mục hành vi).\n\n"
        "Với mỗi mục, ghi vào bảng `sheet-<tên>.csv` cột `verdict` một trong: `met`, `not_met`, "
        "`unclear`; cột `note` ghi lý do ngắn. Chấm độc lập, không trao đổi với người chấm kia. "
        "Nếu đoán được cách làm (spec/vibe), ghi `lộ cách làm` vào note.\n\n"
        "Tiêu chí (giống hệt người chấm máy, `prompts/judge.md`):\n\n" + crit + "\n"
    )


def cmd_draw(a) -> int:
    if a.force:
        if a.out is None or a.key is None:
            raise SystemExit("--force needs an explicit --out and --key (a scratch location)")
        if a.out.resolve() == PACKETS.resolve() or a.key.resolve() == KEY.resolve():
            raise SystemExit("--force may not write to the real packet or key location")
    out, key_path = a.out or PACKETS, a.key or KEY
    for p in (out, key_path):
        if p.exists():
            raise SystemExit(f"{p} exists; the draw is made once")
    cohorts = [c for c in a.cohorts.split(",") if c]
    tasks, runs = e2.load_e2([], a.brief, a.tasks)
    runs = runs[runs["cohort"].isin(cohorts) & (runs["rep"] <= a.reps)]
    cov = e2.coverage(runs, tasks, cohorts, a.reps)
    expected = len(tasks) * 2 * a.reps * len(cohorts)
    problems = humancheck.finished_check(cov, EXPECTED_BRIEF)
    if expected != EXPECTED_BRIEF:
        problems.append(f"design gives {expected} units, prereg-v1.2 says {EXPECTED_BRIEF}")
    if problems and not a.force:
        raise SystemExit("not drawing yet: " + "; ".join(problems))
    valid = runs[runs["valid"].astype(bool)]
    key = humancheck.draw(valid, cohorts, a.seed)
    n_items = {}
    for t in key["task_id"].unique():
        n_items[t] = len(ITEM_RE.findall((a.tasks / t / "checklist.md").read_text()))
    judge_md = (REPO / "prompts" / "judge.md").read_text()
    for rater in RATERS:
        base = out / rater
        for r in key.to_dict("records"):
            d = base / r["unit_code"]
            d.mkdir(parents=True)
            shutil.copy(a.tasks / r["task_id"] / "brief.md", d / "brief.md")
            patch = (Path(r["root"]) / r["unit"] / "patch.diff").read_text(errors="replace")
            (d / "change.diff").write_text(strip_process(patch))
            (d / "checklist.md").write_text(
                shown_checklist((a.tasks / r["task_id"] / "checklist.md").read_text()))
        humancheck.blank_sheet(key, n_items).to_csv(base / f"sheet-{rater}.csv", index=False)
        (base / "HUONG-DAN.md").write_text(readme(judge_md))
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key.to_csv(key_path, index=False)
    print(f"{len(key)} units x {len(RATERS)} raters -> {out}; key -> {key_path}"
          + (" (FORCED: brief condition not finished)" if problems else ""))
    return 0


def cmd_kappa(a) -> int:
    import pandas as pd

    key = pd.read_csv(a.key, dtype={"rep": int})
    sheets = {"loi": humancheck.read_sheet(a.loi), "bao": humancheck.read_sheet(a.bao)}
    judge = humancheck.judge_sheet(key)
    rep = humancheck.agreement_report(sheets, judge)
    rep["units_without_judge"] = sorted(set(key["unit_code"]) - set(judge["unit_code"]))
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n")
    print(f"agreement -> {a.out}")
    return 0


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draw")
    d.add_argument("--brief", type=Path, nargs="+", required=True)
    d.add_argument("--tasks", type=Path, default=REPO / "tasks")
    d.add_argument("--out", type=Path, default=None)
    d.add_argument("--key", type=Path, default=None)
    d.add_argument("--seed", type=int, default=SEED_DEFAULT)
    d.add_argument("--cohorts", default=",".join(e2.E2_COHORTS))
    d.add_argument("--reps", type=int, default=3)
    d.add_argument("--force", action="store_true",
                   help="testing only: draw from unfinished data into a scratch --out/--key")
    k = sub.add_parser("kappa")
    k.add_argument("--key", type=Path, default=KEY)
    k.add_argument("--loi", type=Path, required=True)
    k.add_argument("--bao", type=Path, required=True)
    k.add_argument("--out", type=Path, default=AGREEMENT)
    return p.parse_args(argv)


def main(argv=None) -> int:
    a = parse_args(argv)
    return cmd_draw(a) if a.cmd == "draw" else cmd_kappa(a)


if __name__ == "__main__":
    raise SystemExit(main())
