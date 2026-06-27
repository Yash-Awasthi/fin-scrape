"""Docker-free Phase 0 self-check.

Validates the things that don't need a live Postgres: the migration SQL is
well-formed and complete, typed settings load with defaults, and the public
schemas validate a real finscrape FinEvent dict. Run standalone:

    python -m tests.server.selfcheck      # or: make selfcheck

SQL/structure checks use stdlib only and always run. Settings/schema checks need
the `server` dep group (pydantic); they're skipped with a notice if it's missing.
"""

from __future__ import annotations

import sys
from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2] / "server" / "migrations" / "0001_init.sql"
)

REQUIRED_TABLES = [
    "events",
    "correlations",
    "scrape_runs",
    "source_health",
    "accuracy_outcomes",
    "ai_analysis_cache",
]


def check_migration_sql() -> None:
    sql = MIGRATION.read_text()
    low = sql.lower()

    for table in REQUIRED_TABLES:
        assert f"create table if not exists {table}" in low, f"missing table: {table}"

    # the dedup linchpin (Appendix B): content_hash must be UNIQUE
    assert "content_hash" in low and "unique" in low, (
        "events.content_hash UNIQUE missing"
    )
    # JSONB tickers need a GIN index for membership queries
    assert "using gin (tickers)" in low, "GIN index on events.tickers missing"
    # time discipline: TIMESTAMPTZ, not naive timestamps
    assert "timestamptz" in low, "expected TIMESTAMPTZ columns"
    # guard against the BIGGENERATED typo class
    assert "biggenerated" not in low, "typo: BIGGENERATED (want BIGINT GENERATED)"
    # cheap balance check on code only (strip -- comments so prose parens don't fool it)
    code = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    assert code.count("(") == code.count(")"), "unbalanced parentheses in migration SQL"
    print(
        f"  ok  migration SQL: {len(REQUIRED_TABLES)} tables, UNIQUE+GIN+TIMESTAMPTZ present"
    )


def check_settings() -> bool:
    try:
        from server.settings import Settings
    except ImportError as exc:
        print(f"  skip settings/schema checks — server deps not installed ({exc})")
        return False
    s = Settings(_env_file=None)  # ignore any local .env for a clean default check
    assert s.database_url.startswith("postgresql://"), "default DATABASE_URL malformed"
    assert s.db_pool_max >= s.db_pool_min, "pool max < min"
    assert s.has_llm is False, "has_llm should be False with no LLM env set"
    assert s.redis_enabled is False, "redis_enabled should be False by default"
    print("  ok  settings load with sane defaults")
    return True


def check_schemas() -> None:
    from datetime import datetime, timezone

    from finscrape.models import FinEvent
    from server.schemas import EventIn, EventOut, IngestResponse

    fe = FinEvent(
        subject="Hormuz tanker incident disrupts oil shipping",
        event_type="geopolitical_event",
        tickers=["XOM", "CVX"],
        impact_direction="positive",
        signal_score=3,
        confidence=0.72,
        verdict="INVEST",
    )
    ev = EventIn.model_validate(fe.to_dict())  # ingest accepts a FinEvent dict verbatim
    assert ev.tickers == ["XOM", "CVX"]
    assert ev.event_type == "geopolitical_event"

    out = EventOut(id=1, created_at=datetime.now(timezone.utc), **ev.model_dump())
    assert out.id == 1

    resp = IngestResponse(inserted=1, duplicates=0, inserted_ids=[1])
    assert resp.ok and resp.inserted == 1
    print("  ok  schemas validate a real FinEvent + ingest response")


def main() -> int:
    print("WorldFin Phase 0 self-check:")
    check_migration_sql()
    if check_settings():
        check_schemas()
    print("self-check PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
