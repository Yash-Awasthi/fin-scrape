"""Tests for market simulator service."""

import pytest
from finscrape.services.market_simulator import (
    MarketDataConfig,
    OHLCV,
    OrderBook,
    OrderBookLevel,
    NewsSentiment,
    calculate_market_stats,
    calculate_order_book_metrics,
    calculate_returns,
    calculate_volatility,
    aggregate_sentiment,
    generate_ohlcv,
    generate_news_sentiment,
    generate_order_book,
    generate_price_series,
)


class TestOHLCV:
    def test_generate_bar(self):
        bar = generate_ohlcv("AAPL", 100.0)
        assert bar.open > 0
        assert bar.high >= bar.open
        assert bar.high >= bar.close
        assert bar.low <= bar.open
        assert bar.low <= bar.close
        assert bar.volume >= 0

    def test_generate_bar_with_config(self):
        config = MarketDataConfig(initial_price=50.0, volatility=0.02)
        bar = generate_ohlcv("GOOGL", 50.0, config)
        assert bar.open > 0

    def test_price_series(self):
        bars = generate_price_series("AAPL", 10)
        assert len(bars) == 10
        # Each bar's open should be close to previous bar's close
        for i in range(1, len(bars)):
            assert abs(bars[i].open - bars[i-1].close) < bars[i-1].close * 0.1


class TestReturns:
    def test_calculate_returns(self):
        returns = calculate_returns([100, 110, 105])
        assert len(returns) == 2
        assert returns[0] == pytest.approx(0.1, abs=0.01)
        assert returns[1] == pytest.approx(-0.045, abs=0.01)

    def test_empty_returns(self):
        assert calculate_returns([]) == []
        assert calculate_returns([100]) == []

    def test_volatility(self):
        returns = [0.01, -0.01, 0.02, -0.02, 0.015]
        vol = calculate_volatility(returns)
        assert vol > 0


class TestOrderBook:
    def test_generate_order_book(self):
        book = generate_order_book("AAPL", 150.0)
        assert book.symbol == "AAPL"
        assert len(book.bids) == 5
        assert len(book.asks) == 5
        # Best bid < best ask
        assert book.bids[0].price < book.asks[0].price

    def test_order_book_metrics(self):
        book = generate_order_book("AAPL", 150.0)
        metrics = calculate_order_book_metrics(book)
        assert metrics["spread"] > 0
        assert metrics["mid_price"] > 0
        assert metrics["bid_depth"] > 0
        assert metrics["ask_depth"] > 0
        assert -1 <= metrics["imbalance"] <= 1


class TestNewsSentiment:
    def test_generate_sentiment(self):
        sentiment = generate_news_sentiment("AAPL")
        assert sentiment.symbol == "AAPL"
        assert -1 <= sentiment.sentiment_score <= 1
        assert 0 <= sentiment.magnitude <= 1

    def test_aggregate_sentiment(self):
        sentiments = [
            NewsSentiment(0, "AAPL", "Good", 0.5, 0.5),
            NewsSentiment(0, "AAPL", "Bad", -0.3, 0.3),
        ]
        result = aggregate_sentiment(sentiments)
        assert result["count"] == 2
        assert result["positive_count"] == 1
        assert result["negative_count"] == 1

    def test_empty_aggregate(self):
        result = aggregate_sentiment([])
        assert result["count"] == 0


class TestMarketStats:
    def test_calculate_stats(self):
        bars = generate_price_series("AAPL", 20)
        stats = calculate_market_stats(bars)
        assert stats["period_bars"] == 20
        assert "total_return_pct" in stats
        assert "volatility" in stats

    def test_empty_stats(self):
        assert calculate_market_stats([]) == {}
