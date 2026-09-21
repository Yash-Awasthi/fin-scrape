"""Local serve app: same API contract the SPA expects, backed by SQLite.

`data/finscrape.db` is gitignored, so the data-backed routes 503 on a fresh checkout.
Those tests auto-skip the same way the Postgres integration tests do, leaving the
contract tests (shape, freshness derivation, degraded states) running everywhere.
"""

import pytest
from fastapi.testclient import TestClient

from finscrape.serve import _DB, app

client = TestClient(app)

requires_db = pytest.mark.skipif(
    not _DB.exists(), reason=f"no local SQLite DB at {_DB} — run: main.py scrape"
)


def test_health_reports_local_mode():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "local"
    # status tracks the database, so this must not assert "ok" outright — a checkout
    # with no data/finscrape.db is a legitimate degraded state, not a failure.
    assert body["status"] == ("ok" if body["db"] else "degraded")


def test_quotes_shape():
    r = client.get("/api/quotes", params={"symbols": "AAPL"})
    assert r.status_code == 200
    quotes = r.json()["quotes"]
    assert isinstance(quotes, list)
    for q in quotes:
        assert {"symbol", "price", "change_pct", "source"} <= set(q)


@requires_db
def test_stats_shape_when_db_present():
    r = client.get("/api/stats")
    assert r.status_code == 200
    body = r.json()
    assert {"total_events", "by_verdict", "last_update"} <= set(body)


@requires_db
def test_suggestions_shape():
    r = client.get("/api/suggestions", params={"limit": 3})
    assert r.status_code == 200
    for s in r.json()["suggestions"]:
        assert {"ticker", "score", "mentions"} <= set(s)


@requires_db
def test_sectors_shape():
    r = client.get("/api/sectors")
    assert r.status_code == 200
    sectors = r.json()["sectors"]
    # current local DB has events, so the sector heat must not be empty
    assert sectors
    for s in sectors:
        assert {
            "sector",
            "event_count",
            "avg_score",
            "bull_bear_ratio",
            "top_tickers",
            "last_event",
        } <= set(s)
        assert s["event_count"] >= 1
        assert isinstance(s["top_tickers"], list)
        assert isinstance(s["sector"], str) and s["sector"]


@requires_db
def test_events_carry_detected_sector():
    r = client.get("/api/events", params={"limit": 20})
    assert r.status_code == 200
    for e in r.json()["events"]:
        assert "sector" in e
        assert isinstance(e["sector"], str)


def test_health_reports_per_source_freshness():
    """The Source Health panel reads /api/health on both servers; the local one used to
    hardcode an empty source list, so the panel was permanently blank on localhost."""
    body = client.get("/api/health").json()
    assert isinstance(body["sources"], list)
    for src in body["sources"]:
        assert set(src) == {"source", "status", "fetched_at", "record_count"}
        assert src["status"] in ("OK", "STALE")
        assert src["record_count"] >= 1


def test_health_llm_flag_follows_the_environment(monkeypatch):
    """It was hardcoded True, which told the UI a model was ready when none was set."""
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    assert client.get("/api/health").json()["llm"] is False
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    assert client.get("/api/health").json()["llm"] is True


def test_local_source_health_survives_malformed_rows():
    """`sources` is stored as a JSON string; a corrupt row must not 500 the endpoint."""
    import sqlite3

    from finscrape.serve import _local_source_health

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE events (sources TEXT, created_at TEXT)")
    conn.executemany(
        "INSERT INTO events (sources, created_at) VALUES (?, ?)",
        [
            ('["world_rss"]', "2999-01-01T00:00:00+00:00"),
            ("not json", "2999-01-01T00:00:00+00:00"),
            ('["world_rss"]', "2999-01-02T00:00:00+00:00"),
            ('[""]', "2999-01-01T00:00:00+00:00"),
        ],
    )
    rows = _local_source_health(conn)
    assert [r["source"] for r in rows] == ["world_rss"]
    assert rows[0]["record_count"] == 2
    assert rows[0]["fetched_at"] == "2999-01-02T00:00:00+00:00"
