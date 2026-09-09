"""Local serve app: same API contract the SPA expects, backed by SQLite."""

from fastapi.testclient import TestClient

from finscrape.serve import app

client = TestClient(app)


def test_health_reports_local_mode():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "local"
    assert body["status"] == "ok"


def test_quotes_shape():
    r = client.get("/api/quotes", params={"symbols": "AAPL"})
    assert r.status_code == 200
    quotes = r.json()["quotes"]
    assert isinstance(quotes, list)
    for q in quotes:
        assert {"symbol", "price", "change_pct", "source"} <= set(q)


def test_stats_shape_when_db_present():
    r = client.get("/api/stats")
    assert r.status_code == 200
    body = r.json()
    assert {"total_events", "by_verdict", "last_update"} <= set(body)


def test_suggestions_shape():
    r = client.get("/api/suggestions", params={"limit": 3})
    assert r.status_code == 200
    for s in r.json()["suggestions"]:
        assert {"ticker", "score", "mentions"} <= set(s)


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


def test_events_carry_detected_sector():
    r = client.get("/api/events", params={"limit": 20})
    assert r.status_code == 200
    for e in r.json()["events"]:
        assert "sector" in e
        assert isinstance(e["sector"], str)
