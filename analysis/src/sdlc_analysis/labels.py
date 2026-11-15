"""Failure labels (prereg-v1 9.8): labeling sheet template, Cohen's kappa of two raters; and the
"passes tests but wrong" sample (9.10)."""

from pathlib import Path

import numpy as np
import pandas as pd

LABELS = ("hieu_sai", "lam_thieu", "sai_giao_dien", "hong_chuc_nang_cu", "loi_logic",
          "khong_hoan_thanh", "de_bai_thieu", "sai_api_co_san", "loi_moi_truong")
CLAUDE = ("claude-sonnet", "claude-opus")
TIER_ORDER = ("small", "medium", "large")
REVEALED = "lộ cách làm"
TIMEOUT_NOTE = "het_gio"


def labeling_template(valid: pd.DataFrame, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every valid failing run of the two Claude cohorts, all tiers, under a random id in a
    shuffled order. Returns (sheet for the raters, private key id -> unit). Timed-out runs carry
    `het_gio` in `note` (labeling guide)."""
    v = valid[valid["cohort"].isin(CLAUDE) & ~valid["task_pass"].astype(bool)]
    v = v.sort_values(["cohort", "task_id", "arm", "rep"]).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(v))
    ids: list[str] = []
    seen = set()
    while len(ids) < len(v):
        uid = "u" + "".join(f"{b:02x}" for b in rng.integers(0, 256, size=4))
        if uid not in seen:
            seen.add(uid)
            ids.append(uid)
    shuffled = v.iloc[order].reset_index(drop=True)
    sheet = pd.DataFrame({
        "unit_id": ids,
        "label": "",
        "note": [TIMEOUT_NOTE if t else "" for t in shuffled["timed_out"].astype(bool)],
    })
    key = pd.DataFrame({"unit_id": ids}).join(
        shuffled[["unit", "cohort", "task_id", "tier", "arm", "rep", "timed_out"]])
    return sheet, key


def cohen_kappa(a: pd.Series, b: pd.Series) -> dict:
    a, b = a.astype(str).reset_index(drop=True), b.astype(str).reset_index(drop=True)
    n = len(a)
    if n == 0:
        return {"kappa": None, "po": None, "pe": None, "n": 0}
    cats = sorted(set(a) | set(b))
    po = float((a == b).mean())
    pa = a.value_counts(normalize=True).reindex(cats, fill_value=0)
    pb = b.value_counts(normalize=True).reindex(cats, fill_value=0)
    pe = float((pa * pb).sum())
    kappa = None if np.isclose(pe, 1.0) else (po - pe) / (1 - pe)
    return {"kappa": kappa, "po": po, "pe": pe, "n": n}


def _read_sheet(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for c in ("unit_id", "label", "note"):
        if c not in df:
            df[c] = ""
    df["label"] = df["label"].str.strip()
    return df.set_index("unit_id")


def kappa_report(path_a: Path, path_b: Path) -> dict:
    """Kappa on the single labels of every unit both raters labeled, the cross-table (rows rater
    A, columns rater B), and the share of units a rater marked "lộ cách làm" (arm revealed)."""
    a, b = _read_sheet(path_a), _read_sheet(path_b)
    la, lb = a[a["label"] != ""], b[b["label"] != ""]
    both = sorted(set(la.index) & set(lb.index))
    k = cohen_kappa(la.loc[both, "label"], lb.loc[both, "label"])
    ct = pd.crosstab(la.loc[both, "label"].rename("a"), lb.loc[both, "label"].rename("b"))
    ra = a.loc[both, "note"].str.lower().str.contains(REVEALED)
    rb = b.loc[both, "note"].str.lower().str.contains(REVEALED)
    invalid = sorted({lbl for lbl in pd.concat([la["label"], lb["label"]]) if lbl not in LABELS})
    return {
        **k,
        "n_both": len(both),
        "n_agree": int((la.loc[both, "label"] == lb.loc[both, "label"]).sum()),
        "n_only_a": len(set(la.index) - set(lb.index)),
        "n_only_b": len(set(lb.index) - set(la.index)),
        "crosstab": {r: {c: int(ct.loc[r, c]) for c in ct.columns} for r in ct.index},
        "revealed_arm": {"rater_a": int(ra.sum()), "rater_b": int(rb.sum()),
                         "either": int((ra | rb).sum()),
                         "share_either": float((ra | rb).mean()) if both else None},
        "disagreements": [u for u in both if la.loc[u, "label"] != lb.loc[u, "label"]],
        "invalid_labels": invalid,
    }


def _allocate(counts: dict[str, int], n: int) -> dict[str, int]:
    """Largest-remainder allocation of n proportional to counts (ties: tier order)."""
    total = sum(counts.values())
    if total <= n:
        return dict(counts)
    quota = {k: n * c / total for k, c in counts.items()}
    alloc = {k: int(np.floor(q)) for k, q in quota.items()}
    rest = n - sum(alloc.values())
    order = sorted(counts, key=lambda k: (-(quota[k] - alloc[k]), TIER_ORDER.index(k)
                                          if k in TIER_ORDER else 99))
    for k in order[:rest]:
        alloc[k] += 1
    return alloc


def passing_sample(valid: pd.DataFrame, seed: int, per_arm: int = 10) -> pd.DataFrame:
    """Prereg 9.10: 20 passing runs of the two Claude cohorts, 10 per arm, allocated to tiers in
    proportion to that arm's passing runs per tier; drawn without replacement with one generator
    (seed), arms in order spec, vibe, tiers small, medium, large, from the list sorted by
    (cohort, task, arm, rep)."""
    p = valid[valid["cohort"].isin(CLAUDE) & valid["task_pass"].astype(bool)]
    p = p.sort_values(["cohort", "task_id", "arm", "rep"]).reset_index(drop=True)
    rng = np.random.default_rng(seed)
    picked = []
    for arm in ("spec", "vibe"):
        pa = p[p["arm"] == arm]
        counts = {t: int((pa["tier"] == t).sum()) for t in TIER_ORDER if (pa["tier"] == t).any()}
        for tier, k in _allocate(counts, per_arm).items():
            stratum = pa[pa["tier"] == tier]
            if k:
                picked.append(stratum.iloc[np.sort(rng.choice(len(stratum), k, replace=False))])
    cols = ["unit", "cohort", "task_id", "tier", "arm", "rep", "task_pass"]
    return pd.concat(picked)[cols].reset_index(drop=True) if picked else pd.DataFrame(columns=cols)
