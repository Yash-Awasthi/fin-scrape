"""Phase 3 DB integration: source_health + scrape_runs round-trip (skip-ready).

Auto-skips without Postgres; runs under `make up` / CI. Verifies the freshness model:
a healthy source reads OK, then reads STALE once its fetch ages past the window.
"""

from __future__ import annotations

import asyncio

import pytest

asyncpg = pytest.importorskip("asyncpg")

from tests.server import fresh_pool, pg_reachable  # noqa: E402

pytestmark = pytest.mark.skipif(
    not pg_reachable(), reason="no Postgres at WORLDFIN_DATABASE_URL (start `make up`)"
)


def test_source_health_ok_then_stale():
    from server import db
    from worker.health import aggregate_health, record_source_health

    async def body():
        pool = await fresh_pool("source_health")
        await record_source_health(pool, "world_rss", 7, "OK")

        rows = {
            r["source"]: r for r in await aggregate_health(pool, stale_after_min=60)
        }
        assert rows["world_rss"]["status"] == "OK"
        assert rows["world_rss"]["record_count"] == 7

        # age the fetch beyond the window → derived STALE (no writer touched it)
        await pool.execute(
            "UPDATE source_health SET fetched_at = now() - interval '2 hours' WHERE source = 'world_rss'"
        )
        rows = {
            r["source"]: r for r in await aggregate_health(pool, stale_after_min=60)
        }
        assert rows["world_rss"]["status"] == "STALE"
        await db.disconnect()

    asyncio.run(body())


def test_scrape_run_lifecycle():
    from server import db
    from worker.health import finish_scrape_run, start_scrape_run

    async def body():
        pool = await fresh_pool("scrape_runs")
        run_id = await start_scrape_run(pool, "gdelt")
        assert run_id is not None
        await finish_scrape_run(pool, run_id, "ok", 3)
        row = await pool.fetchrow(
            "SELECT status, events_ingested FROM scrape_runs WHERE id = $1", run_id
        )
        assert row["status"] == "ok" and row["events_ingested"] == 3
        await db.disconnect()

    asyncio.run(body())
