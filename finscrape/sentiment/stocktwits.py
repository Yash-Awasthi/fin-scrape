"""
StockTwits sentiment scraper using the public API.

Uses the unauthenticated StockTwits stream endpoint to fetch
recent messages and their crowd-sourced sentiment labels.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests

from finscrape.sentiment.base import (
    BaseSentimentScraper,
    SentimentPost,
    SentimentResult,
)

logger = logging.getLogger(__name__)

STOCKTWITS_API_BASE = "https://api.stocktwits.com/api/2"

# Default User-Agent
USER_AGENT = "FinScrape/0.3 (social sentiment analysis)"

# Volume spike multiplier
VOLUME_SPIKE_MULTIPLIER = 2.0


class StockTwitsScraper(BaseSentimentScraper):
    """Scrapes StockTwits for social sentiment on financial tickers.

    Uses the public (no-auth) stream endpoint:
        GET /api/2/streams/symbol/{ticker}.json
    """

    name = "stocktwits"

    def __init__(
        self,
        session: requests.Session | None = None,
        history_counts: dict[str, list[int]] | None = None,
    ):
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", USER_AGENT)
        self._history_counts = history_counts or {}

    def scrape(self, tickers: list[str]) -> list[SentimentResult]:
        """Scrape StockTwits for the given tickers."""
        results = []
        for ticker in tickers:
            result = self._scrape_ticker(ticker)
            results.append(result)
        return results

    def _scrape_ticker(self, ticker: str) -> SentimentResult:
        """Fetch and analyze messages for a single ticker."""
        url = f"{STOCKTWITS_API_BASE}/streams/symbol/{ticker}.json"

        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            logger.warning("[stocktwits/%s] Fetch error: %s", ticker, e)
            return SentimentResult(ticker=ticker, platform="stocktwits")

        messages = data.get("messages", [])
        return self._analyze_messages(ticker, messages)

    def _analyze_messages(
        self, ticker: str, messages: list[dict[str, Any]]
    ) -> SentimentResult:
        """Analyze a list of StockTwits messages for sentiment."""
        bullish = 0
        bearish = 0
        neutral = 0
        posts: list[SentimentPost] = []

        for msg in messages:
            body = msg.get("body", "")
            author = msg.get("user", {}).get("username", "")
            likes = msg.get("likes", {})
            like_count = likes.get("total", 0) if isinstance(likes, dict) else 0

            # Parse timestamp
            ts = None
            created_at = msg.get("created_at")
            if created_at:
                try:
                    ts = datetime.strptime(
                        created_at, "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # StockTwits provides its own sentiment labels
            entities = msg.get("entities", {})
            st_sentiment = entities.get("sentiment", {}) if isinstance(entities, dict) else {}
            if isinstance(st_sentiment, dict):
                basic = st_sentiment.get("basic", "")
            else:
                basic = ""

            if basic == "Bullish":
                sentiment = "bullish"
                bullish += 1
            elif basic == "Bearish":
                sentiment = "bearish"
                bearish += 1
            else:
                sentiment = "neutral"
                neutral += 1

            post = SentimentPost(
                text=body,
                author=author,
                platform="stocktwits",
                ticker_mentions=[ticker],
                timestamp=ts,
                likes=like_count,
                url=f"https://stocktwits.com/symbol/{ticker}",
                is_bot=False,
            )
            posts.append(post)

        total = bullish + bearish + neutral
        if total > 0:
            score = (bullish - bearish) / total
        else:
            score = 0.0

        score = max(-1.0, min(1.0, score))

        volume_spike = self._detect_volume_spike(ticker, total)

        # Top posts by likes
        top_posts = sorted(posts, key=lambda p: p.likes, reverse=True)[:10]

        return SentimentResult(
            ticker=ticker,
            platform="stocktwits",
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            total_posts=total,
            sentiment_score=round(score, 4),
            volume_spike=volume_spike,
            top_posts=top_posts,
        )

    def _detect_volume_spike(self, ticker: str, current_count: int) -> bool:
        """Detect if current message volume is a spike vs 7-day average."""
        history = self._history_counts.get(ticker, [])
        if not history:
            return False

        avg = sum(history) / len(history)
        if avg <= 0:
            return current_count > 0

        return current_count >= avg * VOLUME_SPIKE_MULTIPLIER
