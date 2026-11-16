"""Kiểm tra lượt đạt (prereg-v1 mục 9.10): mẫu 20 lượt đạt, Lợi và Bảo đối chiếu mù cách làm.

Nguồn: results/analysis/main/labeling/returned/passcheck-{loi,bao}.csv (cột dung_that(yes/no)) và
passing-key-PRIVATE.csv (mã p… -> người kiểm, cách làm; chỉ dùng để đếm). Báo cáo chỉ in số gộp.
Thiếu nguồn thì mọi khóa là None (\\pending).
"""

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from report_data import fmt

Numbers = dict[str, str | None]

LABELING = Path("results/analysis/main/labeling")
RATERS = ("loi", "bao")
KEYS = ["PassCheckRuns", "PassCheckCorrect", "PassCheckLoi", "PassCheckBao", "PassCheckPerArm"]


def numbers(src: dict[str, Any]) -> Numbers:
    pc = src["passcheck"]
    out: Numbers = {}
    out["PassCheckRuns"] = fmt.number(sum(len(v) for v in pc.values()))
    out["PassCheckCorrect"] = fmt.number(
        sum(r["dung_that(yes/no)"].strip().lower() == "yes" for v in pc.values() for r in v)
    )
    out["PassCheckLoi"] = fmt.number(len(pc["loi"]))
    out["PassCheckBao"] = fmt.number(len(pc["bao"]))
    per_arm = set(Counter((r["rater"], r["arm"]) for r in src["passing_key"]).values())
    out["PassCheckPerArm"] = fmt.number(per_arm.pop()) if len(per_arm) == 1 else None
    assert set(out) == set(KEYS), set(out) ^ set(KEYS)
    return out


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load(root: Path) -> dict[str, Any] | None:
    d = Path(root) / LABELING
    files = {who: d / "returned" / f"passcheck-{who}.csv" for who in RATERS}
    key = d / "passing-key-PRIVATE.csv"
    if not key.exists() or not all(f.exists() for f in files.values()):
        return None
    return {
        "passcheck": {who: _read(f) for who, f in files.items()},
        "passing_key": _read(key),
    }
