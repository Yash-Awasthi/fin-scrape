"""Tests for factor analysis service."""

import pytest
from finscrape.services.factor_analysis import (
    FactorData,
    calculate_ic,
    calculate_factor_returns,
    calculate_factor_weights,
    calculate_ic_decay,
    rank_correlation,
)


@pytest.fixture
def sample_factor_data():
    return [
        FactorData(1.0, "A", 0.5, 0.02),
        FactorData(1.0, "B", -0.3, -0.01),
        FactorData(1.0, "C", 0.8, 0.03),
        FactorData(2.0, "A", 0.4, 0.01),
        FactorData(2.0, "B", -0.2, -0.005),
        FactorData(2.0, "C", 0.9, 0.04),
    ]


class TestRankCorrelation:
    def test_perfect_correlation(self):
        assert rank_correlation([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0, abs=0.01)

    def test_inverse_correlation(self):
        assert rank_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0, abs=0.01)

    def test_no_correlation(self):
        result = rank_correlation([1, 2, 3], [1, 3, 2])
        assert -1 <= result <= 1

    def test_empty(self):
        assert rank_correlation([], []) == 0.0

    def test_single_element(self):
        assert rank_correlation([1], [2]) == 0.0


class TestIC:
    def test_calculate_ic(self, sample_factor_data):
        result = calculate_ic(sample_factor_data)
        assert -1 <= result.mean_ic <= 1
        assert result.std_ic >= 0
        assert len(result.ic_series) > 0

    def test_empty_data(self):
        result = calculate_ic([])
        assert result.mean_ic == 0.0


class TestFactorReturns:
    def test_calculate_returns(self, sample_factor_data):
        result = calculate_factor_returns(sample_factor_data)
        assert result.max_drawdown >= 0
        assert result.turnover >= 0

    def test_empty_data(self):
        result = calculate_factor_returns([])
        assert result.long_short_return == 0


class TestFactorWeights:
    def test_calculate_weights(self, sample_factor_data):
        weights = calculate_factor_weights(sample_factor_data)
        assert len(weights) > 0
        total = sum(abs(w) for w in weights.values())
        assert total == pytest.approx(1.0, abs=0.01)

    def test_empty_data(self):
        assert calculate_factor_weights([]) == {}


class TestICDecay:
    def test_decay(self, sample_factor_data):
        decay = calculate_ic_decay(sample_factor_data, max_lag=2)
        assert len(decay) == 2

    def test_empty_data(self):
        assert calculate_ic_decay([]) == []
