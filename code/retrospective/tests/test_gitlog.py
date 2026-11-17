from retro.gitlog import load_commits, parse_type

from .conftest import git


def test_parse_type():
    assert parse_type("feat(api): add x") == "feat"
    assert parse_type("fix!: y") == "fix"
    assert parse_type("refactor(core)!: z") == "refactor"
    assert parse_type("initial commit") == "other"
    assert parse_type('Revert "docs(paper): z"') == "other"


def test_load_commits_counts_lines_and_renames(make_repo):
    repo = make_repo(
        [
            {
                "message": "feat: a",
                "date": "2026-08-01T10:00:00+07:00",
                "files": {"backend/src/a.py": "x\ny\n", "logo.png": b"\x00\x01"},
            },
            {
                "message": "refactor: move",
                "date": "2026-08-02T10:00:00+07:00",
                "rename": {"backend/src/a.py": "backend/src/b.py"},
            },
            {
                "message": "chore: rename dir",
                "date": "2026-08-03T10:00:00+07:00",
                "rename": {"backend/src/b.py": "b.py"},
            },
        ]
    )
    commits = load_commits(repo, ["HEAD"])
    assert [c.type for c in commits] == ["feat", "refactor", "chore"]
    first = {f.path: (f.added, f.deleted) for f in commits[0].files}
    assert first == {"backend/src/a.py": (2, 0), "logo.png": (0, 0)}
    assert [f.path for f in commits[1].files] == ["backend/src/b.py"]
    assert [f.path for f in commits[2].files] == ["b.py"]
    assert commits[0].date.isoformat() == "2026-08-01T10:00:00+07:00"


def test_rename_path_forms():
    from retro.gitlog import _new_path

    assert _new_path("backend/{old => new}/x.py") == "backend/new/x.py"
    assert _new_path("a.py => b.py") == "b.py"
    assert _new_path("src/{ => sub}/x.py") == "src/sub/x.py"
    assert _new_path("src/{sub => }/x.py") == "src/x.py"
    assert _new_path("{seed-pipeline => corpus-pipeline}/a.py") == "corpus-pipeline/a.py"
    assert _new_path("plain/path.py") == "plain/path.py"


def test_union_counts_each_commit_once(make_repo):
    repo = make_repo(
        [
            {"message": "feat: root", "date": "2026-08-01T10:00:00+00:00", "files": {"a": "1"}},
            {
                "message": "feat: side",
                "date": "2026-08-02T10:00:00+00:00",
                "files": {"b": "1"},
                "checkout": "-b side main",
            },
            {
                "message": "fix: main",
                "date": "2026-08-03T10:00:00+00:00",
                "files": {"c": "1"},
                "checkout": "main",
            },
        ]
    )
    commits = load_commits(repo, [git(repo, "rev-parse", "main"), git(repo, "rev-parse", "side")])
    assert [c.subject for c in commits] == ["feat: root", "feat: side", "fix: main"]
