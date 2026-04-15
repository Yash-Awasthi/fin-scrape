"""
Social sentiment analysis engine.

Provides Reddit and StockTwits scrapers plus an aggregator that
combines multi-platform sentiment into unified signals.
"""

from finscrape.sentiment.base import (
    BaseSentimentScraper,
    SentimentPost,
    SentimentResult,
)
from finscrape.sentiment.reddit import RedditSentimentScraper
from finscrape.sentiment.stocktwits import StockTwitsScraper
from finscrape.sentiment.aggregator import SentimentAggregator

__all__ = [
    "BaseSentimentScraper",
    "SentimentPost",
    "SentimentResult",
    "RedditSentimentScraper",
    "StockTwitsScraper",
    "SentimentAggregator",
]
