import json
import re
from pathlib import Path

import pytest

from report_data import build, sources

FIXTURE = Path(__file__).parent / "fixtures" / "root"
REPO = Path(__file__).resolve().parents[4]
HAS_REPO_DATA = (REPO / "data" / "tasks" / "screening.json").exists() and (
    REPO / "data" / "retrospective" / "link-check.csv"
).exists()


def read_numbers_tex(path: Path) -> dict[str, str]:
    pairs = re.findall(r"\\newcommand\{\\Num([A-Za-z]+)\}\{(.*)\}$", path.read_text(), re.M)
    return dict(pairs)


def test_missing_source_gives_pending(tmp_path):
    data = sources.load(tmp_path)  # thư mục rỗng: không có nguồn nào
    assert all(v is None for v in data.values())
    out = tmp_path / "gen"
    build.write(data, out)
    tex = read_numbers_tex(out / "numbers.tex")
    assert tex, "phải sinh macro dù thiếu nguồn"
    assert tex["Commits"] == r"\pending{Commits}"
    assert tex["PilotUnits"] == r"\pending{PilotUnits}"
    assert json.loads((out / "numbers.json").read_text())["Commits"] is None


def test_fixture_without_results_marks_only_pilot_pending(tmp_path):
    data = sources.load(FIXTURE)
    assert data["pilot_results"] is None
    build.write(data, tmp_path)
    tex = read_numbers_tex(tmp_path / "numbers.tex")
    assert tex["Commits"] == "4"
    assert tex["PilotUnits"].startswith(r"\pending")


def test_numbers_tex_and_json_have_same_keys(tmp_path):
    build.write(sources.load(FIXTURE), tmp_path)
    tex = read_numbers_tex(tmp_path / "numbers.tex")
    js = json.loads((tmp_path / "numbers.json").read_text())
    assert set(tex) == set(js)
    for key in js:
        assert re.fullmatch(r"[A-Za-z]+", key), key  # tên macro LaTeX không có chữ số
        if js[key] is not None:
            assert tex[key] == js[key]


def test_same_keys_with_and_without_sources(tmp_path):
    full = build.numbers(sources.load(FIXTURE))
    empty = build.numbers(sources.load(tmp_path))
    assert set(full) == set(empty)


def test_fixture_values(tmp_path):
    n = build.numbers(sources.load(FIXTURE))
    assert n["CommitsFeat"] == "2"
    assert n["LinkCorrect"] == "1" and n["LinkChecked"] == "2"
    assert n["LinkAgreeAI"] == "1"
    assert n["Candidates"] == "3" and n["Eligible"] == "1"
    assert n["Tasks"] == "1" and n["PilotTasks"] == "1" and n["FeatureTasks"] == "1"
    assert n["MediumTasks"] == "1" and n["MediumCommitsMin"] == "2"
    assert n["FeatureCommitsMax"] == "6"  # từ ranges.json, đoạn F08
    assert (n["TasksMain"], n["RunsTotal"]) == ("3", "72")  # 3 nhiệm vụ × 4 nhóm × 2 × 3
    assert (n["MediumWindows"], n["MediumEligible"]) == ("3", "2")
    assert n["GradedMediumMin"] == "46" and n["GradedMediumMinTasks"] == r"\texttt{m01}"
    assert n["LitPengFasterPct"] == "55,8"
    assert n["ReworkWithPlanMean"] == "2,00"


def test_writes_tables_and_figures(tmp_path):
    build.write(sources.load(FIXTURE), tmp_path)
    for name in ("lifecycle", "rework", "funnel", "tasks", "literature"):
        text = (tmp_path / "tables" / f"{name}.tex").read_text()
        assert r"\toprule" in text and r"\bottomrule" in text
    for name in ("lifecycle_by_week", "rework_by_group"):
        assert (tmp_path / "figures" / f"{name}.pdf").read_bytes().startswith(b"%PDF")


def test_pilot_results_counted(tmp_path):
    root = tmp_path / "root"
    for cohort, arm, rep, ok in [
        ("claude-sonnet", "spec", 1, True),
        ("claude-sonnet", "vibe", 1, False),
    ]:
        d = root / "data" / "results" / "raw" / "pilot" / cohort / "p01" / f"{arm}-r{rep}"
        d.mkdir(parents=True)
        (d / "grade.json").write_text(json.dumps({"task_pass": ok}))
    data = sources.load(root)
    n = build.numbers(data)
    assert n["PilotUnits"] == "2" and n["PilotPassed"] == "1"
    build.write(data, tmp_path / "gen")
    assert "claude-sonnet" in (tmp_path / "gen" / "tables" / "pilot.tex").read_text()


@pytest.mark.skipif(not HAS_REPO_DATA, reason="cần dữ liệu thật trong repo")
def test_funnel_matches_screening():
    n = build.numbers(sources.load(REPO))
    funnel = [
        n[k]
        for k in ("Candidates", "AfterCritOne", "AfterCritFour", "AfterCritFive", "AfterCritTwo")
    ]
    assert funnel == ["110", "64", "47", "47", "43"]


@pytest.mark.skipif(not HAS_REPO_DATA, reason="cần dữ liệu thật trong repo")
def test_link_accuracy():
    n = build.numbers(sources.load(REPO))
    assert (n["LinkCorrect"], n["LinkChecked"]) == ("15", "20")
    assert n["FeatWithPlanPct"] == "88,7"


def test_link_errors_split_by_direction():
    # fixture: a3 không có plan theo quy tắc nhưng An ghi wrong → bỏ sót (âm tính giả)
    n = build.numbers(sources.load(FIXTURE))
    assert (n["LinkFalsePositive"], n["LinkFalseNegative"]) == ("0", "1")


def test_feat_stage_and_session_span():
    n = build.numbers(sources.load(FIXTURE))
    assert n["FeatInTestStage"] == "1"
    assert (n["SessionFirstDate"], n["SessionLastDate"]) == ("2026-10-25", "2026-10-25")


@pytest.mark.skipif(not HAS_REPO_DATA, reason="cần dữ liệu thật trong repo")
def test_link_errors_real():
    n = build.numbers(sources.load(REPO))
    assert (n["LinkFalsePositive"], n["LinkFalseNegative"]) == ("4", "1")
    assert n["FeatInTestStage"] == "94"


def test_pilot_run_tokens():
    n = build.numbers(sources.load(FIXTURE))
    assert n["PilotAgyRuns"] == "2" and n["PilotAgyInputMedianM"] == "2,0"
    assert n["PilotAgyTurnsMedian"] == "50" and n["PilotAgyCacheReadPct"] == "95"
    assert n["PilotSonnetInputMedianM"] == "0,40" and n["PilotSonnetTurnsMedian"] == "12"
    assert n["PilotAgyInputRatio"] == "5"


@pytest.mark.skipif(not HAS_REPO_DATA, reason="cần dữ liệu thật trong repo")
def test_tiers_real():
    n = build.numbers(sources.load(REPO))
    assert (n["Tasks"], n["MediumTasks"], n["FeatureTasks"]) == ("15", "5", "3")
    assert n["RunsTotal"] == "552"
    assert n["GradedMediumMin"] == "46"


@pytest.mark.skipif(
    not (REPO / "data" / "results" / "analysis" / "main" / "summary.json").exists(),
    reason="chưa có kết quả phân tích chính",
)
def test_main_results_numbers_and_tables(tmp_path):
    data = sources.load(REPO)
    build.write(data, tmp_path)
    tex = read_numbers_tex(tmp_path / "numbers.tex")
    assert not any(v.startswith(r"\pending") for k, v in tex.items() if k.startswith("Res"))
    s = json.loads((REPO / "data/results/analysis/main/summary.json").read_text())
    h1 = s["estimates"]["h1.primary"]
    assert tex["ResHOneEstPp"] == build.fmt.number(h1["estimate"] * 100, 1)
    assert "-0,0" not in (tmp_path / "tables" / "results_main.tex").read_text()
    for name in ("results_main", "results_secondary", "results_tests", "results_cost"):
        assert (tmp_path / "tables" / f"{name}.tex").read_text().startswith("\\begin{tabular}")


def test_missing_analysis_gives_pending_result_tables(tmp_path):
    data = sources.load(tmp_path)
    build.write(data, tmp_path / "gen")
    tex = read_numbers_tex(tmp_path / "gen" / "numbers.tex")
    assert tex["ResHOneEstPp"] == r"\pending{ResHOneEstPp}"
    assert "pending" in (tmp_path / "gen" / "tables" / "results_main.tex").read_text()


def test_passcheck_counts(tmp_path):
    d = tmp_path / "data" / "results" / "analysis" / "main" / "labeling"
    (d / "returned").mkdir(parents=True)
    head = "ma_luot,dung_that(yes/no),ghi_chu\n"
    (d / "returned" / "passcheck-loi.csv").write_text(head + "p1,yes,\np2,no,x\n")
    (d / "returned" / "passcheck-bao.csv").write_text(head + "p3,yes,\np4,yes,\n")
    (d / "passing-key-PRIVATE.csv").write_text(
        "code,rater,arm\np1,loi,spec\np2,loi,vibe\np3,bao,spec\np4,bao,vibe\n"
    )
    data = sources.load(tmp_path)
    build.write(data, tmp_path / "gen")
    tex = read_numbers_tex(tmp_path / "gen" / "numbers.tex")
    assert tex["PassCheckRuns"] == "4"
    assert tex["PassCheckCorrect"] == "3"
    assert tex["PassCheckLoi"] == "2"
    assert tex["PassCheckPerArm"] == "1"


def test_labels_counts(tmp_path):
    d = tmp_path / "data" / "results" / "analysis" / "main" / "labeling"
    d.mkdir(parents=True)
    (d / "final-labels.csv").write_text(
        "code2,unit_id_r1,label_loi,label_bao,label_final,source,label_fable\n"
        "v1,u1,de_bai_thieu,de_bai_thieu,de_bai_thieu,agree,de_bai_thieu\n"
        "v2,u2,loi_logic,hieu_sai,loi_logic,An_adjudicated,de_bai_thieu\n"
        "v3,u3,sai_api_co_san,sai_api_co_san,sai_api_co_san,agree,loi_logic\n"
    )
    (d / "key-round2-PRIVATE.csv").write_text(
        "code2,unit_id,unit,cohort,task_id,tier,arm,rep,timed_out\n"
        "v1,u1,x,claude-opus,t01,small,spec,1,False\n"
        "v2,u2,x,claude-sonnet,t02,small,vibe,1,False\n"
        "v3,u3,x,claude-opus,f15,large,spec,1,False\n"
    )
    data = sources.load(tmp_path)
    build.write(data, tmp_path / "gen")
    tex = read_numbers_tex(tmp_path / "gen" / "numbers.tex")
    assert tex["LabAgree"] == "2"
    assert tex["LabAdjudicated"] == "1"
    assert tex["LabDeBaiThieuSpec"] == "1"
    assert tex["LabSaiApiCoSanLarge"] == "1"
    assert tex["LabOutside"] == "2"
    assert tex["LabFableAgreeLoi"] == "1"
    assert (tmp_path / "gen" / "tables" / "labels.tex").read_text().startswith("\\begin{tabular}")


def test_e2_reading_and_pending(tmp_path):
    from report_data import explore

    e = {"estimate": 0.04, "ci_low": 0.004, "ci_high": 0.09}
    long, short = explore._reading(e, "tầng nhỏ", complete=False)
    assert "sơ bộ" in long and "chưa kết luận" in long and "tầng nhỏ" in short
    long, _ = explore._reading({**e, "ci_low": -0.01}, "cả ba tầng", complete=True)
    assert "chứa 0" in long and "sơ bộ" not in long
    data = sources.load(tmp_path)
    build.write(data, tmp_path / "gen")
    tex = read_numbers_tex(tmp_path / "gen" / "numbers.tex")
    assert tex["ETwoPooledAllPp"] == r"\pending{ETwoPooledAllPp}"
    assert tex["EOneSmallSpecPct"] == r"\pending{EOneSmallSpecPct}"


def test_e2_primary_table_marks_reference_only():
    from report_data import explore

    ref = {"estimate": -0.011, "ci_low": -0.037, "ci_high": 0.004, "reference_only": True}
    main = {"estimate": 0.042, "ci_low": 0.007, "ci_high": 0.081, "reference_only": False}
    E = {"primary.score.pooled.small": main, "primary.score.pooled.large": ref}
    tex = explore.e2_primary_table({"summary": {"estimates": E}})
    row = next(line for line in tex.splitlines() if line.startswith("gộp"))
    assert "4,2 [0,7; 8,1]" in row and "(-1,1 [-3,7; 0,4])" in row
