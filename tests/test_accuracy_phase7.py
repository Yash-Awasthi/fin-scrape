"""Phase 7: accuracy correctness rule + aggregation (pure, offline).

The backtest DB path (server.accuracy.backtest) is covered by the docker integration run.
"""
from server.accuracy import aggregate, verdict_outcome


def test_verdict_outcome_directional():
    assert verdict_outcome("INVEST", 2.0) == "correct"
    assert verdict_outcome("INVEST", -2.0) == "incorrect"
    assert verdict_outcome("INVEST", 0.5) == "neutral"  # below ±1% threshold
    assert verdict_outcome("PULL_OUT", -2.0) == "correct"
    assert verdict_outcome("PULL_OUT", 2.0) == "incorrect"


def test_verdict_outcome_nondirectional():
    assert verdict_outcome("OBSERVE", 5.0) == "neutral"
    assert verdict_outcome("CAUTIOUS", -5.0) == "neutral"


def test_aggregate_hit_rate_and_equity_curve():
    rows = [
        {"verdict": "INVEST", "correct": True, "checked_at": "2026-01-01T00:00:00"},
        {"verdict": "INVEST", "correct": False, "checked_at": "2026-01-02T00:00:00"},
        {"verdict": "PULL_OUT", "correct": True, "checked_at": "2026-01-03T00:00:00"},
        {"verdict": "OBSERVE", "correct": None, "checked_at": "2026-01-04T00:00:00"},  # unscored
    ]
    agg = aggregate(rows)
    assert agg["total"] == 4 and agg["scored"] == 3
    assert agg["hits"] == 2
    assert agg["hit_rate"] == round(2 / 3, 3)
    assert agg["by_verdict"]["INVEST"] == {"hits": 1, "total": 2, "hit_rate": 0.5}
    # cumulative +1 / -1 in time order: +1, 0, +1
    assert agg["equity_curve"] == [1, 0, 1]


def test_aggregate_empty():
    agg = aggregate([])
    assert agg["hit_rate"] == 0.0 and agg["equity_curve"] == []
