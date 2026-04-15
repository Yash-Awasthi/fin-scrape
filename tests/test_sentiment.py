"""
Comprehensive tests for the social sentiment engine.

Covers Reddit scraping, StockTwits scraping, bot detection,
volume spike detection, aggregation, and edge cases.
"""

from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

# Ensure the sentiment sub-package can be imported in the test environment.
# The conftest.py stubs finscrape and finscrape.analysis; we also need
# finscrape.sentiment stubbed so the sub-module imports resolve.
if "finscrape.sentiment" not in sys.modules:
    from pathlib import Path
    _sentiment_stub = types.ModuleType("finscrape.sentiment")
    _sentiment_stub.__path__ = [str(Path(__file__).resolve().parent.parent / "finscrape" / "sentiment")]
    _sentiment_stub.__package__ = "finscrape.sentiment"
    sys.modules["finscrape.sentiment"] = _sentiment_stub

from finscrape.sentiment.base import SentimentPost, SentimentResult, BaseSentimentScraper
from finscrape.sentiment.reddit import (
    RedditSentimentScraper,
    classify_sentiment,
    detect_bot,
    extract_ticker_mentions,
    BULLISH_KEYWORDS,
    BEARISH_KEYWORDS,
)
from finscrape.sentiment.stocktwits import StockTwitsScraper
from finscrape.sentiment.aggregator import SentimentAggregator


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_reddit_response(posts: list[dict]) -> dict:
    """Build a Reddit JSON API response envelope."""
    children = [{"kind": "t3", "data": p} for p in posts]
    return {"kind": "Listing", "data": {"children": children, "after": None}}


def _make_stocktwits_response(messages: list[dict]) -> dict:
    """Build a StockTwits API response envelope."""
    return {
        "response": {"status": 200},
        "messages": messages,
    }


def _reddit_post(
    title: str = "Test post",
    selftext: str = "",
    author: str = "testuser",
    score: int = 10,
    created_utc: float = 1700000000.0,
    permalink: str = "/r/stocks/comments/abc/test_post/",
    subreddit: str = "stocks",
) -> dict:
    return {
        "title": title,
        "selftext": selftext,
        "author": author,
        "score": score,
        "created_utc": created_utc,
        "permalink": permalink,
        "_subreddit": subreddit,
    }


def _stocktwits_msg(
    body: str = "Test message",
    username: str = "trader1",
    sentiment: str | None = None,
    likes: int = 0,
    created_at: str = "2024-01-15T12:00:00Z",
) -> dict:
    msg: dict = {
        "body": body,
        "user": {"username": username},
        "likes": {"total": likes},
        "created_at": created_at,
        "entities": {},
    }
    if sentiment:
        msg["entities"]["sentiment"] = {"basic": sentiment}
    return msg


class MockResponse:
    """Minimal requests.Response stand-in."""
    def __init__(self, json_data: dict, status_code: int = 200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


# ===========================================================================
# 1. Sentiment Classification Tests
# ===========================================================================

class TestClassifySentiment:
    def test_bullish_text(self):
        assert classify_sentiment("AAPL to the moon! Bullish calls all day") == "bullish"

    def test_bearish_text(self):
        assert classify_sentiment("This stock is going to crash, puts puts puts") == "bearish"

    def test_neutral_text(self):
        assert classify_sentiment("AAPL reported earnings today") == "neutral"

    def test_mixed_defaults_neutral_when_equal(self):
        # One bullish keyword ("buy") and one bearish ("sell") -> neutral
        assert classify_sentiment("Should I buy or sell TSLA?") == "neutral"

    def test_empty_text(self):
        assert classify_sentiment("") == "neutral"

    def test_bullish_keywords_dominate(self):
        text = "Long NVDA, huge upside, breakout incoming, undervalued gem"
        assert classify_sentiment(text) == "bullish"

    def test_bearish_keywords_dominate(self):
        text = "Short this overvalued dump, bearish puts, rug pull soon"
        assert classify_sentiment(text) == "bearish"


# ===========================================================================
# 2. Bot Detection Tests
# ===========================================================================

class TestBotDetection:
    def test_deleted_user_is_bot(self):
        assert detect_bot("[deleted]") is True

    def test_empty_author_is_bot(self):
        assert detect_bot("") is True

    def test_bot_suffix_detected(self):
        assert detect_bot("news_bot") is True

    def test_auto_prefix_detected(self):
        assert detect_bot("auto_moderator") is True

    def test_generic_username_detected(self):
        assert detect_bot("ab12345678") is True

    def test_normal_user_passes(self):
        assert detect_bot("warren_buffett_fan") is False

    def test_repeated_text_detected(self):
        seen: set[str] = set()
        assert detect_bot("user1", text="buy AAPL now!", seen_texts=seen) is False
        assert detect_bot("user2", text="buy AAPL now!", seen_texts=seen) is True

    def test_repeated_text_case_insensitive(self):
        seen: set[str] = set()
        detect_bot("user1", text="BUY AAPL NOW!", seen_texts=seen)
        assert detect_bot("user2", text="buy aapl now!", seen_texts=seen) is True


# ===========================================================================
# 3. Ticker Mention Extraction Tests
# ===========================================================================

class TestTickerExtraction:
    def test_dollar_sign_mention(self):
        assert extract_ticker_mentions("I'm buying $AAPL today", ["AAPL"]) == ["AAPL"]

    def test_plain_mention(self):
        assert extract_ticker_mentions("TSLA is mooning", ["TSLA"]) == ["TSLA"]

    def test_parenthetical_mention(self):
        assert extract_ticker_mentions("Apple (AAPL) beat earnings", ["AAPL"]) == ["AAPL"]

    def test_no_match(self):
        assert extract_ticker_mentions("Nothing here", ["AAPL"]) == []

    def test_multiple_tickers(self):
        text = "Both $AAPL and $MSFT looking good"
        result = extract_ticker_mentions(text, ["AAPL", "MSFT", "TSLA"])
        assert "AAPL" in result
        assert "MSFT" in result
        assert "TSLA" not in result


# ===========================================================================
# 4. Reddit Scraper Tests
# ===========================================================================

class TestRedditScraper:
    def _make_scraper(self, response_data: dict | None = None, subreddits=None) -> RedditSentimentScraper:
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        if response_data is not None:
            session.get.return_value = MockResponse(response_data)
        else:
            session.get.return_value = MockResponse(_make_reddit_response([]))
        return RedditSentimentScraper(
            subreddits=subreddits or ["stocks"],
            session=session,
            request_delay=0,
        )

    def test_basic_scrape(self):
        posts = [
            _reddit_post(title="AAPL is bullish, buy calls!", score=100),
            _reddit_post(title="AAPL crash incoming, puts", score=50),
        ]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["AAPL"])
        assert len(results) == 1
        r = results[0]
        assert r.ticker == "AAPL"
        assert r.platform == "reddit"
        assert r.total_posts > 0

    def test_sentiment_counts(self):
        posts = [
            _reddit_post(title="$AAPL to the moon! Bullish!", score=10),
            _reddit_post(title="$AAPL bearish crash puts", score=5),
            _reddit_post(title="$AAPL reported earnings", score=3),
        ]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["AAPL"])
        r = results[0]
        assert r.bullish_count == 1
        assert r.bearish_count == 1
        assert r.neutral_count == 1
        assert r.total_posts == 3

    def test_sentiment_score_range(self):
        posts = [_reddit_post(title="$TSLA moon rocket bullish!", score=10)]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["TSLA"])
        r = results[0]
        assert -1.0 <= r.sentiment_score <= 1.0

    def test_top_posts_sorted_by_upvotes(self):
        posts = [
            _reddit_post(title="$AAPL low", score=5),
            _reddit_post(title="$AAPL high", score=500),
            _reddit_post(title="$AAPL mid", score=50),
        ]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["AAPL"])
        top = results[0].top_posts
        assert top[0].upvotes == 500

    def test_bot_posts_excluded_from_counts(self):
        posts = [
            _reddit_post(title="$AAPL bullish moon!", author="auto_bot", score=10),
            _reddit_post(title="$AAPL bearish crash puts", author="realuser", score=5),
        ]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["AAPL"])
        r = results[0]
        # The bot post should not be counted in sentiment tallies
        assert r.bearish_count == 1
        assert r.bullish_count == 0
        assert r.total_posts == 1

    def test_empty_response(self):
        scraper = self._make_scraper(_make_reddit_response([]))
        results = scraper.scrape(["AAPL"])
        r = results[0]
        assert r.total_posts == 0
        assert r.sentiment_score == 0.0

    def test_api_error_returns_empty(self):
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        session.get.side_effect = requests.ConnectionError("timeout")
        scraper = RedditSentimentScraper(
            subreddits=["stocks"], session=session, request_delay=0
        )
        results = scraper.scrape(["AAPL"])
        assert results[0].total_posts == 0

    def test_volume_spike_detected(self):
        # Each post has unique text to avoid bot detection for duplicates
        posts = [
            _reddit_post(title=f"$AAPL moon post {i}!", author=f"user{i}", score=10)
            for i in range(20)
        ]
        scraper = self._make_scraper(_make_reddit_response(posts))
        scraper._history_counts = {"AAPL": [2, 3, 1, 2, 4, 3, 2]}  # avg ~2.4
        results = scraper.scrape(["AAPL"])
        assert results[0].volume_spike is True

    def test_no_volume_spike_without_history(self):
        posts = [_reddit_post(title="$AAPL moon!", score=10)]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["AAPL"])
        assert results[0].volume_spike is False

    def test_multiple_subreddits(self):
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        session.get.return_value = MockResponse(
            _make_reddit_response([_reddit_post(title="$AAPL bullish")])
        )
        scraper = RedditSentimentScraper(
            subreddits=["wallstreetbets", "investing", "stocks"],
            session=session,
            request_delay=0,
        )
        results = scraper.scrape(["AAPL"])
        # Should have called get once per subreddit
        assert session.get.call_count == 3

    def test_no_ticker_mentions_yields_zero(self):
        posts = [_reddit_post(title="The market is crazy today!", score=50)]
        scraper = self._make_scraper(_make_reddit_response(posts))
        results = scraper.scrape(["AAPL"])
        assert results[0].total_posts == 0


# ===========================================================================
# 5. StockTwits Scraper Tests
# ===========================================================================

class TestStockTwitsScraper:
    def _make_scraper(self, response_data: dict | None = None) -> StockTwitsScraper:
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        if response_data is not None:
            session.get.return_value = MockResponse(response_data)
        else:
            session.get.return_value = MockResponse(_make_stocktwits_response([]))
        return StockTwitsScraper(session=session)

    def test_basic_scrape(self):
        msgs = [
            _stocktwits_msg(body="AAPL going up!", sentiment="Bullish", likes=5),
            _stocktwits_msg(body="AAPL tanking", sentiment="Bearish", likes=2),
        ]
        scraper = self._make_scraper(_make_stocktwits_response(msgs))
        results = scraper.scrape(["AAPL"])
        assert len(results) == 1
        r = results[0]
        assert r.ticker == "AAPL"
        assert r.platform == "stocktwits"
        assert r.bullish_count == 1
        assert r.bearish_count == 1

    def test_neutral_when_no_label(self):
        msgs = [_stocktwits_msg(body="AAPL earnings today")]
        scraper = self._make_scraper(_make_stocktwits_response(msgs))
        results = scraper.scrape(["AAPL"])
        assert results[0].neutral_count == 1

    def test_sentiment_score(self):
        msgs = [
            _stocktwits_msg(sentiment="Bullish"),
            _stocktwits_msg(sentiment="Bullish"),
            _stocktwits_msg(sentiment="Bearish"),
        ]
        scraper = self._make_scraper(_make_stocktwits_response(msgs))
        results = scraper.scrape(["AAPL"])
        r = results[0]
        # (2 - 1) / 3 = 0.3333
        assert abs(r.sentiment_score - 0.3333) < 0.01

    def test_empty_messages(self):
        scraper = self._make_scraper(_make_stocktwits_response([]))
        results = scraper.scrape(["AAPL"])
        assert results[0].total_posts == 0

    def test_api_error(self):
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        session.get.side_effect = requests.ConnectionError("fail")
        scraper = StockTwitsScraper(session=session)
        results = scraper.scrape(["AAPL"])
        assert results[0].total_posts == 0
        assert results[0].platform == "stocktwits"

    def test_likes_sorting(self):
        msgs = [
            _stocktwits_msg(body="low likes", likes=1),
            _stocktwits_msg(body="high likes", likes=100),
            _stocktwits_msg(body="mid likes", likes=10),
        ]
        scraper = self._make_scraper(_make_stocktwits_response(msgs))
        results = scraper.scrape(["AAPL"])
        assert results[0].top_posts[0].likes == 100

    def test_volume_spike(self):
        msgs = [_stocktwits_msg() for _ in range(30)]
        scraper = self._make_scraper(_make_stocktwits_response(msgs))
        scraper._history_counts = {"TSLA": [5, 4, 6, 3, 5, 7, 4]}
        results = scraper.scrape(["TSLA"])
        assert results[0].volume_spike is True

    def test_timestamp_parsing(self):
        msgs = [_stocktwits_msg(created_at="2024-01-15T12:00:00Z")]
        scraper = self._make_scraper(_make_stocktwits_response(msgs))
        results = scraper.scrape(["AAPL"])
        post = results[0].top_posts[0]
        assert post.timestamp is not None
        assert post.timestamp.year == 2024


# ===========================================================================
# 6. Aggregator Tests
# ===========================================================================

class TestSentimentAggregator:
    def test_aggregate_combines_counts(self):
        r1 = SentimentResult(
            ticker="AAPL", platform="reddit",
            bullish_count=10, bearish_count=5, neutral_count=5,
            total_posts=20, sentiment_score=0.25,
        )
        r2 = SentimentResult(
            ticker="AAPL", platform="stocktwits",
            bullish_count=8, bearish_count=2, neutral_count=5,
            total_posts=15, sentiment_score=0.4,
        )
        agg = SentimentAggregator(scrapers=[])
        combined = agg.aggregate([r1, r2])
        assert combined.bullish_count == 18
        assert combined.bearish_count == 7
        assert combined.total_posts == 35
        assert combined.platform == "aggregated"

    def test_aggregate_weighted_score(self):
        r1 = SentimentResult(
            ticker="AAPL", platform="reddit",
            bullish_count=5, bearish_count=5, neutral_count=0,
            total_posts=10, sentiment_score=0.0,
        )
        r2 = SentimentResult(
            ticker="AAPL", platform="stocktwits",
            bullish_count=10, bearish_count=0, neutral_count=0,
            total_posts=10, sentiment_score=1.0,
        )
        agg = SentimentAggregator(
            scrapers=[],
            platform_weights={"reddit": 0.5, "stocktwits": 1.0},
        )
        combined = agg.aggregate([r1, r2])
        # weighted: (0.0 * 0.5 + 1.0 * 1.0) / (0.5 + 1.0) = 0.6667
        assert abs(combined.sentiment_score - 0.6667) < 0.01

    def test_aggregate_empty_list(self):
        agg = SentimentAggregator(scrapers=[])
        combined = agg.aggregate([])
        assert combined.ticker == ""
        assert combined.total_posts == 0

    def test_aggregate_filters_bot_posts(self):
        bot_post = SentimentPost(
            text="spam", author="bot_acct", platform="reddit",
            upvotes=1000, is_bot=True,
        )
        real_post = SentimentPost(
            text="real analysis", author="investor", platform="reddit",
            upvotes=50, is_bot=False,
        )
        r = SentimentResult(
            ticker="AAPL", platform="reddit",
            bullish_count=1, bearish_count=0, neutral_count=0,
            total_posts=1, sentiment_score=1.0,
            top_posts=[bot_post, real_post],
        )
        agg = SentimentAggregator(scrapers=[])
        combined = agg.aggregate([r])
        # Bot post should be filtered from top_posts
        assert all(not p.is_bot for p in combined.top_posts)
        assert len(combined.top_posts) == 1

    def test_aggregate_volume_spike_propagates(self):
        r1 = SentimentResult(ticker="AAPL", platform="reddit", volume_spike=True)
        r2 = SentimentResult(ticker="AAPL", platform="stocktwits", volume_spike=False)
        agg = SentimentAggregator(scrapers=[])
        combined = agg.aggregate([r1, r2])
        assert combined.volume_spike is True

    def test_get_social_signal_structure(self):
        """Verify the social signal dict has the required keys."""
        mock_scraper = MagicMock(spec=BaseSentimentScraper)
        mock_scraper.name = "mock"
        mock_scraper.scrape.return_value = [
            SentimentResult(
                ticker="AAPL", platform="mock",
                bullish_count=7, bearish_count=3, neutral_count=0,
                total_posts=10, sentiment_score=0.4,
            )
        ]
        agg = SentimentAggregator(
            scrapers=[mock_scraper],
            platform_weights={"mock": 1.0},
        )
        signal = agg.get_social_signal("AAPL")
        assert "social_sentiment_score" in signal
        assert "social_volume" in signal
        assert "social_volume_spike" in signal
        assert "social_bullish_pct" in signal
        assert "platforms" in signal
        assert isinstance(signal["platforms"], list)
        assert signal["social_volume"] == 10

    def test_get_social_signal_score_range(self):
        mock_scraper = MagicMock(spec=BaseSentimentScraper)
        mock_scraper.name = "mock"
        mock_scraper.scrape.return_value = [
            SentimentResult(
                ticker="TSLA", platform="mock",
                bullish_count=0, bearish_count=10, neutral_count=0,
                total_posts=10, sentiment_score=-1.0,
            )
        ]
        agg = SentimentAggregator(
            scrapers=[mock_scraper],
            platform_weights={"mock": 1.0},
        )
        signal = agg.get_social_signal("TSLA")
        assert -1.0 <= signal["social_sentiment_score"] <= 1.0

    def test_scraper_failure_handled_gracefully(self):
        failing_scraper = MagicMock(spec=BaseSentimentScraper)
        failing_scraper.name = "failing"
        failing_scraper.scrape.side_effect = Exception("API down")

        ok_scraper = MagicMock(spec=BaseSentimentScraper)
        ok_scraper.name = "ok"
        ok_scraper.scrape.return_value = [
            SentimentResult(ticker="AAPL", platform="ok", total_posts=5,
                            bullish_count=3, bearish_count=1, neutral_count=1,
                            sentiment_score=0.4)
        ]

        agg = SentimentAggregator(scrapers=[failing_scraper, ok_scraper])
        results = agg.scrape_all(["AAPL"])
        assert len(results["AAPL"]) == 1  # only the ok scraper


# ===========================================================================
# 7. Data Model Tests
# ===========================================================================

class TestDataModels:
    def test_sentiment_post_defaults(self):
        p = SentimentPost(text="test", author="user", platform="reddit")
        assert p.upvotes == 0
        assert p.likes == 0
        assert p.is_bot is False
        assert p.url == ""

    def test_sentiment_result_defaults(self):
        r = SentimentResult(ticker="AAPL", platform="reddit")
        assert r.bullish_count == 0
        assert r.sentiment_score == 0.0
        assert r.volume_spike is False
        assert r.analyzed_at  # non-empty

    def test_sentiment_result_bullish_pct(self):
        r = SentimentResult(
            ticker="AAPL", platform="reddit",
            bullish_count=7, bearish_count=2, neutral_count=1, total_posts=10,
        )
        assert abs(r.bullish_pct - 0.7) < 0.001

    def test_sentiment_result_bullish_pct_zero_posts(self):
        r = SentimentResult(ticker="AAPL", platform="reddit", total_posts=0)
        assert r.bullish_pct == 0.0


# ===========================================================================
# 8. Volume Spike Edge Cases
# ===========================================================================

class TestVolumeSpikeEdgeCases:
    def _mock_session(self):
        session = MagicMock(spec=requests.Session)
        session.headers = {}
        return session

    def test_spike_with_zero_history(self):
        """Zero average history, any current count is a spike."""
        scraper = RedditSentimentScraper(
            subreddits=["stocks"],
            session=self._mock_session(),
            request_delay=0,
        )
        scraper._history_counts = {"AAPL": [0, 0, 0]}
        assert scraper._detect_volume_spike("AAPL", 1) is True

    def test_no_spike_below_threshold(self):
        scraper = RedditSentimentScraper(
            subreddits=["stocks"],
            session=self._mock_session(),
            request_delay=0,
        )
        scraper._history_counts = {"AAPL": [10, 10, 10]}
        assert scraper._detect_volume_spike("AAPL", 15) is False

    def test_spike_at_exactly_threshold(self):
        scraper = RedditSentimentScraper(
            subreddits=["stocks"],
            session=self._mock_session(),
            request_delay=0,
        )
        scraper._history_counts = {"AAPL": [10, 10, 10]}
        # 2x average = 20
        assert scraper._detect_volume_spike("AAPL", 20) is True
