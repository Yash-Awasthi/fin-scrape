"""Tests for sentiment_analyzer.py — financial sentiment analysis."""

import pytest
from finscrape.services.sentiment_analyzer import (
    Sentiment, SentimentResult, NewsSentiment,
    score_text, analyze_news, analyze_earnings_call, analyze_trend,
)


class TestScoreText:
    def test_bullish_text(self):
        result = score_text("Revenue surged 50% beating all estimates with exceptional growth")
        assert result.score > 0
        assert result.sentiment in (Sentiment.BULLISH, Sentiment.VERY_BULLISH)

    def test_bearish_text(self):
        result = score_text("Company crashes after bankruptcy filing and massive losses")
        assert result.score < 0
        assert result.sentiment in (Sentiment.BEARISH, Sentiment.VERY_BEARISH)

    def test_neutral_text(self):
        result = score_text("The market opened today")
        assert abs(result.score) < 0.5

    def test_negation(self):
        result = score_text("The company is not strong and will not rise")
        assert result.score < 0

    def test_intensifier(self):
        result = score_text("extremely strong earnings beat")
        assert result.score > 0

    def test_empty_text(self):
        result = score_text("")
        assert result.sentiment == Sentiment.NEUTRAL

    def test_financial_context_boost(self):
        result = score_text("revenue earnings profit growth surge")
        assert result.score > 0.3


class TestAnalyzeNews:
    def test_positive_news(self):
        news = analyze_news(
            headline="Stock surges on record earnings beat",
            body="The company reported revenue of $10B, exceeding guidance by 20%.",
            source="Bloomberg",
            tickers=["AAPL"],
        )
        assert news.overall.score > 0
        assert news.source_credibility > 0.8
        assert news.market_relevance > 0

    def test_negative_news(self):
        news = analyze_news(
            headline="Stock crashes amid fraud investigation",
            body="SEC launches investigation into accounting irregularities.",
            source="Reuters",
        )
        assert news.overall.score < 0

    def test_source_credibility(self):
        reuters = analyze_news("Test", source="Reuters")
        reddit = analyze_news("Test", source="Reddit")
        assert reuters.source_credibility > reddit.source_credibility

    def test_urgency(self):
        news = analyze_news("Breaking: Flash alert on emergency")
        assert news.urgency > 0


class TestEarningsCall:
    def test_positive_earnings(self):
        segments = [
            {"speaker": "CEO", "text": "Strong revenue growth and excellent margin expansion", "role": "management"},
            {"speaker": "CFO", "text": "We are raising guidance for the full year", "role": "management"},
            {"speaker": "Analyst", "text": "Can you discuss the growth strategy?", "role": "analyst"},
        ]
        result = analyze_earnings_call(segments, company="TEST", quarter="Q1")
        assert result.management_tone.score > 0
        assert "guidance" in result.forward_keywords

    def test_empty_segments(self):
        result = analyze_earnings_call([], company="TEST")
        assert result.management_tone.sentiment == Sentiment.NEUTRAL


class TestTrend:
    def test_uptrend(self):
        data = [{"date": f"2024-01-{i:02d}", "score": 0.1 + i * 0.05, "volume": 1000} for i in range(30)]
        trend = analyze_trend("AAPL", data)
        assert trend.trend_direction in (Sentiment.BULLISH, Sentiment.VERY_BULLISH)
        assert trend.trend_strength > 0

    def test_downtrend(self):
        data = [{"date": f"2024-01-{i:02d}", "score": 0.5 - i * 0.03, "volume": 1000} for i in range(30)]
        trend = analyze_trend("AAPL", data)
        assert trend.trend_direction in (Sentiment.BEARISH, Sentiment.VERY_BEARISH)

    def test_empty_data(self):
        trend = analyze_trend("AAPL", [])
        assert trend.trend_direction == Sentiment.NEUTRAL
