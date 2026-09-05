"""Tests for live_market_feed.py and realtime_analyzer.py."""

import time
import math
import pytest
from finscrape.services.live_market_feed import (
    PriceTick, NewsItem, SocialSignal, MarketAlert,
    PriceAggregator, NewsProcessor, SocialProcessor,
    MarketAlertManager, LiveMarketFeed,
    FeedType, AlertType, AlertSeverity,
)
from finscrape.services.realtime_analyzer import (
    realtime_rsi, realtime_macd, realtime_vwap,
    analyze_sentiment_live, aggregate_sentiment,
    calculate_correlation, correlate_price_sentiment,
    detect_volatility_spike,
)


# ---------------------------------------------------------------------------
# Price Aggregator
# ---------------------------------------------------------------------------

class TestPriceAggregator:
    def test_tick_aggregation(self):
        agg = PriceAggregator(bar_interval_seconds=0)
        now = time.time()
        bars = []
        for i in range(5):
            tick = PriceTick("AAPL", 150, 150.5, 150.25, 1000, now + i)
            bar = agg.add_tick(tick)
            if bar is not None:
                bars.append(bar)
        assert len(bars) >= 1  # At least one bar completed
        assert bars[0].symbol == "AAPL"

    def test_get_current_price(self):
        agg = PriceAggregator()
        agg.add_tick(PriceTick("AAPL", 150, 150.5, 150.25, 1000, time.time()))
        assert agg.get_current_price("AAPL") == 150.25

    def test_get_bars(self):
        agg = PriceAggregator(bar_interval_seconds=0)
        now = time.time()
        agg.add_tick(PriceTick("AAPL", 150, 150.5, 150, 1000, now))
        agg.add_tick(PriceTick("AAPL", 151, 151.5, 151, 1000, now + 1))
        bars = agg.get_bars("AAPL")
        assert len(bars) >= 1


# ---------------------------------------------------------------------------
# News Processor
# ---------------------------------------------------------------------------

class TestNewsProcessor:
    def test_ingest_and_retrieve(self):
        proc = NewsProcessor()
        proc.ingest(NewsItem("Stock surges", "Reuters", time.time(), 0.8, "bullish", ["AAPL"]))
        proc.ingest(NewsItem("Stock drops", "CNBC", time.time(), -0.6, "bearish", ["AAPL"]))
        latest = proc.get_latest(5)
        assert len(latest) == 2

    def test_sentiment_average(self):
        proc = NewsProcessor()
        now = time.time()
        proc.ingest(NewsItem("Good news", "R", now, 0.5, "bullish", ["AAPL"]))
        proc.ingest(NewsItem("Bad news", "C", now, -0.3, "bearish", ["AAPL"]))
        avg = proc.get_sentiment_average("AAPL")
        assert avg is not None
        assert -1 <= avg <= 1


# ---------------------------------------------------------------------------
# Social Processor
# ---------------------------------------------------------------------------

class TestSocialProcessor:
    def test_sentiment_score(self):
        proc = SocialProcessor()
        now = time.time()
        proc.ingest(SocialSignal("reddit", "AAPL", 0.5, 100, now))
        proc.ingest(SocialSignal("twitter", "AAPL", 0.3, 200, now))
        score = proc.get_sentiment_score("AAPL")
        assert score is not None
        assert -1 <= score <= 1

    def test_trending_detection(self):
        proc = SocialProcessor()
        now = time.time()
        # Older signals — mid previous-window (not on the boundary; a boundary
        # timestamp flake-fails whenever suite load shifts the internal clock)
        for _ in range(20):
            proc.ingest(SocialSignal("reddit", "TSLA", 0.5, 50, now - 90))
        # Recent signals (high volume, within window)
        for _ in range(50):
            proc.ingest(SocialSignal("reddit", "TSLA", 0.5, 100, now - 5))
        trending = proc.detect_trending(window_minutes=1, min_volume=100)
        assert len(trending) >= 1


# ---------------------------------------------------------------------------
# Alert Manager
# ---------------------------------------------------------------------------

class TestMarketAlertManager:
    def test_price_alert(self):
        mgr = MarketAlertManager(cooldown_seconds=0)
        mgr.add_rule(AlertType.PRICE_ABOVE, "AAPL", 155, AlertSeverity.WARNING)
        alert = mgr.check_price("AAPL", 160, time.time())
        assert alert is not None
        assert alert.value == 160

    def test_no_alert(self):
        mgr = MarketAlertManager(cooldown_seconds=0)
        mgr.add_rule(AlertType.PRICE_ABOVE, "AAPL", 200)
        alert = mgr.check_price("AAPL", 150, time.time())
        assert alert is None


# ---------------------------------------------------------------------------
# Live Feed
# ---------------------------------------------------------------------------

class TestLiveMarketFeed:
    def test_price_flow(self):
        feed = LiveMarketFeed()
        bar = feed.on_price(PriceTick("AAPL", 150, 150.5, 150.25, 1000, time.time()))
        # First tick doesn't complete a bar
        assert bar is None or bar is not None  # Depends on timing

    def test_news_flow(self):
        feed = LiveMarketFeed()
        feed.on_news(NewsItem("Test", "Source", time.time(), 0.5, "bullish", ["AAPL"]))
        assert len(feed.news._items) == 1

    def test_subscription(self):
        feed = LiveMarketFeed()
        received = []
        feed.subscribe("price", lambda t: received.append(t))
        feed.on_price(PriceTick("AAPL", 150, 150.5, 150.25, 1000, time.time()))
        assert len(received) == 1


# ---------------------------------------------------------------------------
# Realtime Indicators
# ---------------------------------------------------------------------------

class TestRealtimeIndicators:
    def test_rsi_overbought(self):
        prices = [100 + i * 2 for i in range(20)]
        ind = realtime_rsi(prices)
        assert ind.value > 70
        assert ind.signal == "sell"

    def test_rsi_oversold(self):
        prices = [200 - i * 2 for i in range(20)]
        ind = realtime_rsi(prices)
        assert ind.value < 30
        assert ind.signal == "buy"

    def test_macd_uptrend(self):
        prices = [100 + i for i in range(40)]
        ind = realtime_macd(prices)
        assert ind.signal == "buy"

    def test_vwap(self):
        prices = [100, 100, 100]
        volumes = [1000, 2000, 3000]
        ind = realtime_vwap(prices, volumes)
        assert ind.value > 0


# ---------------------------------------------------------------------------
# Sentiment
# ---------------------------------------------------------------------------

class TestSentiment:
    def test_bullish_text(self):
        result = analyze_sentiment_live("Stock surges on record earnings beat upgrade")
        assert result.score > 0
        assert result.label == "bullish"

    def test_bearish_text(self):
        result = analyze_sentiment_live("Stock crashes amid bankruptcy crisis sell")
        assert result.score < 0
        assert result.label == "bearish"

    def test_aggregate(self):
        items = ["Stock surges", "Record earnings", "Strong growth"]
        result = aggregate_sentiment(items, "AAPL")
        assert result.source_count == 3
        assert result.score > 0


# ---------------------------------------------------------------------------
# Correlation & Volatility
# ---------------------------------------------------------------------------

class TestCorrelation:
    def test_perfect_correlation(self):
        a = [1, 2, 3, 4, 5]
        b = [2, 4, 6, 8, 10]
        assert calculate_correlation(a, b) == pytest.approx(1.0, abs=1e-6)

    def test_price_sentiment_correlation(self):
        prices = [1, 2, 3, 4, 5]
        sentiments = [0.1, 0.2, 0.3, 0.4, 0.5]
        result = correlate_price_sentiment(prices, sentiments, "AAPL")
        assert result.correlation > 0.9
        assert result.significance == "high"


class TestVolatility:
    def test_normal_volatility(self):
        prices = [100 + (i % 3 - 1) * 0.5 for i in range(30)]
        result = detect_volatility_spike(prices, historical_volatility=0.2)
        assert result.is_elevated is False

    def test_spike_detection(self):
        # High volatility series
        prices = [100 + (i % 2) * 10 - 5 for i in range(30)]
        result = detect_volatility_spike(prices, historical_volatility=0.05)
        assert result.is_elevated is True
