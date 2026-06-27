"""Source registry for the worker.

Each source is a name -> producer() returning a list of (ScrapedArticle, (lat, lon)).
World RSS has no per-item geo (server.geocode derives it from text); structured
ingestors carry exact coords. Producers do network I/O and are called inside a thread.
"""

from __future__ import annotations

from collections.abc import Callable

from finscrape.ingestors import EVENT_INGESTORS
from finscrape.models import ScrapedArticle
from finscrape.scrapers.world import WorldRSSScraper

Item = tuple[ScrapedArticle, tuple[float | None, float | None]]
Producer = Callable[[], list[Item]]


def _world_rss_producer(max_articles: int) -> Producer:
    def produce() -> list[Item]:
        articles = WorldRSSScraper(max_articles=max_articles).scrape_news()
        return [(a, (None, None)) for a in articles]

    return produce


def _ingestor_producer(cls) -> Producer:
    def produce() -> list[Item]:
        out: list[Item] = []
        for e in cls().fetch():
            out.append((e.to_article(), (e.lat, e.lon)))
        return out

    return produce


def build_sources(max_articles: int = 20) -> dict[str, Producer]:
    sources: dict[str, Producer] = {"world_rss": _world_rss_producer(max_articles)}
    for cls in EVENT_INGESTORS:
        sources[cls.name] = _ingestor_producer(cls)
    return sources
