import csv
from datetime import datetime

from retro.plan_corpus import plan_shape, spec_sections, write_plan_corpus
from retro.specplans import DocFile

PLAN = (
    "# P\n## Global Constraints\n- x\n### Task 1: A\n**Files:**\n- Create: `a.py`\n"
    "- Test: `t.py`\n- [ ] **Step 1: w**\n- [ ] **Step 2: r**\n### Task 2: B\n- Modify: `b.py`\n"
    "- [ ] **Step 1: w**\n## Self-review\nignored\n"
)
SPEC_A = "# S\n## 1. Goals\nx\n## 2. Design\ny\n## Odd\n"
SPEC_B = "# S\n## Goals\nx\n## 3. design\n"


def doc(text, path="backend/docs/superpowers/plans/p.md", kind="plan", sha="abc1234"):
    return DocFile(path, kind, sha, datetime(2026, 9, 1), text)


def test_plan_shape():
    s = plan_shape(doc(PLAN))
    assert (s.tasks, s.steps, s.files_per_task) == (2, 3, (2, 1))
    assert s.steps_per_task == (2, 1)
    assert s.lines_per_task == (6, 3)
    assert s.lines == PLAN.count("\n")
    assert s.has_global_constraints and not s.has_file_structure


def test_plan_shape_accepts_level_four_task_headings():
    s = plan_shape(doc("## Phase 1\n#### Task 1: a\n- [ ] **Step 1: x**\n#### Task 2: b\n"))
    assert s.tasks == 2


def test_spec_sections():
    assert spec_sections(doc(SPEC_A, kind="spec")) == ["1. Goals", "2. Design", "Odd"]


def test_write_plan_corpus_does_not_copy_text(tmp_path):
    docs = [
        doc(PLAN),
        doc(SPEC_A, "docs/superpowers/specs/a.md", "spec"),
        doc(SPEC_B, "docs/superpowers/specs/b.md", "spec"),
        doc(SPEC_B, "docs/superpowers/specs/c.md", "spec"),
    ]
    write_plan_corpus(docs, tmp_path)
    assert (tmp_path / "index.csv").exists() and (tmp_path / "summary.md").exists()
    assert not (tmp_path / "files").exists()
    summary = (tmp_path / "summary.md").read_text()
    assert "Create: `a.py`" not in summary
    assert "git show abc1234:backend/docs/superpowers/plans/p.md" in summary
    assert "goals" in summary.lower() and "design" in summary.lower()
    assert "odd" not in summary.lower()
    with (tmp_path / "index.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert [r["kind"] for r in rows] == ["plan", "spec", "spec", "spec"]
    assert rows[0]["tasks"] == "2" and rows[0]["median_files_per_task"] == "1.5"


def test_write_plan_corpus_materialize(tmp_path):
    write_plan_corpus([doc(PLAN)], tmp_path, materialize=True)
    assert (tmp_path / "files/backend/docs/superpowers/plans/p.md").read_text() == PLAN
