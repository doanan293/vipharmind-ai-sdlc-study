"""Đọc các file kết quả. Thiếu file nào thì khóa tương ứng là None."""

import csv
import json
import tomllib
from pathlib import Path
from typing import Any

RETRO = Path("retrospective/out")
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
# Ba đoạn của tầng tính năng, cố định trong bản thiết kế nghiên cứu mục 7.2b.
FEATURE_IDS = ("F08", "F14", "F15")


def _csv(path: Path) -> list[dict[str, str]] | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tasks(root: Path, pattern: str) -> list[dict[str, Any]] | None:
    found = sorted((root / "tasks").glob(f"{pattern}/task.toml"))
    if not found:
        return None
    return [tomllib.loads(p.read_text(encoding="utf-8")) for p in found]


def _features(root: Path) -> list[dict[str, Any]] | None:
    path = root / "tasks" / "feature-feasibility" / "ranges.json"
    if not path.exists():
        return None
    ranges = json.loads(path.read_text(encoding="utf-8"))["sub_ranges"]
    picked = [r for r in ranges if r["id"] in FEATURE_IDS]
    return picked or None


def _pilot_results(root: Path) -> list[dict[str, Any]] | None:
    """results/raw/<cohort>/<task>/<arm>-r<rep>/grade.json; chỉ đơn vị đã chấm xong."""
    raw = root / "results" / "raw"
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
    screening = root / "tasks" / "screening.json"
    data["screening"] = (
        json.loads(screening.read_text(encoding="utf-8")) if screening.exists() else None
    )
    data["tasks"] = _tasks(root, "t*")
    data["pilots"] = _tasks(root, "p*")
    data["features"] = _features(root)
    lit = root / "docs" / "report" / "data" / "literature.toml"
    data["literature"] = tomllib.loads(lit.read_text(encoding="utf-8")) if lit.exists() else None
    data["pilot_results"] = _pilot_results(root)
    return data
