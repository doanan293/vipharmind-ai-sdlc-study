import numpy as np
import pytest

from sdlc_analysis.bootstrap import (
    B_DEFAULT,
    SEED_DEFAULT,
    boot_independent_diff,
    boot_mean,
    boot_ratio,
    boot_stat,
    verdict,
)


def test_prereg_constants():
    assert B_DEFAULT == 10_000
    assert SEED_DEFAULT == 20261115


def test_constant_task_effects_give_a_degenerate_interval_at_the_true_value():
    est = boot_mean(np.full(15, 2 / 3), B=2000, seed=1)
    assert est.estimate == pytest.approx(2 / 3)
    assert est.ci_low == pytest.approx(2 / 3) and est.ci_high == pytest.approx(2 / 3)
    assert est.n_tasks == 15


def test_mean_matches_a_naive_loop_with_the_same_generator():
    values = np.array([0.0, 1 / 3, 1.0, -1 / 3, 2 / 3, 0.0, 1.0])
    est = boot_mean(values, B=500, seed=7)
    rng = np.random.default_rng(7)
    idx = rng.integers(0, len(values), size=(500, len(values)))
    stats = [values[row].mean() for row in idx]
    lo, hi = np.percentile(stats, [2.5, 97.5])
    assert est.estimate == pytest.approx(values.mean())
    assert (est.ci_low, est.ci_high) == pytest.approx((lo, hi))


def test_same_seed_same_interval():
    v = np.random.default_rng(3).normal(size=20)
    a, b = boot_mean(v, B=1000, seed=5), boot_mean(v, B=1000, seed=5)
    assert (a.ci_low, a.ci_high) == (b.ci_low, b.ci_high)


def test_interval_covers_known_mean_of_large_sample():
    v = np.random.default_rng(11).normal(loc=0.3, scale=0.2, size=400)
    est = boot_mean(v, B=2000, seed=1)
    assert est.ci_low < 0.3 < est.ci_high
    assert est.ci_high - est.ci_low == pytest.approx(2 * 1.96 * 0.2 / 20, rel=0.15)


def test_joint_resampling_keeps_columns_of_a_task_together():
    # two cohorts with identical per-task effects: their difference is 0 in every resample
    v = np.random.default_rng(0).normal(size=12)
    data = np.column_stack([v, v])
    est = boot_stat(data, lambda x: x[..., 0].mean(-1) - x[..., 1].mean(-1), B=1000, seed=1)
    assert est.estimate == 0 and est.ci_low == 0 and est.ci_high == 0


def test_independent_resampling_per_group():
    est = boot_independent_diff(np.full(3, 0.6), np.full(15, 0.2), B=1000, seed=1)
    assert est.estimate == pytest.approx(0.4)
    assert est.ci_low == pytest.approx(0.4) and est.ci_high == pytest.approx(0.4)
    noisy = boot_independent_diff(np.array([0.0, 1.0]), np.full(15, 0.0), B=1000, seed=1)
    assert noisy.ci_low == 0.0 and noisy.ci_high == 1.0
    assert noisy.n_tasks == {"a": 2, "b": 15}


def test_ratio_counts_undefined_resamples():
    num = np.array([0.0, 0.0, 3.0])  # passes per task
    den = np.array([1.0, 1.0, 1.0])  # cost per task
    est = boot_ratio(den, num, B=2000, seed=2)  # cost per pass: undefined without passes
    assert est.estimate == pytest.approx(1.0)
    assert 0 < est.n_undefined < 2000  # P(no task 3 drawn) = (2/3)^3 ~ 0.30
    assert est.n_undefined / 2000 == pytest.approx((2 / 3) ** 3, abs=0.04)
    none = boot_ratio(den, np.zeros(3), B=100, seed=2)
    assert none.estimate is None and none.ci_low is None


def test_empty_input_gives_no_estimate():
    est = boot_mean(np.array([]), B=100, seed=1)
    assert est.estimate is None and est.n_tasks == 0


@pytest.mark.parametrize(
    ("lo", "hi", "direction", "margin", "expected"),
    [
        (0.1, 0.3, 1, 0.0, "supported"),
        (-0.3, -0.1, 1, 0.0, "contrary"),
        (-0.1, 0.3, 1, 0.0, "inconclusive"),
        (0.0, 0.3, 1, 0.0, "inconclusive"),  # "entirely on one side": a bound on 0 is not
        (-0.3, -0.1, -1, 0.0, "supported"),
        (-4.0, 2.0, 1, -5.0, "supported"),  # non-inferiority: lower bound above -5
        (-7.0, 2.0, 1, -5.0, "inconclusive"),
        (-9.0, -6.0, 1, -5.0, "contrary"),
        (None, None, 1, 0.0, "not_estimable"),
    ],
)
def test_reading_rule(lo, hi, direction, margin, expected):
    assert verdict(lo, hi, direction, margin) == expected
