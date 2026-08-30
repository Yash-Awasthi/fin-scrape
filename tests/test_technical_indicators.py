"""Tests for technical_indicators.py — technical analysis."""

import math
import pytest
from finscrape.services.technical_indicators import (
    PriceBar, TechnicalAnalysis,
    relative_strength_index, bollinger_bands, average_true_range,
    moving_average_convergence, stochastic_oscillator,
    on_balance_volume, volume_weighted_average_price,
    find_support_resistance, analyze,
)


def _make_bars(prices, volumes=None):
    """Create PriceBar list from close prices."""
    if volumes is None:
        volumes = [100000] * len(prices)
    bars = []
    for i, (p, v) in enumerate(zip(prices, volumes)):
        bars.append(PriceBar(
            timestamp=f"2024-01-{i+1:02d}",
            open=p * 0.99, high=p * 1.02, low=p * 0.98,
            close=p, volume=v,
        ))
    return bars


class TestRSI:
    def test_overbought(self):
        # Strong uptrend → high RSI
        prices = [100 + i * 2 for i in range(20)]
        bars = _make_bars(prices)
        result = relative_strength_index(bars)
        assert result[0].value > 70
        assert result[0].signal == "sell"

    def test_oversold(self):
        # Strong downtrend → low RSI
        prices = [200 - i * 2 for i in range(20)]
        bars = _make_bars(prices)
        result = relative_strength_index(bars)
        assert result[0].value < 30
        assert result[0].signal == "buy"

    def test_neutral(self):
        # Sideways → RSI around 50
        prices = [100 + (i % 2) for i in range(20)]
        bars = _make_bars(prices)
        result = relative_strength_index(bars)
        assert 30 <= result[0].value <= 70


class TestBollingerBands:
    def test_bands_exist(self):
        prices = [100 + i * 0.5 for i in range(30)]
        bars = _make_bars(prices)
        result = bollinger_bands(bars)
        assert len(result) == 4
        upper = next(r for r in result if r.name == "BB_Upper")
        lower = next(r for r in result if r.name == "BB_Lower")
        assert upper.value > lower.value


class TestATR:
    def test_volatility(self):
        # High volatility — need at least 14 bars for default ATR period
        prices = [100, 110, 95, 115, 90, 120, 85, 125, 80, 130, 75, 135, 70, 140, 65]
        bars = _make_bars(prices)
        result = average_true_range(bars)
        assert result[0].value > 0

    def test_low_volatility(self):
        prices = [100.0 + i * 0.01 for i in range(20)]
        bars = _make_bars(prices)
        result = average_true_range(bars)
        assert result[0].value > 0


class TestMACD:
    def test_bullish_crossover(self):
        prices = [100 + i for i in range(40)]
        bars = _make_bars(prices)
        result = moving_average_convergence(bars)
        assert len(result) == 1
        assert result[0].value > 0  # Fast > Slow in uptrend


class TestStochastic:
    def test_overbought(self):
        prices = [100 + i for i in range(20)]
        bars = _make_bars(prices)
        result = stochastic_oscillator(bars)
        assert len(result) == 2  # %K and %D


class TestOBV:
    def test_volume_trend(self):
        prices = [100, 101, 102, 103, 104]
        volumes = [1000, 1200, 1100, 1300, 1400]
        bars = _make_bars(prices, volumes)
        result = on_balance_volume(bars)
        assert result[0].value > 0  # Uptrend = positive OBV


class TestVWAP:
    def test_vwap(self):
        bars = _make_bars([100, 100, 100], [1000, 2000, 3000])
        result = volume_weighted_average_price(bars)
        assert result[0].value > 0


class TestSupportResistance:
    def test_levels(self):
        prices = [100, 105, 95, 110, 90, 108, 92]
        bars = _make_bars(prices)
        support, resistance = find_support_resistance(bars)
        assert support < resistance
        assert support > 0
        assert resistance > 0


class TestFullAnalysis:
    def test_complete(self):
        prices = [100 + i * 0.5 + (i % 3 - 1) for i in range(50)]
        bars = _make_bars(prices)
        result = analyze(bars)
        assert isinstance(result, TechnicalAnalysis)
        assert result.trend in ("uptrend", "downtrend", "sideways")
        assert result.momentum in ("overbought", "oversold", "neutral")
        assert result.volatility in ("high", "medium", "low")
        assert result.overall_signal in ("buy", "sell", "hold")
        assert len(result.indicators) > 0

    def test_insufficient_data(self):
        bars = _make_bars([100, 101])
        result = analyze(bars)
        assert result.overall_signal == "hold"
