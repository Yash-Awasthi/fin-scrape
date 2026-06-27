"""Shared helpers for server/worker DB integration tests.

Integration tests skip cleanly when no Postgres is reachable at WORLDFIN_DATABASE_URL,
so the suite stays green without docker and runs automatically under `make up` / CI.
"""

from __future__ import annotations

import asyncio
import os

PG_DSN = os.getenv(
    "WORLDFIN_DATABASE_URL", "postgresql://worldfin:worldfin@localhost:5432/worldfin"
)


def pg_reachable() -> bool:
    import asyncpg

    async def _check() -> bool:
        try:
            conn = await asyncio.wait_for(asyncpg.connect(PG_DSN), timeout=2)
        except (OSError, asyncpg.PostgresError, asyncio.TimeoutError):
            return False
        await conn.close()
        return True

    return asyncio.run(_check())


async def fresh_pool(*truncate):
    """Connect, apply migrations, and TRUNCATE the named tables for a clean slate."""
    from server import db

    await db.disconnect()
    pool = await db.connect(PG_DSN)
    await db.run_migrations(pool)
    for table in truncate:
        await pool.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")
    return pool
