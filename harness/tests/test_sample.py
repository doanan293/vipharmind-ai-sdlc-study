import pytest

from sdlc_harness.sample import quotas, review_order, select


def _rec(i: int, layer: str | None) -> dict:
    return {"sha": f"{i:040x}", "subject": f"feat: c{i}", "layer": layer}


def _pool(counts: dict[str, int]) -> list[dict]:
    recs, i = [], 0
    for layer, n in counts.items():
        for _ in range(n):
            recs.append(_rec(i, layer))
            i += 1
    return recs


def test_review_order_is_deterministic():
    pool = _pool({"api": 5, "domain": 7, "infrastructure": 8})
    first = review_order(pool)
    assert [r["sha"] for r in first] == [r["sha"] for r in review_order(list(reversed(pool)))]
    assert sorted(r["sha"] for r in first) == sorted(r["sha"] for r in pool)
    assert [r["sha"] for r in first] != [r["sha"] for r in pool]
    assert [r["sha"] for r in review_order(pool, seed=1)] != [r["sha"] for r in first]


def test_review_order_drops_commits_without_layer():
    pool = _pool({"api": 2}) + [_rec(99, None)]
    assert {r["sha"] for r in review_order(pool)} == {_rec(0, "api")["sha"], _rec(1, "api")["sha"]}


def test_quotas_sum_to_k_and_cover_layers():
    pool = _pool({"infrastructure": 20, "domain": 10, "application": 6, "api": 4})
    q = quotas(pool)
    assert sum(q.values()) == 15
    assert set(q) == {"infrastructure", "domain", "application", "api"}
    assert all(v >= 1 for v in q.values())
    # 7.5 / 3.75 / 2.25 / 1.5 -> floors 7/3/2/1; remainders .75 (domain), then .5 tied
    # between infrastructure and api: the tie goes to the larger layer
    assert q == {"infrastructure": 8, "domain": 4, "application": 2, "api": 1}


def test_quotas_give_every_layer_at_least_one():
    q = quotas(_pool({"infrastructure": 40, "api": 1}), k=5)
    assert q == {"infrastructure": 4, "api": 1}


def test_quotas_ignore_commits_without_layer():
    q = quotas(_pool({"domain": 3}) + [_rec(99, None)], k=2)
    assert q == {"domain": 2}


def test_select_fills_quotas_in_order_and_picks_pilots():
    a = [_rec(i, "api") for i in range(4)]
    d = [_rec(i, "domain") for i in range(10, 14)]
    order = [a[0], d[0], a[1], d[1], a[2], d[2], d[3], a[3]]
    approved = {r["sha"] for r in order} - {d[1]["sha"]}
    tasks, pilots = select(order, approved, {"api": 1, "domain": 2})
    assert [r["sha"] for r in tasks] == [a[0]["sha"], d[0]["sha"], d[2]["sha"]]
    # a[1] and a[2] are the first approved commits that fit no quota
    assert [r["sha"] for r in pilots] == [a[1]["sha"], a[2]["sha"]]


def test_select_takes_later_approved_commits_as_pilots():
    a = [_rec(i, "api") for i in range(4)]
    tasks, pilots = select(a, {r["sha"] for r in a[:1] + a[2:]}, {"api": 1})
    assert [r["sha"] for r in tasks] == [a[0]["sha"]]
    assert [r["sha"] for r in pilots] == [a[2]["sha"], a[3]["sha"]]


def test_select_raises_when_quota_unfilled():
    a = [_rec(i, "api") for i in range(4)]
    with pytest.raises(ValueError, match="api"):
        select(a, {a[0]["sha"]}, {"api": 2})


def test_select_raises_when_pilots_short():
    a = [_rec(i, "api") for i in range(4)]
    with pytest.raises(ValueError, match="pilot"):
        select(a, {a[0]["sha"], a[1]["sha"]}, {"api": 1})
