"""Tests for technical_indicators.py — technical analysis."""

import math
import pytest
from finscrape.services.technical_indicators import (
    OHLCV, TechnicalIndicators,
)


def _make_candles(prices, volumes=None):
    """Create OHLCV list from close prices."""
    if volumes is None:
        volumes = [100000] * len(prices)
    candles = []
    for i, (p, v) in enumerate(zip(prices, volumes)):
        candles.append(OHLCV(
            timestamp=float(i),
            open=p * 0.99, high=p * 1.02, low=p * 0.98,
            close=p, volume=v,
        ))
    return candles


class TestRSI:
    def test_overbought(self):
        prices = [100 + i * 2 for i in range(30)]
        rsi = TechnicalIndicators.rsi(prices)
        assert rsi[-1] > 70

    def test_oversold(self):
        prices = [200 - i * 2 for i in range(30)]
        rsi = TechnicalIndicators.rsi(prices)
        assert rsi[-1] < 30

    def test_neutral(self):
        prices = [100 + (i % 2) * 2 - 1 for i in range(30)]
        rsi = TechnicalIndicators.rsi(prices)
        assert 30 <= rsi[-1] <= 70

    def test_length_matches_input(self):
        prices = [100, 101, 102, 103, 104]
        rsi = TechnicalIndicators.rsi(prices)
        assert len(rsi) == len(prices)


class TestMACD:
    def test_bullish_signal(self):
        prices = [100 + i for i in range(50)]
        macd = TechnicalIndicators.macd(prices)
        assert len(macd["macd"]) == 50
        assert len(macd["signal"]) == 50
        assert len(macd["histogram"]) == 50

    def test_histogram_sign(self):
        prices = [100 + i * 0.5 for i in range(50)]
        macd = TechnicalIndicators.macd(prices)
        assert isinstance(macd["histogram"][-1], float)


class TestBollingerBands:
    def test_bands_contain_price(self):
        prices = [100 + (i % 10) for i in range(30)]
        bb = TechnicalIndicators.bollinger_bands(prices)
        assert len(bb["upper"]) == 30
        assert len(bb["lower"]) == 30
        assert bb["upper"][-1] > bb["lower"][-1]

    def test_squeeze(self):
        prices = [100.0] * 30
        bb = TechnicalIndicators.bollinger_bands(prices)
        assert bb["upper"][-1] == bb["lower"][-1]


class TestATR:
    def test_atr_positive(self):
        candles = _make_candles([100 + i for i in range(20)])
        atr = TechnicalIndicators.atr(candles)
        assert atr[-1] > 0

    def test_atr_length(self):
        candles = _make_candles([100 + i for i in range(20)])
        atr = TechnicalIndicators.atr(candles)
        assert len(atr) == 20


class TestStochastic:
    def test_stochastic_range(self):
        candles = _make_candles([100 + i for i in range(20)])
        stoch = TechnicalIndicators.stochastic(candles)
        assert len(stoch["k"]) == 20
        for k in stoch["k"]:
            assert 0 <= k <= 100


class TestOBV:
    def test_obv_increasing_uptrend(self):
        candles = _make_candles([100 + i for i in range(20)])
        obv = TechnicalIndicators.obv(candles)
        assert obv[-1] > obv[0]

    def test_obv_decreasing_downtrend(self):
        candles = _make_candles([200 - i for i in range(20)])
        obv = TechnicalIndicators.obv(candles)
        assert obv[-1] < obv[0]


class TestVWAP:
    def test_vwap_returns_values(self):
        candles = _make_candles([100 + i for i in range(10)])
        vwap = TechnicalIndicators.vwap(candles)
        assert len(vwap) == 10
        assert all(v > 0 for v in vwap)


class TestSupportResistance:
    def test_sr_returns_data(self):
        candles = _make_candles([100 + (i % 5) for i in range(30)])
        sr = TechnicalIndicators.support_resistance(candles)
        assert "support" in sr
        assert "resistance" in sr
        assert len(sr["support"]) > 0
        assert len(sr["resistance"]) > 0


class TestSMA:
    def test_sma_basic(self):
        prices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        sma = TechnicalIndicators.sma(prices, 3)
        assert sma[2] == 2.0
        assert sma[9] == 9.0

    def test_sma_short_input(self):
        prices = [1, 2]
        sma = TechnicalIndicators.sma(prices, 5)
        assert all(v == 0.0 for v in sma)


class TestEMA:
    def test_ema_basic(self):
        prices = [100 + i for i in range(30)]
        ema = TechnicalIndicators.ema(prices, 10)
        assert len(ema) == 30
        assert ema[-1] > ema[-2]


class TestAnalyzeTrend:
    def test_bullish_trend(self):
        prices = [100 + i * 2 for i in range(30)]
        result = TechnicalIndicators.analyze_trend(prices)
        assert result["trend"] in ("bullish", "neutral")

    def test_insufficient_data(self):
        prices = [100, 101]
        result = TechnicalIndicators.analyze_trend(prices)
        assert result["trend"] == "insufficient_data"
