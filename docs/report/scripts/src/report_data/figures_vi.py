"""Hình kết quả chính, nhãn tiếng Việt. Vẽ lại từ file mà gói phân tích đã ghi (summary.json,
task_diffs.csv, pooled_task_diffs.csv), không tính lại số nào; hình gốc tiếng Anh của gói phân tích
vẫn nằm trong data/results/analysis/main/figures."""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, ScalarFormatter

SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
TIERS = {"small": "nhỏ", "medium": "vừa", "large": "lớn"}
TIER_STYLE = {"small": (SERIES[0], "o"), "medium": (SERIES[1], "s"), "large": (SERIES[2], "^")}
COHORT_MARK = {"claude-sonnet": "o", "claude-opus": "s", "codex-luna": "D"}
COHORTS = ["claude-sonnet", "claude-opus", "codex-luna"]


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=12)
    ax.set_axisbelow(True)


def _save(fig, path: Path) -> None:
    fig.savefig(path, bbox_inches="tight", metadata={"CreationDate": None})
    plt.close(fig)


def _pct(v: float) -> str:
    return f"{v:+.0f}".replace("-", "−")


def pass_diff_forest(estimates: dict, path: Path) -> None:
    rows = []
    for t in TIERS:
        for c in COHORTS:
            e = estimates.get(f"pass_diff.{c}.{t}")
            if e and e.get("estimate") is not None:
                rows.append((c, t, e))
    fig, ax = plt.subplots(figsize=(5.4, 0.36 * len(rows) + 1.0))
    _style(ax)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.axvline(0, color=MUTED, linewidth=1)
    for i, (c, t, e) in enumerate(rows):
        color, _ = TIER_STYLE[t]
        y = len(rows) - 1 - i
        lo, hi, est = (100 * e[k] for k in ("ci_low", "ci_high", "estimate"))
        ax.plot([lo, hi], [y, y], color=color, linewidth=2, solid_capstyle="round")
        ax.scatter(
            [est],
            [y],
            color=color,
            marker=COHORT_MARK[c],
            s=40,
            zorder=3,
            edgecolors="white",
            linewidths=1,
        )
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(
        [f"{c}, tầng {TIERS[t]} ({e['n_tasks']} nv)" for c, t, e in reversed(rows)], fontsize=12
    )
    ax.set_xlim(-105, 105)
    ax.set_xlabel("Hiệu số tỉ lệ đạt, đặc tả trừ vibe (pp), KTC 95%", color=INK, fontsize=13)
    _save(fig, path)


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def effect_vs_size(task_diffs: Path, pooled: Path, path: Path) -> None:
    td, pt = _read(task_diffs), _read(pooled)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    _style(ax)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.axhline(0, color=MUTED, linewidth=1)
    for tier, (color, marker) in TIER_STYLE.items():
        a = [r for r in td if r["tier"] == tier]
        ax.scatter(
            [int(r["src_lines"]) for r in a],
            [100 * float(r["pass_diff"]) for r in a],
            s=14,
            marker=marker,
            color=color,
            alpha=0.3,
            linewidths=0,
        )
        b = [r for r in pt if r["tier"] == tier]
        ax.scatter(
            [int(r["src_lines"]) for r in b],
            [100 * float(r["pooled_pass_diff"]) for r in b],
            s=42,
            marker=marker,
            color=color,
            edgecolors="white",
            linewidths=1.2,
            label=f"tầng {TIERS[tier]} ({len(b)} nhiệm vụ)",
        )
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([25, 50, 100, 200, 400, 800, 1600])
    ax.set_ylim(-105, 105)
    ax.set_xlabel("Số dòng backend/src của patch gốc (thang log)", color=INK, fontsize=13)
    ax.set_ylabel("Đặc tả trừ vibe (pp)", color=INK, fontsize=13)
    ax.legend(
        frameon=False,
        fontsize=11,
        loc="lower right",
        title="đậm: trung bình các nhóm; nhạt: từng nhóm",
        title_fontsize=10,
    )
    _save(fig, path)


def draw(analysis_dir: Path, out_dir: Path) -> None:
    from matplotlib import font_manager

    names = {f.name for f in font_manager.fontManager.ttflist}
    plt.rcParams.update(
        {
            "font.family": "Times New Roman" if "Times New Roman" in names else "serif",
            "font.size": 10,
            "pdf.fonttype": 42,
        }
    )
    summary = json.loads((analysis_dir / "summary.json").read_text(encoding="utf-8"))
    pass_diff_forest(summary["estimates"], out_dir / "pass_diff_by_cohort.pdf")
    effect_vs_size(
        analysis_dir / "task_diffs.csv",
        analysis_dir / "pooled_task_diffs.csv",
        out_dir / "effect_vs_size.pdf",
    )
