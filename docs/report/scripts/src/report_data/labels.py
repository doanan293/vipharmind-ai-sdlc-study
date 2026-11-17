"""Nhãn nguyên nhân thất bại (prereg-v1 mục 9.8), vòng gán nhãn thứ hai (kết quả chính).

Nguồn: results/analysis/main/labeling/
- final-labels.csv: code2 (mã vòng 2), unit_id_r1, label_loi, label_bao, label_final,
  source (agree / An_adjudicated), label_fable (người chấm thứ ba, ngoài bản đăng ký, chỉ mô tả);
- key-round2-PRIVATE.csv: code2 -> cohort, task_id, tier, arm (chỉ dùng để gộp).
Báo cáo chỉ in số gộp, không in khóa của từng lượt. Thiếu nguồn thì mọi khóa là None (\\pending).
"""

import csv
from collections import Counter
from pathlib import Path
from typing import Any

from report_data import fmt

Numbers = dict[str, str | None]

LABELING = Path("data/results/analysis/main/labeling")

# Mã nhãn, tên khóa, tên hiển thị (prereg/labeling-guide.md mục 3)
LABELS = [
    ("hieu_sai", "HieuSai", "hiểu sai yêu cầu"),
    ("lam_thieu", "LamThieu", "làm thiếu"),
    ("sai_giao_dien", "SaiGiaoDien", "sai giao diện đã nêu trong đề"),
    ("hong_chuc_nang_cu", "HongChucNangCu", "làm hỏng chức năng cũ"),
    ("loi_logic", "LoiLogic", "lỗi logic"),
    ("khong_hoan_thanh", "KhongHoanThanh", "không hoàn thành trong giới hạn"),
    ("de_bai_thieu", "DeBaiThieu", "đề bài thiếu hoặc mơ hồ"),
    ("sai_api_co_san", "SaiApiCoSan", "dùng sai kiểu hoặc API có sẵn"),
    ("loi_moi_truong", "LoiMoiTruong", "lỗi môi trường"),
]
GROUPS = {
    "arm": [("spec", "Spec"), ("vibe", "Vibe")],
    "cohort": [("claude-sonnet", "Sonnet"), ("claude-opus", "Opus")],
    "tier": [("small", "Small"), ("medium", "Medium"), ("large", "Large")],
}
# Hai nhãn ngoài phần mã tác tử tự viết: đề không chốt chi tiết, hoặc nối sai với mã có sẵn
OUTSIDE = ("de_bai_thieu", "sai_api_co_san")


def _keys() -> list[str]:
    k = [
        "LabRuns",
        "LabSpecRuns",
        "LabVibeRuns",
        "LabAgree",
        "LabKappa",
        "LabAdjudicated",
        "LabOutside",
        "LabOutsidePct",
        "LabOutsideSpecPct",
        "LabOutsideVibePct",
        "LabOther",
        "LabFableAgreeLoi",
        "LabFableAgreeBao",
        "LabFableKappaLoi",
        "LabFableKappaBao",
        "LabFableDeBaiThieu",
    ]
    for _, c, _ in LABELS:
        k.append(f"Lab{c}Total")
        for group in GROUPS.values():
            k += [f"Lab{c}{g}" for _, g in group]
    return k


KEYS = _keys()


def kappa(a: list[str], b: list[str]) -> float:
    """Kappa của Cohen (như sdlc_analysis.labels.kappa_report)."""
    n = len(a)
    po = sum(x == y for x, y in zip(a, b, strict=True)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum(ca[k] * cb[k] for k in set(a) | set(b)) / (n * n)
    return (po - pe) / (1 - pe)


def _rows(src: dict[str, Any]) -> list[dict[str, str]]:
    """Mỗi lượt một dòng, kèm cohort, tier, arm từ khóa."""
    key = src["key"]
    return [r | {g: key[r["code2"]][g] for g in GROUPS} for r in src["labels"]]


def numbers(src: dict[str, Any]) -> Numbers:
    rows = _rows(src)
    out: Numbers = {}
    n = len(rows)
    arm = Counter(r["arm"] for r in rows)
    out["LabRuns"] = fmt.number(n)
    out["LabSpecRuns"], out["LabVibeRuns"] = fmt.number(arm["spec"]), fmt.number(arm["vibe"])
    loi = [r["label_loi"] for r in rows]
    bao = [r["label_bao"] for r in rows]
    fable = [r["label_fable"] for r in rows]
    out["LabAgree"] = fmt.number(sum(x == y for x, y in zip(loi, bao, strict=True)))
    out["LabKappa"] = fmt.number(kappa(loi, bao), 2)
    out["LabAdjudicated"] = fmt.number(sum(r["source"] != "agree" for r in rows))

    final = Counter(r["label_final"] for r in rows)
    for code, c, _ in LABELS:
        out[f"Lab{c}Total"] = fmt.number(final[code])
        for g, group in GROUPS.items():
            cnt = Counter(r[g] for r in rows if r["label_final"] == code)
            for value, name in group:
                out[f"Lab{c}{name}"] = fmt.number(cnt[value])
    outside = [r for r in rows if r["label_final"] in OUTSIDE]
    out["LabOutside"] = fmt.number(len(outside))
    out["LabOutsidePct"] = fmt.percent(len(outside), n, 0)
    for a, A in GROUPS["arm"]:
        out[f"LabOutside{A}Pct"] = fmt.percent(sum(r["arm"] == a for r in outside), arm[a], 0)
    top = {"de_bai_thieu", "sai_api_co_san", "hong_chuc_nang_cu"}
    out["LabOther"] = fmt.number(sum(final[c] for c in final if c not in top))

    out["LabFableAgreeLoi"] = fmt.number(sum(x == y for x, y in zip(fable, loi, strict=True)))
    out["LabFableAgreeBao"] = fmt.number(sum(x == y for x, y in zip(fable, bao, strict=True)))
    out["LabFableKappaLoi"] = fmt.number(kappa(fable, loi), 2)
    out["LabFableKappaBao"] = fmt.number(kappa(fable, bao), 2)
    out["LabFableDeBaiThieu"] = fmt.number(fable.count("de_bai_thieu"))
    assert set(out) == set(KEYS), set(out) ^ set(KEYS)
    return out


def table(src: dict[str, Any]) -> str:
    """Nhãn cuối (Lợi, Bảo; An phân xử) theo cách làm và nhóm, cột cuối là tổng nhãn của Fable 5.2.

    Chỉ in nhãn có ít nhất một lượt; xếp theo số lượt của người, rồi của Fable."""
    rows = _rows(src)
    cols = [("arm", "spec"), ("arm", "vibe")]
    cols += [("cohort", "claude-sonnet"), ("cohort", "claude-opus")]
    body = []
    for code, _, name in LABELS:
        mine = [r for r in rows if r["label_final"] == code]
        cells = [sum(r[g] == v for r in mine) for g, v in cols]
        third = sum(r["label_fable"] == code for r in rows)
        if mine or third:
            body.append((-len(mine), -third, name, cells + [len(mine), third]))
    lines = [
        "\\begin{tabular}{lrrrrrr}",
        "\\toprule",
        "Nhãn & Đặc tả & Vibe & Sonnet & Opus & Tổng & Fable 5.2 \\\\",
        "\\midrule",
    ]
    for *_, name, cells in sorted(body):
        lines.append(" & ".join([name] + [fmt.number(x) if x else "--" for x in cells]) + " \\\\")
    tot = [sum(r[g] == v for r in rows) for g, v in cols] + [len(rows), len(rows)]
    lines += ["\\midrule", " & ".join(["Tổng"] + [fmt.number(x) for x in tot]) + " \\\\"]
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(lines)


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load(root: Path) -> dict[str, Any] | None:
    d = Path(root) / LABELING
    if not (d / "final-labels.csv").exists() or not (d / "key-round2-PRIVATE.csv").exists():
        return None
    return {
        "labels": _read(d / "final-labels.csv"),
        "key": {r["code2"]: r for r in _read(d / "key-round2-PRIVATE.csv")},
    }
