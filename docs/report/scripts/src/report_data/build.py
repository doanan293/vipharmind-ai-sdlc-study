"""Từ dữ liệu đã đọc, sinh macro số liệu, bảng LaTeX và hình.

Mỗi nhóm số liệu gắn với một nguồn. Thiếu nguồn thì mọi khóa của nhóm vẫn được sinh, giá trị None,
và macro tương ứng thành \\pending{<Tên>}. Nhờ vậy văn bản luôn build được và tập khóa không đổi.
"""

import json
import statistics
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from report_data import explore, fmt, labels, passcheck, results

Numbers = dict[str, str | None]

# Khâu vòng đời: mã trong data/retrospective, tên macro, tên tiếng Việt (như summary.md).
STAGES = [
    ("research_eval", "ResearchEval", "nghiên cứu và đánh giá"),
    ("data", "Data", "dữ liệu"),
    ("backend", "Backend", "mã backend"),
    ("frontend", "Frontend", "mã frontend"),
    ("test", "Test", "kiểm thử"),
    ("deploy", "Deploy", "triển khai"),
    ("docs", "Docs", "tài liệu"),
    ("other", "Other", "khác"),
]
COMMIT_TYPES = ["feat", "docs", "fix", "refactor", "chore", "test"]
LAYERS = ["api", "application", "domain", "infrastructure"]
# Thứ tự áp tiêu chí sàng lọc của bộ chạy (data/tasks/SCREENING.md): 1, 4, 5, rồi 2.
CRITERIA = [(1, "One"), (4, "Four"), (5, "Five"), (2, "Two")]
CRITERION_TEXT = {
    1: "1. Không sửa file dùng chung của bộ test",
    4: "4. Phần thay đổi ở \\texttt{backend/src} từ 30 đến 400 dòng",
    5: "5. Không chỉ đổi tên hay di chuyển file",
    2: "2. Test ẩn hỏng ở commit cha, đạt ở commit gốc",
}
LIT_STEPS = [
    ("queries", "Queries"),
    ("found", "Found"),
    ("dropped_by_title", "DroppedByTitle"),
    ("screened", "Screened"),
    ("dropped_by_abstract", "DroppedByAbstract"),
    ("kept_new", "KeptNew"),
    ("prior", "Prior"),
    ("total", "Total"),
]
LIT_GROUPS = [
    ("benchmarks", "Benchmarks", "Bộ đo cho coding agent và hạn chế"),
    ("productivity", "Productivity", "Năng suất và chất lượng khi dùng AI"),
    ("spec", "Spec", "Đặc tả, lập kế hoạch, vibe coding"),
    ("method", "Method", "Phương pháp nghiên cứu"),
]
# Con số chép từ abstract các nguồn (literature-log.md, cột phát hiện). Khai báo ở đây để tập khóa
# không phụ thuộc file; literature.toml mục [findings] cho giá trị.
LIT_FINDINGS = [
    "JimenezTasks",
    "AleithanLeakPct",
    "AleithanWeakPct",
    "WangDiffPct",
    "LiangPathPct",
    "LiangPathOtherPct",
    "ChenTasks",
    "ChenRepos",
    "ChenBestPct",
    "PengFasterPct",
    "BeckerSlowerPct",
    "WatanabePRs",
    "WatanabeMergedPct",
    "WatanabeReworkPct",
    "HillPRs",
    "HillRepos",
    "JiangGainPct",
    "TaghaviGain",
    "TaghaviFeatures",
    "AgarwalInterviews",
    "AgarwalRepos",
]
ARMS = [("spec", "theo đặc tả"), ("vibe", "vibe coding")]


def _group(keys: list[str], source: Any, compute: Callable[[Any], Numbers]) -> Numbers:
    if source is None:
        return dict.fromkeys(keys)
    values = compute(source)
    assert set(values) == set(keys), set(values) ^ set(keys)
    return values


def _commits(rows: list[dict[str, str]]) -> Numbers:
    types = Counter(r["type"] for r in rows)
    dates = sorted(r["date"] for r in rows)
    out: Numbers = {"Commits": fmt.number(len(rows)), "FirstDate": dates[0], "LastDate": dates[-1]}
    for t in COMMIT_TYPES:
        out[f"Commits{t.capitalize()}"] = fmt.number(types.get(t, 0))
    return out


COMMITS_KEYS = ["Commits", "FirstDate", "LastDate"] + [
    f"Commits{t.capitalize()}" for t in COMMIT_TYPES
]


def _lifecycle_rows(rows: list[dict[str, str]]) -> dict[str, tuple[int, int]]:
    by_stage = {r["stage"]: (int(r["commits"]), int(r["lines_changed"])) for r in rows}
    return {code: by_stage.get(code, (0, 0)) for code, _, _ in STAGES}


def _lifecycle(rows: list[dict[str, str]]) -> Numbers:
    stages = _lifecycle_rows(rows)
    commits = sum(c for c, _ in stages.values())
    lines = sum(n for _, n in stages.values())
    out: Numbers = {"LinesChanged": fmt.number(lines)}
    for code, name, _ in STAGES:
        c, n = stages[code]
        out[f"Stage{name}Commits"] = fmt.number(c)
        out[f"Stage{name}CommitsPct"] = fmt.percent(c, commits)
        out[f"Stage{name}LinesPct"] = fmt.percent(n, lines)
    return out


LIFECYCLE_KEYS = ["LinesChanged"] + [
    f"Stage{name}{suffix}"
    for _, name, _ in STAGES
    for suffix in ("Commits", "CommitsPct", "LinesPct")
]


def _spec_trace(rows: list[dict[str, str]]) -> Numbers:
    kinds = Counter(r["kind"] for r in rows)
    return {
        "SpecPlanFiles": fmt.number(len(rows)),
        "SpecFiles": fmt.number(kinds.get("spec", 0)),
        "PlanFiles": fmt.number(kinds.get("plan", 0)),
    }


def _rework(rows: list[dict[str, str]]) -> Numbers:
    g = {r["group"]: r for r in rows}
    w, wo = g["with_plan"], g["without_plan"]
    n_w, n_wo = int(w["n_feat"]), int(wo["n_feat"])
    out: Numbers = {
        "FeatWithPlan": fmt.number(n_w),
        "FeatWithoutPlan": fmt.number(n_wo),
        "FeatWithPlanPct": fmt.percent(n_w, n_w + n_wo),
    }
    for key, r in (("WithPlan", w), ("WithoutPlan", wo)):
        out[f"Rework{key}Mean"] = fmt.number(float(r["mean_rework"]), 2)
        out[f"Rework{key}Median"] = fmt.number(float(r["median_rework"]), 0)
        out[f"Rework{key}SharePct"] = fmt.number(float(r["share_with_rework"]) * 100, 1)
    return out


REWORK_KEYS = ["FeatWithPlan", "FeatWithoutPlan", "FeatWithPlanPct"] + [
    f"Rework{g}{s}" for g in ("WithPlan", "WithoutPlan") for s in ("Mean", "Median", "SharePct")
]


def _link_check(rows: list[dict[str, str]]) -> Numbers:
    correct = sum(r["an_verdict"] == "correct" for r in rows)
    judged = [(r, r["an_verdict"] == "wrong") for r in rows]
    return {
        "LinkChecked": fmt.number(len(rows)),
        "LinkCorrect": fmt.number(correct),
        "LinkCorrectPct": fmt.percent(correct, len(rows)),
        "LinkAgreeAI": fmt.number(sum(r["an_verdict"] == r["ai_suggestion"] for r in rows)),
        # sai khi quy tắc nối với một plan (dương tính giả) và khi quy tắc không thấy plan nào
        "LinkFalsePositive": fmt.number(sum(wrong and bool(r["rule_plan"]) for r, wrong in judged)),
        "LinkFalseNegative": fmt.number(sum(wrong and not r["rule_plan"] for r, wrong in judged)),
    }


def _sessions(rows: list[dict[str, str]]) -> Numbers:
    main = [r for r in rows if r["is_subagent"] == "False"]

    def total(field: str, of: list[dict[str, str]]) -> str:
        return fmt.number(sum(int(r[field]) for r in of))

    # Như data/retrospective/summary.md: tin nhắn người dùng chỉ tính phiên chính; lượt trả lời,
    # lời gọi công cụ và số lần ngắt tính mọi nhật ký.
    return {
        "SessionsMain": fmt.number(len(main)),
        "SessionsSub": fmt.number(len(rows) - len(main)),
        "SessionUserMessages": total("user_messages", main),
        "SessionAssistantTurns": total("assistant_turns", rows),
        "SessionToolCalls": total("tool_calls", rows),
        "SessionInterrupts": total("user_interrupts", rows),
        "SessionFirstDate": min(r["first_ts"] for r in rows),
        "SessionLastDate": max(r["first_ts"] for r in rows),
    }


def _session_tools(rows: list[dict[str, str]]) -> Numbers:
    calls = {r["tool"]: int(r["calls"]) for r in rows}
    total = sum(calls.values())
    return {
        "ToolBashCalls": fmt.number(calls.get("Bash", 0)),
        "ToolBashPct": fmt.percent(calls.get("Bash", 0), total),
    }


def _funnel_steps(rows: list[dict[str, Any]]) -> list[tuple[int, int, int]]:
    """(tiêu chí, còn lại, bị loại) theo thứ tự áp."""
    rejected = Counter(r["failed_criterion"] for r in rows)
    left = len(rows)
    steps = []
    for crit, _ in CRITERIA:
        left -= rejected.get(crit, 0)
        steps.append((crit, left, rejected.get(crit, 0)))
    return steps


def _screening(rows: list[dict[str, Any]]) -> Numbers:
    out: Numbers = {"Candidates": fmt.number(len(rows))}
    for (_crit, left, rej), (_, word) in zip(_funnel_steps(rows), CRITERIA, strict=True):
        out[f"AfterCrit{word}"] = fmt.number(left)
        out[f"RejectedCrit{word}"] = fmt.number(rej)
    eligible = [r for r in rows if r["failed_criterion"] is None]
    layers = Counter(r["layer"] for r in eligible)
    out["Eligible"] = fmt.number(len(eligible))
    out["EligibleNoLayer"] = fmt.number(layers.get(None, 0))
    out["EligibleStratifiable"] = fmt.number(len(eligible) - layers.get(None, 0))
    for layer in LAYERS:
        out[f"Eligible{layer.capitalize()}"] = fmt.number(layers.get(layer, 0))
    return out


SCREENING_KEYS = (
    ["Candidates", "Eligible", "EligibleNoLayer", "EligibleStratifiable"]
    + [f"{prefix}Crit{word}" for _, word in CRITERIA for prefix in ("After", "Rejected")]
    + [f"Eligible{layer.capitalize()}" for layer in LAYERS]
)


# Thiết kế chạy chính (prereg-v1 mục 3, 4): 4 nhóm chạy × 2 cách làm × 3 lần lặp cho mỗi nhiệm vụ.
COHORTS, N_ARMS, REPS = 4, 2, 3


def _runs(n_tasks: int) -> str:
    return fmt.number(n_tasks * COHORTS * N_ARMS * REPS)


def _tasks(rows: list[dict[str, Any]]) -> Numbers:
    lines = [int(t["src_lines"]) for t in rows]
    layers = Counter(t["layer"] for t in rows)
    out: Numbers = {
        "Tasks": fmt.number(len(rows)),
        "TaskSrcLinesMin": fmt.number(min(lines)),
        "TaskSrcLinesMax": fmt.number(max(lines)),
        "TaskSrcLinesMedian": fmt.number(int(statistics.median_low(lines))),
        "RunsSmallTotal": _runs(len(rows)),
    }
    for layer in LAYERS:
        out[f"Tasks{layer.capitalize()}"] = fmt.number(layers.get(layer, 0))
    return out


TASKS_KEYS = [
    "Tasks",
    "TaskSrcLinesMin",
    "TaskSrcLinesMax",
    "TaskSrcLinesMedian",
    "RunsSmallTotal",
] + [f"Tasks{layer.capitalize()}" for layer in LAYERS]


def _range_tier(prefix: str, runs_key: str) -> Callable[[list[dict[str, Any]]], Numbers]:
    """Tầng nhiều commit: số nhiệm vụ, khoảng số commit và số dòng, số lượt chạy chính."""

    def compute(rows: list[dict[str, Any]]) -> Numbers:
        commits = [int(r["n_commits"]) for r in rows if r.get("n_commits") is not None]
        lines = [int(r["src_lines"]) for r in rows]
        return {
            f"{prefix}Tasks": fmt.number(len(rows)),
            f"{prefix}CommitsMin": fmt.number(min(commits)) if commits else None,
            f"{prefix}CommitsMax": fmt.number(max(commits)) if commits else None,
            f"{prefix}SrcLinesMin": fmt.number(min(lines)),
            f"{prefix}SrcLinesMax": fmt.number(max(lines)),
            runs_key: _runs(len(rows)),
        }

    return compute


def _range_keys(prefix: str, runs_key: str) -> list[str]:
    return [
        f"{prefix}{k}" for k in ("Tasks", "CommitsMin", "CommitsMax", "SrcLinesMin", "SrcLinesMax")
    ] + [runs_key]


MEDIUM_KEYS = _range_keys("Medium", "RunsMediumTotal")
FEATURES_KEYS = _range_keys("Feature", "RunsLargeTotal")


def _all_tiers(src: tuple[list, list, list]) -> Numbers:
    n = sum(len(rows) for rows in src)
    return {"TasksMain": fmt.number(n), "RunsTotal": _runs(n)}


TIER_OF = {"t": "Small", "m": "Medium", "f": "Large"}


def _graded(graded: dict[str, Any]) -> Numbers:
    """graded_src_lines (prereg-v1.1): nhỏ nhất, lớn nhất theo tầng; nhiệm vụ tầng vừa nhỏ nhất."""
    by: dict[str, dict[str, int]] = {}
    for task, rec in graded.items():
        if rec.get("graded_src_lines") is not None and task[0] in TIER_OF:
            by.setdefault(TIER_OF[task[0]], {})[task] = int(rec["graded_src_lines"])
    out: Numbers = {}
    for tier in TIER_OF.values():
        vals = by.get(tier, {})
        out[f"Graded{tier}Min"] = fmt.number(min(vals.values())) if vals else None
        out[f"Graded{tier}Max"] = fmt.number(max(vals.values())) if vals else None
    medium = by.get("Medium", {})
    low = min(medium.values()) if medium else None
    out["GradedMediumMinTasks"] = (
        " và ".join(f"\\texttt{{{t}}}" for t in sorted(medium) if medium[t] == low)
        if medium
        else None
    )
    return out


GRADED_KEYS = [f"Graded{t}{m}" for t in TIER_OF.values() for m in ("Min", "Max")] + [
    "GradedMediumMinTasks"
]


def _medium_candidates(rows: list[dict[str, Any]]) -> Numbers:
    return {
        "MediumWindows": fmt.number(len(rows)),
        "MediumEligible": fmt.number(sum(bool(r.get("eligible")) for r in rows)),
    }


def _pilot_runs(rows: list[dict[str, str]]) -> Numbers:
    """Token và số lượt gọi mô hình của lượt chạy thử (data/results/analysis/pilot/runs.csv).

    Lấy mọi lượt có số token, kể cả lượt agy bị ngắt vì hạn mức (nhật ký vẫn ghi lượng dùng).
    Token vào gồm token đọc và ghi cache."""

    def of(cohort: str) -> list[dict[str, str]]:
        return [r for r in rows if r["cohort"] == cohort and r["tokens_total_input"]]

    agy, sonnet = of("agy-gemini"), of("claude-sonnet")

    def med(rs: list[dict[str, str]], field: str) -> float:
        return statistics.median(float(r[field]) for r in rs)

    out: Numbers = dict.fromkeys(PILOT_RUN_KEYS)
    if not agy or not sonnet:
        return out
    agy_in, son_in = med(agy, "tokens_total_input"), med(sonnet, "tokens_total_input")
    cache = sum(float(r["tok_cache_read"] or 0) for r in agy)
    total = sum(float(r["tokens_total_input"]) for r in agy)
    out |= {
        "PilotAgyRuns": fmt.number(len(agy)),
        "PilotAgyInputMedianM": fmt.number(agy_in / 1e6, 1),
        "PilotAgyTurnsMedian": fmt.number(med(agy, "turns"), 0),
        "PilotAgyCacheReadPct": fmt.number(100 * cache / total, 0),
        "PilotSonnetRuns": fmt.number(len(sonnet)),
        "PilotSonnetInputMedianM": fmt.number(son_in / 1e6, 2),
        "PilotSonnetTurnsMedian": fmt.number(med(sonnet, "turns"), 0),
        "PilotAgyInputRatio": fmt.number(agy_in / son_in, 0),
    }
    return out


PILOT_RUN_KEYS = [
    "PilotAgyRuns",
    "PilotAgyInputMedianM",
    "PilotAgyTurnsMedian",
    "PilotAgyCacheReadPct",
    "PilotSonnetRuns",
    "PilotSonnetInputMedianM",
    "PilotSonnetTurnsMedian",
    "PilotAgyInputRatio",
]


def _literature(lit: dict[str, Any]) -> Numbers:
    out: Numbers = {f"Lit{name}": fmt.number(int(lit[key])) for key, name in LIT_STEPS}
    for key, name, _ in LIT_GROUPS:
        out[f"LitGroup{name}"] = fmt.number(int(lit["groups"][key]))
    findings = lit.get("findings", {})
    for name in LIT_FINDINGS:
        out[f"Lit{name}"] = fmt.as_written(findings[name]) if name in findings else None
    return out


LIT_KEYS = (
    [f"Lit{name}" for _, name in LIT_STEPS]
    + [f"LitGroup{name}" for _, name, _ in LIT_GROUPS]
    + [f"Lit{name}" for name in LIT_FINDINGS]
)


def _pilot(units: list[dict[str, Any]]) -> Numbers:
    passed = sum(bool(u["task_pass"]) for u in units)
    return {
        "PilotUnits": fmt.number(len(units)),
        "PilotPassed": fmt.number(passed),
        "PilotPassPct": fmt.percent(passed, len(units)),
    }


PILOT_KEYS = ["PilotUnits", "PilotPassed", "PilotPassPct"]


def numbers(data: dict[str, Any]) -> Numbers:
    out: Numbers = {}
    out |= _group(COMMITS_KEYS, data.get("commits"), _commits)
    out |= _group(LIFECYCLE_KEYS, data.get("lifecycle"), _lifecycle)
    out |= _group(["SpecPlanFiles", "SpecFiles", "PlanFiles"], data.get("spec_trace"), _spec_trace)
    out |= _group(REWORK_KEYS, data.get("rework_summary"), _rework)
    out |= _group(
        [
            "LinkChecked",
            "LinkCorrect",
            "LinkCorrectPct",
            "LinkAgreeAI",
            "LinkFalsePositive",
            "LinkFalseNegative",
        ],
        data.get("link_check"),
        _link_check,
    )
    out |= _group(
        [
            "SessionsMain",
            "SessionsSub",
            "SessionUserMessages",
            "SessionAssistantTurns",
            "SessionToolCalls",
            "SessionInterrupts",
            "SessionFirstDate",
            "SessionLastDate",
        ],
        data.get("sessions"),
        _sessions,
    )
    out |= _group(["ToolBashCalls", "ToolBashPct"], data.get("session_tools"), _session_tools)
    out |= _group(
        ["FeatInTestStage"],
        data.get("rework"),
        lambda r: {"FeatInTestStage": fmt.number(sum(x["stage"] == "test" for x in r))},
    )
    out |= _group(SCREENING_KEYS, data.get("screening"), _screening)
    out |= _group(TASKS_KEYS, data.get("tasks"), _tasks)
    out |= _group(["PilotTasks"], data.get("pilots"), lambda r: {"PilotTasks": fmt.number(len(r))})
    out |= _group(MEDIUM_KEYS, data.get("medium"), _range_tier("Medium", "RunsMediumTotal"))
    out |= _group(FEATURES_KEYS, data.get("features"), _range_tier("Feature", "RunsLargeTotal"))
    tiers = (data.get("tasks"), data.get("medium"), data.get("features"))
    out |= _group(
        ["TasksMain", "RunsTotal"], tiers if all(t is not None for t in tiers) else None, _all_tiers
    )
    out |= _group(GRADED_KEYS, data.get("graded_lines"), _graded)
    out |= _group(
        ["MediumWindows", "MediumEligible"], data.get("medium_candidates"), _medium_candidates
    )
    out |= _group(PILOT_RUN_KEYS, data.get("pilot_runs"), _pilot_runs)
    out |= _group(LIT_KEYS, data.get("literature"), _literature)
    out |= _group(PILOT_KEYS, data.get("pilot_results"), _pilot)
    out |= _group(results.KEYS, data.get("analysis"), results.numbers)
    out |= _group(passcheck.KEYS, data.get("passcheck"), passcheck.numbers)
    out |= _group(labels.KEYS, data.get("labeling"), labels.numbers)
    out |= _group(explore.E2_KEYS, data.get("e2"), explore.e2_numbers)
    out |= _group(explore.E1_KEYS, data.get("e1"), explore.e1_numbers)
    return out


# ---------- bảng ----------


def _tabular(
    spec: str, header: list[str], rows: list[list[str]], total: list[str] | None = None
) -> str:
    lines = [
        f"\\begin{{tabular}}{{{spec}}}",
        "\\toprule",
        " & ".join(header) + " \\\\",
        "\\midrule",
    ]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    if total:
        lines += ["\\midrule", " & ".join(total) + " \\\\"]
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def _pending_table(name: str, ncols: int) -> str:
    cell = f"\\multicolumn{{{ncols}}}{{c}}{{\\pending{{{name}}}}}"
    return _tabular("l" * ncols, [""] * ncols, [[cell]])


def _lifecycle_table(rows: list[dict[str, str]]) -> str:
    stages = _lifecycle_rows(rows)
    commits = sum(c for c, _ in stages.values())
    lines = sum(n for _, n in stages.values())
    body = [
        [label, fmt.number(c), fmt.percent(c, commits), fmt.number(n), fmt.percent(n, lines)]
        for (code, _, label), (c, n) in zip(STAGES, stages.values(), strict=True)
    ]
    return _tabular(
        "lrrrr",
        ["Khâu", "Commit", "\\% commit", "Dòng thay đổi", "\\% dòng"],
        body,
        ["Tổng", fmt.number(commits), "", fmt.number(lines), ""],
    )


def _rework_table(rows: list[dict[str, str]]) -> str:
    g = {r["group"]: r for r in rows}
    labels = [("with_plan", "Có plan đi trước"), ("without_plan", "Không có plan")]
    body = [
        [
            label,
            fmt.number(int(g[k]["n_feat"])),
            fmt.number(float(g[k]["mean_rework"]), 2),
            fmt.number(float(g[k]["median_rework"]), 0),
            fmt.number(float(g[k]["share_with_rework"]) * 100, 1),
        ]
        for k, label in labels
    ]
    return _tabular(
        "lrrrr",
        ["Nhóm", "Số \\texttt{feat}", "Trung bình", "Trung vị", "\\% có sửa lại"],
        body,
    )


def _funnel_table(rows: list[dict[str, Any]]) -> str:
    body = [
        [
            "Ứng viên: commit \\texttt{feat} chạm cả \\texttt{backend/src}"
            " và \\texttt{backend/tests}",
            fmt.number(len(rows)),
            "",
        ]
    ]
    for crit, left, rej in _funnel_steps(rows):
        body.append([CRITERION_TEXT[crit], fmt.number(left), fmt.number(rej)])
    return _tabular("p{0.62\\linewidth}rr", ["Bước", "Còn lại", "Bị loại"], body)


def _short(sha: str, n: int = 10) -> str:
    return f"\\texttt{{{sha[:n]}}}"


TASK_COLS = 7


def _tasks_table(
    tasks: list[dict] | None,
    pilots: list[dict] | None,
    medium: list[dict] | None,
    features: list[dict] | None,
    graded: dict[str, Any] | None,
) -> str:
    """Nhiệm vụ của ba tầng và nhiệm vụ thử. Nhiệm vụ nhiều commit ghi base..end."""

    def graded_of(t: dict) -> str:
        rec = (graded or {}).get(t["id"])
        if rec is None or rec.get("graded_src_lines") is None:
            return "--"
        return fmt.number(int(rec["graded_src_lines"]))

    def rows(src: list[dict] | None, name: str) -> list[list[str]]:
        if src is None:
            return [[f"\\multicolumn{{{TASK_COLS}}}{{c}}{{\\pending{{{name}}}}}"]]
        out = []
        for t in src:
            if t.get("base"):
                where = f"{_short(t['base'], 7)}..{_short(t['commit'], 7)}"
                n = fmt.number(int(t["n_commits"])) if t.get("n_commits") else "--"
            else:
                where, n = _short(t["commit"]), "1"
            out.append(
                [
                    f"\\texttt{{{t['id']}}}",
                    t["layer"] or "",
                    where,
                    n,
                    fmt.number(int(t["src_lines"])),
                    graded_of(t),
                    fmt.number(len(t["hidden_tests"])),
                ]
            )
        return out

    def heading(text: str) -> list[list[str]]:
        return [[f"\\midrule\\multicolumn{{{TASK_COLS}}}{{l}}{{\\textit{{{text}}}}}"]]

    body = [[f"\\multicolumn{{{TASK_COLS}}}{{l}}{{\\textit{{Tầng nhỏ}}}}"]]
    body += rows(tasks, "tasks")
    body += heading("Tầng vừa") + rows(medium, "medium")
    body += heading("Tầng lớn") + rows(features, "features")
    body += heading("Nhiệm vụ thử (không tính vào kết quả)") + rows(pilots, "pilots")
    return _tabular(
        "llllrrr",
        ["Mã", "Lớp", "Commit", "Số commit", "Dòng src", "Dòng chấm", "File test ẩn"],
        body,
    )


def _literature_table(lit: dict[str, Any]) -> str:
    labels = {
        "queries": "Truy vấn đã chạy",
        "found": "Mục riêng biệt tìm thấy (không kể nguồn đã có)",
        "dropped_by_title": "Loại ở bước đọc tiêu đề (blog, trang nhà cung cấp, bài phổ thông)",
        "screened": "Bài học thuật sàng lọc qua abstract",
        "dropped_by_abstract": "Loại sau sàng lọc",
        "kept_new": "Giữ lại, đã mở trang gốc và kiểm tra",
        "prior": "Nguồn đã kiểm tra từ đề cương",
        "total": "Tổng nguồn trong \\texttt{references.bib}",
    }
    body = [[labels[k], fmt.number(int(lit[k]))] for k, _ in LIT_STEPS]
    body += [["\\midrule\\multicolumn{2}{l}{\\textit{Theo nhóm}}"]]
    body += [[label, fmt.number(int(lit["groups"][k]))] for k, _, label in LIT_GROUPS]
    return _tabular("p{0.75\\linewidth}r", ["Bước", "Số mục"], body)


def _pilot_table(units: list[dict[str, Any]]) -> str:
    by: dict[tuple[str, str], list[bool]] = {}
    for u in units:
        by.setdefault((u["cohort"], u["arm"]), []).append(bool(u["task_pass"]))
    arm_label = dict(ARMS)
    body = [
        [
            f"\\texttt{{{cohort}}}",
            arm_label.get(arm, arm),
            f"{fmt.number(sum(v))}/{fmt.number(len(v))}",
        ]
        for (cohort, arm), v in sorted(by.items())
    ]
    return _tabular("llr", ["Nhóm chạy", "Cách làm", "Đạt/tổng"], body)


# ---------- hình ----------


def _figure_setup():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    names = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update(
        {
            "font.family": "Times New Roman" if "Times New Roman" in names else "serif",
            "font.size": 9,
            "pdf.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    return plt


def _pending_figure(path: Path) -> None:
    plt = _figure_setup()
    fig, ax = plt.subplots(figsize=(6, 1.5))
    ax.axis("off")
    ax.text(0.5, 0.5, "[chờ kết quả]", ha="center", va="center")
    fig.savefig(path)
    plt.close(fig)


GREYS = ["#000000", "#404040", "#707070", "#a0a0a0", "#c8c8c8", "#ffffff", "#e0e0e0", "#585858"]
HATCHES = ["", "", "", "", "", "///", "...", "xx"]


def _lifecycle_figure(rows: list[dict[str, str]], path: Path) -> None:
    plt = _figure_setup()
    seen = sorted({r["week"] for r in rows})
    year = seen[0].split("-W")[0]
    lo, hi = int(seen[0].split("-W")[1]), int(seen[-1].split("-W")[1])
    weeks = [f"{year}-W{w:02d}" for w in range(lo, hi + 1)]  # cả tuần không có commit
    counts = {(r["week"], r["stage"]): int(r["commits"]) for r in rows}
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    bottom = [0] * len(weeks)
    x = range(len(weeks))
    for i, (code, _, label) in enumerate(STAGES):
        h = [counts.get((w, code), 0) for w in weeks]
        if not any(h):
            continue
        ax.bar(
            x,
            h,
            bottom=bottom,
            color=GREYS[i],
            hatch=HATCHES[i],
            edgecolor="black",
            linewidth=0.4,
            label=label,
        )
        bottom = [b + v for b, v in zip(bottom, h, strict=True)]
    ax.set_xticks(list(x), [w.split("-W")[1] for w in weeks])
    ax.set_xlabel(f"Tuần (ISO, năm {year})")
    ax.set_ylabel("Số commit")
    ax.legend(ncol=4, fontsize=7, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def _rework_figure(rows: list[dict[str, str]], path: Path) -> None:
    plt = _figure_setup()
    groups = [
        ("True", "Có plan đi trước", "#404040", ""),
        ("False", "Không có plan", "#ffffff", "///"),
    ]
    counts = {g: Counter(int(r["rework"]) for r in rows if r["has_plan"] == g) for g, *_ in groups}
    top = max(max(c, default=0) for c in counts.values())
    xs = list(range(top + 1))
    fig, ax = plt.subplots(figsize=(6.3, 2.4))
    width = 0.4
    for i, (g, label, color, hatch) in enumerate(groups):
        total = sum(counts[g].values()) or 1
        share = [100 * counts[g].get(x, 0) / total for x in xs]
        ax.bar(
            [x + (i - 0.5) * width for x in xs],
            share,
            width,
            color=color,
            hatch=hatch,
            edgecolor="black",
            linewidth=0.4,
            label=label,
        )
    ax.set_xticks(xs)
    ax.set_xlabel("Số commit fix hoặc refactor chạm cùng file trong 14 ngày sau commit feat")
    ax.set_ylabel("% số commit feat của nhóm")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ---------- ghi ra ----------


def write(data: dict[str, Any], out: Path) -> None:
    out = Path(out)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    nums = numbers(data)
    tex = ["% Sinh bởi report-data build. Không sửa tay.", ""]
    for key, value in nums.items():
        shown = value if value is not None else f"\\pending{{{key}}}"
        tex.append(f"\\newcommand{{\\Num{key}}}{{{shown}}}")
    (out / "numbers.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")
    (out / "numbers.json").write_text(
        json.dumps(nums, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )

    def table(name: str, source: Any, render: Callable[[Any], str], ncols: int) -> None:
        text = render(source) if source is not None else _pending_table(name, ncols)
        (out / "tables" / f"{name}.tex").write_text(text, encoding="utf-8")

    table("lifecycle", data.get("lifecycle"), _lifecycle_table, 5)
    table("rework", data.get("rework_summary"), _rework_table, 5)
    table("funnel", data.get("screening"), _funnel_table, 3)
    table("literature", data.get("literature"), _literature_table, 2)
    table("pilot", data.get("pilot_results"), _pilot_table, 3)
    table("labels", data.get("labeling"), labels.table, 7)
    table("e2_primary", data.get("e2"), explore.e2_primary_table, 5)
    table("e2_x2", data.get("e2"), explore.e2_x2_table, 6)
    table("e2_coverage", data.get("e2"), explore.e2_coverage_table, 4)
    (out / "tables" / "tasks.tex").write_text(
        _tasks_table(
            data.get("tasks"),
            data.get("pilots"),
            data.get("medium"),
            data.get("features"),
            data.get("graded_lines"),
        ),
        encoding="utf-8",
    )

    if data.get("analysis") is not None:
        results.write_tables(data["analysis"], out)
        results.copy_figures(data["analysis"], out)
    else:
        results.pending_tables(out, _pending_table)
        for name in results.FIGURES:
            _pending_figure(out / "figures" / f"{name}.pdf")

    for name, source, render in (
        ("lifecycle_by_week", data.get("lifecycle_week"), _lifecycle_figure),
        ("rework_by_group", data.get("rework"), _rework_figure),
    ):
        path = out / "figures" / f"{name}.pdf"
        if source is None:
            _pending_figure(path)
        else:
            render(source, path)
