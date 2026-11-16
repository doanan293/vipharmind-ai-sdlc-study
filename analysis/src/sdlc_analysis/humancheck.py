"""prereg-v1.2 judge reliability check (a): the 24 brief-prompt units Lợi and Bảo grade by hand,
and the agreement between them and with the checklist judge.

Draw: from the finished, graded (valid) brief-prompt units, stratified by cohort x arm (4 x 2
strata), 3 units per stratum, without replacement, one generator seeded 20261115; strata in the
order of `cohorts` then spec, vibe; each stratum's units sorted by (task, rep) before drawing. Each
drawn unit gets a code derived from the seed and the unit (no cohort, arm or rep text); the packet
order is a permutation by the same generator.

Agreement: per checklist item (one observation = one item of one unit), Cohen's kappa and raw
agreement, on the three verdicts (met / not_met / unclear) and on the binary score scale (met vs
not met, since `unclear` scores as not met), for rater-rater and each rater against the judge.
"""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from sdlc_analysis.labels import cohen_kappa

PER_STRATUM = 3
VERDICTS = ("met", "not_met", "unclear")
SHEET_COLS = ["unit_code", "item_n", "verdict", "note"]
KEY_COLS = ["unit_code", "unit", "cohort", "task_id", "tier", "arm", "rep", "root"]


def unit_code(unit: str, seed: int) -> str:
    return "h" + hashlib.sha256(f"{seed}:human-check:{unit}".encode()).hexdigest()[:8]


def finished_check(cov: pd.DataFrame, expected_total: int) -> list[str]:
    """Reasons the draw must wait: the brief condition is not fully finished (every expected unit
    graded, or excluded after its system-error reruns). Empty list = ready."""
    b = cov[cov["detail"] == "brief"]
    problems = []
    if int(b["expected"].sum()) != expected_total:
        problems.append(f"design has {int(b['expected'].sum())} brief units, expected "
                        f"{expected_total}")
    nf = int(b["not_finished"].sum())
    if nf:
        problems.append(f"{nf} brief units not finished (run, pending or missing)")
    return problems


def draw(valid_brief: pd.DataFrame, cohorts: list[str], seed: int,
         per_stratum: int = PER_STRATUM) -> pd.DataFrame:
    """The private key: one row per drawn unit, in packet order."""
    v = valid_brief.sort_values(["cohort", "task_id", "arm", "rep"]).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    picked = []
    for c in cohorts:
        for arm in ("spec", "vibe"):
            s = v[(v["cohort"] == c) & (v["arm"] == arm)].sort_values(["task_id", "rep"])
            if len(s) < per_stratum:
                raise ValueError(f"stratum {c}/{arm}: {len(s)} units, need {per_stratum}")
            picked.append(s.iloc[np.sort(rng.choice(len(s), per_stratum, replace=False))])
    key = pd.concat(picked).reset_index(drop=True)
    key = key.iloc[rng.permutation(len(key))].reset_index(drop=True)
    key["unit_code"] = [unit_code(u, seed) for u in key["unit"]]
    if key["unit_code"].nunique() != len(key):
        raise ValueError("unit code collision")
    return key[KEY_COLS]


def blank_sheet(key: pd.DataFrame, n_items: dict[str, int]) -> pd.DataFrame:
    rows = [{"unit_code": r["unit_code"], "item_n": n, "verdict": "", "note": ""}
            for r in key.to_dict("records") for n in range(1, n_items[r["task_id"]] + 1)]
    return pd.DataFrame(rows, columns=SHEET_COLS)


def read_sheet(path: Path) -> pd.DataFrame:
    """A filled sheet: unit_code, item_n, verdict (lower-cased, '' when blank)."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["verdict"] = df["verdict"].str.strip().str.lower().str.replace(" ", "_")
    df["item_n"] = df["item_n"].astype(int)
    return df[["unit_code", "item_n", "verdict"]]


def judge_sheet(key: pd.DataFrame) -> pd.DataFrame:
    """The judge's verdicts on the drawn units, in sheet form (units without judge.json absent)."""
    rows = []
    for r in key.to_dict("records"):
        p = Path(r["root"]) / r["unit"] / "judge.json"
        try:
            j = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        for it in j.get("items", []):
            rows.append({"unit_code": r["unit_code"], "item_n": int(it["n"]),
                         "verdict": str(it["verdict"])})
    return pd.DataFrame(rows, columns=["unit_code", "item_n", "verdict"])


def item_agreement(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    """Per-item agreement of two sheets on the items both gave a valid verdict."""
    ka, kb = a[a["verdict"].isin(VERDICTS)], b[b["verdict"].isin(VERDICTS)]
    m = ka.merge(kb, on=["unit_code", "item_n"], suffixes=("_a", "_b"))
    three = cohen_kappa(m["verdict_a"], m["verdict_b"])
    binary = cohen_kappa(m["verdict_a"] == "met", m["verdict_b"] == "met")
    ct = pd.crosstab(m["verdict_a"], m["verdict_b"]) if len(m) else pd.DataFrame()
    return {
        "n_items": len(m),
        "n_units": int(m["unit_code"].nunique()),
        "agreement": three["po"], "kappa": three["kappa"],
        "agreement_binary": binary["po"], "kappa_binary": binary["kappa"],
        "crosstab": {r: {c: int(ct.loc[r, c]) for c in ct.columns} for r in ct.index},
        "invalid_or_blank_a": int((~a["verdict"].isin(VERDICTS)).sum()),
        "invalid_or_blank_b": int((~b["verdict"].isin(VERDICTS)).sum()),
    }


def agreement_report(sheets: dict[str, pd.DataFrame], judge: pd.DataFrame | None) -> dict:
    """Every pair of raters, and each rater against the judge."""
    names = list(sheets)
    out = {}
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            out[f"{x}~{y}"] = item_agreement(sheets[x], sheets[y])
        if judge is not None:
            out[f"{x}~judge"] = item_agreement(sheets[x], judge)
    return out
