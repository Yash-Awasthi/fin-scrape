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


# --- realtime feed --------------------------------------------------------------
def test_websocket_is_mounted_where_the_spa_connects():
    """The SPA builds ws://host/api/ws (see web/src/ws.ts wsUrl). Mounted at /ws the
    handshake answered 403 and the live feed never connected on localhost at all."""
    paths = {getattr(r, "path", None) for r in app.routes}
    assert "/api/ws" in paths
    assert "/ws" not in paths


@requires_db
def test_websocket_sends_a_snapshot_and_answers_a_json_ping():
    """The client sends JSON ({"type":"ping"}); comparing the raw frame to "ping"
    never matched, so the keep-alive silently did nothing."""
    import json

    with client.websocket_connect("/api/ws") as ws:
        init = ws.receive_json()
        assert init["type"] == "init"
        assert isinstance(init["events"], list)
        ws.send_text(json.dumps({"type": "ping"}))
        assert ws.receive_json()["type"] == "pong"


@requires_db
def test_a_bare_ping_still_answers():
    with client.websocket_connect("/api/ws") as ws:
        ws.receive_json()  # init
        ws.send_text("ping")
        assert ws.receive_json()["type"] == "pong"


def test_push_new_events_sends_only_rows_after_the_last_seen_id(monkeypatch, tmp_path):
    """The scraper is a separate process, so the database is the broadcast channel:
    each client polls for ids past the snapshot it already has."""
    import asyncio
    import sqlite3

    from finscrape import serve

    db = tmp_path / "t.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, subject TEXT,"
        " event_type TEXT, tickers TEXT, sources TEXT, articles TEXT, verdict TEXT,"
        " signal_score INTEGER, confidence REAL, created_at TEXT)"
    )
    for subj in ("already seen", "brand new"):
        conn.execute(
            "INSERT INTO events (subject, event_type, tickers, sources, articles,"
            " verdict, signal_score, confidence, created_at)"
            " VALUES (?,'other','[]','[]','[]','OBSERVE',0,0.5,'2026-01-01')",
            (subj,),
        )
    conn.commit()
    conn.close()

    monkeypatch.setattr(serve, "_DB", db)
    monkeypatch.setattr(serve, "_WS_POLL_S", 0)

    sent = []

    class FakeWS:
        async def send_json(self, payload):
            sent.append(payload)
            raise RuntimeError("stop after the first push")

    async def run():
        with __import__("contextlib").suppress(RuntimeError):
            await serve._push_new_events(FakeWS(), after_id=1)  # id 1 already seen

    asyncio.run(run())
    assert len(sent) == 1
    assert sent[0]["type"] == "new_events"
    assert [e["subject"] for e in sent[0]["events"]] == ["brand new"]
