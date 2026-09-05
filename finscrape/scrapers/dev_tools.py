"""Dev-mode news fetch providers — external scraping/search tools by API key.

Each scraper reads its key from the dev-mode registry (secrets/dev_tools.json,
class `news_fetch`) or a direct env var, and degrades to an empty result with
a clear message when no key is configured — never crashes the pipeline.

    FirecrawlNewsScraper  — firecrawl.dev /v1/search (news query → markdown pages)
    SerpNewsScraper       — serpapi.com Google News (structured news results)

Both emit plain ScrapedArticles, so they slot into AVAILABLE_SCRAPERS like any
builtin source: `main.py scrape --sources firecrawl --max-articles 8`.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
import urllib.request
from datetime import UTC, datetime

from finscrape.devmode import get_provider
from finscrape.models import ScrapedArticle

logger = logging.getLogger(__name__)

_QUERY = "stock market financial news"
_UA = {"User-Agent": "finscrape-dev-mode/1.0"}


def _json_request(url: str, payload: dict | None = None, api_key: str = "") -> dict | None:
    try:
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, headers={**_UA, "Content-Type": "application/json"},
                                     method="POST" if data else "GET")
        if api_key:
            req.add_header("Authorization", f"Bearer {api_key}")
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, OSError, ValueError) as e:
        logger.warning("dev-mode fetch failed: %s", e)
        return None


def _age_hours(iso_or_ts: str | None) -> float | None:
    if not iso_or_ts:
        return None
    try:
        published = datetime.fromisoformat(str(iso_or_ts))
        if published.tzinfo is None:
            published = published.replace(tzinfo=UTC)
        return max(0.0, (datetime.now(UTC) - published).total_seconds() / 3600)
    except ValueError:
        return None


class FirecrawlNewsScraper:
    """News search via firecrawl.dev (dev-mode class: news_fetch / firecrawl)."""

    name = "firecrawl"

    def __init__(self, max_articles: int = 10):
        self.max_articles = max_articles

    def _api_key(self) -> str:
        fields = get_provider("news_fetch", "firecrawl") or {}
        return str(fields.get("api_key") or os.getenv("FIRECRAWL_API_KEY", ""))

    def scrape_news(self) -> list[ScrapedArticle]:
        key = self._api_key()
        if not key:
            logger.warning(
                "[firecrawl] no API key — run: main.py devtools set news_fetch firecrawl --field api_key=..."
            )
            return []
        base = (get_provider("news_fetch", "firecrawl") or {}).get("base_url", "https://api.firecrawl.dev")
        data = _json_request(
            f"{base.rstrip('/')}/v1/search",
            {"query": _QUERY, "limit": self.max_articles, "scrapeOptions": {"formats": ["markdown"]}},
            api_key=key,
        )
        articles: list[ScrapedArticle] = []
        for item in (data or {}).get("data", [])[: self.max_articles]:
            metadata = item.get("metadata") or {}
            title = metadata.get("title") or item.get("title") or ""
            text = (item.get("markdown") or "")[:8000]
            if not title or not text:
                continue
            articles.append(ScrapedArticle(
                url=item.get("url") or metadata.get("sourceURL") or "",
                title=title,
                text=text,
                source="firecrawl",
                published_at=metadata.get("publishedTime"),
                age_hours=_age_hours(metadata.get("publishedTime")),
            ))
        return articles


class SerpNewsScraper:
    """Google News via serpapi.com (dev-mode class: news_fetch / serpapi)."""

    name = "serp"

    def __init__(self, max_articles: int = 10):
        self.max_articles = max_articles

    def _api_key(self) -> str:
        fields = get_provider("news_fetch", "serpapi") or {}
        return str(fields.get("api_key") or os.getenv("SERPAPI_API_KEY", ""))

    def scrape_news(self) -> list[ScrapedArticle]:
        key = self._api_key()
        if not key:
            logger.warning(
                "[serp] no API key — run: main.py devtools set news_fetch serpapi --field api_key=..."
            )
            return []
        params = urllib.parse.urlencode({
            "engine": "google_news", "q": _QUERY, "api_key": key,
        })
        data = _json_request(f"https://serpapi.com/search.json?{params}")
        articles: list[ScrapedArticle] = []
        for item in (data or {}).get("news_results", [])[: self.max_articles]:
            title = item.get("title") or ""
            url = item.get("link") or ""
            if not title or not url:
                continue
            # serpapi returns a snippet sometimes; headline itself is content-ful
            text = item.get("snippet") or title
            articles.append(ScrapedArticle(
                url=url,
                title=title,
                text=text,
                source="serp",
                published_at=item.get("date"),
                age_hours=_age_hours(item.get("date")),
            ))
        return articles
