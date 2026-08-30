"""Tests for market_data.py — market data normalization and quality."""

import pytest
from finscrape.services.market_data import (
    normalize_symbol, parse_historical_data, adjust_for_splits,
    calculate_returns, assess_data_quality, determine_market_status,
    calculate_portfolio_metrics, calculate_sector_performance,
    get_sector_for_symbol, HistoricalBar, MarketQuote,
)


class TestNormalizeSymbol:
    def test_lowercase(self):
        assert normalize_symbol("aapl") == "AAPL"

    def test_european_dot(self):
        assert normalize_symbol("SIE.DE") == "SIE-DE"

    def test_crypto(self):
        assert normalize_symbol("BTC-USD") == "BTC-USD"

    def test_already_upper(self):
        assert normalize_symbol("MSFT") == "MSFT"

    def test_spaces(self):
        assert normalize_symbol("  TSLA  ") == "TSLA"


class TestParseHistoricalData:
    def test_yahoo_format(self):
        data = [{"Date": "2024-01-01", "Open": 100, "High": 105, "Low": 95, "Close": 102, "Volume": 1000000, "Adj Close": 102}]
        bars = parse_historical_data(data, "AAPL")
        assert len(bars) == 1
        assert bars[0].close == 102

    def test_lowercase_keys(self):
        data = [{"date": "2024-01-01", "open": 50, "high": 55, "low": 48, "close": 52, "volume": 500000}]
        bars = parse_historical_data(data, "TEST")
        assert len(bars) == 1

    def test_empty_data(self):
        assert parse_historical_data([], "TEST") == []


class TestAdjustForSplits:
    def test_no_splits(self):
        bars = [HistoricalBar(date="2024-01-01", open=100, high=105, low=95, close=102, volume=1000, adjusted_close=102)]
        adjusted = adjust_for_splits(bars)
        assert adjusted[0].close == 102

    def test_split_adjustment(self):
        bars = [
            HistoricalBar(date="2024-01-01", open=200, high=210, low=190, close=204, volume=1000, adjusted_close=204, stock_split=2.0),
            HistoricalBar(date="2024-01-02", open=100, high=105, low=95, close=102, volume=2000, adjusted_close=102, stock_split=1.0),
        ]
        adjusted = adjust_for_splits(bars)
        # Pre-split price should be halved
        assert adjusted[0].close == pytest.approx(102, abs=1)


class TestCalculateReturns:
    def test_simple_returns(self):
        bars = [
            HistoricalBar(date="2024-01-01", open=0, high=0, low=0, close=100, volume=0, adjusted_close=100),
            HistoricalBar(date="2024-01-02", open=0, high=0, low=0, close=110, volume=0, adjusted_close=110),
            HistoricalBar(date="2024-01-03", open=0, high=0, low=0, close=105, volume=0, adjusted_close=105),
        ]
        returns = calculate_returns(bars)
        assert len(returns) == 2
        assert returns[0] == pytest.approx(0.1, abs=1e-6)
        assert returns[1] == pytest.approx(-0.0476, abs=0.01)

    def test_empty(self):
        assert calculate_returns([]) == []


class TestDataQuality:
    def test_good_data(self):
        bars = [
            HistoricalBar(date=f"2024-01-{i:02d}", open=100, high=100, low=100, close=100, volume=1000, adjusted_close=100)
            for i in range(1, 11)
        ]
        quality = assess_data_quality(bars, "TEST")
        assert quality.total_bars == 10
        assert quality.completeness > 0.9

    def test_empty_data(self):
        quality = assess_data_quality([], "TEST")
        assert quality.total_bars == 0


class TestMarketStatus:
    def test_returns_valid(self):
        status = determine_market_status()
        assert status in ("open", "closed", "pre-market", "after-hours")


class TestSectorMapping:
    def test_known_symbol(self):
        assert get_sector_for_symbol("AAPL") == "Technology"
        assert get_sector_for_symbol("JPM") == "Financial"

    def test_unknown_symbol(self):
        assert get_sector_for_symbol("XYZ") == "Unknown"


class TestPortfolioMetrics:
    def test_basic_portfolio(self):
        holdings = {"AAPL": 10, "MSFT": 5}
        quotes = {
            "AAPL": MarketQuote(symbol="AAPL", name="Apple", price=150, change=5, change_pct=3.45, volume=1000000, market_cap=3e12),
            "MSFT": MarketQuote(symbol="MSFT", name="Microsoft", price=300, change=-3, change_pct=-1, volume=500000, market_cap=2.5e12),
        }
        metrics = calculate_portfolio_metrics(holdings, quotes)
        assert metrics["total_value"] == 3000  # 10*150 + 5*300
        assert metrics["holding_count"] == 2
        assert "allocation" in metrics


class TestSectorPerformance:
    def test_calculation(self):
        quotes = {
            "AAPL": MarketQuote(symbol="AAPL", name="Apple", price=150, change=5, change_pct=3.0, volume=0, market_cap=0),
            "MSFT": MarketQuote(symbol="MSFT", name="Microsoft", price=300, change=6, change_pct=2.0, volume=0, market_cap=0),
            "JPM": MarketQuote(symbol="JPM", name="JPMorgan", price=150, change=-3, change_pct=-2.0, volume=0, market_cap=0),
        }
        perf = calculate_sector_performance(quotes)
        assert "Technology" in perf
        assert "Financial" in perf
        assert perf["Technology"] > 0
        assert perf["Financial"] < 0
