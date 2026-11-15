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
    assert main(["--results", str(results), "--tasks", str(tasks_dir), "--out", str(o),
                 "--bootstrap", "500", "--labels", str(labels / "a.csv"),
                 str(labels / "b.csv")]) == 0
    return o, json.loads((o / "summary.json").read_text())


def test_outputs_exist(out):
    o, s = out
    for f in ("runs.csv", "runs.parquet", "task_diffs.csv", "pooled_task_diffs.csv",
              "passing_sample.csv", "labeling/sheet-template.csv", "labeling/key-PRIVATE.csv",
              "figures/effect_vs_size.pdf", "figures/effect_vs_size.png",
              "figures/pass_diff_by_cohort.pdf", "figures/two_by_two_small.png",
              "figures/cost_per_pass.pdf"):
        assert (o / f).is_file(), f
    assert len(pd.read_parquet(o / "runs.parquet")) == 552
    assert s["meta"]["bootstrap"] == {"B": 500, "seed": 20261115, "ci": s["meta"]["bootstrap"]["ci"]}


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
    assert s["not_run_units"] == [{"cohort": "codex-luna", "task_id": "f02", "arm": "spec",
                                   "rep": 2, "status": "deferred"}]
    assert s["estimates"]["pooled.pass_diff.small"]["estimate"] == pytest.approx(1 / 6)
    assert s["estimates"]["pooled.pass_diff.large"]["estimate"] == pytest.approx(7 / 9)


def test_h5(out):
    _, s = out
    assert s["estimates"]["h5.primary"]["estimate"] == pytest.approx(2 / 3)
    assert s["estimates"]["h5.hidden_pass_rate"]["estimate"] == pytest.approx(0.2)
    m = s["h5"]["mixed_model"]
    assert m["model_level"] in (1, 2, 3)
    assert m["interaction"]["coef"] > 0
    assert s["verdicts"]["H5"] == "supported"
    assert set(s["h5"]["reference_only_tiers"]) == {"medium", "large"}


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
    assert s["meta"]["n_secondary_comparisons"] == len(v) - 1


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
        45 * c / 30)
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
    s, _ = build_summary(runs, tasks, list(syn.COHORTS), 3, B=200, seed=1,
                         overlap={"pairs": [], "tasks": ["t01", "f01"]})
    e = s["estimates"]["sensitivity.overlap.h5"]
    assert e["tasks_dropped"] == ["f01", "t01"]
    assert e["n_tasks"] == {"large": 2, "small": 14}
    assert e["estimate"] == pytest.approx(2 / 3)  # effects are constant within tiers
