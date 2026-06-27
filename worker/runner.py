"""One ingestion cycle per source: scrape → analyze → geocode → ingest → health.

Blocking finscrape work (scrape_news / ingestor.fetch / _analyze_article, which calls
the LLM and market data) runs via asyncio.to_thread; only the DB writes touch the loop.
A source that throws degrades to WARN and is recorded — it never crashes the worker.
"""

from __future__ import annotations

import asyncio
import logging

import asyncpg

from finscrape.pipeline import FinScrapePipeline
from server.correlate import NewsItem, analyze_correlations
from server.geocode import geocode_event
from server.ingest import ingest_events
from server.settings import get_settings
from worker.health import (
    finish_scrape_run,
    record_source_health,
    start_scrape_run,
)
from worker.sources import Item, build_sources

log = logging.getLogger("worldfin.worker")

_TIERS = {"wire", "gov", "intel", "mainstream", "market", "tech", "other"}


async def persist_correlations(pool: asyncpg.Pool, signals: list) -> None:
    """Write correlation signals to the correlations table (one row each)."""
    for sig in signals:
        await pool.execute(
            "INSERT INTO correlations (dedupe_key, signal_type, confidence, payload) "
            "VALUES ($1, $2, $3, $4)",
            sig.dedupe_key,
            sig.type,
            sig.confidence,
            {"id": sig.id, "value": sig.value, **sig.payload},
        )


def _source_type(source: str) -> str:
    """Tier is encoded as the suffix after ':' in our source tags (world/<feed>:<tier>,
    gdelt/<domain>:wire, usgs_quakes:gov, …)."""
    tail = (source or "").rsplit(":", 1)[-1]
    return tail if tail in _TIERS else "other"


class Worker:
    def __init__(self, pool: asyncpg.Pool, max_articles: int = 20):
        self.pool = pool
        self.sources = build_sources(max_articles)
        # Reuse the fusion brain; disable side-effects the worker doesn't own.
        self.pipeline = FinScrapePipeline(
            sources=[],
            enable_alerts=False,
            enable_accuracy=False,
            enable_portfolio=False,
        )
        # Correlation state persists across cycles (first cycle emits nothing).
        self._corr_snapshot: dict | None = None
        self._corr_seen: set[str] = set()

    def _analyze_blocking(self, source_name: str, items: list[Item]) -> list[dict]:
        """Thread body: articles -> ingest dicts (FinEvent.to_dict() + geo)."""
        dicts: list[dict] = []
        for article, geo in items:
            try:
                fe = self.pipeline._analyze_article(source_name, article)
            except Exception as exc:
                log.warning("[%s] analyze failed: %s", source_name, exc)
                continue
            if fe is None:
                continue
            d = fe.to_dict()
            lat, lon = geocode_event(
                fe.subject, fe.affected_entities, explicit_latlon=geo
            )
            d["lat"], d["lon"] = lat, lon
            dicts.append(d)
        return dicts

    async def run_source(self, name: str) -> dict:
        """Run one source end to end. Returns the ingest result (or zeros on failure)."""
        run_id = await start_scrape_run(self.pool, name)
        try:
            items = await asyncio.to_thread(self.sources[name])
            dicts = await asyncio.to_thread(self._analyze_blocking, name, items)
            result = await ingest_events(self.pool, dicts)
            status = "OK" if items else "EMPTY"
            await record_source_health(self.pool, name, len(items), status)
            await finish_scrape_run(self.pool, run_id, "ok", result["inserted"])
            log.info(
                "[%s] %d fetched, %d inserted, %d dup",
                name,
                len(items),
                result["inserted"],
                result["duplicates"],
            )
            return result
        except Exception as exc:
            log.exception("[%s] cycle failed", name)
            await record_source_health(self.pool, name, 0, "WARN", str(exc))
            await finish_scrape_run(self.pool, run_id, "failed", 0)
            return {
                "inserted": 0,
                "duplicates": 0,
                "inserted_ids": [],
                "inserted_rows": [],
            }

    async def run_all_once(self) -> None:
        """Run every source once concurrently (startup warm-up), then correlate."""
        await asyncio.gather(
            *(self.run_source(n) for n in self.sources), return_exceptions=True
        )
        await self.run_correlations()

    async def run_correlations(self, lookback_hours: int = 24) -> int:
        """Cluster recent events + flag corroboration/divergence; persist signals.
        First call seeds the snapshot and emits nothing (Appendix A). Returns count."""
        if not get_settings().enable_correlation:
            return 0
        rows = await self.pool.fetch(
            "SELECT subject, sources, articles, timestamp, lat, lon FROM events "
            "WHERE timestamp >= now() - ($1 || ' hours')::interval",
            str(lookback_hours),
        )
        items = [
            NewsItem(
                title=r["subject"],
                link=(r["articles"][0] if r["articles"] else r["subject"]),
                source=(r["sources"][0] if r["sources"] else ""),
                source_type=_source_type(r["sources"][0] if r["sources"] else ""),
                lat=r["lat"],
                lon=r["lon"],
                timestamp=r["timestamp"].timestamp(),
            )
            for r in rows
        ]
        signals, snapshot = analyze_correlations(
            items, prev_snapshot=self._corr_snapshot, seen=self._corr_seen
        )
        self._corr_snapshot = snapshot
        await persist_correlations(self.pool, signals)
        if signals:
            log.info("correlations: emitted %d signals", len(signals))
        return len(signals)
