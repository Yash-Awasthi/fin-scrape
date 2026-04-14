"""
Base scraper class using Scrapling.

All source-specific scrapers inherit from BaseScraper and implement
the `scrape_news()` method.
"""

from __future__ import annotations

import logging
import re
import json
import datetime
from abc import ABC, abstractmethod
from typing import Optional

from scrapling.fetchers import Fetcher, StealthyFetcher, DynamicFetcher

from finscrape.models import ScrapedArticle

logger = logging.getLogger(__name__)

# Shared constants
MAX_WORDS = 700
MAX_PARAGRAPHS = 25
MIN_TEXT_LENGTH = 150
MAX_AGE_HOURS = 24


class BaseScraper(ABC):
    """Base class for all news scrapers."""

    name: str = "base"

    def __init__(self, max_articles: int = 20):
        self.max_articles = max_articles
        self._fetcher = Fetcher(auto_match=False)

    @abstractmethod
    def scrape_news(self) -> list[ScrapedArticle]:
        """Scrape and return a list of articles."""
        ...

    def fetch_page(self, url: str, stealthy: bool = False, dynamic: bool = False) -> Optional[object]:
        """Fetch a page using the appropriate Scrapling fetcher."""
        try:
            if dynamic:
                page = DynamicFetcher.fetch(url, headless=True, network_idle=True)
            elif stealthy:
                page = StealthyFetcher.fetch(url, headless=True)
            else:
                page = Fetcher.fetch(url, stealthy_headers=True)
            return page
        except Exception as e:
            logger.warning("[%s] Failed to fetch %s: %s", self.name, url, e)
            return None

    def extract_article_text(self, page, max_paragraphs: int = MAX_PARAGRAPHS) -> str:
        """Extract article text from a Scrapling page response."""
        article = page.css("article")
        if article:
            paragraphs = article[0].css("p")
        else:
            paragraphs = page.css("p")

        selected = []
        for p in paragraphs[:max_paragraphs]:
            text = p.text.strip() if p.text else ""
            if len(text) > 40:
                selected.append(text)

        text = " ".join(selected)

        # Remove junk
        for phrase in ["Continue reading", "Sign up", "Advertisement", "Read more", "Related stories"]:
            text = text.split(phrase)[0]

        words = text.split()[:MAX_WORDS]
        return " ".join(words)

    def extract_title(self, page) -> str:
        """Extract article title from meta tags or <title>."""
        # Try og:title first
        meta = page.css('meta[property="og:title"]')
        if meta:
            content = meta[0].attrib.get("content", "")
            if content:
                return re.sub(r'\s*[-|]\s*(Yahoo|Bloomberg|Reuters|CNBC).*$', '', content).strip()

        # Fallback to <title>
        title_tag = page.css("title")
        if title_tag:
            text = title_tag[0].text or ""
            return re.sub(r'\s*[-|]\s*(Yahoo|Bloomberg|Reuters|CNBC).*$', '', text).strip()

        return ""

    def extract_publish_date(self, page) -> tuple[Optional[str], Optional[float]]:
        """Extract publication date and calculate age in hours."""
        pub_str = None

        # meta tag
        meta = page.css('meta[property="article:published_time"]')
        if meta:
            pub_str = meta[0].attrib.get("content")

        # JSON-LD fallback
        if not pub_str:
            for script in page.css('script[type="application/ld+json"]'):
                try:
                    text = script.text
                    if not text:
                        continue
                    data = json.loads(text)
                    if isinstance(data, list):
                        data = data[0]
                    if isinstance(data, dict):
                        pub_str = data.get("datePublished")
                    if pub_str:
                        break
                except Exception:
                    pass

        if not pub_str:
            return None, None

        try:
            dt = datetime.datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
            age_hours = (datetime.datetime.now(datetime.timezone.utc) - dt).total_seconds() / 3600
            return pub_str, round(age_hours, 1)
        except Exception:
            return pub_str, None

    @staticmethod
    def extract_tickers_from_text(text: str) -> list[str]:
        """Extract ticker symbols from text using regex patterns."""
        from finscrape.analysis.constants import TICKER_STOPWORDS

        tickers = set()

        # (TICKER) pattern
        tickers.update(re.findall(r'\(([A-Z]{2,5})\)', text))
        # $TICKER pattern
        tickers.update(re.findall(r'\$([A-Z]{2,5})\b', text))
        # Futures
        tickers.update(re.findall(r'\b([A-Z]{1,2}=F)\b', text))
        # Indexes
        tickers.update(re.findall(r'(\^[A-Z]{2,5})\b', text))

        return [t for t in tickers if t not in TICKER_STOPWORDS and 2 <= len(t) <= 5]
