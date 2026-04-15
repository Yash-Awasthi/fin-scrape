"""
Google SERP API scraper using serper.dev.

Rate-limited to 1 query per 20 minutes (max 3/hour).
NOT included in manual refresh — runs only on scheduled intervals.
Requires SERPER_API_KEY environment variable.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone

import requests

from finscrape.scrapers import BaseScraper
from finscrape.models import ScrapedArticle

logger = logging.getLogger(__name__)

SERPER_API_URL = "https://google.serper.dev/news"
RATE_LIMIT_SECONDS = 20 * 60  # 20 minutes between queries

# Module-level timestamp to enforce rate limiting across calls
_last_query_time: float = 0.0


class GoogleSerpScraper(BaseScraper):
    name = "google_serp"
    manual_refresh = False  # Excluded from manual refresh

    QUERIES = [
        "stock market financial news today",
        "earnings report breaking news",
        "merger acquisition deal news",
    ]

    def __init__(self, max_articles: int = 20, api_key: str | None = None):
        super().__init__(max_articles)
        self.api_key = api_key or os.environ.get("SERPER_API_KEY", "")

    def scrape_news(self) -> list[ScrapedArticle]:
        if not self.api_key:
            logger.warning("[%s] SERPER_API_KEY not set, skipping", self.name)
            return []

        global _last_query_time
        now = time.time()
        elapsed = now - _last_query_time

        if _last_query_time > 0 and elapsed < RATE_LIMIT_SECONDS:
            remaining = int(RATE_LIMIT_SECONDS - elapsed)
            logger.info(
                "[%s] Rate limited — %d seconds until next query allowed",
                self.name, remaining,
            )
            return []

        # Pick the next query (rotate through them)
        query_idx = int(now / RATE_LIMIT_SECONDS) % len(self.QUERIES)
        query = self.QUERIES[query_idx]

        logger.info("[%s] Querying SERP API: %s", self.name, query)
        _last_query_time = now

        try:
            resp = requests.post(
                SERPER_API_URL,
                json={"q": query, "num": min(self.max_articles, 20)},
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error("[%s] SERP API request failed: %s", self.name, e)
            return []

        news_results = data.get("news", [])
        if not news_results:
            logger.info("[%s] No news results from SERP API", self.name)
            return []

        articles = []
        for item in news_results[: self.max_articles]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            url = item.get("link", "")
            date_str = item.get("date", "")

            if not title or not url:
                continue

            # Try to parse the date from SERP results
            pub_date = None
            age_hours = None
            if date_str:
                try:
                    # serper.dev returns relative dates like "2 hours ago" or ISO dates
                    if "ago" in date_str.lower():
                        pub_date = datetime.now(timezone.utc).isoformat()
                    else:
                        pub_date = date_str
                except Exception:
                    pass

            tickers = self.extract_tickers_from_text(title + " " + snippet)

            # Try to fetch the full article for more text
            full_text = snippet
            page = self.fetch_page(url)
            if page:
                extracted = self.extract_article_text(page)
                if len(extracted) > len(snippet):
                    full_text = extracted
                # Better publish date from the article
                if not pub_date:
                    pub_date, age_hours = self.extract_publish_date(page)
                # More tickers from full text
                more_tickers = self.extract_tickers_from_text(full_text)
                tickers = list(set(tickers + more_tickers))

            articles.append(
                ScrapedArticle(
                    url=url,
                    title=title,
                    text=full_text,
                    source=self.name,
                    published_at=pub_date,
                    age_hours=age_hours,
                    raw_tickers=tickers,
                )
            )

        logger.info("[%s] Got %d articles from SERP API", self.name, len(articles))
        return articles
