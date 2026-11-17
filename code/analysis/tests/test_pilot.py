"""Checks against the real pilot data (data/results/raw/pilot), skipped when it is absent."""

import json
from pathlib import Path

import pytest

from sdlc_analysis.load import load_runs, load_tasks

ROOT = Path(__file__).resolve().parents[3] / "data"
PILOT = ROOT / "results" / "raw" / "pilot"
pytestmark = pytest.mark.skipif(not PILOT.is_dir(), reason="no pilot results")


def test_claude_cost_matches_claude_codes_own_list_price_cost():
    runs = load_runs(PILOT, load_tasks(ROOT / "tasks", ["p01", "p02"]))
    claude = runs[runs["agent"] == "claude"]
    assert len(claude) == 24
    for row in claude.itertuples():
        lines = (PILOT / row.unit / "transcript.jsonl").read_text().splitlines()
        result = [json.loads(x) for x in lines if x.startswith("{") and '"result"' in x]
        result = [e for e in result if e.get("type") == "result"][-1]
        reported = sum(m["costUSD"] for m in result["modelUsage"].values())
        assert row.cost_usd == pytest.approx(reported, rel=1e-9)


def test_pilot_statuses():
    runs = load_runs(PILOT, load_tasks(ROOT / "tasks", ["p01", "p02"]))
    assert int(runs["valid"].sum()) == 38
    assert set(runs.loc[~runs["valid"], "status"]) == {"quota"}
