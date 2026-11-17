from pathlib import Path

from sdlc_harness.vcs import export_tree, list_candidates, read_file

SRC = "backend/src/pharma_agent"


def _history(toy_repo):
    a = toy_repo.commit(
        "feat: add search",
        {f"{SRC}/domain/search.py": "a\nb\nc\n", "backend/tests/test_search.py": "t1\nt2\n"},
    )
    toy_repo.commit("feat: src only", {f"{SRC}/domain/only.py": "x\n"})
    toy_repo.commit(
        "fix: bug", {f"{SRC}/domain/search.py": "a\nb\nc\nd\n", "backend/tests/test_fix.py": "t\n"}
    )
    d = toy_repo.commit(
        "feat(api)!: breaking",
        {f"{SRC}/api/routes.py": "r\n", "backend/tests/test_routes.py": "t\n"},
    )
    return a, d


def test_list_candidates_filters_feat_touching_src_and_tests(toy_repo):
    a, d = _history(toy_repo)
    cands = list_candidates(toy_repo.path, "main")
    assert [c.sha for c in cands] == [a, d]
    assert [c.subject for c in cands] == ["feat: add search", "feat(api)!: breaking"]
    assert cands[0].parent == toy_repo.git("rev-parse", f"{a}^")


def test_candidate_records_numstat(toy_repo):
    _history(toy_repo)
    first = list_candidates(toy_repo.path, "main")[0]
    by_path = {c.path: c for c in first.changes}
    search = by_path[f"{SRC}/domain/search.py"]
    assert (search.status, search.added, search.deleted) == ("A", 3, 0)
    test = by_path["backend/tests/test_search.py"]
    assert (test.status, test.added, test.deleted) == ("A", 2, 0)


def test_export_tree_has_no_git_dir(toy_repo, tmp_path: Path):
    a, _ = _history(toy_repo)
    dest = tmp_path / "out"
    dest.mkdir()
    export_tree(toy_repo.path, a, dest)
    assert (dest / SRC / "domain" / "search.py").read_text() == "a\nb\nc\n"
    assert not (dest / ".git").exists()


def test_read_file(toy_repo):
    a, _ = _history(toy_repo)
    assert read_file(toy_repo.path, a, "backend/tests/test_search.py") == "t1\nt2\n"
