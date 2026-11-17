"""Figures (matplotlib, PDF + PNG). Read in black and white: tiers and cohorts also differ by
marker shape."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import NullFormatter, ScalarFormatter

# reference categorical palette, fixed order (dataviz skill)
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
TIER_STYLE = {"small": (SERIES[0], "o"), "medium": (SERIES[1], "s"), "large": (SERIES[2], "^")}
COHORT_MARK = {"claude-sonnet": "o", "claude-opus": "s", "agy-gemini": "^", "codex-luna": "D"}


def _style(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, out: Path, name: str) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("pdf", "png"):
        p = out / f"{name}.{ext}"
        fig.savefig(
            p,
            dpi=200,
            bbox_inches="tight",
            metadata={"CreationDate": None} if ext == "pdf" else None,
        )
        paths.append(p.name)
    plt.close(fig)
    return paths


def effect_vs_size(task_diffs: pd.DataFrame, pooled: pd.DataFrame, out: Path) -> list[str]:
    """Per-task spec-minus-vibe pass-rate difference against the original patch size: faint
    marks per cohort, solid marks for the cohort mean of each task."""
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    _style(ax)
    ax.axhline(0, color=MUTED, linewidth=1)
    for tier, (color, marker) in TIER_STYLE.items():
        td = task_diffs[task_diffs["tier"] == tier]
        if len(td):
            ax.scatter(
                td["src_lines"],
                td["pass_diff"],
                s=14,
                marker=marker,
                color=color,
                alpha=0.25,
                linewidths=0,
            )
        pt = pooled[pooled["tier"] == tier]
        if len(pt):
            ax.scatter(
                pt["src_lines"],
                pt["pooled_pass_diff"],
                s=42,
                marker=marker,
                color=color,
                edgecolors="white",
                linewidths=1.2,
                label=f"{tier} tier ({len(pt)} tasks)",
            )
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([25, 50, 100, 200, 400, 800, 1600])
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel(
        "backend/src lines changed by the original patch (log scale)", color=INK, fontsize=9
    )
    ax.set_ylabel("pass rate, spec minus vibe", color=INK, fontsize=9)
    ax.set_title(
        "Effect vs task size (solid: mean over cohorts; faint: each cohort)",
        fontsize=10,
        color=INK,
        loc="left",
    )
    if len(pooled):
        ax.legend(frameon=False, fontsize=8, loc="lower right")
    return _save(fig, out, "effect_vs_size")


def pass_diff_forest(estimates: dict, cohorts: list[str], tiers: list[str], out: Path) -> list[str]:
    rows = [(c, t, estimates.get(f"pass_diff.{c}.{t}")) for t in tiers for c in cohorts]
    rows = [r for r in rows if r[2] and r[2].get("estimate") is not None]
    fig, ax = plt.subplots(figsize=(6.4, 0.35 * max(len(rows), 2) + 1.0))
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.axvline(0, color=MUTED, linewidth=1)
    for i, (c, t, e) in enumerate(rows):
        color, _ = TIER_STYLE[t]
        y = len(rows) - 1 - i
        ax.plot(
            [e["ci_low"], e["ci_high"]], [y, y], color=color, linewidth=2, solid_capstyle="round"
        )
        ax.scatter(
            [e["estimate"]],
            [y],
            color=color,
            marker=COHORT_MARK.get(c, "o"),
            s=40,
            zorder=3,
            edgecolors="white",
            linewidths=1,
        )
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels([f"{c} / {t} (n={r['n_tasks']})" for c, t, r in reversed(rows)], fontsize=8)
    ax.set_xlim(-1.05, 1.05)
    ax.set_xlabel("pass rate, spec minus vibe (95% bootstrap CI)", color=INK, fontsize=9)
    ax.set_title("Pass-rate difference by cohort and tier", fontsize=10, color=INK, loc="left")
    return _save(fig, out, "pass_diff_by_cohort")


def two_by_two_rates(estimates: dict, tier: str, out: Path) -> list[str]:
    keys = [
        ("claude-sonnet", "spec"),
        ("claude-sonnet", "vibe"),
        ("claude-opus", "spec"),
        ("claude-opus", "vibe"),
    ]
    vals = [estimates.get(f"h4.{tier}.rate.{c}.{a}") for c, a in keys]
    if not all(vals):
        return []
    fig, ax = plt.subplots(figsize=(4.8, 3.2))
    _style(ax)
    for j, (c, mark) in enumerate((("claude-sonnet", "o"), ("claude-opus", "s"))):
        ys = [vals[2 * j]["estimate"], vals[2 * j + 1]["estimate"]]
        ax.plot([0, 1], ys, color=SERIES[j], linewidth=2, marker=mark, markersize=8, label=c)
        for x, v in zip((0, 1), (vals[2 * j], vals[2 * j + 1])):
            ax.plot([x, x], [v["ci_low"], v["ci_high"]], color=SERIES[j], linewidth=1, alpha=0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["spec", "vibe"])
    ax.set_xlim(-0.4, 1.4)
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("pass rate (mean over tasks)", fontsize=9, color=INK)
    ax.set_title(f"Arm x model, {tier} tier", fontsize=10, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8)
    return _save(fig, out, f"two_by_two_{tier}")


def cost_per_pass(estimates: dict, cohorts: list[str], tiers: list[str], out: Path) -> list[str]:
    rows = []
    for t in tiers:
        for c in cohorts:
            for a in ("spec", "vibe"):
                e = estimates.get(f"cost_eff.{c}.{t}.{a}.cost_per_pass")
                if e and e.get("estimate") is not None:
                    rows.append((f"{c}\n{t}", a, e))
    if not rows:
        return []
    labels = list(dict.fromkeys(r[0] for r in rows))
    fig, ax = plt.subplots(figsize=(max(4.8, 1.0 * len(labels) + 1.5), 3.4))
    _style(ax)
    w = 0.38
    for j, a in enumerate(("spec", "vibe")):
        for lbl, arm, e in rows:
            if arm != a:
                continue
            x = labels.index(lbl) + (j - 0.5) * w
            ax.bar(
                x,
                e["estimate"],
                width=w - 0.04,
                color=SERIES[j],
                hatch="//" if a == "vibe" else None,
                edgecolor="white",
                linewidth=0.5,
                label=a if lbl == next(r[0] for r in rows if r[1] == a) else None,
            )
            if e.get("ci_low") is not None:
                ax.plot([x, x], [e["ci_low"], e["ci_high"]], color=INK, linewidth=1)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("converted USD per passing run", fontsize=9, color=INK)
    ax.set_title("Cost per passing run (95% bootstrap CI)", fontsize=10, color=INK, loc="left")
    ax.legend(frameon=False, fontsize=8)
    return _save(fig, out, "cost_per_pass")
