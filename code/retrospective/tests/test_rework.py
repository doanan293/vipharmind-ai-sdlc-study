from datetime import datetime, timedelta

from retro.gitlog import Commit, FileChange, load_commits
from retro.rework import rework_by_stage, rework_count, rework_rows, rework_summary
from retro.specplans import load_spec_plan_files

DAY1 = datetime.fromisoformat("2026-09-01T10:00:00+00:00")


def _c(kind, day, *paths, sha=None):
    return Commit(
        sha or f"{kind}{day}{paths}",
        DAY1 + timedelta(days=day - 1),
        f"{kind}: x",
        kind,
        tuple(FileChange(p, 1, 0) for p in paths),
    )


def test_rework_window_and_overlap():
    feat = _c("feat", 1, "backend/a.py", "README.md")
    later = [
        _c("fix", 5, "backend/a.py"),  # counted
        _c("refactor", 16, "backend/a.py"),  # outside 14 days
        _c("fix", 3, "backend/b.py"),  # other file
        _c("chore", 2, "backend/a.py"),  # wrong type
        _c("fix", 4, "README.md"),  # docs-stage file does not count
        _c("fix", 1, "backend/a.py", sha="same-day-earlier"),  # not after feat
    ]
    later[-1] = Commit("x", DAY1 - timedelta(hours=1), "fix: x", "fix", later[-1].files)
    assert rework_count(feat, later) == 1


def test_rework_window_is_inclusive_at_14_days():
    feat = _c("feat", 1, "backend/a.py")
    assert rework_count(feat, [_c("refactor", 15, "backend/a.py")]) == 1


def _row(has_plan, rework, stage="backend"):
    return {"has_plan": has_plan, "rework": rework, "stage": stage}


def test_rework_summary_groups():
    rows = [_row(True, 0), _row(True, 1), _row(True, 2), _row(False, 0), _row(False, 0)]
    by_group = {r["group"]: r for r in rework_summary(rows)}
    assert by_group["with_plan"] == {
        "group": "with_plan",
        "n_feat": 3,
        "mean_rework": 1.0,
        "median_rework": 1,
        "share_with_rework": 2 / 3,
    }
    assert by_group["without_plan"]["mean_rework"] == 0.0
    assert by_group["without_plan"]["share_with_rework"] == 0.0


def test_rework_by_stage():
    rows = [_row(True, 2, "backend"), _row(False, 0, "backend"), _row(False, 1, "data")]
    by_stage = {r["stage"]: r for r in rework_by_stage(rows)}
    assert by_stage["backend"] == {
        "stage": "backend",
        "n_feat": 2,
        "mean_rework": 1.0,
        "share_with_rework": 0.5,
    }
    assert by_stage["data"]["n_feat"] == 1
    assert "frontend" not in by_stage


def test_rework_rows(make_repo):
    repo = make_repo(
        [
            {
                "message": "docs: plan",
                "date": "2026-09-01T10:00:00+00:00",
                "files": {"docs/superpowers/plans/p.md": "`backend/x.py`"},
            },
            {
                "message": "feat: x",
                "date": "2026-09-02T10:00:00+00:00",
                "files": {"backend/x.py": "a\nb\n"},
            },
            {
                "message": "fix: x",
                "date": "2026-09-03T10:00:00+00:00",
                "files": {"backend/x.py": "a\n"},
            },
            {
                "message": "feat: y",
                "date": "2026-09-04T10:00:00+00:00",
                "files": {"frontend/y.tsx": "a\n"},
            },
        ]
    )
    commits = load_commits(repo, ["HEAD"])
    rows = rework_rows(commits, load_spec_plan_files(repo, ["HEAD"]))
    assert [(r["stage"], r["lines_changed"], r["has_plan"], r["rework"]) for r in rows] == [
        ("backend", 2, True, 1),
        ("frontend", 1, False, 0),
    ]
    assert rows[0]["date"] == "2026-09-02"


def test_markdown_inside_subprojects_is_not_code():
    feat = _c("feat", 1, "backend/docs/superpowers/plans/p.md", "backend/src/a.py")
    later = [_c("fix", 3, "backend/docs/superpowers/plans/p.md")]
    assert rework_count(feat, later) == 0
