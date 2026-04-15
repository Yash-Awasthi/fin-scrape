"""
Base classes and data models for social sentiment analysis.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class SentimentPost:
    """A single social media post with sentiment-relevant data."""
    text: str
    author: str
    platform: str
    ticker_mentions: list[str] = field(default_factory=list)
    timestamp: datetime | None = None
    upvotes: int = 0
    likes: int = 0
    url: str = ""
    is_bot: bool = False


@dataclass
class SentimentResult:
    """Aggregated sentiment analysis for a ticker on a platform."""
    ticker: str
    platform: str
    bullish_count: int = 0
    bearish_count: int = 0
    neutral_count: int = 0
    total_posts: int = 0
    sentiment_score: float = 0.0  # -1.0 (bearish) to 1.0 (bullish)
    volume_spike: bool = False
    top_posts: list[SentimentPost] = field(default_factory=list)
    analyzed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def bullish_pct(self) -> float:
        """Percentage of posts that are bullish."""
        if self.total_posts == 0:
            return 0.0
        return self.bullish_count / self.total_posts


class BaseSentimentScraper(ABC):
    """Abstract base class for social sentiment scrapers."""

    name: str = "base"

    @abstractmethod
    def scrape(self, tickers: list[str]) -> list[SentimentResult]:
        """Scrape sentiment data for the given tickers.

        Args:
            tickers: List of ticker symbols to search for.

        Returns:
            List of SentimentResult, one per ticker per platform.
        """
        ...
