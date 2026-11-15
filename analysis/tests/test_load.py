import pandas as pd
import pytest
import synthetic as syn

from sdlc_analysis.load import completeness, expected_units, load_tasks


def test_tasks_table(study):
    _, _, tasks, _ = study
    assert len(tasks) == 23
    t = tasks.set_index("task_id")
    assert t.loc["t01", "tier"] == "small" and t.loc["f03", "tier"] == "large"
    assert t.loc["m02", "src_lines"] == 380
    assert t.loc["t04", "size_group"] == "small" and t.loc["t06", "size_group"] == "medium"
    assert t.loc["t11", "size_group"] == "large" and pd.isna(t.loc["f01", "size_group"])


def test_task_selection_and_pilot_flag(tmp_path):
    d = tmp_path / "p01"
    d.mkdir()
    (d / "task.toml").write_text(
        'id = "p01"\ncommit = "c"\nparent = "p"\nlayer = "domain"\nsrc_lines = 201\n'
        'hidden_tests = []\npilot = true\nbaseline_radon_mi = 49.6\n'
    )
    assert load_tasks(tmp_path).empty  # pilots are left out unless named
    t = load_tasks(tmp_path, ["p01"])
    assert t.iloc[0]["tier"] == "small" and bool(t.iloc[0]["pilot"])
    with pytest.raises(ValueError):
        load_tasks(tmp_path, ["zz"])


def test_runs_table_values(study):
    _, _, _, runs = study
    assert len(runs) == 4 * 23 * 2 * 3  # every unit directory, including non-done
    r = runs.set_index(["cohort", "task_id", "arm", "rep"])
    row = r.loc[("claude-sonnet", "t05", "spec", 1)]
    assert bool(row["valid"]) and bool(row["task_pass"])
    assert row["tier"] == "small" and row["src_lines"] == 80
    assert row["static_errors"] == 1 and row["radon_mi_delta"] == pytest.approx(-2.0)
    assert row["tokens_total"] == syn.run_tokens("claude-sonnet", "spec")
    assert row["cost_usd"] == pytest.approx(syn.run_cost("claude-sonnet", "spec"))
    assert bool(row["pytest_ran"]) and bool(row["patch_design_doc"]) and bool(row["patch_plan_doc"])
    assert row["hidden_pass_rate"] == 1.0 and row["patch_lines"] == 210
    v = r.loc[("codex-luna", "t05", "vibe", 3)]
    assert not v["task_pass"] and v["regressions_n"] == 1 and bool(v["regression_any"])
    assert v["cost_usd"] == pytest.approx(syn.run_cost("codex-luna", "vibe"))
    assert v["cost_usd_upper"] > v["cost_usd"]  # codex long-context price as a bound
    assert not r.loc[("claude-sonnet", "t01", "spec", 3)]["process_artifacts"]
    assert bool(r.loc[syn.UPSTREAM]["upstream"])
    assert bool(r.loc[syn.CONFIG_TOUCHED]["pytest_config_touched"])
    assert r.loc[syn.EXCLUDED_ERROR]["status"] == "excluded"
    assert not r.loc[syn.EXCLUDED_ERROR]["valid"]
    assert r.loc[syn.DEFERRED]["status"] == "deferred"


def test_expected_units_and_completeness(study):
    _, _, tasks, runs = study
    exp = expected_units(tasks, list(syn.COHORTS), reps=3)
    assert len(exp) == 4 * 23 * 6
    comp = completeness(exp, runs).set_index(["cohort", "tier"])
    assert bool(comp.loc[("claude-sonnet", "large"), "complete"])  # excluded error counts
    assert comp.loc[("claude-sonnet", "large"), "excluded"] == 1
    assert not comp.loc[("codex-luna", "large"), "complete"]
    assert comp.loc[("codex-luna", "large"), "pending"] == 1
    assert comp.loc[("claude-opus", "small"), "valid"] == 90


def test_missing_unit_dirs_are_pending(tmp_path):
    tasks_dir, results = syn.write_study(tmp_path, statuses=False)
    import shutil

    shutil.rmtree(results / "agy-gemini" / "m01" / "spec-r1")
    from sdlc_analysis.load import load_runs

    tasks = load_tasks(tasks_dir)
    comp = completeness(expected_units(tasks, list(syn.COHORTS), 3), load_runs(results, tasks))
    c = comp.set_index(["cohort", "tier"])
    assert not c.loc[("agy-gemini", "medium"), "complete"]
    assert c.loc[("agy-gemini", "medium"), "missing"] == 1
