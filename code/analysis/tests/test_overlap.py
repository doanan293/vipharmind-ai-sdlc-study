import subprocess

import pandas as pd

from sdlc_analysis.overlap import commit_sets, cross_tier_overlaps, overlap_tasks


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def test_overlap_from_git_history(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    shas = []
    for i in range(6):
        (repo / "f").write_text(str(i))
        git(repo, "add", "f")
        git(repo, "-c", "user.name=x", "-c", "user.email=x@x", "commit", "-qm", f"c{i}")
        shas.append(git(repo, "rev-parse", "HEAD"))
    tasks = pd.DataFrame(
        [
            {
                "task_id": "s1",
                "tier": "small",
                "kind": "commit",
                "commit": shas[2][:12],
                "base": "",
            },
            {"task_id": "s2", "tier": "small", "kind": "commit", "commit": shas[5], "base": ""},
            {"task_id": "s3", "tier": "small", "kind": "commit", "commit": shas[3], "base": ""},
            {
                "task_id": "m1",
                "tier": "medium",
                "kind": "range",
                "commit": shas[5],
                "base": shas[3],
            },
            {"task_id": "L1", "tier": "large", "kind": "range", "commit": shas[3], "base": shas[1]},
            # same-tier overlap does not count
            {"task_id": "L2", "tier": "large", "kind": "range", "commit": shas[4], "base": shas[2]},
        ]
    )
    sets = commit_sets(tasks, repo)
    assert sets["s1"] == {shas[2]}
    assert sets["L1"] == {shas[2], shas[3]}
    pairs = cross_tier_overlaps(tasks, sets)
    found = {(p["a"], p["b"]) for p in pairs}
    assert found == {("L1", "s1"), ("L1", "s3"), ("L2", "s3"), ("m1", "s2"), ("L2", "m1")}
    # symmetric: every task in a cross-tier pair is dropped
    assert overlap_tasks(pairs) == {"s1", "s2", "s3", "m1", "L1", "L2"}
