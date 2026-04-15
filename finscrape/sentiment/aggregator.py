"""
Sentiment aggregator that combines results from multiple platforms.

Produces a unified SentimentResult per ticker with platform-weighted
scoring and bot-filtered metrics, plus a pipeline-compatible signal dict.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from finscrape.sentiment.base import (
    BaseSentimentScraper,
    SentimentPost,
    SentimentResult,
)
from finscrape.sentiment.reddit import RedditSentimentScraper
from finscrape.sentiment.stocktwits import StockTwitsScraper

logger = logging.getLogger(__name__)

# Platform/subreddit reliability weights for aggregation.
# Higher weight = more influence on the combined score.
DEFAULT_PLATFORM_WEIGHTS: dict[str, float] = {
    "reddit": 0.6,
    "stocktwits": 0.8,
}

# Per-subreddit weights within Reddit (applied as multiplier on reddit weight)
SUBREDDIT_WEIGHTS: dict[str, float] = {
    "wallstreetbets": 0.5,   # high noise, meme-heavy
    "investing": 1.0,        # more measured discussion
    "stocks": 0.9,
    "options": 0.7,
}


class SentimentAggregator:
    """Combines sentiment results from multiple scrapers into a unified signal.

    Applies platform reliability weights, filters bot posts, and produces
    a pipeline-compatible social signal dictionary.
    """

    def __init__(
        self,
        scrapers: list[BaseSentimentScraper] | None = None,
        platform_weights: dict[str, float] | None = None,
    ):
        self.scrapers = scrapers or [
            RedditSentimentScraper(),
            StockTwitsScraper(),
        ]
        self.platform_weights = platform_weights or DEFAULT_PLATFORM_WEIGHTS

    def scrape_all(self, tickers: list[str]) -> dict[str, list[SentimentResult]]:
        """Scrape all platforms and return results grouped by ticker.

        Returns:
            Dict mapping ticker -> list of SentimentResult (one per platform).
        """
        ticker_results: dict[str, list[SentimentResult]] = {t: [] for t in tickers}

        for scraper in self.scrapers:
            try:
                results = scraper.scrape(tickers)
                for result in results:
                    if result.ticker in ticker_results:
                        ticker_results[result.ticker].append(result)
            except Exception as e:
                logger.warning(
                    "[aggregator] Scraper %s failed: %s", scraper.name, e
                )

        return ticker_results

    def aggregate(self, results: list[SentimentResult]) -> SentimentResult:
        """Combine multiple platform results into a single SentimentResult.

        Weights each platform's sentiment score by its reliability weight.
        Bot posts are excluded from the aggregated counts.
        """
        if not results:
            return SentimentResult(ticker="", platform="aggregated")

        ticker = results[0].ticker
        total_bullish = 0
        total_bearish = 0
        total_neutral = 0
        all_top_posts: list[SentimentPost] = []
        any_spike = False

        weighted_score_sum = 0.0
        weight_sum = 0.0

        for result in results:
            platform_weight = self.platform_weights.get(result.platform, 0.5)

            # Filter bot posts from top_posts
            filtered_posts = [p for p in result.top_posts if not p.is_bot]
            all_top_posts.extend(filtered_posts)

            total_bullish += result.bullish_count
            total_bearish += result.bearish_count
            total_neutral += result.neutral_count

            if result.total_posts > 0:
                weighted_score_sum += result.sentiment_score * platform_weight
                weight_sum += platform_weight

            if result.volume_spike:
                any_spike = True

        total_posts = total_bullish + total_bearish + total_neutral

        if weight_sum > 0:
            combined_score = weighted_score_sum / weight_sum
        else:
            combined_score = 0.0

        combined_score = max(-1.0, min(1.0, round(combined_score, 4)))

        # Top posts across all platforms, sorted by engagement
        top_posts = sorted(
            all_top_posts,
            key=lambda p: p.upvotes + p.likes,
            reverse=True,
        )[:10]

        return SentimentResult(
            ticker=ticker,
            platform="aggregated",
            bullish_count=total_bullish,
            bearish_count=total_bearish,
            neutral_count=total_neutral,
            total_posts=total_posts,
            sentiment_score=combined_score,
            volume_spike=any_spike,
            top_posts=top_posts,
        )

    def get_social_signal(self, ticker: str) -> dict[str, Any]:
        """Produce a pipeline-compatible social signal dict for a ticker.

        Returns:
            Dict with keys:
                - social_sentiment_score: float (-1.0 to 1.0)
                - social_volume: int (total mentions)
                - social_volume_spike: bool
                - social_bullish_pct: float (0.0 to 1.0)
                - platforms: list[str] of contributing platforms
        """
        all_results = self.scrape_all([ticker])
        results = all_results.get(ticker, [])
        aggregated = self.aggregate(results)

        platforms = [r.platform for r in results if r.total_posts > 0]

        return {
            "social_sentiment_score": aggregated.sentiment_score,
            "social_volume": aggregated.total_posts,
            "social_volume_spike": aggregated.volume_spike,
            "social_bullish_pct": round(aggregated.bullish_pct, 4),
            "platforms": platforms,
        }
