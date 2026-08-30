"""Tests for quant_factor_engine.py — qlib-inspired factor analysis."""

import math
import pytest
from finscrape.services.quant_factor_engine import (
    OHLCVBar, FactorSet, RiskModel, PortfolioWeight,
    calculate_price_factors, calculate_moving_average_factors,
    calculate_momentum_factors, calculate_volatility_factors,
    calculate_volume_factors, calculate_vwap, calculate_rsi,
    compute_all_factors, calculate_risk_metrics,
    equal_weight_portfolio, min_variance_portfolio,
    risk_parity_portfolio, calculate_factor_correlation,
    rank_factors_by_ic,
)


def _make_bars(prices, volumes=None):
    """Helper to create OHLCV bars from close prices."""
    if volumes is None:
        volumes = [1000000] * len(prices)
    bars = []
    for i, (p, v) in enumerate(zip(prices, volumes)):
        bars.append(OHLCVBar(
            timestamp=f"2024-01-{i+1:02d}",
            open=p * 0.99,
            high=p * 1.02,
            low=p * 0.98,
            close=p,
            volume=v,
        ))
    return bars


class TestPriceFactors:
    def test_single_day_return(self):
        bars = _make_bars([100, 105])
        factors = calculate_price_factors(bars)
        assert abs(factors["returns_1d"] - 0.05) < 1e-6

    def test_5day_return(self):
        bars = _make_bars([100, 101, 102, 103, 104, 110])
        factors = calculate_price_factors(bars)
        assert abs(factors["returns_5d"] - 0.10) < 1e-6

    def test_log_volume(self):
        bars = _make_bars([100, 105], [1000, 1200])
        factors = calculate_price_factors(bars)
        assert factors["log_volume"] == pytest.approx(math.log(1201), abs=1e-6)

    def test_empty_bars(self):
        assert calculate_price_factors([]) == {}


class TestMovingAverageFactors:
    def test_above_ma(self):
        bars = _make_bars([100, 100, 100, 100, 100, 110])
        factors = calculate_moving_average_factors(bars)
        assert factors["ma5_ratio"] > 0  # Price above MA

    def test_below_ma(self):
        bars = _make_bars([100, 100, 100, 100, 100, 90])
        factors = calculate_moving_average_factors(bars)
        assert factors["ma5_ratio"] < 0


class TestVolatilityFactors:
    def test_high_volatility(self):
        # Alternating prices = high volatility
        bars = _make_bars([100, 110, 100, 110, 100, 110])
        factors = calculate_volatility_factors(bars)
        assert factors["volatility_5d"] > 0

    def test_low_volatility(self):
        # Constant prices = zero volatility
        bars = _make_bars([100, 100, 100, 100, 100, 100])
        factors = calculate_volatility_factors(bars)
        assert factors["volatility_5d"] == pytest.approx(0.0, abs=1e-10)


class TestRSI:
    def test_all_gains(self):
        bars = _make_bars([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115])
        rsi = calculate_rsi(bars)
        assert rsi == 100.0

    def test_all_losses(self):
        bars = _make_bars([115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100])
        rsi = calculate_rsi(bars)
        assert rsi == 0.0

    def test_neutral(self):
        bars = _make_bars([100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101, 100, 101])
        rsi = calculate_rsi(bars)
        assert 40 <= rsi <= 60


class TestVWAP:
    def test_vwap_calculation(self):
        bars = _make_bars([100, 100, 100], [1000, 2000, 3000])
        vwap = calculate_vwap(bars)
        assert vwap > 0


class TestRiskMetrics:
    def test_positive_returns(self):
        returns = [0.01, 0.02, 0.015, -0.005, 0.01, 0.008, -0.002, 0.012]
        risk = calculate_risk_metrics(returns)
        assert risk.sharpe_ratio > 0
        assert risk.volatility > 0
        assert risk.max_drawdown <= 0

    def test_negative_returns(self):
        returns = [-0.01, -0.02, -0.015, -0.005, -0.01]
        risk = calculate_risk_metrics(returns)
        assert risk.sharpe_ratio < 0
        assert risk.max_drawdown < 0

    def test_with_benchmark(self):
        returns = [0.01, 0.02, 0.015, -0.005, 0.01]
        benchmark = [0.005, 0.01, 0.008, -0.002, 0.005]
        risk = calculate_risk_metrics(returns, benchmark_returns=benchmark)
        assert risk.beta != 1.0  # Should differ from benchmark

    def test_empty_returns(self):
        risk = calculate_risk_metrics([])
        assert risk.variance == 0


class TestPortfolioOptimization:
    def test_equal_weight(self):
        instruments = ["A", "B", "C"]
        weights = equal_weight_portfolio(instruments)
        assert len(weights) == 3
        assert all(w.weight == pytest.approx(1/3) for w in weights)

    def test_min_variance_2_assets(self):
        returns = {
            "A": [0.02, 0.03, -0.02, 0.025, -0.01],
            "B": [0.005, 0.008, -0.003, 0.006, -0.002],
        }
        weights = min_variance_portfolio(returns)
        assert len(weights) == 2
        assert sum(w.weight for w in weights) == pytest.approx(1.0, abs=1e-6)
        # Low-vol asset should get higher weight
        b_weight = next(w for w in weights if w.instrument == "B")
        a_weight = next(w for w in weights if w.instrument == "A")
        assert b_weight.weight > a_weight.weight

    def test_risk_parity(self):
        returns = {
            "A": [0.02, 0.03, -0.02, 0.025, -0.01],
            "B": [0.005, 0.008, -0.003, 0.006, -0.002],
        }
        weights = risk_parity_portfolio(returns)
        assert len(weights) == 2
        assert sum(w.weight for w in weights) == pytest.approx(1.0, abs=1e-6)


class TestFactorCorrelation:
    def test_perfect_correlation(self):
        a = [1, 2, 3, 4, 5]
        b = [2, 4, 6, 8, 10]
        corr = calculate_factor_correlation(a, b)
        assert corr == pytest.approx(1.0, abs=1e-6)

    def test_inverse_correlation(self):
        a = [1, 2, 3, 4, 5]
        b = [5, 4, 3, 2, 1]
        corr = calculate_factor_correlation(a, b)
        assert corr == pytest.approx(-1.0, abs=1e-6)


class TestRankFactorsByIC:
    def test_ranking(self):
        forward = [0.01, 0.02, 0.03, 0.04, 0.05]
        factors = {
            "strong": [1, 2, 3, 4, 5],  # Perfect positive correlation
            "weak": [5, 3, 1, 4, 2],    # Weak correlation
            "inverse": [5, 4, 3, 2, 1],  # Perfect negative
        }
        ranked = rank_factors_by_ic(factors, forward)
        assert ranked[0][0] in ("strong", "inverse")  # Both have |IC| ≈ 1


class TestComputeAllFactors:
    def test_full_pipeline(self):
        bars = _make_bars([100, 101, 102, 103, 104, 105, 106, 107, 108, 109,
                          110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120])
        factors = compute_all_factors(bars)
        assert isinstance(factors, FactorSet)
        assert factors.rsi_14 >= 0
        assert factors.volatility_20d >= 0
