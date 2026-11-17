from retro.figures import week_range


def test_week_range_fills_empty_weeks():
    assert week_range(["2026-W33", "2026-W30"]) == ["2026-W30", "2026-W31", "2026-W32", "2026-W33"]


def test_week_range_crosses_year():
    assert week_range(["2026-W52", "2027-W02"]) == ["2026-W52", "2026-W53", "2027-W01", "2027-W02"]


def test_week_range_empty():
    assert week_range([]) == []
