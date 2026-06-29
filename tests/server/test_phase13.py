"""Phase 13 — sentiment / portfolio / telegram / prompt-A-B (no DB, no network).

Each route is mounted on a throwaway FastAPI app (like test_hardening) so we exercise
behaviour without the DB lifespan; network + Telegram sends are monkeypatched/no-op.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from finscrape.analysis import prompt_registry as pr  # noqa: E402
from server import cache  # noqa: E402
from server.routes import portfolio as portfolio_routes  # noqa: E402
from server.routes import sentiment as sentiment_routes  # noqa: E402
from server.routes import telegram as tg  # noqa: E402

AUTH = {"X-API-Key": "local-dev-key"}


# --- prompt A/B registry ----------------------------------------------------
def test_pick_variant_off_is_v1(monkeypatch):
    monkeypatch.delenv("WORLDFIN_PROMPT_AB", raising=False)
    assert pr.pick_variant("any headline") == "v1"


def test_pick_variant_ab_deterministic_and_prompts_resolve(monkeypatch):
    monkeypatch.setenv("WORLDFIN_PROMPT_AB", "true")
    a = pr.pick_variant("Apple beats earnings")
    assert a == pr.pick_variant("Apple beats earnings")  # stable
    assert a in pr.VARIANT_IDS
    for v in pr.VARIANT_IDS:
        system, analysis = pr.get_prompts(v)
        assert system and "{{title}}" in analysis


# --- sentiment route --------------------------------------------------------
def _sentiment_client() -> TestClient:
    app = FastAPI()
    app.include_router(sentiment_routes.router)
    cache.clear()
    return TestClient(app)


def test_sentiment_degrades_to_empty_on_error(monkeypatch):
    def boom(_ticker):
        raise RuntimeError("upstream down")

    monkeypatch.setattr(sentiment_routes, "_fetch", boom)
    r = _sentiment_client().get("/api/sentiment?ticker=aapl")
    assert r.status_code == 200
    body = r.json()
    assert body["ticker"] == "AAPL" and body["total_posts"] == 0


def test_sentiment_returns_fetch_result(monkeypatch):
    monkeypatch.setattr(
        sentiment_routes,
        "_fetch",
        lambda t: {"ticker": t, "total_posts": 5, "sentiment_score": 0.3},
    )
    r = _sentiment_client().get("/api/sentiment?ticker=tsla")
    assert r.json()["total_posts"] == 5 and r.json()["ticker"] == "TSLA"


# --- portfolio routes -------------------------------------------------------
def test_portfolio_crud(tmp_path):
    from finscrape.portfolio import PortfolioManager

    portfolio_routes._pm = PortfolioManager(db_path=tmp_path / "p.db")
    try:
        app = FastAPI()
        app.include_router(portfolio_routes.router)
        c = TestClient(app)

        assert c.post(
            "/api/portfolio/position",
            json={"ticker": "aapl", "shares": 10, "avg_cost": 150},
            headers=AUTH,
        ).json()["ok"]
        got = c.get("/api/portfolio").json()
        assert any(p["ticker"] == "AAPL" for p in got["positions"])

        assert c.post(
            "/api/portfolio/watchlist",
            json={"name": "tech", "tickers": ["msft"]},
            headers=AUTH,
        ).json()["ok"]
        assert any(
            w["name"] == "tech" for w in c.get("/api/portfolio").json()["watchlists"]
        )

        assert c.delete("/api/portfolio/position?ticker=AAPL", headers=AUTH).json()[
            "ok"
        ]
        # auth required on mutations
        assert (
            c.post("/api/portfolio/position", json={"ticker": "x"}).status_code == 401
        )
    finally:
        portfolio_routes._pm = None


# --- telegram webhook -------------------------------------------------------
def test_telegram_webhook_always_200_and_subscribes(tmp_path, monkeypatch):
    monkeypatch.setattr(tg, "_subs_path", lambda: tmp_path / "subs.json")
    app = FastAPI()
    app.include_router(tg.router)
    c = TestClient(app)
    r = c.post(
        "/api/telegram/webhook",
        json={"message": {"chat": {"id": 42}, "text": "/subscribe"}},
    )
    assert r.status_code == 200 and r.json() == {"ok": True}
    # background task ran during the client call → chat id recorded
    assert "42" in (tmp_path / "subs.json").read_text()


def test_telegram_notify_noop_without_token():
    # default settings carry no bot token → no sends, returns 0 (never raises)
    n = tg.notify_new_events(
        [{"verdict": "INVEST", "subject": "x", "tickers": ["AAPL"], "signal_score": 3}]
    )
    assert n == 0


def test_format_alert_shape():
    msg = tg.format_alert(
        {
            "verdict": "PULL_OUT",
            "signal_score": -3,
            "confidence": 0.8,
            "tickers": ["TSLA"],
            "subject": "recall",
        }
    )
    assert "PULL_OUT" in msg and "TSLA" in msg and "-3" in msg
