"""Worker entrypoint: `python -m worker.main`.

AsyncIOScheduler runs one interval job per source (staggered + jittered so they don't
all hammer the network at once). max_instances=1 + coalesce so a slow cycle never
stacks. Runs every source once at startup so the dashboard fills immediately.
"""

from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from prometheus_client import start_http_server

from finscrape.logging_config import setup_logging
from server import db
from server.settings import get_settings
from worker.runner import Worker

log = logging.getLogger("worldfin.worker.main")


async def main() -> None:
    s = get_settings()
    setup_logging(level=s.log_level, json_format=s.log_json)
    if s.metrics_port:
        start_http_server(s.metrics_port)
        log.info("worker metrics on :%d/metrics", s.metrics_port)
    pool = await db.connect(
        s.database_url, min_size=s.db_pool_min, max_size=s.db_pool_max
    )
    await db.run_migrations(pool)

    worker = Worker(pool, max_articles=s.worker_max_articles)
    scheduler = AsyncIOScheduler()

    for name in worker.sources:
        scheduler.add_job(
            worker.run_source,
            "interval",
            minutes=s.worker_interval_minutes,
            args=[name],
            id=name,
            jitter=60,
            max_instances=1,
            coalesce=True,
        )
    if s.enable_correlation:
        # correlate slightly after sources so it sees the freshest ingest
        scheduler.add_job(
            worker.run_correlations,
            "interval",
            minutes=s.worker_interval_minutes,
            id="correlations",
            jitter=30,
            max_instances=1,
            coalesce=True,
        )
    scheduler.start()
    log.info(
        "worker started: %d sources every %d min",
        len(worker.sources),
        s.worker_interval_minutes,
    )

    await worker.run_all_once()  # warm-up

    try:
        await asyncio.Event().wait()  # run forever
    finally:
        scheduler.shutdown(wait=False)
        await db.disconnect()


async def run_once() -> None:
    """One ingestion cycle (every source + correlate + backtest) then exit. Drives the
    free no-host deploy: a scheduled GitHub Action calls `python -m worker.main --once`
    against Neon instead of an always-on worker process."""
    s = get_settings()
    setup_logging(level=s.log_level, json_format=s.log_json)
    pool = await db.connect(
        s.database_url, min_size=s.db_pool_min, max_size=s.db_pool_max
    )
    await db.run_migrations(pool)
    worker = Worker(pool, max_articles=s.worker_max_articles)
    await worker.run_all_once()  # all sources once + correlate
    try:
        wrote = await worker.run_backtest()
        log.info("one-shot backtest scored %d outcomes", wrote)
    except Exception as exc:  # pragma: no cover - market data flaky
        log.warning("one-shot backtest skipped: %s", exc)
    await db.disconnect()


if __name__ == "__main__":
    import sys

    asyncio.run(run_once() if "--once" in sys.argv else main())
