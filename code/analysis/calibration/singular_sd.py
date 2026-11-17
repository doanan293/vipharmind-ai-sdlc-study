"""Calibrate the singular-fit criterion of the H5 mixed model (README, note 2).

On the 23-task main design, simulate data with a true random-slope SD of 0, 0.4 and 0.8 (20 data
sets each, intercept SD 0.8, interaction 0), fit level 1 with the analysis' own settings, and
record the variational posterior-mean SD of each component and the evidence lower bound of
level 1 and level 2. Writes calibration/singular_sd.csv and prints the firing rates.

    cd analysis && nice -n 19 uv run python calibration/singular_sd.py [--jobs 2]
"""

import argparse
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from sdlc_analysis import mixed
from sdlc_analysis.simulate import main_design

OUT = Path(__file__).with_suffix(".csv")
SLOPE_SDS = (0.0, 0.4, 0.8)
N_SETS = 20


def one(args):
    seed, sd1 = args
    warnings.simplefilter("ignore")
    df = mixed._prepare(main_design(seed, beta_int=0.0, sd0=0.8, sd1=sd1))
    f = mixed._formula(df)
    row = {"seed": seed, "true_slope_sd": sd1}
    for level in (1, 2):
        res = mixed._fit_glmm(df, mixed.VC[level], f, seed)
        row[f"elbo{level}"] = mixed.elbo(res)
        if level == 1:
            row["fit_intercept_sd"], row["fit_slope_sd"] = np.exp(res.vcp_mean)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", type=int, default=1)
    a = ap.parse_args()
    jobs = [(s, sd1) for sd1 in SLOPE_SDS for s in range(N_SETS)]
    with ProcessPoolExecutor(a.jobs) as ex:
        d = pd.DataFrame(list(ex.map(one, jobs)))
    d["elbo1_minus_elbo2"] = d["elbo1"] - d["elbo2"]
    d.to_csv(OUT, index=False)
    print(d.groupby("true_slope_sd")[["fit_slope_sd", "elbo1_minus_elbo2"]].describe().T)
    for thr in (0.25, 0.30, 0.35, 0.40):
        rates = d.assign(f=d["fit_slope_sd"] < thr).groupby("true_slope_sd")["f"].mean()
        print(f"slope SD < {thr}: fires at", rates.round(2).to_dict())
    print(
        "ELBO(level 2) >= ELBO(level 1):",
        d.assign(f=d["elbo1_minus_elbo2"] <= 0).groupby("true_slope_sd")["f"].mean().to_dict(),
    )


if __name__ == "__main__":
    main()
