import pandas as pd
import pytest
import synthetic as syn

from sdlc_analysis.labels import (
    LABELS,
    cohen_kappa,
    kappa_report,
    labeling_template,
    passing_sample,
)


def test_label_set_is_the_locked_prereg_set():
    assert LABELS == ("hieu_sai", "lam_thieu", "sai_giao_dien", "hong_chuc_nang_cu", "loi_logic",
                      "khong_hoan_thanh", "de_bai_thieu", "sai_api_co_san", "loi_moi_truong")


def test_kappa_textbook_example():
    # 50 items: yes/yes 20, yes/no 5, no/yes 10, no/no 15 -> po 0.7, pe 0.5, kappa 0.4
    a = ["y"] * 25 + ["n"] * 25
    b = ["y"] * 20 + ["n"] * 5 + ["y"] * 10 + ["n"] * 15
    k = cohen_kappa(pd.Series(a), pd.Series(b))
    assert k["kappa"] == pytest.approx(0.4)
    assert k["po"] == pytest.approx(0.7) and k["pe"] == pytest.approx(0.5)


def test_kappa_perfect_and_chance():
    s = pd.Series(["a", "b", "c", "a"])
    assert cohen_kappa(s, s)["kappa"] == pytest.approx(1.0)
    one = pd.Series(["a", "a"])
    assert cohen_kappa(one, one)["kappa"] is None  # pe = 1: undefined


def test_kappa_report_from_two_sheets(tmp_path):
    a = pd.DataFrame({"unit_id": ["u1", "u2", "u3", "u4"],
                      "label": ["hieu_sai", "loi_logic", "lam_thieu", "loi_logic"],
                      "note": ["", "lộ cách làm", "", ""]})
    b = pd.DataFrame({"unit_id": ["u4", "u3", "u2", "u1"],
                      "label": ["loi_logic", "lam_thieu", "hieu_sai", "hieu_sai"],
                      "note": ["", "", "Lộ cách làm: plan", ""]})
    pa, pb = tmp_path / "a.csv", tmp_path / "b.csv"
    a.to_csv(pa, index=False)
    b.to_csv(pb, index=False)
    r = kappa_report(pa, pb)
    assert r["n_both"] == 4 and r["n_agree"] == 3
    assert r["crosstab"]["loi_logic"]["hieu_sai"] == 1
    assert r["revealed_arm"] == {"rater_a": 1, "rater_b": 1, "either": 1, "share_either": 0.25}
    assert r["disagreements"] == ["u2"]
    assert r["invalid_labels"] == []


def test_labeling_template_covers_failing_claude_runs_only(study):
    runs = study[3]
    sheet, key = labeling_template(runs[runs["valid"]], seed=20261115)
    v = runs[runs["valid"] & runs["cohort"].str.startswith("claude") & ~runs["task_pass"].astype(bool)]
    assert len(sheet) == len(v) == len(key)
    assert list(sheet.columns) == ["unit_id", "label", "note"]
    assert sheet["unit_id"].is_unique
    assert set(key["unit"]) == set(v["unit"])
    # ids reveal nothing: no cohort, arm or rep text; order is shuffled
    assert not sheet["unit_id"].str.contains("spec|vibe|claude").any()
    assert list(key["unit"]) != sorted(key["unit"])
    again, _ = labeling_template(runs[runs["valid"]], seed=20261115)
    assert again.equals(sheet)


def test_passing_sample_allocation_and_reproducibility(study):
    runs = study[3]
    valid = runs[runs["valid"]]
    s = passing_sample(valid, seed=20261115)
    assert len(s) == 20
    assert all(s["task_pass"].astype(bool)) and set(s["cohort"]) <= {"claude-sonnet", "claude-opus"}
    by = s.groupby(["arm", "tier"]).size().to_dict()
    # spec passes per tier: 60, 25, 18 -> 6, 2, 2; vibe: 45, 10, 3 -> 8, 2, 0
    assert by == {("spec", "small"): 6, ("spec", "medium"): 2, ("spec", "large"): 2,
                  ("vibe", "small"): 8, ("vibe", "medium"): 2}
    assert passing_sample(valid, seed=20261115)["unit"].tolist() == s["unit"].tolist()
    assert not s.duplicated("unit").any()
    assert syn  # fixture module in use
