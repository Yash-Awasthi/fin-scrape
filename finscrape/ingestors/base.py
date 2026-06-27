"""Base ingestor + the RawGeoEvent the pipeline consumes."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import requests

from finscrape.models import ScrapedArticle

logger = logging.getLogger(__name__)

_TIMEOUT = 20
_HEADERS = {
    "User-Agent": "finscrape-worldfin/0.1 (+https://github.com/Yash-Awasthi/fin-scrape)"
}


@dataclass
class RawGeoEvent:
    """A pre-analysis signal from a structured API. Carries geo when the source knows
    it (USGS), else lat/lon stay None and server.geocode derives them from text."""

    title: str
    text: str
    source: str
    event_type: str = "other"  # hint; the LLM may reclassify
    lat: float | None = None
    lon: float | None = None
    published_at: str | None = None
    url: str = ""
    tickers: list[str] = field(default_factory=list)

    def to_article(self) -> ScrapedArticle:
        """Adapt to the ScrapedArticle the analyze pipeline expects (geo carried
        separately by the worker, since ScrapedArticle has no geo field)."""
        return ScrapedArticle(
            url=self.url or f"ingestor://{self.source}",
            title=self.title,
            text=self.text or self.title,
            source=self.source,
            published_at=self.published_at,
            age_hours=0.0,  # API pulls are current
            raw_tickers=list(self.tickers),
        )


class BaseIngestor(ABC):
    name: str = "base"
    base_url: str = ""

    def fetch_raw(self, url: str | None = None, params: dict | None = None) -> Any:
        """GET + JSON. Returns None on any network/parse error (degrade, never crash)."""
        try:
            resp = requests.get(
                url or self.base_url, params=params, headers=_HEADERS, timeout=_TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("[ingestor/%s] fetch failed: %s", self.name, exc)
            return None

    @abstractmethod
    def parse(self, data: Any) -> list[RawGeoEvent]:
        """Pure: raw API payload → events. Unit-tested with fixtures, no network."""
        ...

    def fetch(self) -> list[RawGeoEvent]:
        data = self.fetch_raw()
        return self.parse(data) if data is not None else []
