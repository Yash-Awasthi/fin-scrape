"""World / geopolitics scraping — thin layer over the existing RSS scraper.

Reuses RSSScraperSource verbatim for fetching/enrichment; the only differences are
(1) the feed set comes from the world registry and (2) a wider freshness window —
geopolitics stories stay relevant far longer than the 2h finance default, so we don't
want the env-driven `is_fresh` gate dropping them.
"""

from __future__ import annotations

import calendar
import datetime as _dt
import logging

from finscrape.models import ScrapedArticle
from finscrape.scrapers.rss import RSSScraperSource
from finscrape.scrapers.world.feeds import FEEDS, feed_urls, tier_of

logger = logging.getLogger(__name__)


class WorldRSSScraper(RSSScraperSource):
    name = "world"

    def __init__(self, max_articles: int = 20, max_age_hours: float = 24.0):
        super().__init__(feeds=feed_urls(), max_articles=max_articles)
        self.max_age_hours = max_age_hours

    def _process_entry(self, entry: dict, feed_name: str) -> ScrapedArticle | None:
        """Like the base, but uses an instance freshness window (not the env gate) and
        tags the source as `world/<feed>:<tier>` so trust scoring can read the tier."""
        title = (entry.get("title") or "").strip()
        url = (entry.get("link") or "").strip()
        summary = (entry.get("summary") or "").strip()
        if not title or not url:
            return None

        age_hours: float | None = None
        parsed_time = entry.get("published_parsed")
        if parsed_time:
            dt = _dt.datetime.fromtimestamp(
                calendar.timegm(parsed_time), tz=_dt.timezone.utc
            )
            age_hours = round(
                (_dt.datetime.now(_dt.timezone.utc) - dt).total_seconds() / 3600, 1
            )
            if age_hours > self.max_age_hours:
                return None

        return ScrapedArticle(
            url=url,
            title=title,
            text=summary,
            source=f"{self.name}/{feed_name}:{tier_of(feed_name)}",
            published_at=entry.get("published") or None,
            age_hours=age_hours,
            raw_tickers=self.extract_tickers_from_text(f"{title} {summary}"),
        )


__all__ = ["WorldRSSScraper", "FEEDS"]
