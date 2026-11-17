"""Simulated data sets shaped like the main design (23 tasks with their real `src_lines` and
tiers, 4 cohorts, 2 arms, 3 reps), from the H5 model with known coefficients. Used by the tests
and by the calibration scripts in code/analysis/calibration/."""

import numpy as np
import pandas as pd

# t01-t15, m01-m05, f08, f14, f15: src_lines from data/tasks/*/task.toml
MAIN_SRC = [
    311,
    197,
    198,
    73,
    186,
    67,
    232,
    43,
    120,
    141,
    102,
    45,
    148,
    68,
    121,
    478,
    335,
    413,
    362,
    515,
    764,
    1464,
    1367,
]
MAIN_TIER = ["small"] * 15 + ["medium"] * 5 + ["large"] * 3


def simulate(
    n_tasks=60,
    cohorts=("a", "b", "c"),
    reps=3,
    beta_int=1.0,
    seed=0,
    sd0=0.8,
    sd1=0.4,
    src=None,
    tiers=None,
) -> pd.DataFrame:
    """Valid runs from pass ~ arm x log(src) + cohort + (1 + arm | task):
    intercept -0.2, arm 0.5, log(src) -0.8, interaction `beta_int` (log src centred),
    cohort effects spread over [-0.5, 0.5], task SDs `sd0` (intercept) and `sd1` (arm)."""
    rng = np.random.default_rng(seed)
    if src is None:
        src = np.exp(rng.uniform(np.log(40), np.log(1500), n_tasks)).round().astype(int)
    src = np.asarray(src)
    n_tasks = len(src)
    tiers = tiers or ["small"] * n_tasks
    x = np.log(src) - np.log(src).mean()
    u0 = rng.normal(0, sd0, n_tasks) if sd0 else np.zeros(n_tasks)
    u1 = rng.normal(0, sd1, n_tasks) if sd1 else np.zeros(n_tasks)
    coh_eff = dict(zip(cohorts, np.linspace(-0.5, 0.5, len(cohorts))))
    rows = []
    for t in range(n_tasks):
        for c in cohorts:
            for arm in (0, 1):
                eta = -0.2 + 0.5 * arm - 0.8 * x[t] + beta_int * arm * x[t] + coh_eff[c]
                eta += u0[t] + u1[t] * arm
                p = 1 / (1 + np.exp(-eta))
                for r in range(reps):
                    rows.append(
                        {
                            "cohort": c,
                            "task_id": f"x{t:03d}",
                            "arm": "spec" if arm else "vibe",
                            "rep": r + 1,
                            "src_lines": int(src[t]),
                            "log_src_lines": float(np.log(src[t])),
                            "tier": tiers[t],
                            "task_pass": bool(rng.random() < p),
                        }
                    )
    return pd.DataFrame(rows)


def main_design(seed: int, **kw) -> pd.DataFrame:
    return simulate(cohorts=("a", "b", "c", "d"), src=MAIN_SRC, tiers=MAIN_TIER, seed=seed, **kw)
