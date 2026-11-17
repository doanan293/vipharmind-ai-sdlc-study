"""Hai thí nghiệm thăm dò của prereg-v1.2: E2 (đề sơ sài, 2 x 2) và E1 (Haiku theo thiết kế gốc).

Nguồn (trong gốc repo, do code/refresh-interim.sh sinh):
- data/results/analysis/e2-interim/: summary.json, runs.csv của sdlc-e2 (có thể chưa đủ lượt: sơ bộ);
- data/results/analysis/e1/summary.json của sdlc-e1 (cùng định dạng với thí nghiệm chính), nếu đã chạy.
Mọi khóa thiếu nguồn hoặc chưa có ước lượng là None (\\pending). Hiệu số tính bằng điểm phần trăm.
Câu đọc kết quả (ETwoReading...) sinh theo dấu của khoảng tin cậy và phạm vi dữ liệu, để văn bản tự
cập nhật khi chạy lại.
"""

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from report_data import fmt

Numbers = dict[str, str | None]

E2_DIR = Path("data/results/analysis/e2-interim")
E1_DIR = Path("data/results/analysis/e1")
HANOI = timezone(timedelta(hours=7))

COHORTS = [
    ("pooled", "Pooled", "gộp bốn nhóm"),
    ("claude-sonnet", "Sonnet", "Sonnet"),
    ("claude-opus", "Opus", "Opus"),
    ("claude-haiku", "Haiku", "Haiku"),
    ("codex-luna", "Codex", "Codex"),
]
TIERS = [
    ("all", "All", "gộp"),
    ("small", "Small", "nhỏ"),
    ("medium", "Medium", "vừa"),
    ("large", "Large", "lớn"),
]
# chỉ số của bảng 2 x 2: khóa, tên khóa macro, nhãn, hệ số nhân, số chữ số
X2 = [
    ("score", "Score", "Điểm danh sách hành vi (\\%)", 100, 1),
    ("task_pass", "Pass", "Lượt đạt hết test ẩn (\\%)$^\\dagger$", 100, 1),
    ("regression_any", "Regression", "Lượt có hồi quy (\\%)", 100, 1),
    ("ai_tests_added", "Tests", "Test mới mỗi lượt", 1, 1),
    ("ai_changed_line_coverage", "Coverage", "Phủ dòng mới, lượt có test (\\%)", 100, 1),
    ("tokens_total", "Tokens", "Token (triệu)", 1e-6, 2),
    ("wall_s", "Wall", "Thời gian (phút)", 1 / 60, 1),
]
# chỉ số có thêm macro trung bình bốn ô và tác động của đề sơ sài trong từng nhánh (sơ sài trừ chi tiết,
# lấy trị tuyệt đối: văn bản tự nói giảm hay tăng)
X2_DETAIL = [
    ("score", "Score"),
    ("task_pass", "Pass"),
    ("hidden_pass_rate", "Hidden"),
    ("regression_any", "Regression"),
]
X2_CELLS = [
    ("detailed_spec", "DetailedSpec"),
    ("detailed_vibe", "DetailedVibe"),
    ("brief_spec", "BriefSpec"),
    ("brief_vibe", "BriefVibe"),
]


def _num(x: float | None, scale: float = 100, d: int = 1) -> str | None:
    if x is None:
        return None
    text = fmt.number(float(x) * scale, d)
    return text[1:] if text.startswith("-") and not text.strip("-0,.") else text


def _est(E: dict, key: str) -> dict:
    e = E.get(key) or {}
    return {} if e.get("reference_only") or e.get("estimate") is None else e


def _ci(e: dict, scale: float = 100, d: int = 1) -> tuple[str | None, str | None, str | None]:
    return (
        _num(e.get("estimate"), scale, d),
        _num(e.get("ci_low"), scale, d),
        _num(e.get("ci_high"), scale, d),
    )


def _tier_list(names: list[str]) -> str:
    if len(names) == 3:
        return "cả ba tầng"
    if len(names) == 1:
        return f"tầng {names[0]}"
    return "tầng " + " và tầng ".join(names)


# ---------- E2 ----------


def _e2_keys() -> list[str]:
    k = [
        "ETwoCutoff",
        "ETwoStatus",
        "ETwoLabel",
        "ETwoStoppedUnits",
        "ETwoScope",
        "ETwoBriefExpected",
        "ETwoBriefGraded",
        "ETwoBriefJudged",
        "ETwoCorePp",
        "ETwoCoreLowPp",
        "ETwoCoreHighPp",
        "ETwoJudgeN",
        "ETwoJudgeAgreePct",
        "ETwoJudgeAgreeLowPct",
        "ETwoJudgeAgreeHighPct",
        "ETwoJudgeKappa",
        "ETwoJudgeAllMetGivenPassPct",
        "ETwoReading",
        "ETwoReadingShort",
    ]
    for _, t, _ in TIERS[1:]:
        k += [f"ETwoBrief{t}Expected", f"ETwoBrief{t}Graded", f"ETwoBrief{t}Judged"]
    for _, c, _ in COHORTS:
        for _, t, _ in TIERS:
            k += [f"ETwo{c}{t}Pp", f"ETwo{c}{t}LowPp", f"ETwo{c}{t}HighPp", f"ETwo{c}{t}Tasks"]
    for _, m, _, _, _ in X2:
        for part in ("Detailed", "Brief", "Inter"):
            k += [f"ETwoX{m}{part}", f"ETwoX{m}{part}Low", f"ETwoX{m}{part}High"]
    # tầng vừa, tầng lớn: ước lượng chỉ để tham khảo (dưới sáu nhiệm vụ), vẫn xuất để mô tả
    for _, c, _ in COHORTS:
        for _, t, _ in TIERS[2:]:
            k += [f"ETwo{c}{t}RefPp", f"ETwo{c}{t}RefLowPp", f"ETwo{c}{t}RefHighPp"]
    for _, m in X2_DETAIL:
        k += [f"ETwoX{m}Shift{a}" for a in ("Spec", "Vibe")]
        k += [f"ETwoX{m}Mean{cell}" for _, cell in X2_CELLS]
    k += [
        "ETwoClaudeBriefJudged",
        "ETwoCodexSmallJudged",
        "ETwoCodexSmallExpected",
        "ETwoHaikuDetailedJudged",
        "ETwoHaikuDetailedExpected",
    ]
    k += HUMAN_KEYS
    return k


# mẫu chấm tay E2 (Lợi, Bảo): mức khớp giữa hai người và với người chấm máy, theo từng mục
HUMAN_KEYS = [
    "ETwoHumanUnits",
    "ETwoHumanItems",
    "ETwoHumanLoiBaoAgreePct",
    "ETwoHumanLoiBaoKappa",
    "ETwoHumanLoiJudgeAgreePct",
    "ETwoHumanLoiJudgeKappa",
    "ETwoHumanBaoJudgeAgreePct",
    "ETwoHumanBaoJudgeKappa",
]


E2_KEYS = _e2_keys()


STOPPED_COHORTS = {"codex-luna"}


def _cutoff(runs: list[dict[str, str]]) -> str | None:
    """Giờ bắt đầu của lượt đề sơ sài muộn nhất có trong dữ liệu, theo giờ Hà Nội."""
    times = [r["started_at"] for r in runs if r.get("detail") == "brief" and r.get("started_at")]
    if not times:
        return None
    t = max(datetime.fromisoformat(x) for x in times).astimezone(HANOI)
    return t.strftime("%Y-%m-%d %H:%M")


def e2_numbers(src: dict[str, Any]) -> Numbers:
    s, runs = src["summary"], src["runs"]
    E = s["estimates"]
    out: Numbers = {}
    cov = [c for c in s["coverage"] if c["detail"] == "brief"]
    exp, gr, ju = (sum(int(c[k]) for c in cov) for k in ("expected", "graded", "judged"))
    out["ETwoBriefExpected"], out["ETwoBriefGraded"], out["ETwoBriefJudged"] = (
        fmt.number(exp),
        fmt.number(gr),
        fmt.number(ju),
    )
    for tier, t, _ in TIERS[1:]:
        cs = [c for c in cov if c["tier"] == tier]
        for k, name in (("expected", "Expected"), ("graded", "Graded"), ("judged", "Judged")):
            out[f"ETwoBrief{t}{name}"] = fmt.number(sum(int(c[k]) for c in cs))
    # nhóm đã dừng thu thập hẳn (prereg-v1 mục 11, 2026-11-16 18:00 và 23:20): lượt chưa chạy của
    # nhóm đó không còn chờ nữa, nên dữ liệu "đầy đủ" khi mọi lượt đã chạy xong đều đã được chấm
    stopped_nf = sum(int(c["not_finished"]) for c in cov if c["cohort"] in STOPPED_COHORTS)
    out["ETwoStoppedUnits"] = fmt.number(stopped_nf)
    complete = ju == gr and gr + stopped_nf == exp
    cutoff = _cutoff(runs)
    out["ETwoCutoff"] = cutoff
    # "đầy đủ" dễ đọc thành mọi lượt dự kiến đều có; khi Codex đã dừng thì nói thẳng ra
    done = "thu thập đã kết thúc" + ("; Codex dừng ở tầng nhỏ" if stopped_nf else "")
    out["ETwoStatus"] = done if complete else "sơ bộ"
    out["ETwoLabel"] = (
        f"thu thập xong (tới {cutoff}){'; Codex dừng ở tầng nhỏ' if stopped_nf else ''}"
        if complete else f"SƠ BỘ — dữ liệu tính đến {cutoff}"
    )
    tiers = [vn for tier, _, vn in TIERS[1:] if _est(E, f"primary.score.pooled.{tier}")]
    out["ETwoScope"] = _tier_list(tiers) if tiers else None

    for cohort, c, _ in COHORTS:
        for tier, t, _ in TIERS:
            e = _est(E, f"primary.score.{cohort}.{tier}")
            out[f"ETwo{c}{t}Pp"], out[f"ETwo{c}{t}LowPp"], out[f"ETwo{c}{t}HighPp"] = _ci(e)
            out[f"ETwo{c}{t}Tasks"] = fmt.number(int(e["n_tasks"])) if e else None
    core = _est(E, "primary.score_core.pooled.all")
    out["ETwoCorePp"], out["ETwoCoreLowPp"], out["ETwoCoreHighPp"] = _ci(core)
    for metric, m, _, scale, d in X2:
        for part, key in (
            ("Detailed", "diff.detailed"),
            ("Brief", "diff.brief"),
            ("Inter", "interaction"),
        ):
            e = _est(E, f"x2.{metric}.pooled.{key}")
            v = _ci(e, scale, d)
            out[f"ETwoX{m}{part}"], out[f"ETwoX{m}{part}Low"], out[f"ETwoX{m}{part}High"] = v

    for cohort, c, _ in COHORTS:
        for tier, t, _ in TIERS[2:]:
            e = E.get(f"primary.score.{cohort}.{tier}") or {}
            e = e if e.get("estimate") is not None else {}
            out[f"ETwo{c}{t}RefPp"], out[f"ETwo{c}{t}RefLowPp"], out[f"ETwo{c}{t}RefHighPp"] = _ci(e)
    for metric, m in X2_DETAIL:
        for arm, a in (("spec", "Spec"), ("vibe", "Vibe")):
            e = _est(E, f"x2.{metric}.pooled.detail_effect.{arm}")
            out[f"ETwoX{m}Shift{a}"] = _num(abs(e["estimate"])) if e else None
        for cell, name in X2_CELLS:
            e = _est(E, f"x2.{metric}.pooled.mean.{cell}")
            out[f"ETwoX{m}Mean{name}"] = _num(e.get("estimate"), 100, 0)

    def _count(detail: str, cohorts: set[str], key: str, tier: str | None = None) -> str:
        cs = [
            c
            for c in s["coverage"]
            if c["detail"] == detail and c["cohort"] in cohorts and (tier is None or c["tier"] == tier)
        ]
        return fmt.number(sum(int(c[key]) for c in cs))

    claude = {"claude-sonnet", "claude-opus", "claude-haiku"}
    out["ETwoClaudeBriefJudged"] = _count("brief", claude, "judged")
    out["ETwoCodexSmallJudged"] = _count("brief", {"codex-luna"}, "judged", "small")
    out["ETwoCodexSmallExpected"] = _count("brief", {"codex-luna"}, "expected", "small")
    out["ETwoHaikuDetailedJudged"] = _count("detailed", {"claude-haiku"}, "judged")
    out["ETwoHaikuDetailedExpected"] = _count("detailed", {"claude-haiku"}, "expected")

    jv = (s.get("judge_validity") or {}).get("hidden_all_pass") or {}
    if jv:
        ag = jv["agreement"]
        out["ETwoJudgeN"] = fmt.number(int(jv["n_units"]))
        out["ETwoJudgeAgreePct"] = _num(ag["estimate"], 100, 0)
        out["ETwoJudgeAgreeLowPct"] = _num(ag["ci_low"], 100, 0)
        out["ETwoJudgeAgreeHighPct"] = _num(ag["ci_high"], 100, 0)
        out["ETwoJudgeKappa"] = _num(jv["kappa"], 1, 2)
        out["ETwoJudgeAllMetGivenPassPct"] = _num(jv["p_all_met_given_pass"], 100, 0)
    else:
        for k in ("N", "AgreePct", "AgreeLowPct", "AgreeHighPct", "Kappa", "AllMetGivenPassPct"):
            out[f"ETwoJudge{k}"] = None

    h = src.get("human") or {}
    lb, lj, bj = (h.get(k) or {} for k in ("loi~bao", "loi~judge", "bao~judge"))
    out["ETwoHumanUnits"] = fmt.number(int(lb["n_units"])) if lb else None
    out["ETwoHumanItems"] = fmt.number(int(lb["n_items"])) if lb else None
    for name, r in (("LoiBao", lb), ("LoiJudge", lj), ("BaoJudge", bj)):
        out[f"ETwoHuman{name}AgreePct"] = _num(r.get("agreement"), 100, 0)
        out[f"ETwoHuman{name}Kappa"] = _num(r.get("kappa"), 1, 2)

    out["ETwoReading"], out["ETwoReadingShort"] = _reading(
        _est(E, "primary.score.pooled.all"),
        "mức gộp mọi tầng" if out["ETwoScope"] is not None else None,
        complete,
    )
    assert set(out) == set(E2_KEYS), set(out) ^ set(E2_KEYS)
    return out


def _reading(e: dict, scope: str | None, complete: bool) -> tuple[str | None, str | None]:
    """Câu đọc kết quả chính của E2, theo dấu của khoảng tin cậy gộp; luôn kèm 'chưa kết luận' khi
    dữ liệu còn sơ bộ. E2 là thăm dò: không dùng từ 'được ủng hộ' của phép thử xác nhận."""
    if not e or scope is None:
        return None, None
    lo, hi = e["ci_low"], e["ci_high"]
    if lo > 0:
        long, short = "xu hướng ủng hộ giả thuyết", "nghiêng về đặc tả"
    elif hi < 0:
        long, short = "xu hướng trái với giả thuyết", "nghiêng về vibe"
    else:
        long, short = "chưa thấy xu hướng rõ (khoảng tin cậy chứa 0)", "chưa thấy xu hướng rõ"
    if complete:
        return f"{long} ở {scope}", f"{short} ({scope})"
    return (
        f"{long.replace('xu hướng', 'xu hướng sơ bộ', 1)} ở {scope}; chưa kết luận",
        f"{short} ({scope}); chưa kết luận",
    )


def e2_primary_table(src: dict[str, Any]) -> str:
    E = src["summary"]["estimates"]
    rows = []
    for cohort, _, name in COHORTS:
        cells = []
        for tier, _, _ in TIERS:
            e = E.get(f"primary.score.{cohort}.{tier}") or {}
            if e.get("estimate") is None:
                cells.append("--")
                continue
            est, lo, hi = _ci(e)
            cell = f"{est} [{lo}; {hi}]"
            cells.append(f"({cell})" if e.get("reference_only") else cell)
        rows.append([name] + cells)
    lines = [
        "\\begin{tabular}{lllll}",
        "\\toprule",
        "Nhóm & Mọi tầng & Tầng nhỏ & Tầng vừa & Tầng lớn \\\\",
        "\\midrule",
    ]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def e2_x2_table(src: dict[str, Any]) -> str:
    E = src["summary"]["estimates"]
    rows = []
    for metric, _, label, scale, d in X2:
        means = [
            _est(E, f"x2.{metric}.pooled.mean.{dt}_{arm}")
            for dt in ("detailed", "brief")
            for arm in ("spec", "vibe")
        ]
        cells = [_num(e.get("estimate"), scale, d) or "--" for e in means]
        it = _est(E, f"x2.{metric}.pooled.interaction")
        if it:
            est, lo, hi = _ci(it, scale, d)
            cells.append(f"{est} [{lo}; {hi}]")
        else:
            cells.append("--")
        rows.append([label] + cells)
    lines = [
        "\\begin{tabular}{lrrrrl}",
        "\\toprule",
        " & \\multicolumn{2}{c}{Đề chi tiết} & \\multicolumn{2}{c}{Đề sơ sài} & \\\\",
        "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}",
        "Chỉ số & Đặc tả & Vibe & Đặc tả & Vibe & Tương tác [KTC 95\\%] \\\\",
        "\\midrule",
    ]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def e2_coverage_table(src: dict[str, Any]) -> str:
    cov = [c for c in src["summary"]["coverage"] if c["detail"] == "brief"]
    rows = []
    for cohort, _, name in COHORTS[1:]:
        cells = []
        for tier, _, _ in TIERS[1:]:
            cs = [c for c in cov if c["cohort"] == cohort and c["tier"] == tier]
            ex, gr, ju = (sum(int(c[k]) for c in cs) for k in ("expected", "graded", "judged"))
            cells.append(f"{fmt.number(gr)} / {fmt.number(ju)} / {fmt.number(ex)}")
        rows.append([name] + cells)
    lines = [
        "\\begin{tabular}{llll}",
        "\\toprule",
        "Nhóm & Tầng nhỏ & Tầng vừa & Tầng lớn \\\\",
        "\\midrule",
    ]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


# ---------- E1 ----------

E1_TIERS = TIERS[1:]


def _e1_keys() -> list[str]:
    k = ["EOneRuns", "EOneSmallSpecTokensM", "EOneSmallVibeTokensM"]
    for _, t, _ in E1_TIERS:
        k += [
            f"EOne{t}SpecPct",
            f"EOne{t}VibePct",
            f"EOne{t}DiffPp",
            f"EOne{t}LowPp",
            f"EOne{t}HighPp",
        ]
    return k


E1_KEYS = _e1_keys()


def e1_numbers(src: dict[str, Any]) -> Numbers:
    E = src["summary"]["estimates"]
    out: Numbers = {}
    runs = [r for r in src["runs"] if r["cohort"] == "claude-haiku" and r["valid"] == "True"]
    out["EOneRuns"] = fmt.number(len(runs)) if runs else None
    tok = E.get("secondary.tokens_total.claude-haiku.small") or {}
    out["EOneSmallSpecTokensM"] = _num(tok.get("mean_spec"), 1e-6, 1)
    out["EOneSmallVibeTokensM"] = _num(tok.get("mean_vibe"), 1e-6, 1)
    for tier, t, _ in E1_TIERS:
        e = E.get(f"pass_diff.claude-haiku.{tier}") or {}
        out[f"EOne{t}SpecPct"] = _num(e.get("mean_spec"), 100, 0)
        out[f"EOne{t}VibePct"] = _num(e.get("mean_vibe"), 100, 0)
        out[f"EOne{t}DiffPp"], out[f"EOne{t}LowPp"], out[f"EOne{t}HighPp"] = _ci(e)
    assert set(out) == set(E1_KEYS), set(out) ^ set(E1_KEYS)
    return out


# ---------- nguồn ----------


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_e2(root: Path) -> dict[str, Any] | None:
    d = Path(root) / E2_DIR
    if not (d / "summary.json").exists():
        return None
    return {
        "summary": json.loads((d / "summary.json").read_text(encoding="utf-8")),
        "runs": _read_csv(d / "runs.csv"),
        "human": json.loads(h.read_text(encoding="utf-8"))
        if (h := d / "human-check-agreement.json").exists()
        else None,
    }


def load_e1(root: Path) -> dict[str, Any] | None:
    d = Path(root) / E1_DIR
    if not (d / "summary.json").exists():
        return None
    return {
        "summary": json.loads((d / "summary.json").read_text(encoding="utf-8")),
        "runs": _read_csv(d / "runs.csv"),
    }
