import csv

import pytest

from retro.cli import main

SPECS = [
    {
        "message": "docs: plan",
        "date": "2026-09-01T10:00:00+00:00",
        "files": {"backend/docs/superpowers/plans/p.md": "### Task 1: a\n- Create: `src/x.py`\n"},
    },
    {
        "message": "feat: x",
        "date": "2026-09-02T10:00:00+00:00",
        "files": {"backend/src/x.py": "a\n"},
    },
    {"message": "feat: y", "date": "2026-09-03T10:00:00+00:00", "files": {"frontend/y.tsx": "a\n"}},
    {
        "message": "fix: x",
        "date": "2026-09-04T10:00:00+00:00",
        "files": {"backend/src/x.py": "b\n"},
    },
]


@pytest.fixture
def run_all(make_repo, tmp_path):
    repo = make_repo(SPECS)
    out = tmp_path / "out"
    sessions = tmp_path / "no-sessions"

    def run():
        args = ["all", "--repo", str(repo), "--out", str(out), "--sessions-dir", str(sessions)]
        return main(args)

    return run, out


def test_all_on_fixture_repo(run_all):
    run, out = run_all
    assert run() == 0
    for name in [
        "commits.csv",
        "lifecycle_by_stage.csv",
        "lifecycle_by_week.csv",
        "spec_trace.csv",
        "rework.csv",
        "rework_summary.csv",
        "rework_by_stage.csv",
        "sessions.csv",
        "session_tools.csv",
        "summary.md",
        "plan-corpus/index.csv",
        "plan-corpus/summary.md",
        "link-check.csv",
        "figures/lifecycle_by_week.png",
        "figures/rework_by_group.png",
    ]:
        assert (out / name).exists(), name
    assert not (out / "plan-corpus/files").exists()
    summary = (out / "summary.md").read_text()
    assert "Đây là quan sát, không phải quan hệ nhân quả." in summary
    assert "chưa chấm" in summary
    assert "0 commit có Co-Authored-By" in summary
    with (out / "rework.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert [(r["has_plan"], r["rework"]) for r in rows] == [("True", "1"), ("False", "0")]
    with (out / "link-check.csv").open() as fh:
        sheet = list(csv.DictReader(fh))
    assert len(sheet) == 2 and all(r["an_verdict"] == "" for r in sheet)
    assert sheet[0]["rule_plan"] == "backend/docs/superpowers/plans/p.md"


def test_all_keeps_existing_link_check(run_all):
    run, out = run_all
    run()
    sheet = out / "link-check.csv"
    text = sheet.read_text().replace(",\n", ",correct\n", 1)
    sheet.write_text(text)
    run()
    assert sheet.read_text() == text


def test_link_accuracy(tmp_path, capsys):
    sheet = tmp_path / "link-check.csv"
    with sheet.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sha", "subject", "rule_plan", "an_verdict"])
        w.writerows([["a", "s", "p", "correct"], ["b", "s", "", "wrong"], ["c", "s", "p", ""]])
    (tmp_path / "summary.md").write_text("# x\n- Độ chính xác của quy tắc nối: chưa chấm\n")
    assert main(["link-accuracy", "--out", str(tmp_path)]) == 0
    assert capsys.readouterr().out.strip() == "1/2"
    assert "- Độ chính xác của quy tắc nối: 1/2" in (tmp_path / "summary.md").read_text()


def test_plan_corpus_materialize(make_repo, tmp_path):
    repo = make_repo(SPECS)
    out = tmp_path / "out"
    assert main(["plan-corpus", "--materialize", "--repo", str(repo), "--out", str(out)]) == 0
    assert (out / "plan-corpus/files/backend/docs/superpowers/plans/p.md").exists()
