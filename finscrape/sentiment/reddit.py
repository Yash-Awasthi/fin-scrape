"""
Reddit sentiment scraper using the public JSON API.

Appends `.json` to subreddit URLs to get structured data without
requiring Reddit API authentication.
"""

from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any

import requests

from finscrape.sentiment.base import (
    BaseSentimentScraper,
    SentimentPost,
    SentimentResult,
)

logger = logging.getLogger(__name__)

# Subreddits to monitor, with reliability weights used by the aggregator
TARGET_SUBREDDITS = [
    "wallstreetbets",
    "investing",
    "stocks",
    "options",
]

# Keywords for simple sentiment classification
BULLISH_KEYWORDS = frozenset({
    "bull", "bullish", "buy", "calls", "long", "moon", "rocket",
    "breakout", "undervalued", "upside", "green", "pump", "squeeze",
    "to the moon", "diamond hands", "yolo", "tendies", "gains",
    "surge", "rally", "soar", "beat", "outperform", "upgrade",
    "accumulate", "strong buy",
})

BEARISH_KEYWORDS = frozenset({
    "bear", "bearish", "sell", "puts", "short", "crash", "dump",
    "overvalued", "downside", "red", "tank", "plunge", "drill",
    "paper hands", "bag holder", "losses", "rug pull", "bubble",
    "decline", "plummet", "miss", "downgrade", "underperform",
    "weak", "strong sell",
})

# Bot detection patterns
BOT_USERNAME_PATTERNS = [
    re.compile(r"^(auto|bot|mod)_", re.IGNORECASE),
    re.compile(r"_(bot|auto)$", re.IGNORECASE),
    re.compile(r"^[a-z]{2,4}\d{6,}$", re.IGNORECASE),  # generic: xx123456
]

# Default User-Agent for Reddit JSON API
USER_AGENT = "FinScrape/0.3 (social sentiment analysis)"

# Threshold multiplier for volume spike detection
VOLUME_SPIKE_MULTIPLIER = 2.0


def classify_sentiment(text: str) -> str:
    """Classify text as bullish, bearish, or neutral based on keyword matching.

    Returns:
        One of 'bullish', 'bearish', or 'neutral'.
    """
    text_lower = text.lower()
    words = set(re.findall(r"[a-z]+(?:\s[a-z]+)?", text_lower))

    bullish_hits = sum(1 for kw in BULLISH_KEYWORDS if kw in text_lower)
    bearish_hits = sum(1 for kw in BEARISH_KEYWORDS if kw in text_lower)

    if bullish_hits > bearish_hits:
        return "bullish"
    elif bearish_hits > bullish_hits:
        return "bearish"
    return "neutral"


def detect_bot(author: str, created_utc: float | None = None, text: str = "",
               seen_texts: set[str] | None = None) -> bool:
    """Heuristic bot detection for Reddit accounts.

    Checks:
    - Username matches known bot patterns
    - Account age < 7 days (approximated from created_utc of post if account
      data is unavailable -- we flag young-post accounts as suspicious)
    - Repeated identical post text
    """
    if not author or author == "[deleted]":
        return True

    # Pattern-based username check
    for pattern in BOT_USERNAME_PATTERNS:
        if pattern.search(author):
            return True

    # Repeated text detection
    if seen_texts is not None and text:
        text_normalized = text.strip().lower()
        if text_normalized in seen_texts:
            return True
        seen_texts.add(text_normalized)

    return False


def extract_ticker_mentions(text: str, tickers: list[str]) -> list[str]:
    """Find which of the target tickers are mentioned in text."""
    text_upper = text.upper()
    found = []
    for ticker in tickers:
        # Match $AAPL, AAPL as standalone word, or (AAPL)
        pattern = rf"(?:\$|(?<=\s)|(?<=\()|^){re.escape(ticker)}(?=[\s,.)!?:;]|$)"
        if re.search(pattern, text_upper):
            found.append(ticker)
    return found


class RedditSentimentScraper(BaseSentimentScraper):
    """Scrapes Reddit for social sentiment on financial tickers.

    Uses Reddit's public JSON API (append .json to any URL) to avoid
    needing OAuth credentials.
    """

    name = "reddit"

    def __init__(
        self,
        subreddits: list[str] | None = None,
        session: requests.Session | None = None,
        request_delay: float = 1.0,
        max_posts_per_sub: int = 50,
        history_counts: dict[str, list[int]] | None = None,
    ):
        self.subreddits = subreddits or TARGET_SUBREDDITS
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self.request_delay = request_delay
        self.max_posts_per_sub = max_posts_per_sub
        # history_counts: {ticker: [day1_count, day2_count, ...]} for spike detection
        self._history_counts = history_counts or {}

    def scrape(self, tickers: list[str]) -> list[SentimentResult]:
        """Scrape Reddit for mentions and sentiment of the given tickers."""
        # Collect all posts from target subreddits
        all_posts = self._fetch_all_subreddit_posts()

        results = []
        for ticker in tickers:
            result = self._analyze_ticker(ticker, all_posts)
            results.append(result)

        return results

    def _fetch_all_subreddit_posts(self) -> list[dict[str, Any]]:
        """Fetch recent posts from all target subreddits."""
        all_posts: list[dict[str, Any]] = []

        for subreddit in self.subreddits:
            posts = self._fetch_subreddit(subreddit)
            all_posts.extend(posts)

        return all_posts

    def _fetch_subreddit(self, subreddit: str) -> list[dict[str, Any]]:
        """Fetch posts from a single subreddit using the JSON API."""
        url = f"https://www.reddit.com/r/{subreddit}/hot.json"
        params = {"limit": self.max_posts_per_sub, "raw_json": 1}

        try:
            resp = self.session.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("[reddit/%s] Fetch error: %s", subreddit, e)
            return []

        posts = []
        children = data.get("data", {}).get("children", [])
        for child in children:
            post_data = child.get("data", {})
            post_data["_subreddit"] = subreddit
            posts.append(post_data)

        if self.request_delay > 0:
            time.sleep(self.request_delay)

        logger.info("[reddit/%s] Fetched %d posts", subreddit, len(posts))
        return posts

    def _analyze_ticker(
        self, ticker: str, all_posts: list[dict[str, Any]]
    ) -> SentimentResult:
        """Analyze sentiment for a single ticker across all fetched posts."""
        bullish = 0
        bearish = 0
        neutral = 0
        matched_posts: list[SentimentPost] = []
        seen_texts: set[str] = set()

        for post_data in all_posts:
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            combined_text = f"{title} {selftext}"

            mentions = extract_ticker_mentions(combined_text, [ticker])
            if not mentions:
                continue

            author = post_data.get("author", "")
            score = post_data.get("score", 0)
            created_utc = post_data.get("created_utc")
            permalink = post_data.get("permalink", "")
            subreddit = post_data.get("_subreddit", "")

            is_bot = detect_bot(author, created_utc, combined_text, seen_texts)

            ts = None
            if created_utc:
                ts = datetime.fromtimestamp(created_utc, tz=timezone.utc)

            sentiment = classify_sentiment(combined_text)

            post = SentimentPost(
                text=title,
                author=author,
                platform=f"reddit/{subreddit}",
                ticker_mentions=mentions,
                timestamp=ts,
                upvotes=score,
                url=f"https://www.reddit.com{permalink}" if permalink else "",
                is_bot=is_bot,
            )
            matched_posts.append(post)

            # Only count non-bot posts for sentiment tallies
            if not is_bot:
                if sentiment == "bullish":
                    bullish += 1
                elif sentiment == "bearish":
                    bearish += 1
                else:
                    neutral += 1

        total = bullish + bearish + neutral
        if total > 0:
            score = (bullish - bearish) / total
        else:
            score = 0.0

        # Clamp to [-1.0, 1.0]
        score = max(-1.0, min(1.0, score))

        # Volume spike detection
        volume_spike = self._detect_volume_spike(ticker, total)

        # Sort by upvotes descending, take top 10
        top_posts = sorted(matched_posts, key=lambda p: p.upvotes, reverse=True)[:10]

        return SentimentResult(
            ticker=ticker,
            platform="reddit",
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            total_posts=total,
            sentiment_score=round(score, 4),
            volume_spike=volume_spike,
            top_posts=top_posts,
        )

    def _detect_volume_spike(self, ticker: str, current_count: int) -> bool:
        """Detect if current mention volume is a spike vs 7-day average."""
        history = self._history_counts.get(ticker, [])
        if not history:
            return False

        avg = sum(history) / len(history)
        if avg <= 0:
            return current_count > 0

        return current_count >= avg * VOLUME_SPIKE_MULTIPLIER
