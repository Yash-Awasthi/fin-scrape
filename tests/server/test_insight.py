"""Production insight routes (predict/reliability) against a fake Postgres pool."""

from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("asyncpg")

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from server.routes import insight  # noqa: E402


class FakeRow(dict):
    """asyncpg Record stand-in: dict with key access."""

    def __getitem__(self, key):
        return dict.__getitem__(self, key)


class FakePool:
    def __init__(self, rows: list[dict], outcome_rows: list[dict]):
        self._rows = [FakeRow(r) for r in rows]
        self._outcomes = [FakeRow(r) for r in outcome_rows]

    async def fetchrow(self, _query, *args):
        for row in self._rows:
            if row["id"] == args[0]:
                return row
        return None

    async def fetch(self, _query, *args):
        return self._outcomes


@pytest.fixture()
def client(monkeypatch):
    now = datetime.now(timezone.utc)
    event_rows = [{
        "id": 7, "subject": "nvda earnings beat", "verdict": "INVEST",
        "signal_score": 4, "confidence": 0.8, "event_type": "earnings",
        "sources": json.dumps(["cnbc", "rss"]), "tickers": json.dumps(["NVDA"]),
        "reasoning": "strong data center demand",
    }]
    outcome_rows = [
        {"verdict": "INVEST", "correct": True, "checked_at": now,
         "confidence": 0.8, "event_type": "earnings", "sources": json.dumps(["cnbc"])},
        {"verdict": "INVEST", "correct": True, "checked_at": now,
         "confidence": 0.7, "event_type": "earnings", "sources": json.dumps(["rss"])},
    ]
    fake = FakePool(event_rows, outcome_rows)
    monkeypatch.setattr(insight.db, "pool", lambda: fake)

    app = FastAPI()
    app.include_router(insight.router)
    return TestClient(app)


def test_reliability_from_outcomes(client):
    body = client.get("/api/reliability").json()
    rel = body["reliability"]
    assert rel["sample_size"] == 2
    assert rel["by_verdict"]["INVEST"]["hit_rate"] == 1.0
    assert rel["by_source"]["cnbc"]["hit_rate"] == 1.0


def test_predict_event_attaches_evidence(client):
    body = client.get("/api/predict/7").json()
    assert body["event"]["id"] == 7
    assert body["event"]["ticker"] == "NVDA"
    assert 0 <= body["p_verdict_correct"] <= 1
    assert body["data_tier"] in ("empirical", "thin-data")
    # INVEST on 2-for-2 outcomes should lean positive
    assert body["p_verdict_correct"] >= 0.5


def test_predict_unknown_event_404(client):
    assert client.get("/api/predict/9999").status_code == 404
