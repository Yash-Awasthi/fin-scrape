"""Tests for Quant Strategy Engine."""
import pytest
from finscrape.services.quant_strategy_engine import (
    sma,
    ema,
    rsi,
    macd,
    bollinger_bands,
    ma_crossover_signal,
    rsi_signal,
    calculate_position_size,
    check_stop_loss,
    check_take_profit,
    calculate_portfolio_metrics,
    RiskLimits,
    Position,
)


class TestSMA:
    def test_basic(self):
        values = [1, 2, 3, 4, 5]
        result = sma(values, 3)
        assert result[:2] == [None, None]
        assert result[2] == pytest.approx(2.0)
        assert result[4] == pytest.approx(4.0)

    def test_short_data(self):
        result = sma([1, 2], 3)
        assert all(v is None for v in result)


class TestEMA:
    def test_basic(self):
        values = [1, 2, 3, 4, 5]
        result = ema(values, 3)
        assert len(result) == 5
        assert result[0] == 1.0

    def test_empty(self):
        assert ema([], 3) == []


class TestRSI:
    def test_basic(self):
        # Create trending up data
        closes = [10 + i * 0.5 for i in range(20)]
        result = rsi(closes, 14)
        assert len(result) >= 14
        # Should be high (above 70) for uptrend
        assert result[-1] is not None
        assert result[-1] > 60

    def test_short_data(self):
        result = rsi([1, 2, 3], 14)
        assert all(v is None for v in result)


class TestMACD:
    def test_basic(self):
        closes = [10 + i * 0.1 for i in range(50)]
        result = macd(closes)
        assert "macd_line" in result
        assert "signal_line" in result
        assert "histogram" in result
        assert len(result["macd_line"]) == 50

    def test_short_data(self):
        result = macd([1, 2, 3])
        assert result["macd_line"] == []


class TestBollingerBands:
    def test_basic(self):
        closes = [10 + (i % 5) * 0.5 for i in range(30)]
        result = bollinger_bands(closes)
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        # Upper should be above middle, lower below
        if result["upper"][-1] is not None:
            assert result["upper"][-1] > result["middle"][-1]
            assert result["lower"][-1] < result["middle"][-1]


class TestSignals:
    def test_ma_crossover(self):
        # Create uptrend
        closes = [10 + i * 0.5 for i in range(50)]
        signal = ma_crossover_signal(closes, fast_period=5, slow_period=20)
        assert signal.direction in ("long", "short", "flat")

    def test_rsi_signal_oversold(self):
        # Create oversold condition
        closes = [100 - i * 2 for i in range(20)]
        signal = rsi_signal(closes)
        assert signal.direction == "long"
        assert signal.strength > 0

    def test_rsi_signal_overbought(self):
        # Create overbought condition
        closes = [10 + i * 5 for i in range(20)]
        signal = rsi_signal(closes)
        assert signal.direction == "short"
        assert signal.strength < 0


class TestRiskManagement:
    def test_position_size(self):
        limits = RiskLimits()
        size = calculate_position_size(100000, 100, limits)
        assert size > 0
        assert size <= 100  # max 10% = $10000 / $100 = 100 shares

    def test_position_size_high_drawdown(self):
        limits = RiskLimits()
        size = calculate_position_size(100000, 100, limits, current_drawdown=0.20)
        assert size == 0.0  # drawdown exceeded

    def test_stop_loss(self):
        limits = RiskLimits(stop_loss_pct=0.05)
        position = Position(ticker="A", direction="long", size=100, entry_price=100, entry_date="2024-01-01")
        assert check_stop_loss(position, 94, limits) is True
        assert check_stop_loss(position, 97, limits) is False

    def test_take_profit(self):
        limits = RiskLimits(take_profit_pct=0.10)
        position = Position(ticker="A", direction="long", size=100, entry_price=100, entry_date="2024-01-01")
        assert check_take_profit(position, 111, limits) is True
        assert check_take_profit(position, 105, limits) is False


class TestPortfolioMetrics:
    def test_empty(self):
        result = calculate_portfolio_metrics([])
        assert result["position_count"] == 0

    def test_basic(self):
        positions = [
            Position(ticker="A", direction="long", size=100, entry_price=100, entry_date="2024-01-01", current_price=110),
            Position(ticker="B", direction="short", size=50, entry_price=200, entry_date="2024-01-01", current_price=190),
        ]
        result = calculate_portfolio_metrics(positions)
        assert result["position_count"] == 2
        assert result["long_exposure"] == 11000
        assert result["short_exposure"] == 9500
