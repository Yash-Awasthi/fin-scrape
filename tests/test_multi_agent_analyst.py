"""Tests for Multi-Agent Analyst Service."""
import pytest
from finscrape.services.multi_agent_analyst import (
    MarketData, AnalystRole, SignalStrength, Decision,
    analyze_market_technicals, analyze_sentiment, analyze_fundamentals,
    calculate_position_size, calculate_target_price, calculate_stop_loss,
    aggregate_signals, generate_trading_decision,
)


def make_data(price=100, pe=20, eps=2.0):
    return MarketData(ticker="TEST", price=price, volume=1000000,
                      market_cap=10e9, pe_ratio=pe, eps=eps,
                      fifty_two_week_high=120, fifty_two_week_low=80)


class TestMarketTechnicals:
    def test_uptrend(self):
        prices = [80 + i for i in range(30)]
        signal = analyze_market_technicals(make_data(price=110), prices)
        assert signal.signal in (SignalStrength.BUY, SignalStrength.STRONG_BUY, SignalStrength.NEUTRAL)

    def test_downtrend(self):
        prices = [120 - i for i in range(30)]
        signal = analyze_market_technicals(make_data(price=90), prices)
        assert signal.signal in (SignalStrength.SELL, SignalStrength.STRONG_SELL, SignalStrength.NEUTRAL)

    def test_insufficient_data(self):
        signal = analyze_market_technicals(make_data(), [])
        assert signal.confidence < 0.5


class TestSentiment:
    def test_positive(self):
        texts = ["This stock is bullish and growing fast", "Strong buy recommendation"]
        signal = analyze_sentiment(texts)
        assert signal.signal in (SignalStrength.BUY, SignalStrength.NEUTRAL)

    def test_negative(self):
        texts = ["Bearish decline, sell now", "Risk of crash and loss"]
        signal = analyze_sentiment(texts)
        assert signal.signal in (SignalStrength.SELL, SignalStrength.NEUTRAL)

    def test_empty(self):
        signal = analyze_sentiment([])
        assert signal.signal == SignalStrength.NEUTRAL


class TestFundamentals:
    def test_undervalued(self):
        data = make_data(price=50, pe=10, eps=5.0)
        signal = analyze_fundamentals(data)
        assert signal.signal in (SignalStrength.BUY, SignalStrength.STRONG_BUY)

    def test_overvalued(self):
        data = make_data(price=200, pe=50, eps=-2.0)
        signal = analyze_fundamentals(data)
        assert signal.signal in (SignalStrength.SELL, SignalStrength.STRONG_SELL)


class TestPositionSizing:
    def test_basic(self):
        size = calculate_position_size(10000, 0.02, 100, 95)
        assert size > 0

    def test_zero_risk(self):
        size = calculate_position_size(10000, 0.02, 100, 100)
        assert size == 0.0


class TestPriceCalc:
    def test_target(self):
        target = calculate_target_price(100, 2.0)
        assert target > 100

    def test_stop_loss(self):
        sl = calculate_stop_loss(100, percent=0.05)
        assert sl < 100

    def test_stop_loss_atr(self):
        sl = calculate_stop_loss(100, atr=5)
        assert sl == 90


class TestAggregate:
    def test_all_buy(self):
        signals = [
            None  # placeholder, will use actual signals below
        ]
        from finscrape.services.multi_agent_analyst import AnalystSignal
        actual_signals = [
            AnalystSignal(analyst=AnalystRole.MARKET, signal=SignalStrength.BUY, confidence=0.7, reasoning="test"),
            AnalystSignal(analyst=AnalystRole.FUNDAMENTALS, signal=SignalStrength.BUY, confidence=0.8, reasoning="test"),
        ]
        decision, conf = aggregate_signals(actual_signals)
        assert decision in (Decision.BUY, Decision.STRONG_BUY)

    def test_all_sell(self):
        from finscrape.services.multi_agent_analyst import AnalystSignal
        signals = [
            AnalystSignal(analyst=AnalystRole.MARKET, signal=SignalStrength.SELL, confidence=0.7, reasoning="test"),
            AnalystSignal(analyst=AnalystRole.FUNDAMENTALS, signal=SignalStrength.SELL, confidence=0.8, reasoning="test"),
        ]
        decision, conf = aggregate_signals(signals)
        assert decision in (Decision.SELL, Decision.STRONG_SELL)

    def test_neutral(self):
        from finscrape.services.multi_agent_analyst import AnalystSignal
        signals = [
            AnalystSignal(analyst=AnalystRole.MARKET, signal=SignalStrength.NEUTRAL, confidence=0.5, reasoning="test"),
        ]
        decision, conf = aggregate_signals(signals)
        assert decision == Decision.HOLD

    def test_empty(self):
        decision, conf = aggregate_signals([])
        assert decision == Decision.HOLD


class TestGenerateDecision:
    def test_basic(self):
        prices = [80 + i for i in range(30)]
        texts = ["bullish growth strong buy"]
        data = make_data(price=110)
        result = generate_trading_decision("TEST", data, prices, texts)
        assert result.ticker == "TEST"
        assert result.entry_price == 110
        assert result.target_price > 110
        assert result.stop_loss < 110
        assert len(result.signals) == 3
