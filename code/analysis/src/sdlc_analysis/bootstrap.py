"""Task-level bootstrap of prereg-v1 section 9, point 1.

Resample tasks with replacement, keeping every repetition of a chosen task (so every statistic
is a function of per-task values); 10,000 resamples; percentile interval 2.5%-97.5%; seed
20261115. Every estimate starts its own generator from the seed, so it does not depend on the
order estimates are computed in.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np

B_DEFAULT = 10_000
SEED_DEFAULT = 20261115
LEVEL = 0.95
CI_TYPE = "percentile 2.5-97.5, tasks resampled with replacement"


@dataclass
class Estimate:
    estimate: float | None
    ci_low: float | None
    ci_high: float | None
    n_tasks: Any  # int, or {group: int} for independent resampling
    B: int
    seed: int
    n_undefined: int = 0  # resamples where the statistic is undefined (left out of the interval)
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        extra = d.pop("extra")
        d["ci_type"] = CI_TYPE
        d.update(extra)
        return d


def _f(x: float) -> float | None:
    return None if x is None or not np.isfinite(x) else float(x)


def _interval(stats: np.ndarray) -> tuple[float | None, float | None, int]:
    ok = np.isfinite(stats)
    undefined = int((~ok).sum())
    if not ok.any():
        return None, None, undefined
    a = (1 - LEVEL) / 2 * 100
    lo, hi = np.percentile(stats[ok], [a, 100 - a])
    return float(lo), float(hi), undefined


def boot_stat(
    data: np.ndarray,
    stat: Callable[[np.ndarray], np.ndarray],
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
) -> Estimate:
    """`data` has one row per task (columns: per-task values). `stat` maps an array of shape
    (..., n_tasks, k) to (...,): it is called on the data itself and on all B resamples."""
    data = np.asarray(data, dtype=float)
    if data.ndim == 1:
        data = data[:, None]
    n = data.shape[0]
    if n == 0:
        return Estimate(None, None, None, 0, B, seed)
    with np.errstate(divide="ignore", invalid="ignore"):
        point = float(stat(data[None])[0])
        rng = np.random.default_rng(seed)
        idx = rng.integers(0, n, size=(B, n))
        stats = np.asarray(stat(data[idx]), dtype=float)
    lo, hi, und = _interval(stats)
    if not np.isfinite(point):
        return Estimate(None, None, None, n, B, seed, und)
    return Estimate(point, lo, hi, n, B, seed, und)


def boot_mean(values, *, B: int = B_DEFAULT, seed: int = SEED_DEFAULT) -> Estimate:
    return boot_stat(np.asarray(values, float), lambda x: x[..., 0].mean(-1), B=B, seed=seed)


def boot_ratio(num, den, *, B: int = B_DEFAULT, seed: int = SEED_DEFAULT) -> Estimate:
    """sum(num) / sum(den) over tasks; undefined (not 0) when sum(den) == 0."""
    data = np.column_stack([np.asarray(num, float), np.asarray(den, float)])

    def stat(x):
        d = x[..., 1].sum(-1)
        return np.where(d > 0, x[..., 0].sum(-1) / np.where(d > 0, d, 1), np.nan)

    return boot_stat(data, stat, B=B, seed=seed)


def boot_independent_diff(
    a,
    b,
    *,
    B: int = B_DEFAULT,
    seed: int = SEED_DEFAULT,
    stat: Callable[[np.ndarray], np.ndarray] | None = None,
) -> Estimate:
    """stat(a) - stat(b), each group resampled on its own (tiers: prereg 9.1). One generator
    from the seed draws group a's resamples, then group b's. Rows of a and b may have several
    columns; default stat is the mean of column 0."""
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    a = a[:, None] if a.ndim == 1 else a
    b = b[:, None] if b.ndim == 1 else b
    stat = stat or (lambda x: x[..., 0].mean(-1))
    if len(a) == 0 or len(b) == 0:
        return Estimate(None, None, None, {"a": len(a), "b": len(b)}, B, seed)
    rng = np.random.default_rng(seed)
    ia = rng.integers(0, len(a), size=(B, len(a)))
    ib = rng.integers(0, len(b), size=(B, len(b)))
    with np.errstate(divide="ignore", invalid="ignore"):
        point = float(stat(a[None])[0] - stat(b[None])[0])
        stats = np.asarray(stat(a[ia]) - stat(b[ib]), float)
    lo, hi, und = _interval(stats)
    return Estimate(_f(point), lo, hi, {"a": len(a), "b": len(b)}, B, seed, und)


def verdict(ci_low, ci_high, direction: int = 1, margin: float = 0.0) -> str:
    """Prereg 9 reading rule. direction +1: the hypothesis says the effect is above `margin`;
    -1: below it. "supported" when the 95% CI lies entirely (strictly) on the hypothesis side,
    "contrary" when entirely on the other side, otherwise "inconclusive"."""
    if ci_low is None or ci_high is None:
        return "not_estimable"
    lo, hi = (ci_low - margin, ci_high - margin)
    if direction < 0:
        lo, hi = -hi, -lo
    if lo > 0:
        return "supported"
    if hi < 0:
        return "contrary"
    return "inconclusive"
