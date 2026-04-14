"""Tests for finscrape.analysis.validator heuristic scoring."""

import pytest

from finscrape.analysis.validator import (
    calculate_heuristic_score,
    check_divergence,
    clean_tickers,
)


# ---------------------------------------------------------------------------
# calculate_heuristic_score
# ---------------------------------------------------------------------------

class TestCalculateHeuristicScore:
    def test_strongly_positive_text(self):
        text = "Company reported record revenue and surged to all-time high"
        sentiment, impact = calculate_heuristic_score(text, "earnings")
        assert sentiment == "positive"
        assert 0.0 <= impact <= 1.0

    def test_strongly_negative_text(self):
        text = "The firm filed for bankruptcy after the fraud scandal collapsed its stock"
        sentiment, impact = calculate_heuristic_score(text, "bankrupt")
        assert sentiment == "negative"
        assert 0.0 <= impact <= 1.0

    def test_neutral_text(self):
        text = "The company held its regular meeting on Tuesday afternoon"
        sentiment, impact = calculate_heuristic_score(text, "other")
        assert sentiment == "neutral"
        assert 0.0 <= impact <= 1.0

    def test_impact_bounded_zero_to_one(self):
        for event_type in ["earnings", "bankrupt", "other", "merger_acquisition"]:
            _, impact = calculate_heuristic_score("some random text", event_type)
            assert 0.0 <= impact <= 1.0

    def test_dollar_billion_boosts_impact(self):
        base_text = "The company announced a deal"
        _, impact_no_dollar = calculate_heuristic_score(base_text, "merger_acquisition")
        _, impact_with_dollar = calculate_heuristic_score(
            base_text + " worth $50 billion", "merger_acquisition"
        )
        assert impact_with_dollar > impact_no_dollar

    def test_dollar_million_boosts_impact(self):
        base_text = "The company announced a deal"
        _, impact_no_dollar = calculate_heuristic_score(base_text, "merger_acquisition")
        _, impact_with_dollar = calculate_heuristic_score(
            base_text + " worth $200 million", "merger_acquisition"
        )
        assert impact_with_dollar > impact_no_dollar

    def test_magnitude_words_boost_impact(self):
        plain = "The company released results"
        boosted = "The company released massive unprecedented historic results"
        _, impact_plain = calculate_heuristic_score(plain, "earnings")
        _, impact_boosted = calculate_heuristic_score(boosted, "earnings")
        assert impact_boosted > impact_plain

    def test_unknown_event_type_uses_default(self):
        sentiment, impact = calculate_heuristic_score("neutral text", "nonexistent_type")
        assert 0.0 <= impact <= 1.0


# ---------------------------------------------------------------------------
# check_divergence
# ---------------------------------------------------------------------------

class TestCheckDivergence:
    def test_same_sentiment_no_divergence(self):
        assert check_divergence("positive", "positive") is False

    def test_opposite_sentiment_diverges(self):
        assert check_divergence("positive", "negative") is True

    def test_ai_neutral_no_divergence(self):
        assert check_divergence("neutral", "negative") is False

    def test_heuristic_neutral_no_divergence(self):
        assert check_divergence("positive", "neutral") is False

    def test_both_neutral_no_divergence(self):
        assert check_divergence("neutral", "neutral") is False

    def test_negative_vs_positive_diverges(self):
        assert check_divergence("negative", "positive") is True


# ---------------------------------------------------------------------------
# clean_tickers
# ---------------------------------------------------------------------------

class TestCleanTickers:
    def test_removes_stopwords(self):
        tickers = ["AAPL", "A", "THE", "TSLA", "IS"]
        cleaned = clean_tickers(tickers)
        assert "AAPL" in cleaned
        assert "TSLA" in cleaned
        assert "A" not in cleaned
        assert "THE" not in cleaned
        assert "IS" not in cleaned

    def test_keeps_valid_tickers(self):
        tickers = ["AAPL", "GOOG", "MSFT"]
        assert clean_tickers(tickers) == ["AAPL", "GOOG", "MSFT"]

    def test_empty_list(self):
        assert clean_tickers([]) == []

    def test_case_insensitive(self):
        # clean_tickers uppercases before checking stopwords
        tickers = ["aapl", "a", "tsla"]
        cleaned = clean_tickers(tickers)
        assert "aapl" in cleaned
        assert "tsla" in cleaned
        assert "a" not in cleaned

    def test_removes_financial_abbreviations(self):
        tickers = ["AAPL", "EPS", "IPO", "SEC", "GOOG"]
        cleaned = clean_tickers(tickers)
        assert "AAPL" in cleaned
        assert "GOOG" in cleaned
        assert "EPS" not in cleaned
        assert "IPO" not in cleaned
        assert "SEC" not in cleaned
