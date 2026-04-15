"""
RSS feed scraper with full-text enrichment.

Handles Yahoo Finance RSS, CNBC RSS, and any generic financial RSS feed.
"""

from __future__ import annotations

import logging
from typing import Optional

import feedparser

from finscrape.scrapers import BaseScraper
from finscrape.models import ScrapedArticle

logger = logging.getLogger(__name__)


# Default financial RSS feeds
DEFAULT_FEEDS = {
    "yahoo_rss": "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
    "cnbc_rss": "https://www.cnbc.com/id/10000664/device/rss/rss.html",
    "marketwatch_rss": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "ft_rss": "https://www.ft.com/rss/home",
}


class RSSScraperSource(BaseScraper):
    name = "rss"

    def __init__(self, feeds: dict[str, str] | None = None, max_articles: int = 20):
        super().__init__(max_articles=max_articles)
        self.feeds = feeds or DEFAULT_FEEDS

    def scrape_news(self) -> list[ScrapedArticle]:
        articles = []

        for feed_name, feed_url in self.feeds.items():
            try:
                feed = feedparser.parse(feed_url)
                logger.info("[%s/%s] Parsed %d entries", self.name, feed_name, len(feed.entries))

                for entry in feed.entries[:self.max_articles]:
                    article = self._process_entry(entry, feed_name)
                    if article:
                        articles.append(article)
            except Exception as e:
                logger.warning("[%s/%s] Feed parse error: %s", self.name, feed_name, e)
                continue

        # Optionally fetch full article text for entries with URLs
        enriched = []
        for article in articles[:self.max_articles]:
            full = self._enrich_with_full_text(article)
            enriched.append(full)

        logger.info("[%s] Total articles from all feeds: %d", self.name, len(enriched))
        return enriched

    def _process_entry(self, entry: dict, feed_name: str) -> ScrapedArticle | None:
        title = entry.get("title", "").strip()
        url = entry.get("link", "").strip()
        summary = entry.get("summary", "").strip()
        published = entry.get("published", "")

        if not title or not url:
            return None

        tickers = self.extract_tickers_from_text(f"{title} {summary}")

        return ScrapedArticle(
            url=url,
            title=title,
            text=summary,
            source=f"{self.name}/{feed_name}",
            published_at=published if published else None,
            raw_tickers=tickers,
        )

    def _enrich_with_full_text(self, article: ScrapedArticle) -> ScrapedArticle:
        """Fetch full article text if the RSS summary is too short."""
        if len(article.text) >= 300:
            return article

        page = self.fetch_page(article.url)
        if not page:
            return article

        full_text = self.extract_article_text(page)
        if len(full_text) > len(article.text):
            article.text = full_text

        if not article.published_at:
            pub_date, age = self.extract_publish_date(page)
            article.published_at = pub_date
            article.age_hours = age

        return article
