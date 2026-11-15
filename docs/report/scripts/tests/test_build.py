import json
import re
from pathlib import Path

import pytest

from report_data import build, sources

FIXTURE = Path(__file__).parent / "fixtures" / "root"
REPO = Path(__file__).resolve().parents[4]
HAS_REPO_DATA = (REPO / "tasks" / "screening.json").exists() and (
    REPO / "retrospective" / "out" / "link-check.csv"
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
        d = root / "results" / "raw" / "pilot" / cohort / "p01" / f"{arm}-r{rep}"
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
