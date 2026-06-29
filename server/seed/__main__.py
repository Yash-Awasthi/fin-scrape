"""`python -m server.seed` — connect, ensure schema, load the curated demo dataset."""

from __future__ import annotations

import asyncio

from server import db
from server.seed.loader import seed
from server.settings import get_settings


async def _main() -> None:
    settings = get_settings()
    pool = await db.connect(settings.database_url)
    await db.run_migrations(pool)
    summary = await seed(pool)
    print(
        "seed complete — "
        f"events +{summary['events_inserted']} "
        f"({summary['events_duplicate']} already present), "
        f"accuracy_outcomes +{summary['accuracy_outcomes']}, "
        f"correlations {summary['correlations']}"
    )
    await db.disconnect()


if __name__ == "__main__":
    asyncio.run(_main())
