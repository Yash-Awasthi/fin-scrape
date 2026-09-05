"""Unit tests for fin-scrape geopolitical dashboard and market sentiment modules."""

import pytest


class TestGeopoliticalDashboard:
    """Tests for geopolitical_dashboard.py"""

    def test_import(self):
        from finscrape.analysis.geopolitical_dashboard import GeopoliticalDashboard
        assert GeopoliticalDashboard is not None

    def test_calculate_global_risk(self):
        from finscrape.analysis.geopolitical_dashboard import GeopoliticalDashboard
        dash = GeopoliticalDashboard()
        risk = dash.calculate_global_risk()
        assert isinstance(risk, (int, float))
        assert 0 <= risk <= 100

    def test_region_risks(self):
        from finscrape.analysis.geopolitical_dashboard import GeopoliticalDashboard
        dash = GeopoliticalDashboard()
        risks = dash.get_region_risks()
        assert isinstance(risks, dict)
        assert len(risks) > 0
        for region, score in risks.items():
            assert isinstance(score, (int, float))
            assert 0 <= score <= 100

    def test_alerts_generation(self):
        from finscrape.analysis.geopolitical_dashboard import GeopoliticalDashboard
        dash = GeopoliticalDashboard()
        alerts = dash.get_alerts()
        assert isinstance(alerts, list)
        for alert in alerts:
            assert "severity" in alert
            assert alert["severity"] in ["critical", "high", "medium", "low"]

    def test_top_risks_sorted(self):
        from finscrape.analysis.geopolitical_dashboard import GeopoliticalDashboard
        dash = GeopoliticalDashboard()
        top = dash.get_top_risks(n=5)
        assert isinstance(top, list)
        assert len(top) <= 5
        if len(top) > 1:
            # Should be sorted descending by risk score
            scores = [r["risk_score"] for r in top]
            assert scores == sorted(scores, reverse=True)


class TestMarketSentiment:
    """Tests for market_sentiment.py"""

    def test_import(self):
        from finscrape.analysis.market_sentiment import MarketSentimentAnalyzer
        assert MarketSentimentAnalyzer is not None

    def test_analyze_asset(self):
        from finscrape.analysis.market_sentiment import MarketSentimentAnalyzer
        analyzer = MarketSentimentAnalyzer()
        result = analyzer.analyze("BTC")
        assert isinstance(result, dict)
        assert "composite_score" in result or "score" in result

    def test_market_overview(self):
        from finscrape.analysis.market_sentiment import MarketSentimentAnalyzer
        analyzer = MarketSentimentAnalyzer()
        overview = analyzer.get_market_overview()
        assert isinstance(overview, (dict, list))

    def test_extremes_detection(self):
        from finscrape.analysis.market_sentiment import MarketSentimentAnalyzer
        analyzer = MarketSentimentAnalyzer()
        extremes = analyzer.get_extremes()
        assert isinstance(extremes, list)
