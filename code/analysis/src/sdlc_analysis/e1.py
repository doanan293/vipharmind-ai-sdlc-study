"""sdlc-e1: exploratory experiment E1 of prereg-v1.2 (Haiku on the main design).

    uv run sdlc-e1 --results MAIN MAIN_TIERS HAIKU [--out DIR] [any sdlc-analysis option]

prereg-v1.2: "analysed with exactly the code locked at tag `prereg-v1-analysis`, but as a separate
analysis (Haiku added as one more cohort), not pooled into the confirmatory results". This entry
point therefore runs the locked `sdlc_analysis.cli.main` unchanged, with three differences only:

- default cohorts `claude-sonnet,claude-opus,codex-luna,claude-haiku` (agy-gemini is not part of
  the E1 comparison; pass `--cohorts` to change it);
- default output directory `data/results/analysis/e1/` (never the confirmatory output);
- `claude-haiku-5-5` has no row in the frozen price table of prereg-v1 section 7, and the locked
  loader raises on a cohort model without a price. Inside this entry point a run whose cohort model
  has no price gets `cost_usd = None` (cost not known) instead; tokens are still counted, and every
  other model is priced exactly as in the locked code. Cost-effectiveness of Haiku is therefore
  not estimable (reported as missing), never imputed.
"""

import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sdlc_analysis import cli, load
from sdlc_analysis.prices import table_model

REPO = Path(__file__).resolve().parents[4]
E1_COHORTS = ("claude-sonnet", "claude-opus", "codex-luna", "claude-haiku")
E1_OUT = REPO / "data" / "results" / "analysis" / "e1"


@contextmanager
def unpriced_cohort_cost_unknown() -> Iterator[None]:
    """While active, the loader's cost of a run whose cohort model is not in the price table is
    None instead of a KeyError. Priced models are untouched (same function, same arguments)."""
    orig = load.cost_usd

    def cost_or_none(tokens, cohort_model, long_context=False):
        if table_model(cohort_model) is None:
            return None
        return orig(tokens, cohort_model, long_context)

    load.cost_usd = cost_or_none
    try:
        yield
    finally:
        load.cost_usd = orig


def _has(argv: list[str], flag: str) -> bool:
    return any(a == flag or a.startswith(flag + "=") for a in argv)


def e1_argv(argv: list[str]) -> list[str]:
    """The sdlc-analysis argument list with the E1 defaults added where not given."""
    out = list(argv)
    if not _has(out, "--tasks"):
        out += ["--tasks", str(REPO / "data" / "tasks")]
    if not _has(out, "--out"):
        out += ["--out", str(E1_OUT)]
    if not _has(out, "--cohorts"):
        out += ["--cohorts", ",".join(E1_COHORTS)]
    return out


EXPLORATORY_NOTE = (
    "E1 of prereg-v1.2: exploratory, added after the main results were seen. Haiku is one more "
    "cohort in a separate run of the locked prereg-v1 analysis; nothing here confirms or refutes "
    "H1-H5, and the verdict labels below are the locked code's reading rule, not a test."
)


def main(argv: list[str] | None = None) -> int:
    argv = e1_argv(sys.argv[1:] if argv is None else argv)
    with unpriced_cohort_cost_unknown():
        rc = cli.main(argv)
    out = cli.parse_args(argv).out
    path = out / "summary.json"
    s = json.loads(path.read_text())
    s["meta"]["exploratory"] = EXPLORATORY_NOTE
    s["meta"]["unpriced_cohort_models_cost_unknown"] = True
    path.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
