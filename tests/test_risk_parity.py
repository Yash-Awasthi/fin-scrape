"""Tests for risk_parity.py — portfolio optimization."""

import math
import pytest
from finscrape.services.risk_parity import (
    Asset, PortfolioAllocation, EfficientFrontier,
    risk_parity, mean_variance_optimize, minimum_variance,
    maximum_sharpe, efficient_frontier, diversification_ratio,
    _mean, _std, _covariance, _correlation,
)


def _make_assets():
    """Create test assets with different risk/return profiles."""
    return {
        "bonds": Asset(
            name="bonds",
            returns=[0.001, 0.002, -0.001, 0.001, 0.002, 0.001, -0.0005, 0.0015, 0.001, 0.0005],
            expected_return=0.001,
            volatility=0.002,
            sector="Fixed Income",
        ),
        "stocks": Asset(
            name="stocks",
            returns=[0.01, 0.02, -0.015, 0.008, -0.005, 0.012, -0.008, 0.015, 0.005, -0.003],
            expected_return=0.005,
            volatility=0.015,
            sector="Equity",
        ),
        "gold": Asset(
            name="gold",
            returns=[0.003, -0.002, 0.005, 0.001, -0.003, 0.004, 0.002, -0.001, 0.003, 0.001],
            expected_return=0.002,
            volatility=0.008,
            sector="Commodity",
        ),
    }


class TestHelpers:
    def test_mean(self):
        assert _mean([1, 2, 3, 4, 5]) == 3.0

    def test_std(self):
        assert _std([1, 1, 1, 1]) == 0.0
        assert _std([1, 2, 3, 4, 5]) > 0

    def test_correlation(self):
        a = [1, 2, 3, 4, 5]
        assert _correlation(a, a) == pytest.approx(1.0, abs=1e-6)
        assert _correlation(a, [5, 4, 3, 2, 1]) == pytest.approx(-1.0, abs=1e-6)


class TestRiskParity:
    def test_weights_sum_to_one(self):
        assets = _make_assets()
        result = risk_parity(assets)
        assert sum(result.weights.values()) == pytest.approx(1.0, abs=1e-4)

    def test_all_assets_have_weight(self):
        assets = _make_assets()
        result = risk_parity(assets)
        assert set(result.weights.keys()) == set(assets.keys())

    def test_bonds_get_higher_weight(self):
        assets = _make_assets()
        result = risk_parity(assets)
        # Lower vol asset should get higher weight
        assert result.weights["bonds"] > result.weights["stocks"]

    def test_method_name(self):
        result = risk_parity(_make_assets())
        assert result.method == "risk_parity"


class TestMeanVariance:
    def test_weights_sum_to_one(self):
        assets = _make_assets()
        result = mean_variance_optimize(assets)
        assert sum(result.weights.values()) == pytest.approx(1.0, abs=1e-4)

    def test_with_target_return(self):
        assets = _make_assets()
        result = mean_variance_optimize(assets, target_return=0.003)
        assert result.expected_return > 0


class TestMinimumVariance:
    def test_minimizes_volatility(self):
        assets = _make_assets()
        result = minimum_variance(assets)
        # Min variance should produce a valid portfolio with low volatility
        assert sum(result.weights.values()) == pytest.approx(1.0, abs=1e-4)
        assert result.expected_volatility >= 0
        assert result.expected_volatility <= 0.02  # Should be low for min-var


class TestMaximumSharpe:
    def test_maximizes_sharpe(self):
        assets = _make_assets()
        result = maximum_sharpe(assets)
        assert result.sharpe_ratio > 0


class TestEfficientFrontier:
    def test_frontier_points(self):
        assets = _make_assets()
        frontier = efficient_frontier(assets, num_points=5)
        assert len(frontier) == 5

    def test_increasing_returns(self):
        assets = _make_assets()
        frontier = efficient_frontier(assets, num_points=5)
        returns = [p.target_return for p in frontier]
        assert all(returns[i] <= returns[i + 1] for i in range(len(returns) - 1))


class TestDiversificationRatio:
    def test_single_asset(self):
        assets = _make_assets()
        weights = {"bonds": 1.0, "stocks": 0, "gold": 0}
        dr = diversification_ratio(weights, assets)
        assert dr == pytest.approx(1.0, abs=1e-6)

    def test_diversified_portfolio(self):
        assets = _make_assets()
        weights = {"bonds": 1/3, "stocks": 1/3, "gold": 1/3}
        dr = diversification_ratio(weights, assets)
        assert dr > 1.0  # Diversification benefit
