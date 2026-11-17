import json

import pandas as pd
import pytest
import synthetic as syn

from sdlc_analysis.cli import main


@pytest.fixture(scope="module")
def out(study, tmp_path_factory):
    tasks_dir, results, _, _ = study
    labels = tmp_path_factory.mktemp("labels")
    a = pd.DataFrame({"unit_id": ["u1", "u2"], "label": ["loi_logic", "hieu_sai"], "note": ""})
    a.to_csv(labels / "a.csv", index=False)
    a.to_csv(labels / "b.csv", index=False)
    o = tmp_path_factory.mktemp("out")
    assert (
        main(
            [
                "--results",
                str(results),
                "--tasks",
                str(tasks_dir),
                "--out",
                str(o),
                "--bootstrap",
                "500",
                "--model-bootstrap",
                "5",
                "--draw-passing-sample",
                "--labels",
                str(labels / "a.csv"),
                str(labels / "b.csv"),
            ]
        )
        == 0
    )
    return o, json.loads((o / "summary.json").read_text())


def test_passing_sample_is_drawn_only_when_asked_and_never_silently_redrawn(out, study, tmp_path):
    _, s = out
    tasks_dir, results, _, _ = study
    assert s["passing_sample"] == {"drawn": True}
    base = [
        "--results",
        str(results),
        "--tasks",
        str(tasks_dir),
        "--bootstrap",
        "50",
        "--model-bootstrap",
        "2",
    ]
    # without the flag: no sample is written
    fresh = tmp_path / "fresh"
    main(base + ["--out", str(fresh)])
    assert not (fresh / "passing_sample.csv").exists()
    assert json.loads((fresh / "summary.json").read_text())["passing_sample"] == {"drawn": False}
    # with the flag on an existing sample: refused without --force
    (fresh / "passing_sample.csv").write_text("kept\n")
    with pytest.raises(SystemExit, match="--force"):
        main(base + ["--out", str(fresh), "--draw-passing-sample"])
    assert (fresh / "passing_sample.csv").read_text() == "kept\n"
    main(base + ["--out", str(fresh), "--draw-passing-sample", "--force"])
    assert len(pd.read_csv(fresh / "passing_sample.csv")) == 20


def test_outputs_exist(out):
    o, s = out
    for f in (
        "runs.csv",
        "runs.parquet",
        "task_diffs.csv",
        "pooled_task_diffs.csv",
        "passing_sample.csv",
        "labeling/sheet-template.csv",
        "labeling/key-PRIVATE.csv",
        "figures/effect_vs_size.pdf",
        "figures/effect_vs_size.png",
        "figures/pass_diff_by_cohort.pdf",
        "figures/two_by_two_small.png",
        "figures/cost_per_pass.pdf",
    ):
        assert (o / f).is_file(), f
    assert len(pd.read_parquet(o / "runs.parquet")) == 552
    assert s["meta"]["bootstrap"] == {
        "B": 500,
        "seed": 20261115,
        "ci": s["meta"]["bootstrap"]["ci"],
    }


def test_h1_confirmatory(out):
    _, s = out
    h1 = s["estimates"]["h1.primary"]
    assert h1["estimate"] == pytest.approx(1 / 3) and h1["n_tasks"] == 15
    assert s["verdicts"]["H1"] == "supported"


def test_completeness_drives_pooling(out):
    _, s = out
    comp = {(r["cohort"], r["tier"]): r["complete"] for r in s["completeness"]}
    assert comp[("codex-luna", "large")] is False and comp[("claude-sonnet", "large")] is True
    assert "pass_diff.codex-luna.large" not in s["estimates"]
    inc = s["estimates"]["descriptive_incomplete.codex-luna.large"]
    assert inc["not_run_or_pending"] == 1 and inc["valid_runs"] == 17
    assert s["h5"]["cohorts"] == ["claude-sonnet", "claude-opus", "agy-gemini"]
    assert s["not_run_units"] == [
        {"cohort": "codex-luna", "task_id": "f02", "arm": "spec", "rep": 2, "status": "deferred"}
    ]
    assert s["estimates"]["pooled.pass_diff.small"]["estimate"] == pytest.approx(1 / 6)
    assert s["estimates"]["pooled.pass_diff.large"]["estimate"] == pytest.approx(7 / 9)


def test_h5(out):
    _, s = out
    assert s["estimates"]["h5.primary"]["estimate"] == pytest.approx(2 / 3)
    assert s["estimates"]["h5.hidden_pass_rate"]["estimate"] == pytest.approx(0.2)
    m = s["h5"]["mixed_model"]
    # the synthetic effects are constant within a tier (no task-level variance): both mixed
    # levels are singular, the ladder ends at level 3, and a difference-scale slope cannot give
    # the logit guard, so H5 stays "inconclusive" although the primary CI is above 0
    assert m["model_level"] == 3
    assert [a["ok"] for a in m["attempts"]] == [False, False, False, True]
    assert "singular" in m["attempts"][1]["reason"]
    assert m["interaction"]["scale"] == "difference" and m["interaction"]["coef"] > 0
    assert s["estimates"]["h5.primary"]["ci_low"] > 0
    assert s["verdicts"]["H5"] == "inconclusive"
    assert set(s["h5"]["reference_only_tiers"]) == {"medium", "large"}
    assert m["interaction"]["bootstrap"]["B"] == 5
    assert m["interaction"]["ci_low"] is not None


def test_h5_graded_lines_sensitivity(out):
    _, s = out
    g = s["h5"]["mixed_model_graded"]
    assert g["size_variable"] == "log_graded_src_lines"
    assert g["tasks_without_size"] == ["m03"]
    assert g["n_tasks"] == 22
    # synthetic graded lines fall as src_lines rise: the interaction flips sign
    assert g["interaction"]["coef"] < 0 < s["h5"]["mixed_model"]["interaction"]["coef"]


def test_case_study_and_new_descriptives(out):
    _, s = out
    cs = s["case_study"]
    # sonnet large: every task has difference 1, ties go to the largest patch (f03, 1300 lines)
    assert cs["task_id"] == "f03" and cs["pass_diff"] == 1.0
    assert cs["units"] == {"spec": "claude-sonnet/f03/spec-r1", "vibe": "claude-sonnet/f03/vibe-r1"}
    d = s["descriptives"]
    assert d["codex_runs_with_several_usage_records"] == 0
    assert d["offtable_models"] == []
    assert d["shared_cpu_window"]["runs_started"] == 0
    assert "cost_eff_upper.codex-luna.small.spec.cost_per_pass" in s["estimates"]


def test_h4_and_secondary_verdicts(out):
    _, s = out
    e, v = s["estimates"], s["verdicts"]
    assert e["h4.small.diff_of_diffs"]["estimate"] == pytest.approx(1 / 3)
    assert v["H4.small"] == "supported"
    assert v["H2.tokens_total.claude-sonnet.small"] == "supported"
    assert v["H2.wall_s.codex-luna.medium"] == "supported"
    assert v["H3a.static_errors.claude-opus.small"] == "supported"
    assert v["H3c.radon_mi_delta.claude-sonnet.small"] == "supported"  # -2 > -5 margin
    # only failing vibe runs regress: opus small vibe fails 1 of 3, spec never regresses
    assert e["secondary.regression_any.claude-opus.small"]["estimate"] == pytest.approx(-1 / 3)
    assert v["H3b.regression_any.claude-opus.small"] == "supported"
    # agy small: equal pass counts (1, 1) -> pass difference 0 -> inconclusive
    assert v["pass_diff.agy-gemini.small"] == "inconclusive"
    assert s["meta"]["n_secondary_comparisons"] == len(v) - 2  # minus H1 and its own copy


def test_sensitivity_known_values(out):
    _, s = out
    e = s["estimates"]
    assert e["sensitivity.spec_noncompliant.h1"]["estimate"] == pytest.approx(16 / 45)
    assert e["sensitivity.upstream_urls.h1"]["estimate"] == pytest.approx(16 / 45)
    assert e["sensitivity.pytest_config_touched.h1"]["estimate"] == pytest.approx(29 / 90)
    assert e["sensitivity.spec_noncompliant.h1"]["runs_dropped_all_cohorts"] == 1
    assert "sensitivity.overlap.h5" not in e  # needs --repo


def test_cost_effectiveness_and_descriptives(out):
    _, s = out
    e = s["estimates"]
    c = syn.run_cost("claude-sonnet", "spec")
    assert e["cost_eff.claude-sonnet.small.spec.cost_per_pass"]["estimate"] == pytest.approx(
        45 * c / 30
    )
    assert e["cost_eff.agy-gemini.medium.vibe.cost_per_pass"]["estimate"] is None
    d = s["descriptives"]
    assert d["excluded_by_arm"] == {"vibe": 1}
    assert d["prompt_sha256_check"]["violations"] == []
    comp = {(r["cohort"], r["tier"]): r for r in d["compliance_spec"]}
    assert comp[("claude-sonnet", "small")]["n"] == 44
    pr = {(r["cohort"], r["arm"]): r["share"] for r in d["pytest_ran"]}
    assert pr[("codex-luna", "spec")] == 1.0 and pr[("codex-luna", "vibe")] == 0.0


def test_kappa_and_labeling(out):
    o, s = out
    assert s["labels"]["kappa"] == pytest.approx(1.0)
    sheet = pd.read_csv(o / "labeling/sheet-template.csv")
    assert len(sheet) > 0 and set(sheet.columns) == {"unit_id", "label", "note"}
    assert len(pd.read_csv(o / "passing_sample.csv")) == 20


def test_size_groups_exploratory(out):
    _, s = out
    e = s["estimates"]
    assert e["exploratory.size_group.claude-sonnet.small"]["n_tasks"] == 5
    assert e["exploratory.size_group.claude-sonnet.large"]["n_tasks"] == 5


def test_overlap_sensitivity_drops_listed_tasks(study):
    from sdlc_analysis.report import build_summary

    _, _, tasks, runs = study
    s, _ = build_summary(
        runs,
        tasks,
        list(syn.COHORTS),
        3,
        B=200,
        seed=1,
        model_B=2,
        overlap={"pairs": [], "tasks": ["t01", "f01"]},
    )
    e = s["estimates"]["sensitivity.overlap.h5"]
    assert e["tasks_dropped"] == ["f01", "t01"]
    assert e["n_tasks"] == {"large": 2, "small": 14}
    assert e["estimate"] == pytest.approx(2 / 3)  # effects are constant within tiers


@pytest.mark.parametrize(
    ("scale", "expected"), [("logit", "supported"), ("difference", "inconclusive")]
)
def test_report_h5_verdict_uses_the_model_scale(study, monkeypatch, scale, expected):
    """Review N3: the H5 verdict through build_summary. The synthetic primary CI is above 0;
    a positive logit-scale interaction makes H5 supported, a difference-scale one cannot."""
    from sdlc_analysis import mixed
    from sdlc_analysis.report import build_summary

    def stub(runs, cohorts, **kw):
        return {
            "model_level": 1 if scale == "logit" else 3,
            "attempts": [],
            "interaction": {"coef": 0.4, "scale": scale, "ci_low": 0.1, "ci_high": 0.7},
        }

    monkeypatch.setattr(mixed, "fit_h5_model", stub)
    _, _, tasks, runs = study
    s, _ = build_summary(runs, tasks, list(syn.COHORTS), 3, B=200, seed=1, model_B=2)
    assert s["estimates"]["h5.primary"]["ci_low"] > 0
    assert s["verdicts"]["H5"] == expected
