"""Static figures for the report (matplotlib, Agg backend)."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from retro.stages import STAGES  # noqa: E402

# Validated categorical order (dataviz reference palette, light mode); "other" is neutral gray.
STAGE_COLORS = dict(
    zip(
        STAGES,
        ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#a3a29c"],
        strict=True,
    )
)
STAGE_LABELS = {
    "research_eval": "Nghiên cứu, đánh giá",
    "data": "Dữ liệu",
    "backend": "Backend",
    "frontend": "Frontend",
    "test": "Kiểm thử",
    "deploy": "Triển khai",
    "docs": "Tài liệu",
    "other": "Khác",
}
_INK = "#52514e"
_SURFACE = "#fcfcfb"


def _style(ax) -> None:
    ax.set_facecolor(_SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color("#c3c2b7")
    ax.tick_params(colors=_INK, labelsize=8)
    ax.yaxis.grid(True, color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)


def week_range(weeks: list[str]) -> list[str]:
    """Every ISO week from the earliest to the latest given, so empty weeks show as gaps."""
    if not weeks:
        return []

    def monday(w: str) -> date:
        year, num = w.split("-W")
        return date.fromisocalendar(int(year), int(num), 1)

    start, end = monday(min(weeks)), monday(max(weeks))
    out = []
    while start <= end:
        y, n, _ = start.isocalendar()
        out.append(f"{y}-W{n:02d}")
        start += timedelta(days=7)
    return out


def lifecycle_by_week(rows: list[dict], path: Path) -> None:
    weeks = week_range([r["week"] for r in rows])
    counts = {(r["week"], r["stage"]): r["commits"] for r in rows}
    fig, ax = plt.subplots(figsize=(10, 4.2), facecolor=_SURFACE)
    bottom = [0] * len(weeks)
    for stage in STAGES:
        values = [counts.get((w, stage), 0) for w in weeks]
        if not any(values):
            continue
        ax.bar(
            weeks,
            values,
            bottom=bottom,
            color=STAGE_COLORS[stage],
            label=STAGE_LABELS[stage],
            width=0.7,
            edgecolor=_SURFACE,
            linewidth=1,
        )
        bottom = [b + v for b, v in zip(bottom, values, strict=True)]
    _style(ax)
    ax.set_ylabel("Số commit", color=_INK)
    ax.set_xlabel("Tuần (ISO)", color=_INK)
    ax.set_title("Commit theo tuần và theo khâu", color="#0b0b0b", fontsize=11, loc="left")
    plt.setp(ax.get_xticklabels(), rotation=60, ha="right")
    ax.legend(frameon=False, fontsize=8, ncol=1, bbox_to_anchor=(1.01, 1), loc="upper left")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)


def rework_by_group(summary: list[dict], path: Path) -> None:
    labels = {"with_plan": "Có plan đi trước", "without_plan": "Không có plan"}
    fig, ax = plt.subplots(figsize=(5, 3.6), facecolor=_SURFACE)
    names = [labels.get(r["group"], r["group"]) for r in summary]
    means = [r["mean_rework"] for r in summary]
    bars = ax.bar(names, means, color=["#2a78d6", "#eb6834"][: len(names)], width=0.5)
    for bar, r in zip(bars, summary, strict=True):
        ax.annotate(
            f"TB {r['mean_rework']:.2f} | n = {r['n_feat']}\n"
            f"{r['share_with_rework'] * 100:.0f}% có sửa lại",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            ha="center",
            va="bottom",
            fontsize=8,
            color=_INK,
            xytext=(0, 3),
            textcoords="offset points",
        )
    _style(ax)
    ax.set_ylabel("Số commit fix/refactor trong 14 ngày (TB)", color=_INK, fontsize=8)
    ax.set_title("Mức phải sửa lại theo nhóm feat", color="#0b0b0b", fontsize=11, loc="left")
    ax.set_ylim(0, max(means + [0.1]) * 1.35)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)
