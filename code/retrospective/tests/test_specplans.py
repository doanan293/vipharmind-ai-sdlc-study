import csv
from datetime import datetime

import pytest

from retro import CAMERA_READY_SHA, DEFAULT_REPO, MAIN_SHA
from retro.gitlog import Commit, load_commits
from retro.specplans import (
    has_preceding_plan,
    link_accuracy,
    load_spec_plan_files,
    referenced_code_paths,
    sample_for_manual_check,
    spec_trace_rows,
)

PLAN_PATH = "backend/docs/superpowers/plans/p.md"


def test_referenced_code_paths():
    text = (
        "- Create: `backend/src/a/x.py`\n- Modify: `./frontend/app.tsx:12-30`\n"
        "Run `uv run pytest`\n`docs/notes.md`\n`src/y.py:7`\n`pkg/z.py::func`"
    )
    assert referenced_code_paths(text) == {
        "backend/src/a/x.py",
        "frontend/app.tsx",
        "src/y.py",
        "pkg/z.py",
    }


@pytest.fixture
def linked_repo(make_repo):
    return make_repo(
        [
            {
                "message": "docs: plan",
                "date": "2026-09-01T10:00:00+00:00",
                "files": {PLAN_PATH: "- Modify: `src/x.py`\n", "backend/src/x.py": "a\n"},
            },
            {
                "message": "feat: in window",
                "date": "2026-09-10T10:00:00+00:00",
                "files": {"backend/src/x.py": "a\nb\n"},
            },
            {
                "message": "feat: unnamed file",
                "date": "2026-09-05T10:00:00+00:00",
                "files": {"backend/src/y.py": "a\n"},
            },
            {
                "message": "feat: too late",
                "date": "2026-09-20T10:00:00+00:00",
                "files": {"backend/src/x.py": "a\nb\nc\n"},
            },
        ]
    )


def test_has_preceding_plan_window(linked_repo):
    commits = {c.subject: c for c in load_commits(linked_repo, ["HEAD"])}
    docs = load_spec_plan_files(linked_repo, ["HEAD"])
    assert [(d.path, d.kind) for d in docs] == [(PLAN_PATH, "plan")]
    assert has_preceding_plan(commits["feat: in window"], docs).path == PLAN_PATH
    assert has_preceding_plan(commits["feat: unnamed file"], docs) is None
    assert has_preceding_plan(commits["feat: too late"], docs) is None
    # a plan is never "preceding" its own commit
    assert has_preceding_plan(commits["docs: plan"], docs) is None


def test_has_preceding_plan_full_path_and_nearest(make_repo):
    repo = make_repo(
        [
            {
                "message": "docs: old plan",
                "date": "2026-09-01T10:00:00+00:00",
                "files": {"docs/superpowers/plans/a.md": "`frontend/src/p.tsx`"},
            },
            {
                "message": "docs: new plan",
                "date": "2026-09-03T10:00:00+00:00",
                "files": {"docs/superpowers/plans/b.md": "`frontend/src/p.tsx`"},
            },
            {
                "message": "feat: p",
                "date": "2026-09-04T10:00:00+00:00",
                "files": {"frontend/src/p.tsx": "x"},
            },
        ]
    )
    feat = load_commits(repo, ["HEAD"])[-1]
    docs = load_spec_plan_files(repo, ["HEAD"])
    assert has_preceding_plan(feat, docs).path == "docs/superpowers/plans/b.md"


def test_first_addition_wins(make_repo):
    path = "docs/superpowers/specs/s.md"
    repo = make_repo(
        [
            {"message": "docs: add", "date": "2026-09-01T10:00:00+00:00", "files": {path: "v1"}},
            {"message": "docs: rm", "date": "2026-09-02T10:00:00+00:00", "files": {path: None}},
            {"message": "docs: re", "date": "2026-09-03T10:00:00+00:00", "files": {path: "v2"}},
        ]
    )
    first = load_commits(repo, ["HEAD"])[0]
    (doc,) = load_spec_plan_files(repo, ["HEAD"])
    assert (doc.kind, doc.added_sha, doc.text) == ("spec", first.sha, "v1")


def test_spec_trace_rows(linked_repo):
    commits = load_commits(linked_repo, ["HEAD"])
    docs = load_spec_plan_files(linked_repo, ["HEAD"])
    (row,) = spec_trace_rows(commits, docs)
    assert row["path"] == PLAN_PATH
    assert row["kind"] == "plan"
    assert row["n_feat_linked"] == 1
    assert row["first_linked_date"] == row["last_linked_date"] == "2026-09-10"


def _feat(i):
    return Commit(f"s{i:02d}", datetime(2026, 9, 1 + i % 28), f"feat: {i}", "feat", ())


def test_sample_for_manual_check_is_deterministic():
    feats = [_feat(i) for i in range(50)]
    a = sample_for_manual_check(feats)
    assert len(a) == 20 and len({c.sha for c in a}) == 20
    assert [c.sha for c in a] == [c.sha for c in sample_for_manual_check(list(reversed(feats)))]
    assert len(sample_for_manual_check(feats[:5])) == 5


def test_link_accuracy(tmp_path):
    sheet = tmp_path / "link-check.csv"
    with sheet.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sha", "subject", "rule_plan", "an_verdict"])
        w.writerows([["a", "s", "p", "correct"], ["b", "s", "", "wrong"], ["c", "s", "p", ""]])
    assert link_accuracy(sheet) == (1, 2)


@pytest.mark.real
def test_real_repo_has_43_docs():
    docs = load_spec_plan_files(DEFAULT_REPO, [MAIN_SHA, CAMERA_READY_SHA])
    assert len(docs) == 43


def test_moved_doc_is_not_a_new_doc(make_repo):
    old, new = "seed-pipeline/docs/superpowers/plans/p.md", "pharma-lab/docs/superpowers/plans/p.md"
    repo = make_repo(
        [
            {
                "message": "docs: add",
                "date": "2026-09-01T10:00:00+00:00",
                "files": {old: "x\n" * 20},
            },
            {"message": "chore: mv", "date": "2026-09-02T10:00:00+00:00", "rename": {old: new}},
        ]
    )
    assert [d.path for d in load_spec_plan_files(repo, ["HEAD"])] == [old]
