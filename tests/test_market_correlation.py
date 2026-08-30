"""Tests for market correlation service."""

import pytest
from finscrape.services.market_correlation import (
    calculate_correlation,
    calculate_returns,
    calculate_rolling_correlation,
    calculate_correlation_matrix,
    find_strongest_correlations,
    find_lead_lag_relationships,
    match_crash_pattern,
    detect_anomaly,
)


class TestCorrelation:
    def test_perfect_positive(self):
        assert calculate_correlation([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) == pytest.approx(1.0, abs=0.01)

    def test_perfect_negative(self):
        assert calculate_correlation([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) == pytest.approx(-1.0, abs=0.01)

    def test_no_correlation(self):
        result = calculate_correlation([1, 3, 2, 5, 4], [2, 1, 4, 3, 5])
        assert -1 <= result <= 1

    def test_empty(self):
        assert calculate_correlation([], []) == 0.0

    def test_different_lengths(self):
        assert calculate_correlation([1, 2], [1, 2, 3]) == 0.0


class TestReturns:
    def test_calculate_returns(self):
        returns = calculate_returns([100, 110, 105])
        assert len(returns) == 2
        assert returns[0] == pytest.approx(0.1, abs=0.01)

    def test_empty(self):
        assert calculate_returns([]) == []

    def test_with_period(self):
        returns = calculate_returns([100, 110, 105, 120], period=2)
        assert len(returns) == 2


class TestRollingCorrelation:
    def test_rolling(self):
        x = list(range(20))
        y = list(range(20))
        result = calculate_rolling_correlation(x, y, window=10)
        assert len(result) > 0
        assert all(-1.01 <= r <= 1.01 for r in result)


class TestCorrelationMatrix:
    def test_matrix(self):
        data = {"A": [1, 2, 3, 4], "B": [4, 3, 2, 1]}
        matrix = calculate_correlation_matrix(data)
        assert "A" in matrix
        assert "B" in matrix["A"]
        assert matrix["A"]["A"] == pytest.approx(1.0, abs=0.01)


class TestStrongestCorrelations:
    def test_find(self):
        data = {"A": list(range(20)), "B": list(range(20))}
        result = find_strongest_correlations(data, min_correlation=0.5)
        assert len(result) > 0
        assert result[0].correlation > 0.5


class TestLeadLag:
    def test_find(self):
        data = {"A": list(range(20)), "B": list(range(20))}
        result = find_lead_lag_relationships(data, max_lag_weeks=3, min_correlation=0.3)
        assert isinstance(result, list)


class TestCrashPattern:
    def test_match(self):
        current = {"vix": 30, "yield_curve": -0.5}
        patterns = [{"name": "2008", "vix": 35, "yield_curve": -0.3}]
        matches = match_crash_pattern(current, patterns, threshold=0.5)
        assert len(matches) > 0
        assert matches[0]["similarity"] > 0.5


class TestAnomaly:
    def test_detect(self):
        import random
        random.seed(42)
        values = [1 + random.gauss(0, 0.1) for _ in range(25)]
        values.append(10)  # clear anomaly
        anomalies = detect_anomaly(values, window=10, std_threshold=2.0)
        assert len(anomalies) > 0
        assert anomalies[0]["direction"] == "high"

    def test_no_anomaly(self):
        values = list(range(30))
        anomalies = detect_anomaly(values, window=10)
        assert len(anomalies) == 0
