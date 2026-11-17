"""Số liệu, bảng và hình của thí nghiệm chính, đọc từ data/results/analysis/main (gói code/analysis/).

Nguồn: summary.json (ước lượng, khoảng tin cậy bootstrap, kết cục theo bản đăng ký), runs.csv
(một dòng mỗi lượt, dùng cho số mô tả mà summary không có) và figures/*.pdf (chép nguyên).
Thiếu nguồn thì mọi khóa vẫn được sinh với giá trị None (macro thành \\pending).
"""

import csv
import shutil
from pathlib import Path
from typing import Any

from report_data import fmt

Numbers = dict[str, str | None]

COHORTS = [
    ("claude-sonnet", "Sonnet"),
    ("claude-opus", "Opus"),
    ("codex-luna", "Codex"),
]
TIERS = [("small", "Small", "nhỏ"), ("medium", "Medium", "vừa"), ("large", "Large", "lớn")]
VERDICT = {
    "supported": "ủng hộ",
    "contrary": "trái",
    "inconclusive": "chưa rõ",
}
FIGURES = ["pass_diff_by_cohort", "effect_vs_size", "cost_per_pass"]
CASE_TOKENS = ("tokens_total", "wall_s")


def _clean(text: str) -> str:
    """Bỏ dấu trừ của số làm tròn về 0 ("-0,0" thành "0,0")."""
    return text[1:] if text.startswith("-") and not text.strip("-0,.") else text


def _pct(x: float | None, d: int = 1) -> str | None:
    return None if x is None else _clean(fmt.number(float(x) * 100, d))


def _num(x: float | None, d: int = 1) -> str | None:
    return None if x is None else _clean(fmt.number(float(x), d))


def _est(E: dict, key: str) -> dict:
    return E.get(key) or {}


def _ci_pp(e: dict) -> tuple[str | None, str | None, str | None]:
    return _pct(e.get("estimate")), _pct(e.get("ci_low")), _pct(e.get("ci_high"))


# ---------- macro ----------

KEYS: list[str] = []


def _keys() -> list[str]:
    k = [
        "ResRuns",
        "ResRunsPerCohort",
        "ResPromptCells",
        "ResSecondaryComparisons",
        "ResBootstrapB",
        "ResModelBootstrapB",
        "ResHOneSpecPct",
        "ResHOneVibePct",
        "ResHOneEstPp",
        "ResHOneLowPp",
        "ResHOneHighPp",
        "ResVarCells",
        "ResVarDisagree",
        "ResVarDisagreePct",
        "ResVarAllCells",
        "ResVarAllDisagree",
        "ResVarAllPct",
        "ResHFiveEstPp",
        "ResHFiveLowPp",
        "ResHFiveHighPp",
        "ResHFiveLargePp",
        "ResHFiveSmallPp",
        "ResHFiveHiddenEstPp",
        "ResHFiveHiddenLowPp",
        "ResHFiveHiddenHighPp",
        "ResHFiveCoef",
        "ResHFiveCoefLow",
        "ResHFiveCoefHigh",
        "ResHFiveTaskSd",
        "ResHFiveArmSd",
        "ResHFiveGradedCoef",
        "ResHFiveGradedLow",
        "ResHFiveGradedHigh",
        "ResHFourDiffOfDiffsPp",
        "ResHFourDiffOfDiffsLowPp",
        "ResHFourDiffOfDiffsHighPp",
        "ResHFourSonnetSpecOpusVibePp",
        "ResHFourSonnetSpecOpusVibeLowPp",
        "ResHFourSonnetSpecOpusVibeHighPp",
        "ResHFourCostRatioPct",
        "ResHFourCostRatioLowPct",
        "ResHFourCostRatioHighPct",
        "ResSensUrlRuns",
        "ResSensUrlEstPp",
        "ResSensUrlLowPp",
        "ResSensUrlHighPp",
        "ResSensPytestRuns",
        "ResSensOverlapEstPp",
        "ResSensOverlapLowPp",
        "ResSensOverlapHighPp",
        "ResUpstreamRuns",
        "ResPytestConfigRuns",
        "ResSharedWindowRuns",
        "ResConcurrentWindowRuns",
        "ResCaseSpecTokensM",
        "ResCaseVibeTokensM",
        "ResCaseSpecMin",
        "ResCaseVibeMin",
        "ResCaseSpecHidden",
        "ResCaseHiddenTotal",
        "ResCaseSpecTests",
        "ResCaseDesignLines",
        "ResCasePlanLines",
        "ResCasePlanTasks",
        "ResCaseSpecPassed",
        "ResCaseVibePassed",
        "ResCaseReps",
        "ResCaseDiffPp",
        "ResAgyDone",
        "ResCoverageHits",
        "ResCoverageSets",
        "ResCoveragePct",
    ]
    for _, c in COHORTS:
        for _, t, _ in TIERS:
            k += [f"Res{c}{t}SpecPct", f"Res{c}{t}VibePct", f"Res{c}{t}DiffPp"]
        for arm in ("Spec", "Vibe"):
            k += [
                f"Res{c}{arm}TestsAnyPct",
                f"Res{c}{arm}TestsMean",
                f"Res{c}{arm}CovPct",
                f"Res{c}{arm}PytestPct",
            ]
        k += [f"Res{c}TokenRatio", f"Res{c}WallRatio"]
    for _, t, _ in TIERS:
        k += [f"ResPooled{t}Pp", f"ResPooled{t}LowPp", f"ResPooled{t}HighPp"]
    k += [
        "ResCodexLargeRegSpecPct",
        "ResCodexLargeRegVibePct",
        "ResCodexLargeStaticSpec",
        "ResCodexLargeStaticVibe",
        "ResTokenRatioMin",
        "ResTokenRatioMax",
        "ResWallRatioMin",
        "ResWallRatioMax",
    ]
    return k


KEYS = _keys()


def _runs_by(runs: list[dict[str, str]], cohort: str, arm: str) -> list[dict[str, str]]:
    return [r for r in runs if r["cohort"] == cohort and r["arm"] == arm]


def _f(r: dict[str, str], k: str) -> float | None:
    v = r.get(k, "")
    return None if v in ("", "nan", "None") else float(v)


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def numbers(src: dict[str, Any]) -> Numbers:
    s, runs, case = src["summary"], src["runs"], src.get("case") or {}
    E = s["estimates"]
    out: Numbers = {}
    out["ResAgyDone"] = fmt.number(
        sum(r["cohort"] == "agy-gemini" and r["valid"] == "True" for r in runs)
    )
    runs = [r for r in runs if r["cohort"] in {c for c, _ in COHORTS}]
    out["ResRuns"] = fmt.number(len(runs))
    out["ResRunsPerCohort"] = fmt.number(len(runs) // len(COHORTS))
    pc = s["descriptives"]["prompt_sha256_check"]
    out["ResPromptCells"] = fmt.number(int(pc["cells_with_one_value"]))
    out["ResSecondaryComparisons"] = fmt.number(int(s["meta"]["n_secondary_comparisons"]))
    out["ResBootstrapB"] = fmt.number(int(s["meta"]["bootstrap"]["B"]))
    mm = s["h5"]["mixed_model"]
    out["ResModelBootstrapB"] = fmt.number(int(mm["interaction"]["bootstrap"]["B"]))

    h1 = _est(E, "h1.primary")
    out["ResHOneSpecPct"], out["ResHOneVibePct"] = _pct(h1["mean_spec"]), _pct(h1["mean_vibe"])
    out["ResHOneEstPp"], out["ResHOneLowPp"], out["ResHOneHighPp"] = _ci_pp(h1)
    v = _est(E, "variability.claude-sonnet.small")
    out["ResVarCells"], out["ResVarDisagree"] = fmt.number(v["cells"]), fmt.number(v["disagree"])
    out["ResVarDisagreePct"] = _pct(v["share"], 0)
    va = _est(E, "variability.all_complete")
    out["ResVarAllCells"], out["ResVarAllDisagree"] = (
        fmt.number(va["cells"]),
        fmt.number(va["disagree"]),
    )
    out["ResVarAllPct"] = _pct(va["share"], 0)

    h5 = _est(E, "h5.primary")
    out["ResHFiveEstPp"], out["ResHFiveLowPp"], out["ResHFiveHighPp"] = _ci_pp(h5)
    out["ResHFiveLargePp"], out["ResHFiveSmallPp"] = (
        _pct(h5["pooled_large"]),
        _pct(h5["pooled_small"]),
    )
    hh = _est(E, "h5.hidden_pass_rate")
    out["ResHFiveHiddenEstPp"], out["ResHFiveHiddenLowPp"], out["ResHFiveHiddenHighPp"] = _ci_pp(hh)
    it = mm["interaction"]
    out["ResHFiveCoef"] = _num(it["coef"], 2)
    out["ResHFiveCoefLow"], out["ResHFiveCoefHigh"] = _num(it["ci_low"], 2), _num(it["ci_high"], 2)
    sd = next(a for a in mm["attempts"] if a.get("ok"))["random_effect_sd"]
    out["ResHFiveTaskSd"], out["ResHFiveArmSd"] = _num(sd["task"], 2), _num(sd["task_arm"], 2)
    ig = s["h5"]["mixed_model_graded"]["interaction"]
    out["ResHFiveGradedCoef"] = _num(ig["coef"], 2)
    out["ResHFiveGradedLow"], out["ResHFiveGradedHigh"] = (
        _num(ig["ci_low"], 2),
        _num(ig["ci_high"], 2),
    )

    dd = _est(E, "h4.small.diff_of_diffs")
    (
        out["ResHFourDiffOfDiffsPp"],
        out["ResHFourDiffOfDiffsLowPp"],
        out["ResHFourDiffOfDiffsHighPp"],
    ) = _ci_pp(dd)
    so = _est(E, "h4.small.sonnet_spec_minus_opus_vibe.pass")
    (
        out["ResHFourSonnetSpecOpusVibePp"],
        out["ResHFourSonnetSpecOpusVibeLowPp"],
        out["ResHFourSonnetSpecOpusVibeHighPp"],
    ) = _ci_pp(so)
    cr = _est(E, "h4.small.sonnet_spec_over_opus_vibe.cost_ratio")
    out["ResHFourCostRatioPct"], out["ResHFourCostRatioLowPct"], out["ResHFourCostRatioHighPct"] = (
        _pct(cr["estimate"], 0),
        _pct(cr["ci_low"], 0),
        _pct(cr["ci_high"], 0),
    )

    su = _est(E, "sensitivity.upstream_urls.h1")
    out["ResSensUrlRuns"] = fmt.number(int(su["runs_dropped_all_cohorts"]))
    out["ResSensUrlEstPp"], out["ResSensUrlLowPp"], out["ResSensUrlHighPp"] = _ci_pp(su)
    out["ResSensPytestRuns"] = fmt.number(
        int(_est(E, "sensitivity.pytest_config_touched.h1")["runs_dropped_all_cohorts"])
    )
    so5 = _est(E, "sensitivity.overlap.h5")
    out["ResSensOverlapEstPp"], out["ResSensOverlapLowPp"], out["ResSensOverlapHighPp"] = _ci_pp(
        so5
    )
    D = s["descriptives"]
    out["ResUpstreamRuns"] = fmt.number(sum(int(r["n"]) for r in D["upstream_urls"]))
    out["ResPytestConfigRuns"] = fmt.number(sum(int(r["n"]) for r in D["pytest_config_touched"]))
    out["ResSharedWindowRuns"] = fmt.number(int(D["shared_cpu_window"]["runs_started"]))
    ins = D["concurrent_tiers_window"]["inside"]
    out["ResConcurrentWindowRuns"] = fmt.number(sum(int(r["of"]) for r in ins))

    token_ratios, wall_ratios = [], []
    for cohort, c in COHORTS:
        for tier, t, _ in TIERS:
            e = _est(E, f"pass_diff.{cohort}.{tier}")
            out[f"Res{c}{t}SpecPct"] = _pct(e.get("mean_spec"), 0)
            out[f"Res{c}{t}VibePct"] = _pct(e.get("mean_vibe"), 0)
            out[f"Res{c}{t}DiffPp"] = _pct(e.get("estimate"))
        for arm, a in (("spec", "Spec"), ("vibe", "Vibe")):
            rs = _runs_by(runs, cohort, arm)
            tests = [_f(r, "ai_tests_added") or 0.0 for r in rs]
            cov = [_f(r, "ai_changed_line_coverage") or 0.0 for r in rs]
            ran = [r["pytest_ran"] in ("True", "true", "1") for r in rs]
            out[f"Res{c}{a}TestsAnyPct"] = fmt.percent(sum(x > 0 for x in tests), len(rs), 0)
            out[f"Res{c}{a}TestsMean"] = _num(_mean(tests))
            out[f"Res{c}{a}CovPct"] = _pct(_mean(cov), 0)
            out[f"Res{c}{a}PytestPct"] = fmt.percent(sum(ran), len(rs), 0)
        sp = [_f(r, "tokens_total") for r in _runs_by(runs, cohort, "spec")]
        vb = [_f(r, "tokens_total") for r in _runs_by(runs, cohort, "vibe")]
        tr = sum(x for x in sp if x) / sum(x for x in vb if x)
        sw = [_f(r, "wall_s") for r in _runs_by(runs, cohort, "spec")]
        vw = [_f(r, "wall_s") for r in _runs_by(runs, cohort, "vibe")]
        wr = sum(x for x in sw if x) / sum(x for x in vw if x)
        token_ratios.append(tr)
        wall_ratios.append(wr)
        out[f"Res{c}TokenRatio"], out[f"Res{c}WallRatio"] = _num(tr), _num(wr)
    out["ResTokenRatioMin"], out["ResTokenRatioMax"] = (
        _num(min(token_ratios)),
        _num(max(token_ratios)),
    )
    out["ResWallRatioMin"], out["ResWallRatioMax"] = _num(min(wall_ratios)), _num(max(wall_ratios))
    for tier, t, _ in TIERS:
        e = _est(E, f"pooled.pass_diff.{tier}")
        out[f"ResPooled{t}Pp"], out[f"ResPooled{t}LowPp"], out[f"ResPooled{t}HighPp"] = _ci_pp(e)
    rg = _est(E, "secondary.regression_any.codex-luna.large")
    out["ResCodexLargeRegSpecPct"] = _pct(rg["mean_spec"], 0)
    out["ResCodexLargeRegVibePct"] = _pct(rg["mean_vibe"], 0)
    st = _est(E, "secondary.static_errors.codex-luna.large")
    out["ResCodexLargeStaticSpec"] = _num(st["mean_spec"])
    out["ResCodexLargeStaticVibe"] = _num(st["mean_vibe"])

    # ca nghiên cứu: hai lượt do quy tắc chọn trước (summary.case_study) và số liệu của chúng
    cs = s["case_study"]
    out["ResCaseDiffPp"] = _pct(cs["pass_diff"])
    unit = {r["unit"]: r for r in runs}
    spec_u, vibe_u = unit[cs["units"]["spec"]], unit[cs["units"]["vibe"]]
    out["ResCaseSpecTokensM"] = _num(_f(spec_u, "tokens_total") / 1e6)
    out["ResCaseVibeTokensM"] = _num(_f(vibe_u, "tokens_total") / 1e6)
    out["ResCaseSpecMin"] = fmt.number(round(_f(spec_u, "wall_s") / 60))
    out["ResCaseVibeMin"] = fmt.number(round(_f(vibe_u, "wall_s") / 60))
    out["ResCaseSpecHidden"] = fmt.number(int(_f(spec_u, "hidden_passed")))
    out["ResCaseHiddenTotal"] = fmt.number(int(_f(spec_u, "hidden_total")))
    out["ResCaseSpecTests"] = fmt.number(int(_f(spec_u, "ai_tests_added")))
    task_runs = [
        r for r in runs if r["cohort"] == "claude-sonnet" and r["task_id"] == cs["task_id"]
    ]
    passed = lambda arm: sum(  # noqa: E731
        r["task_pass"] in ("True", "true", "1") for r in task_runs if r["arm"] == arm
    )
    out["ResCaseSpecPassed"], out["ResCaseVibePassed"] = (
        fmt.number(passed("spec")),
        fmt.number(passed("vibe")),
    )
    out["ResCaseReps"] = fmt.number(len([r for r in task_runs if r["arm"] == "spec"]))
    for k in ("ResCaseDesignLines", "ResCasePlanLines", "ResCasePlanTasks"):
        out[k] = fmt.number(case[k]) if k in case else None
    cov = src.get("coverage") or []
    out["ResCoverageHits"] = fmt.number(sum(cov)) if cov else None
    out["ResCoverageSets"] = fmt.number(len(cov)) if cov else None
    out["ResCoveragePct"] = fmt.percent(sum(cov), len(cov)) if cov else None
    assert set(out) == set(KEYS), set(out) ^ set(KEYS)
    return out


# ---------- bảng ----------


def _cell_ci(e: dict) -> str:
    if e.get("estimate") is None:
        return "--"
    est, lo, hi = _ci_pp(e)
    return f"{est} [{lo}; {hi}]"


def _tabular(spec: str, header: list[str], rows: list[list[str]]) -> str:
    lines = [f"\\begin{{tabular}}{{{spec}}}", "\\toprule"]
    lines += [" & ".join(header) + " \\\\", "\\midrule"]
    lines += [" & ".join(r) + " \\\\" for r in rows]
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def main_table(s: dict) -> str:
    E, V = s["estimates"], s["verdicts"]
    rows = []
    for cohort, _ in COHORTS:
        for tier, _, vn in TIERS:
            e = _est(E, f"pass_diff.{cohort}.{tier}")
            rows.append(
                [
                    f"\\texttt{{{cohort}}}",
                    vn,
                    _pct(e["mean_spec"], 0),
                    _pct(e["mean_vibe"], 0),
                    _cell_ci(e),
                    VERDICT[V[f"pass_diff.{cohort}.{tier}"]],
                ]
            )
    for tier, _, vn in TIERS:
        e = _est(E, f"pooled.pass_diff.{tier}")
        rows.append(["gộp ba nhóm", vn, "", "", _cell_ci(e), ""])
    return _tabular(
        "llrrlr",
        ["Nhóm", "Tầng", "Đặc tả (\\%)", "Vibe (\\%)", "Hiệu số (đpt) [KTC 95\\%]", "Kết cục"],
        rows,
    )


def _sv(e: dict, scale: float = 1.0, d: int = 1) -> str:
    if e.get("mean_spec") is None:
        return "--"
    return f"{_num(e['mean_spec'] * scale, d)} / {_num(e['mean_vibe'] * scale, d)}"


def _secondary_row(E: dict, V: dict, cohort: str, tier: str, vn: str) -> list[str]:
    def g(m: str) -> dict:
        return _est(E, f"secondary.{m}.{cohort}.{tier}")

    def vd(h: str, m: str) -> str:
        return VERDICT[V[f"{h}.{m}.{cohort}.{tier}"]]

    return [
        f"\\texttt{{{cohort}}}",
        vn,
        _sv(g("tokens_total"), 1e-6, 2),
        _sv(g("wall_s"), 1 / 60, 1),
        vd("H2", "tokens_total"),
        _sv(g("static_errors"), 1, 1),
        vd("H3a", "static_errors"),
        _sv(g("regression_any"), 100, 0),
        vd("H3b", "regression_any"),
        _sv(g("radon_mi_delta"), 1, 1),
        vd("H3c", "radon_mi_delta"),
    ]


def secondary_table(s: dict) -> str:
    """H2 và H3: trung bình theo cách làm (đặc tả / vibe) và kết cục."""
    E, V = s["estimates"], s["verdicts"]
    rows = [
        _secondary_row(E, V, cohort, tier, vn) for cohort, _ in COHORTS for tier, _, vn in TIERS
    ]
    header = [
        "Nhóm",
        "Tầng",
        "Token (triệu)",
        "Phút",
        "H2",
        "Lỗi tĩnh",
        "H3a",
        "Hồi quy (\\%)",
        "H3b",
        "$\\Delta$MI",
        "H3c",
    ]
    return _tabular("llrrlrlrlrl", header, rows)


def tests_table(runs: list[dict[str, str]]) -> str:
    rows = []
    for cohort, _ in COHORTS:
        for arm, label in (("spec", "đặc tả"), ("vibe", "vibe")):
            rs = _runs_by(runs, cohort, arm)
            tests = [_f(r, "ai_tests_added") or 0.0 for r in rs]
            cov = [_f(r, "ai_changed_line_coverage") or 0.0 for r in rs]
            ran = [r["pytest_ran"] in ("True", "true", "1") for r in rs]
            rows.append(
                [
                    f"\\texttt{{{cohort}}}",
                    label,
                    fmt.number(len(rs)),
                    fmt.percent(sum(ran), len(rs), 0),
                    fmt.percent(sum(x > 0 for x in tests), len(rs), 0),
                    _num(_mean(tests)),
                    _pct(_mean(cov), 0),
                ]
            )
    header = [
        "Nhóm",
        "Cách làm",
        "Lượt",
        "Chạy \\texttt{pytest} (\\%)",
        "Viết test (\\%)",
        "Test mới/lượt",
        "Phủ dòng mới (\\%)",
    ]
    return _tabular("llrrrrr", header, rows)


def _cost_cell(E: dict, cohort: str, tier: str, arm: str) -> str:
    lo = _est(E, f"cost_eff.{cohort}.{tier}.{arm}.cost_per_pass").get("estimate")
    if lo is None:
        return "--"
    if cohort != "codex-luna":
        return _num(lo, 2)
    hi = _est(E, f"cost_eff_upper.{cohort}.{tier}.{arm}.cost_per_pass").get("estimate")
    return f"{_num(lo, 2)}--{_num(hi, 2)}"


def cost_table(s: dict) -> str:
    E = s["estimates"]
    rows = [
        [
            f"\\texttt{{{cohort}}}",
            vn,
            _cost_cell(E, cohort, tier, "spec"),
            _cost_cell(E, cohort, tier, "vibe"),
        ]
        for cohort, _ in COHORTS
        for tier, _, vn in TIERS
    ]
    return _tabular("llrr", ["Nhóm", "Tầng", "Đặc tả (USD)", "Vibe (USD)"], rows)


def write_tables(src: dict[str, Any], out: Path) -> None:
    s, runs = src["summary"], src["runs"]
    runs = [r for r in runs if r["cohort"] in {c for c, _ in COHORTS}]
    for name, text in (
        ("results_main", main_table(s)),
        ("results_secondary", secondary_table(s)),
        ("results_tests", tests_table(runs)),
        ("results_cost", cost_table(s)),
    ):
        (out / "tables" / f"{name}.tex").write_text(text, encoding="utf-8")


def copy_figures(src: dict[str, Any], out: Path) -> None:
    for name in FIGURES:
        shutil.copyfile(src["dir"] / "figures" / f"{name}.pdf", out / "figures" / f"{name}.pdf")


def pending_tables(out: Path, pending: Any) -> None:
    for name, ncols in (
        ("results_main", 6),
        ("results_secondary", 11),
        ("results_tests", 7),
        ("results_cost", 4),
    ):
        (out / "tables" / f"{name}.tex").write_text(pending(name, ncols), encoding="utf-8")


# ---------- nguồn ----------

ANALYSIS = Path("data/results/analysis/main")
CASE_FILE = "case_study.csv"


def load(root: Path) -> dict[str, Any] | None:
    d = Path(root) / ANALYSIS
    if not (d / "summary.json").exists() or not (d / "runs.csv").exists():
        return None
    import json

    with (d / "runs.csv").open(newline="", encoding="utf-8") as f:
        runs = list(csv.DictReader(f))
    case: dict[str, int] = {}
    if (d / CASE_FILE).exists():
        with (d / CASE_FILE).open(newline="", encoding="utf-8") as f:
            case = {r["key"]: int(r["value"]) for r in csv.DictReader(f)}
    # bài kiểm tra độ phủ của khoảng bootstrap (code/analysis/calibration/coverage-run.txt):
    # một dòng mỗi bộ
    # dữ liệu mô phỏng, cột cuối True khi khoảng chứa giá trị thật
    coverage: list[bool] = []
    if (d / "coverage-run.txt").exists():
        for line in (d / "coverage-run.txt").read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 7 and parts[0].isdigit() and parts[-1] in ("True", "False"):
                coverage.append(parts[-1] == "True")
    return {
        "coverage": coverage,
        "dir": d,
        "summary": json.loads((d / "summary.json").read_text(encoding="utf-8")),
        "runs": runs,
        "case": case,
    }
