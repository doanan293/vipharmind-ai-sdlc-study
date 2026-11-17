import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest
import synthetic_e2 as se

from sdlc_analysis import e2, humancheck

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "draw_human_check.py"


def _script():
    spec = importlib.util.spec_from_file_location("draw_human_check", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def brief_study(tmp_path_factory):
    root = tmp_path_factory.mktemp("hc")
    tasks_dir, _, brief = se.write_e2(root)
    tasks, runs = e2.load_e2([], [brief], tasks_dir)
    return tasks_dir, brief, tasks, runs


def _sheet(verdicts, code="h1"):
    return pd.DataFrame(
        {"unit_code": code, "item_n": range(1, len(verdicts) + 1), "verdict": verdicts}
    )


def test_kappa_known_values():
    a = _sheet(["met", "met", "not_met", "not_met"])
    b = _sheet(["met", "not_met", "not_met", "not_met"])
    r = humancheck.item_agreement(a, b)
    # po = .75; pe = .5 * .25 + .5 * .75 = .5; kappa = .5
    assert r["agreement"] == pytest.approx(0.75) and r["kappa"] == pytest.approx(0.5)
    assert r["n_items"] == 4 and r["crosstab"]["met"]["not_met"] == 1


def test_kappa_three_way_vs_binary_and_blanks():
    a = _sheet(["met", "unclear", "not_met", "", "met", "bogus"])
    b = _sheet(["met", "not_met", "not_met", "met", "met", "met"])
    r = humancheck.item_agreement(a, b)
    assert r["n_items"] == 4  # blank and invalid verdicts are left out and counted
    assert r["invalid_or_blank_a"] == 2 and r["invalid_or_blank_b"] == 0
    assert r["agreement"] == pytest.approx(0.75)
    assert r["agreement_binary"] == pytest.approx(1.0)  # unclear scores as not met
    assert r["kappa_binary"] == pytest.approx(1.0)


def test_agreement_report_pairs():
    s = {"loi": _sheet(["met", "not_met"]), "bao": _sheet(["met", "met"])}
    rep = humancheck.agreement_report(s, _sheet(["met", "not_met"]))
    assert set(rep) == {"loi~bao", "loi~judge", "bao~judge"}
    assert rep["loi~judge"]["agreement"] == 1.0 and rep["loi~bao"]["agreement"] == 0.5


def test_draw_is_stratified_seeded_and_blind(brief_study):
    _, _, _, runs = brief_study
    valid = runs[runs["valid"].astype(bool)]
    key = humancheck.draw(valid, list(se.COHORTS), 20261115)
    assert len(key) == 12  # 2 cohorts x 2 arms x 3
    assert key.groupby(["cohort", "arm"]).size().eq(3).all()
    assert key.equals(humancheck.draw(valid, list(se.COHORTS), 20261115))
    assert not key.equals(humancheck.draw(valid, list(se.COHORTS), 1))
    for c in key["unit_code"]:
        assert c.startswith("h") and len(c) == 9
        assert not any(w in c for w in ("spec", "vibe", "claude", "codex"))
    with pytest.raises(ValueError, match="stratum"):
        humancheck.draw(valid.head(4), list(se.COHORTS), 20261115)


def test_judge_sheet_reads_judge_json(brief_study):
    _, _, _, runs = brief_study
    key = humancheck.draw(runs[runs["valid"].astype(bool)], list(se.COHORTS), 20261115)
    j = humancheck.judge_sheet(key)
    assert set(j["verdict"]) <= set(humancheck.VERDICTS)
    assert j.groupby("unit_code").size().max() == 4


def test_script_refuses_unfinished_and_force_builds_packets(brief_study, tmp_path):
    tasks_dir, brief, _, _ = brief_study
    mod = _script()
    base = [
        "draw",
        "--brief",
        str(brief),
        "--tasks",
        str(tasks_dir),
        "--cohorts",
        ",".join(se.COHORTS),
    ]
    out, key = tmp_path / "packets", tmp_path / "key.csv"
    with pytest.raises(SystemExit, match="not drawing yet"):
        mod.main(base + ["--out", str(out), "--key", str(key)])
    with pytest.raises(SystemExit, match="explicit"):
        mod.main(base + ["--force"])
    assert mod.main(base + ["--force", "--out", str(out), "--key", str(key)]) == 0
    k = pd.read_csv(key)
    assert len(k) == 12 and "unit" in k and "root" in k
    for rater in ("loi", "bao"):
        sheet = pd.read_csv(out / rater / f"sheet-{rater}.csv")
        assert list(sheet.columns) == ["unit_code", "item_n", "verdict", "note"]
        assert len(sheet) == 12 * 4
        d = out / rater / k["unit_code"][0]
        assert {p.name for p in d.iterdir()} == {"brief.md", "change.diff", "checklist.md"}
        assert "[exact]" not in (d / "checklist.md").read_text()
        assert "docs/design.md" not in (d / "change.diff").read_text()
        assert "a.py" in (d / "change.diff").read_text()
        assert not any(
            w in " ".join(p.name for p in (out / rater).rglob("*"))
            for w in ("spec", "vibe", "claude-", "codex")
        )
    with pytest.raises(SystemExit, match="exists"):
        mod.main(base + ["--force", "--out", str(out), "--key", str(key)])
    # kappa subcommand: identical sheets agree fully with each other
    s = pd.read_csv(out / "loi" / "sheet-loi.csv")
    s["verdict"] = "met"
    s.to_csv(tmp_path / "a.csv", index=False)
    s.to_csv(tmp_path / "b.csv", index=False)
    rep_path = tmp_path / "agree.json"
    assert (
        mod.main(
            [
                "kappa",
                "--key",
                str(key),
                "--loi",
                str(tmp_path / "a.csv"),
                "--bao",
                str(tmp_path / "b.csv"),
                "--out",
                str(rep_path),
            ]
        )
        == 0
    )
    rep = json.loads(rep_path.read_text())
    assert rep["loi~bao"]["agreement"] == 1.0 and rep["loi~judge"]["n_items"] == 4 * (
        12 - len(rep["units_without_judge"])
    )


def test_finished_check_ignores_only_stopped_cohorts():
    import pandas as pd

    cov = pd.DataFrame(
        [
            {"detail": "brief", "cohort": "a", "expected": 4, "not_finished": 0},
            {"detail": "brief", "cohort": "b", "expected": 4, "not_finished": 3},
        ]
    )
    assert humancheck.finished_check(cov, 8) == [
        "3 brief units not finished (run, pending or missing)"
    ]
    assert humancheck.finished_check(cov, 8, frozenset({"b"})) == []
    assert humancheck.finished_check(cov, 8, frozenset({"a"}))
