import json

import pandas as pd
import pytest
import synthetic as syn

from sdlc_analysis import e1, load
from sdlc_analysis.load import load_runs, load_tasks


@pytest.fixture(scope="module")
def haiku_study(tmp_path_factory):
    """The synthetic study plus a claude-haiku cohort (written as sonnet units, then renamed)."""
    root = tmp_path_factory.mktemp("e1")
    tasks_dir, results = syn.write_study(root)
    tmp = root / "tmp"
    for tier, tasks in syn.TIERS.items():
        for tid in tasks:
            for arm in ("spec", "vibe"):
                for rep in (1, 2, 3):
                    syn.write_unit(
                        tmp, "claude-sonnet", tid, tier, arm, rep, arm == "spec" and rep == 1
                    )
    haiku = root / "haiku"
    haiku.mkdir()
    (tmp / "claude-sonnet").rename(haiku / "claude-haiku")
    for f in list(haiku.rglob("meta.json")) + list(haiku.rglob("transcript.jsonl")):
        f.write_text(f.read_text().replace("claude-sonnet", "claude-haiku"))
    return tasks_dir, results, haiku


def test_locked_loader_fails_on_unpriced_cohort_and_wrapper_marks_cost_unknown(haiku_study):
    tasks_dir, _, haiku = haiku_study
    tasks = load_tasks(tasks_dir)
    with pytest.raises(KeyError):
        load_runs(haiku, tasks)
    orig = load.cost_usd
    with e1.unpriced_cohort_cost_unknown():
        runs = load_runs(haiku, tasks)
    assert load.cost_usd is orig  # restored
    assert runs["cost_usd"].isna().all() and (runs["tokens_total"] > 0).all()


def test_priced_cohorts_unchanged_by_wrapper(haiku_study):
    tasks_dir, results, _ = haiku_study
    tasks = load_tasks(tasks_dir)
    plain = load_runs(results, tasks)
    with e1.unpriced_cohort_cost_unknown():
        wrapped = load_runs(results, tasks)
    pd.testing.assert_series_equal(plain["cost_usd"], wrapped["cost_usd"])


def test_e1_argv_defaults():
    a = e1.e1_argv(["--results", "x"])
    assert a[a.index("--cohorts") + 1] == "claude-sonnet,claude-opus,codex-luna,claude-haiku"
    assert a[a.index("--out") + 1].endswith("data/results/analysis/e1")
    a = e1.e1_argv(["--results", "x", "--out", "o", "--cohorts", "claude-haiku"])
    assert a.count("--out") == 1 and a.count("--cohorts") == 1


def test_e1_runs_the_locked_analysis_with_haiku(haiku_study, tmp_path):
    tasks_dir, results, haiku = haiku_study
    out = tmp_path / "e1"
    assert (
        e1.main(
            [
                "--results",
                str(results),
                str(haiku),
                "--tasks",
                str(tasks_dir),
                "--out",
                str(out),
                "--bootstrap",
                "200",
                "--model-bootstrap",
                "2",
            ]
        )
        == 0
    )
    s = json.loads((out / "summary.json").read_text())
    assert "exploratory" in s["meta"]["exploratory"]
    assert s["meta"]["cohorts"] == list(e1.E1_COHORTS)
    # haiku: spec passes 1 of 3, vibe 0 of 3 in every task
    assert s["estimates"]["pass_diff.claude-haiku.small"]["estimate"] == pytest.approx(1 / 3)
    assert s["estimates"]["cost_eff.claude-haiku.small.spec.cost_per_pass"]["estimate"] is None
