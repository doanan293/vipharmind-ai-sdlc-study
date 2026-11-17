"""Đọc các file kết quả. Thiếu file nào thì khóa tương ứng là None."""

import csv
import json
import tomllib
from pathlib import Path
from typing import Any

from report_data import explore, labels, passcheck, results

RETRO = Path("data/retrospective")
RETRO_CSV = {
    "commits": "commits.csv",
    "lifecycle": "lifecycle_by_stage.csv",
    "lifecycle_week": "lifecycle_by_week.csv",
    "rework_summary": "rework_summary.csv",
    "rework": "rework.csv",
    "sessions": "sessions.csv",
    "session_tools": "session_tools.csv",
    "spec_trace": "spec_trace.csv",
    "link_check": "link-check.csv",
}
PILOT_RUNS = Path("data/results/analysis/pilot/runs.csv")


def _csv(path: Path) -> list[dict[str, str]] | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tasks(root: Path, pattern: str) -> list[dict[str, Any]] | None:
    found = sorted((root / "data" / "tasks").glob(f"{pattern}/task.toml"))
    if not found:
        return None
    return [tomllib.loads(p.read_text(encoding="utf-8")) for p in found]


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _range_tasks(root: Path, pattern: str) -> list[dict[str, Any]] | None:
    """Nhiệm vụ nhiều commit (tầng vừa m*, tầng lớn f*), kèm số commit `n_commits`.

    Số commit lấy từ hồ sơ chọn nhiệm vụ: `medium_candidates.json` (trường `selected_as`) cho tầng
    vừa, `ranges.json` (mã đoạn viết hoa) cho tầng lớn. Không tìm thấy thì `n_commits` là None.
    """
    tasks = _tasks(root, pattern)
    if tasks is None:
        return None
    feas = root / "data" / "tasks" / "feature-feasibility"
    commits: dict[str, int] = {}
    medium = _json(feas / "medium_candidates.json")
    if medium:
        for c in medium["candidates"]:
            if c.get("selected_as"):
                commits[c["selected_as"]] = int(c["n_commits"])
    ranges = _json(feas / "ranges.json")
    if ranges:
        for r in ranges["sub_ranges"]:
            commits[r["id"].lower()] = int(r["n_commits"])
    return [t | {"n_commits": commits.get(t["id"])} for t in tasks]


def _pilot_results(root: Path) -> list[dict[str, Any]] | None:
    """results/raw/pilot/<cohort>/<task>/<arm>-r<rep>/grade.json; chỉ đơn vị đã chấm xong.

    Chỉ đọc thư mục chạy thử; kết quả lượt chạy chính do gói analysis/ tổng hợp."""
    raw = root / "data" / "results" / "raw" / "pilot"
    units = []
    for grade in sorted(raw.glob("*/*/*/grade.json")):
        arm, _, rep = grade.parent.name.rpartition("-r")
        units.append(
            {
                "cohort": grade.parents[2].name,
                "task": grade.parents[1].name,
                "arm": arm,
                "rep": int(rep),
                **json.loads(grade.read_text(encoding="utf-8")),
            }
        )
    return units or None


def load(root: Path) -> dict[str, Any]:
    root = Path(root)
    data: dict[str, Any] = {key: _csv(root / RETRO / name) for key, name in RETRO_CSV.items()}
    screening = root / "data" / "tasks" / "screening.json"
    data["screening"] = (
        json.loads(screening.read_text(encoding="utf-8")) if screening.exists() else None
    )
    data["tasks"] = _tasks(root, "t*")
    data["pilots"] = _tasks(root, "p*")
    data["medium"] = _range_tasks(root, "m[0-9]*")
    data["features"] = _range_tasks(root, "f[0-9]*")
    data["graded_lines"] = _json(root / "data" / "tasks" / "graded_lines.json")
    medium = _json(root / "data" / "tasks" / "feature-feasibility" / "medium_candidates.json")
    data["medium_candidates"] = medium["candidates"] if medium else None
    lit = root / "docs" / "report" / "data" / "literature.toml"
    data["literature"] = tomllib.loads(lit.read_text(encoding="utf-8")) if lit.exists() else None
    data["pilot_results"] = _pilot_results(root)
    data["pilot_runs"] = _csv(root / PILOT_RUNS)
    data["analysis"] = results.load(root)
    data["passcheck"] = passcheck.load(root)
    data["labeling"] = labels.load(root)
    data["e2"] = explore.load_e2(root)
    data["e1"] = explore.load_e1(root)
    return data
