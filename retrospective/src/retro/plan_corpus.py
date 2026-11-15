"""Shape of the historical specs and plans, for the spec-driven arm's prompt.

Outputs only statistics and (sha, path) references; the original text is materialised
only on request, into a git-ignored folder.
"""

from __future__ import annotations

import csv
import re
import statistics
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from retro.specplans import DocFile

_HEADING_RE = re.compile(r"^(#{1,6})\s")
_TASK_RE = re.compile(r"^(#{2,4})\s+Task\s+\d+")
_STEP_RE = re.compile(r"^\s*- \[[ xX]\] \*\*Step")
_FILE_RE = re.compile(r"^\s*- (Create|Modify|Test):")
_NUMBER_RE = re.compile(r"^\d+(\.\d+)*\.?\s*")
REPRESENTATIVE_DIRS = ("backend", "docs", "seed-pipeline")


@dataclass(frozen=True)
class PlanShape:
    path: str
    added_sha: str
    lines: int
    tasks: int
    steps: int
    lines_per_task: tuple[int, ...]
    files_per_task: tuple[int, ...]
    steps_per_task: tuple[int, ...]
    has_global_constraints: bool
    has_file_structure: bool


def plan_shape(doc: DocFile) -> PlanShape:
    lines = doc.text.splitlines()
    tasks: list[list[str]] = []
    task_level = 0
    current: list[str] | None = None
    for line in lines:
        task = _TASK_RE.match(line)
        heading = _HEADING_RE.match(line)
        if task:
            task_level = len(task.group(1))
            current = [line]
            tasks.append(current)
        elif current is not None and heading and len(heading.group(1)) <= task_level:
            current = None
        elif current is not None:
            current.append(line)
    headings = [line.lstrip("#").strip().lower() for line in lines if _HEADING_RE.match(line)]
    return PlanShape(
        path=doc.path,
        added_sha=doc.added_sha,
        lines=len(lines),
        tasks=len(tasks),
        steps=sum(bool(_STEP_RE.match(line)) for line in lines),
        lines_per_task=tuple(len(t) for t in tasks),
        files_per_task=tuple(sum(bool(_FILE_RE.match(x)) for x in t) for t in tasks),
        steps_per_task=tuple(sum(bool(_STEP_RE.match(x)) for x in t) for t in tasks),
        has_global_constraints=any(h.startswith("global constraints") for h in headings),
        has_file_structure=any(h.startswith("file structure") for h in headings),
    )


def spec_sections(doc: DocFile) -> list[str]:
    return [line[3:].strip() for line in doc.text.splitlines() if line.startswith("## ")]


def _norm_section(title: str) -> str:
    return _NUMBER_RE.sub("", title).strip().lower()


def _median(values) -> float | int | str:
    values = list(values)
    return statistics.median(values) if values else ""


def _median_iqr(values: list[int]) -> str:
    if not values:
        return "không có dữ liệu"
    if len(values) < 2:
        return f"trung vị {values[0]} (một giá trị)"
    q1, q2, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return f"trung vị {q2:g}, khoảng tứ phân vị {q1:g}–{q3:g} (n = {len(values)})"


def _index_rows(docs: list[DocFile]) -> list[dict]:
    rows = []
    for d in docs:
        s = plan_shape(d)
        rows.append(
            {
                "path": d.path,
                "kind": d.kind,
                "added_sha": d.added_sha,
                "added_date": d.added_date.date().isoformat(),
                "lines": s.lines,
                "tasks": s.tasks,
                "steps": s.steps,
                "median_lines_per_task": _median(s.lines_per_task),
                "median_files_per_task": _median(s.files_per_task),
            }
        )
    return rows


def _representatives(shapes: list[PlanShape]) -> list[tuple[str, PlanShape]]:
    with_tasks = [s for s in shapes if s.tasks]
    if not with_tasks:
        return []
    median_tasks = statistics.median(s.tasks for s in with_tasks)
    picks = []
    for top in REPRESENTATIVE_DIRS:
        group = [s for s in with_tasks if s.path.split("/", 1)[0] == top]
        if group:
            best = min(group, key=lambda s: (abs(s.tasks - median_tasks), s.path))
            picks.append((top, best))
    return picks


def _summary(docs: list[DocFile]) -> str:
    specs = [d for d in docs if d.kind == "spec"]
    plans = [d for d in docs if d.kind == "plan"]
    shapes = [plan_shape(d) for d in plans]
    tasked = [s for s in shapes if s.tasks]
    out = [
        "# Bộ plan cũ của ViPharmind: hình dạng",
        "",
        "File này chỉ chứa số liệu và tham chiếu `(mã commit, đường dẫn)`, không chép nội dung "
        "spec hay plan. Muốn đọc bản gốc, chạy `uv run retro plan-corpus --materialize` hoặc lệnh "
        "`git show` ghi bên dưới.",
        "",
        f"- Số spec: {len(specs)}",
        f"- Số plan: {len(plans)} (trong đó {len(tasked)} plan có tiêu đề `Task <số>`)",
        "",
        "## Kích thước plan",
        "",
        f"- Số task mỗi plan: {_median_iqr([s.tasks for s in tasked])}",
        f"- Số bước mỗi task: {_median_iqr([n for s in tasked for n in s.steps_per_task])}",
        f"- Số dòng mỗi task: {_median_iqr([n for s in tasked for n in s.lines_per_task])}",
        f"- Số file mỗi task: {_median_iqr([n for s in tasked for n in s.files_per_task])}",
        f"- Plan có mục `Global Constraints`: "
        f"{sum(s.has_global_constraints for s in shapes)}/{len(shapes)}",
        f"- Plan có mục `File Structure`: "
        f"{sum(s.has_file_structure for s in shapes)}/{len(shapes)}",
        "",
        "## Các mục `##` thường gặp trong spec",
        "",
    ]
    counts: Counter[str] = Counter()
    for d in specs:
        counts.update({_norm_section(t) for t in spec_sections(d)})
    common = [(t, n) for t, n in counts.most_common() if specs and n * 2 >= len(specs)]
    if common:
        out.append("Mục xuất hiện ở ít nhất một nửa số spec (đã bỏ số thứ tự, viết thường):")
        out.append("")
        out += [f"- {t}: {n}/{len(specs)} spec" for t, n in common]
    else:
        out.append("Không có mục nào xuất hiện ở ít nhất một nửa số spec.")
    out += ["", "## Ba plan tiêu biểu", ""]
    out.append("Plan có số task gần trung vị chung nhất trong mỗi thư mục:")
    out.append("")
    for top, s in _representatives(shapes):
        out.append(
            f"- `{top}/`: `({s.added_sha[:7]}, {s.path})`, {s.tasks} task, {s.steps} bước. "
            f"Mở: `git show {s.added_sha}:{s.path}`"
        )
    return "\n".join(out) + "\n"


def write_plan_corpus(docs: list[DocFile], out_dir: Path, materialize: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = _index_rows(docs)
    with (out_dir / "index.csv").open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "path",
                "kind",
                "added_sha",
                "added_date",
                "lines",
                "tasks",
                "steps",
                "median_lines_per_task",
                "median_files_per_task",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    (out_dir / "summary.md").write_text(_summary(docs))
    if materialize:
        for d in docs:
            target = out_dir / "files" / d.path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(d.text)
