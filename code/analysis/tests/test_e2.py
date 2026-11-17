import json

import pandas as pd
import pytest
import synthetic_e2 as se

from sdlc_analysis import e2

B = 300


@pytest.fixture(scope="module")
def e2_study(tmp_path_factory):
    root = tmp_path_factory.mktemp("e2")
    tasks_dir, detailed, brief = se.write_e2(root)
    tasks, runs = e2.load_e2([detailed], [brief], tasks_dir)
    return tasks_dir, detailed, brief, tasks, runs


@pytest.fixture(scope="module")
def e2_summary(e2_study):
    _, _, _, tasks, runs = e2_study
    return e2.build_e2(runs, tasks, list(se.COHORTS), 3, B=B, seed=20261115)


def test_load_marks_conditions_and_judge(e2_study):
    _, _, _, _, runs = e2_study
    assert set(runs["detail"]) == {"detailed", "brief"}
    assert not runs["prompt_file_mismatch"].any()
    r = runs.set_index("unit")
    b = runs[runs["detail"] == "brief"].set_index("unit")
    assert b.loc["claude-sonnet/t01/vibe-r1", "judge_status"] == "none"
    assert pd.isna(b.loc["claude-sonnet/t01/vibe-r1", "score"])
    assert b.loc["claude-sonnet/t03/spec-r1", "judge_status"] == "rejected"
    assert pd.isna(b.loc["claude-sonnet/t03/spec-r1", "score"])
    assert b.loc["claude-sonnet/t01/vibe-r3", "score"] == pytest.approx(0.25)
    assert b.loc["claude-sonnet/t01/vibe-r3", "score_core"] == pytest.approx(1 / 3)
    assert not bool(b.loc["codex-luna/t04/vibe-r3", "valid"])
    assert len(r.index.unique()) < len(runs)  # the same unit name exists in both conditions


def test_primary_brief_score_difference(e2_summary):
    s, _ = e2_summary
    est = s["estimates"]
    son = est["primary.score.claude-sonnet.all"]
    assert son["estimate"] == pytest.approx(0.5) and son["n_tasks"] == 23
    assert son["ci_low"] == pytest.approx(0.5) and son["ci_high"] == pytest.approx(0.5)
    # 3 valid unscored sonnet brief runs (2 without judge.json, 1 rejected) are counted
    assert son["n_null_runs"] == 3
    cod = est["primary.score.codex-luna.all"]
    assert cod["estimate"] == pytest.approx(0.0) and cod["n_tasks"] == 22  # t02 spec unjudged
    assert est["primary.score.pooled.all"]["estimate"] == pytest.approx(6 / 23)
    assert est["primary.score_core.claude-sonnet.all"]["estimate"] == pytest.approx(2 / 3)
    assert est["primary.score_core.codex-luna.all"]["estimate"] == pytest.approx(-1 / 3)
    assert est["primary.score.claude-sonnet.large"]["n_tasks"] == 3
    assert est["primary.score.claude-sonnet.large"]["reference_only"] is True


def test_missing_judge_is_excluded_not_imputed(e2_study):
    *_, runs = e2_study
    # imputing 0 for the two unjudged t01 vibe runs would pull this cell mean to 0.25 / 3
    t = e2.detail_arm_table(runs[runs["valid"].astype(bool)], "score", "claude-sonnet")
    assert t.loc["t01", "brief_vibe"] == pytest.approx(0.25)
    assert (
        "t02"
        not in e2.detail_arm_table(runs[runs["valid"].astype(bool)], "score", "codex-luna").index
    )


def test_coverage_counts(e2_summary):
    s, tables = e2_summary
    tot = {(r["detail"], r["cohort"]): r for r in s["coverage_totals"]}
    son, cod = tot[("brief", "claude-sonnet")], tot[("brief", "codex-luna")]
    assert son["expected"] == 138 and son["graded"] == 138 and son["judged"] == 135
    assert son["graded_not_judged"] == 3 and son["judge_rejected"] == 1
    assert cod["graded"] == 137 and cod["not_finished"] == 1 and cod["judged"] == 134
    assert tot[("detailed", "codex-luna")]["judged"] == 138
    assert s["unjudged_valid_units"] == 6 and len(tables["unjudged_units"]) == 6


def test_two_by_two_interaction(e2_summary):
    s, _ = e2_summary
    est = s["estimates"]
    assert est["x2.score.claude-sonnet.interaction"]["estimate"] == pytest.approx(0.25)
    assert est["x2.score.claude-sonnet.diff.detailed"]["estimate"] == pytest.approx(0.25)
    assert est["x2.score.claude-sonnet.diff.brief"]["estimate"] == pytest.approx(0.5)
    assert est["x2.score.claude-sonnet.detail_effect.spec"]["estimate"] == pytest.approx(-0.25)
    assert est["x2.score.codex-luna.interaction"]["estimate"] == pytest.approx(0.0)
    assert est["x2.score.pooled.interaction"]["estimate"] == pytest.approx(3 / 23)
    assert est["x2.ai_tests_added.claude-sonnet.interaction"]["estimate"] == pytest.approx(2)
    assert est["x2.ai_tests_added.codex-luna.interaction"]["estimate"] == pytest.approx(0)
    assert est["x2.ai_tests_added.pooled.interaction"]["estimate"] == pytest.approx(1)
    assert "x2.hidden_pass_rate.pooled.interaction" in est
    assert "not a correctness measure" in s["meta"]["notes"]["hidden_pass_rate"]


def test_bootstrap_matches_locked_scheme():
    # the 2 x 2 resamples tasks jointly for the four cells: its interval equals boot_stat's
    from sdlc_analysis.bootstrap import boot_stat

    t = pd.DataFrame({c: [0.1 * i + j for i in range(8)] for j, c in enumerate(e2.COLS4)})
    t.iloc[3, 2] = 2.0
    got = e2.interaction(t, B=999, seed=20261115)["interaction"]
    ref = boot_stat(
        t.to_numpy(),
        lambda x: ((x[..., 2] - x[..., 3]) - (x[..., 0] - x[..., 1])).mean(-1),
        B=999,
        seed=20261115,
    )
    assert (got.estimate, got.ci_low, got.ci_high) == (ref.estimate, ref.ci_low, ref.ci_high)


def test_judge_validity_counts():
    v = pd.DataFrame(
        {
            "detail": ["detailed"] * 6 + ["brief"],
            "judged": [True, True, True, True, True, False, True],
            "task_id": ["a", "a", "b", "b", "c", "c", "c"],
            "cohort": ["x"] * 7,
            "judge_all_met": [True, False, True, False, False, None, True],
            "hidden_all_pass": [True, False, False, True, False, True, True],
            "task_pass": [True, False, False, True, False, True, True],
            "score": [1.0, 0.5, 1.0, 0.75, 0.25, None, 1.0],
            "hidden_pass_rate": [1.0, 0.4, 0.8, 1.0, 0.1, 1.0, 1.0],
        }
    )
    r = e2.judge_validity(v, B=200, seed=1)
    assert r["n_units"] == 5
    assert (r["both_pass"], r["judge_only"], r["tests_only"], r["neither"]) == (1, 1, 1, 2)
    assert r["agreement"]["estimate"] == pytest.approx(3 / 5)
    # po = .6; pe = (2/5)(2/5) + (3/5)(3/5) = .52; kappa = .08 / .48
    assert r["kappa"] == pytest.approx(0.08 / 0.48)
    assert r["p_all_met_given_pass"] == pytest.approx(0.5)


def test_cli_writes_outputs(e2_study, tmp_path):
    tasks_dir, detailed, brief, _, _ = e2_study
    out = tmp_path / "e2"
    assert (
        e2.main(
            [
                "--detailed",
                str(detailed),
                "--brief",
                str(brief),
                "--tasks",
                str(tasks_dir),
                "--out",
                str(out),
                "--bootstrap",
                "200",
                "--cohorts",
                ",".join(se.COHORTS),
            ]
        )
        == 0
    )
    s = json.loads((out / "summary.json").read_text())
    assert s["meta"]["bootstrap"]["B"] == 200 and "thăm dò" in s["meta"]["exploratory"]
    for f in (
        "runs.csv",
        "coverage.csv",
        "unjudged_units.csv",
        "task_cells.csv",
        "estimates.csv",
        "figures/e2_score_diff.png",
        "figures/e2_detail_x_arm_score.pdf",
    ):
        assert (out / f).is_file(), f
    assert e2.B_E2 == 9999 and e2.parse_args(["--brief", "x"]).bootstrap == 9999


def test_brief_only_without_detailed_judgement(e2_study, tmp_path):
    tasks_dir, _, brief, _, _ = e2_study
    tasks, runs = e2.load_e2([], [brief], tasks_dir)
    s, _ = e2.build_e2(runs, tasks, list(se.COHORTS), 3, B=50)
    assert s["meta"]["score_on_detailed"] is False
    assert not any(k.startswith("x2.score.") for k in s["estimates"])
    assert s["estimates"]["primary.score.claude-sonnet.all"]["estimate"] == pytest.approx(0.5)
