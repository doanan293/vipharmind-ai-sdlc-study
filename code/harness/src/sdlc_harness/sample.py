"""Stratified sampling of screened commits: review order, layer quotas and final selection."""

import math
import random
from collections import Counter

SEED = 20261115


def _stratifiable(eligible: list[dict]) -> list[dict]:
    # A commit with no layer cannot be stratified (ruling: excluded, listed in REVIEW.md).
    return [r for r in eligible if r.get("layer")]


def review_order(eligible: list[dict], seed: int = SEED) -> list[dict]:
    """Shuffle the eligible commits with a fixed seed; independent of the input order."""
    order = sorted(_stratifiable(eligible), key=lambda r: r["sha"])
    random.Random(seed).shuffle(order)
    return order


def quotas(eligible: list[dict], k: int = 15) -> dict[str, int]:
    """Per-layer quotas proportional to eligible counts (largest remainder, at least 1 each)."""
    counts = Counter(r["layer"] for r in _stratifiable(eligible))
    if not counts:
        return {}
    if len(counts) > k:
        raise ValueError(f"{len(counts)} layers cannot each get a slot out of {k}")
    total = sum(counts.values())
    exact = {layer: k * n / total for layer, n in counts.items()}
    result = {layer: max(1, math.floor(x)) for layer, x in exact.items()}

    def by_remainder(layer: str) -> tuple[float, int, str]:
        return (exact[layer] - math.floor(exact[layer]), counts[layer], layer)

    ranked = sorted(counts, key=by_remainder, reverse=True)
    i = 0
    while sum(result.values()) < k:
        result[ranked[i % len(ranked)]] += 1
        i += 1
    for layer in reversed(ranked):
        if sum(result.values()) == k:
            break
        if result[layer] > 1:
            result[layer] -= 1
    return result


def select(
    order: list[dict], approved: set[str], quotas: dict[str, int], pilots: int = 2
) -> tuple[list[dict], list[dict]]:
    """Walk order; approved commits fill their layer's quota, the first overflow ones are pilots."""
    left = dict(quotas)
    tasks: list[dict] = []
    trial: list[dict] = []
    for rec in order:
        if rec["sha"] not in approved:
            continue
        if left.get(rec["layer"], 0) > 0:
            left[rec["layer"]] -= 1
            tasks.append(rec)
        elif len(trial) < pilots:
            trial.append(rec)
    unfilled = {layer: n for layer, n in left.items() if n > 0}
    if unfilled:
        raise ValueError(f"quotas not filled, review more commits: {unfilled}")
    if len(trial) < pilots:
        raise ValueError(f"only {len(trial)} of {pilots} pilot commits, review more commits")
    return tasks, trial
