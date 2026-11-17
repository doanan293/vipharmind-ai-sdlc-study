"""``retro`` command: run the retrospective analysis and write ``out/``."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from retro import DEFAULT_REPO, PINNED_REVS, figures
from retro.gitlog import Commit, git, load_commits
from retro.plan_corpus import write_plan_corpus
from retro.rework import rework_by_stage, rework_rows, rework_summary
from retro.sessions import SESSION_DIRS, collect_sessions, session_rows, tool_rows
from retro.specplans import (
    DocFile,
    has_preceding_plan,
    link_accuracy,
    load_spec_plan_files,
    sample_for_manual_check,
    spec_trace_rows,
)
from retro.stages import commit_stage, lifecycle_tables

DEFAULT_OUT = Path(__file__).resolve().parents[4] / "data" / "retrospective"
LINK_LINE = "- Độ chính xác của quy tắc nối:"
LINK_FIELDS = ["sha", "subject", "rule_plan", "rule_plan_sha", "an_verdict"]
REFERENCE = {
    "commits": 505,
    "first_date": "2026-07-23",
    "last_date": "2026-11-10",
    "feat": 221,
    "docs": 115,
    "fix": 50,
    "refactor": 47,
    "chore": 34,
    "test": 20,
    "spec_plan_files": 43,
    "merge_commits": 0,
    "co_authored_by": 0,
}
STAGE_NAMES = {
    "research_eval": "nghiên cứu và đánh giá",
    "data": "dữ liệu",
    "backend": "mã backend",
    "frontend": "mã frontend",
    "test": "kiểm thử",
    "deploy": "triển khai",
    "docs": "tài liệu",
    "other": "khác",
}


def write_csv(path: Path, rows: list[dict], fields: Sequence[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(fields or (rows[0].keys() if rows else []))
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _pinned_available(repo: Path) -> bool:
    for sha in PINNED_REVS:
        r = subprocess.run(
            ["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"], capture_output=True
        )
        if r.returncode != 0:
            return False
    return True


def resolve_revs(repo: Path, revs: list[str] | None) -> tuple[list[str], bool]:
    """Return (revs, pinned). Without --rev, use the two pinned commits; fall back to HEAD
    only when the repo does not contain them (toy repos in tests)."""
    if revs:
        return revs, sorted(revs) == sorted(PINNED_REVS)
    if _pinned_available(repo):
        return list(PINNED_REVS), True
    print("warning: pinned commits not found in repo, analysing HEAD", file=sys.stderr)
    return ["HEAD"], False


def measured_reference(
    repo: Path, revs: list[str], commits: list[Commit], docs: list[DocFile]
) -> dict:
    types = Counter(c.type for c in commits)
    merges = int(git(repo, "rev-list", "--merges", "--count", *revs).strip() or 0)
    co_authored = len(git(repo, "log", "-i", "--grep=Co-Authored-By", "--format=%H", *revs).split())
    return {
        "commits": len(commits),
        "first_date": commits[0].date.date().isoformat() if commits else "",
        "last_date": commits[-1].date.date().isoformat() if commits else "",
        **{t: types[t] for t in ("feat", "docs", "fix", "refactor", "chore", "test")},
        "spec_plan_files": len(docs),
        "merge_commits": merges,
        "co_authored_by": co_authored,
    }


def _pct(n: int | float, d: int | float) -> str:
    return f"{100 * n / d:.1f}%" if d else "không có"


def _table(headers: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |", "|" + " --- |" * len(headers)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def build_summary(ctx: dict) -> str:
    lines = [
        "# Phân tích hồi cứu ViPharmind: tóm tắt",
        "",
        "Sinh bởi `uv run retro all`. Chỉ có số liệu; không chép mã, plan hay nội dung "
        "nhật ký phiên.",
        "",
        f"Tập commit: hợp của {', '.join(f'`{r}`' for r in ctx['revs'])}, mỗi commit tính một lần.",
        "",
        "## Giá trị đối chiếu",
        "",
    ]
    ref_rows = []
    for key, expected in REFERENCE.items():
        got = ctx["reference"][key]
        if ctx["pinned"]:
            mark = "khớp" if got == expected else "lệch"
        else:
            mark = "không áp dụng"
        ref_rows.append([key, expected, got, mark])
    lines += _table(["chỉ số", "kỳ vọng", "đo được", "kết quả"], ref_rows)

    commits = ctx["commits"]
    total = len(commits)
    lines += ["", "## Bản đồ vòng đời (RQ1)", ""]
    total_lines = sum(r["lines_changed"] for r in ctx["by_stage"])
    lines += _table(
        ["khâu", "commit", "tỉ lệ commit", "dòng thay đổi", "tỉ lệ dòng"],
        [
            [
                STAGE_NAMES[r["stage"]],
                r["commits"],
                _pct(r["commits"], total),
                r["lines_changed"],
                _pct(r["lines_changed"], total_lines),
            ]
            for r in ctx["by_stage"]
        ],
    )
    lines += [
        "",
        "Khâu của một commit là khâu có nhiều dòng thay đổi nhất trong commit đó (luật đường dẫn "
        "ở `src/retro/stages.py`). Hình theo tuần: `figures/lifecycle_by_week.png`.",
    ]

    rework = ctx["rework"]
    with_plan = sum(r["has_plan"] for r in rework)
    docs = ctx["docs"]
    n_spec = sum(d.kind == "spec" for d in docs)
    lines += [
        "",
        "## Dấu vết quy trình theo đặc tả (RQ1)",
        "",
        f"- File spec, plan từng được thêm vào: {len(docs)} ({n_spec} spec, "
        f"{len(docs) - n_spec} plan). Chi tiết: `spec_trace.csv`.",
        f"- Commit `feat` có plan đi trước (quy tắc 14 ngày, plan nêu file mã mà commit chạm): "
        f"{with_plan}/{len(rework)} ({_pct(with_plan, len(rework))}).",
        f"{LINK_LINE} {ctx['link_accuracy']}",
        "",
        "## Mức phải sửa lại (RQ2)",
        "",
        "Số commit `fix` hoặc `refactor` chạm cùng file mã trong 14 ngày sau mỗi commit `feat`.",
        "",
    ]
    group_names = {"with_plan": "có plan đi trước", "without_plan": "không có plan"}
    lines += _table(
        ["nhóm", "số feat", "trung bình", "trung vị", "tỉ lệ feat có sửa lại"],
        [
            [
                group_names[r["group"]],
                r["n_feat"],
                f"{r['mean_rework']:.2f}",
                f"{r['median_rework']:g}",
                _pct(r["share_with_rework"], 1),
            ]
            for r in ctx["rework_summary"]
        ],
    )
    lines += ["", "Theo khâu:", ""]
    lines += _table(
        ["khâu", "số feat", "trung bình", "tỉ lệ feat có sửa lại"],
        [
            [
                STAGE_NAMES[r["stage"]],
                r["n_feat"],
                f"{r['mean_rework']:.2f}",
                _pct(r["share_with_rework"], 1),
            ]
            for r in ctx["rework_by_stage"]
        ],
    )
    lines += ["", "Đây là quan sát, không phải quan hệ nhân quả.", ""]

    stats, dropped = ctx["sessions"], ctx["dropped"]
    main_sessions = [s for s in stats if not s.is_subagent]
    sub_sessions = [s for s in stats if s.is_subagent]
    lines += [
        "## Nhật ký phiên",
        "",
        f"- Phiên chính: {len(main_sessions)}; nhật ký tác tử con: {len(sub_sessions)}.",
        f"- Đã loại: {dropped['after_cutoff']} file có thời điểm đầu tiên sau 2026-11-10, "
        f"{dropped['no_timestamp']} file không có thời điểm.",
        f"- Tin nhắn người dùng (phiên chính): {sum(s.user_messages for s in main_sessions)}; "
        f"lượt trả lời của mô hình: {sum(s.assistant_turns for s in stats)}; "
        f"lời gọi công cụ: {sum(sum(s.tool_calls.values()) for s in stats)}.",
        f"- Số lần người dùng ngắt ngang (`[Request interrupted by user`): "
        f"{sum(s.user_interrupts for s in stats)}. Đây là thước đo thay thế cho "
        '"số lần người sửa hướng" ở bản thiết kế mục 7.1.',
    ]
    top = ctx["tools"][:8]
    if top:
        lines.append(
            "- Công cụ được gọi nhiều nhất: "
            + ", ".join(f"{r['tool']} ({r['calls']})" for r in top)
            + "."
        )
    lines += [
        "- Nhật ký không đầy đủ (An xóa lịch sử chat giữa các phiên); không suy rộng ra "
        "toàn dự án.",
        "",
        "## Giới hạn",
        "",
        "0 commit có Co-Authored-By, nên mức tham gia của AI dựa trên lời khai của tác giả và "
        "phần nhật ký còn lại.",
        "",
    ]
    return "\n".join(lines)


def _link_check_rows(commits: list[Commit], plans: list[DocFile]) -> list[dict]:
    feats = [c for c in commits if c.type == "feat"]
    rows = []
    for c in sample_for_manual_check(feats):
        plan = has_preceding_plan(c, plans)
        rows.append(
            {
                "sha": c.sha,
                "subject": c.subject,
                "rule_plan": plan.path if plan else "",
                "rule_plan_sha": plan.added_sha if plan else "",
                "an_verdict": "",
            }
        )
    return rows


def _accuracy_text(sheet: Path) -> str:
    if not sheet.exists():
        return "chưa chấm"
    correct, graded = link_accuracy(sheet)
    return f"{correct}/{graded}" if graded else "chưa chấm"


def cmd_all(args) -> int:
    repo, out = Path(args.repo), Path(args.out)
    revs, pinned = resolve_revs(repo, args.rev)
    commits = load_commits(repo, revs)
    docs = load_spec_plan_files(repo, revs)
    plans = [d for d in docs if d.kind == "plan"]
    out.mkdir(parents=True, exist_ok=True)

    write_csv(
        out / "commits.csv",
        [
            {
                "sha": c.sha,
                "date": c.date.date().isoformat(),
                "type": c.type,
                "stage": commit_stage(c),
                "files": len(c.files),
                "lines_changed": c.lines_changed,
            }
            for c in commits
        ],
        ["sha", "date", "type", "stage", "files", "lines_changed"],
    )
    tables = lifecycle_tables(commits)
    write_csv(out / "lifecycle_by_stage.csv", tables["by_stage"])
    write_csv(
        out / "lifecycle_by_week.csv",
        tables["by_week"],
        ["week", "stage", "commits", "lines_changed"],
    )
    write_csv(
        out / "spec_trace.csv",
        spec_trace_rows(commits, docs),
        [
            "path",
            "kind",
            "added_sha",
            "added_date",
            "n_feat_linked",
            "first_linked_date",
            "last_linked_date",
        ],
    )
    rework = rework_rows(commits, plans)
    summary_rows = rework_summary(rework)
    by_stage_rows = rework_by_stage(rework)
    write_csv(
        out / "rework.csv", rework, ["sha", "date", "stage", "lines_changed", "has_plan", "rework"]
    )
    write_csv(out / "rework_summary.csv", summary_rows)
    write_csv(
        out / "rework_by_stage.csv",
        by_stage_rows,
        ["stage", "n_feat", "mean_rework", "share_with_rework"],
    )

    session_dirs = [Path(p) for p in args.sessions_dir] if args.sessions_dir else list(SESSION_DIRS)
    stats, dropped = collect_sessions(session_dirs)
    write_csv(
        out / "sessions.csv",
        session_rows(stats),
        [
            "session_no",
            "is_subagent",
            "first_ts",
            "user_messages",
            "assistant_turns",
            "tool_calls",
            "user_interrupts",
        ],
    )
    tools = tool_rows(stats)
    write_csv(out / "session_tools.csv", tools, ["tool", "calls"])

    write_plan_corpus(docs, out / "plan-corpus")
    figures.lifecycle_by_week(tables["by_week"], out / "figures" / "lifecycle_by_week.png")
    figures.rework_by_group(summary_rows, out / "figures" / "rework_by_group.png")

    sheet = out / "link-check.csv"
    if not sheet.exists():
        write_csv(sheet, _link_check_rows(commits, plans), LINK_FIELDS)

    ctx = {
        "revs": revs,
        "pinned": pinned,
        "reference": measured_reference(repo, revs, commits, docs),
        "commits": commits,
        "docs": docs,
        "by_stage": tables["by_stage"],
        "rework": rework,
        "rework_summary": summary_rows,
        "rework_by_stage": by_stage_rows,
        "link_accuracy": _accuracy_text(sheet),
        "sessions": stats,
        "dropped": dropped,
        "tools": tools,
    }
    (out / "summary.md").write_text(build_summary(ctx))
    return 0


def cmd_link_accuracy(args) -> int:
    out = Path(args.out)
    correct, graded = link_accuracy(out / "link-check.csv")
    text = f"{correct}/{graded}"
    print(text)
    summary = out / "summary.md"
    if summary.exists():
        lines = [
            f"{LINK_LINE} {text}" if line.startswith(LINK_LINE) else line
            for line in summary.read_text().splitlines()
        ]
        summary.write_text("\n".join(lines) + "\n")
    return 0


def cmd_plan_corpus(args) -> int:
    repo = Path(args.repo)
    revs, _ = resolve_revs(repo, args.rev)
    write_plan_corpus(
        load_spec_plan_files(repo, revs), Path(args.out) / "plan-corpus", args.materialize
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="retro", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p, repo: bool = True) -> None:
        p.add_argument("--out", default=str(DEFAULT_OUT))
        if repo:
            p.add_argument("--repo", default=str(DEFAULT_REPO))
            p.add_argument(
                "--rev", action="append", help="commit to include (default: the two pinned SHAs)"
            )

    p_all = sub.add_parser("all", help="write every table, figure and summary.md")
    common(p_all)
    p_all.add_argument(
        "--sessions-dir", action="append", help="session log dir (default: ViPharmind's)"
    )
    p_all.set_defaults(func=cmd_all)

    p_acc = sub.add_parser("link-accuracy", help="score An's manual check of link-check.csv")
    common(p_acc, repo=False)
    p_acc.set_defaults(func=cmd_link_accuracy)

    p_pc = sub.add_parser("plan-corpus", help="rewrite out/plan-corpus/")
    common(p_pc)
    p_pc.add_argument(
        "--materialize", action="store_true", help="also restore the original files (git-ignored)"
    )
    p_pc.set_defaults(func=cmd_plan_corpus)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
