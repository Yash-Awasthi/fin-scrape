"""Insight routes: calibrated predictions + reliability, from Postgres outcomes.

The CEIP engine (finscrape.prediction) is pure — these routes feed it outcome
rows from `accuracy_outcomes` joined to `events` (for source/event_type/
confidence) and return the audited prediction payload.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException

from server import db

router = APIRouter()


async def _outcomes_from_pool() -> list[dict[str, Any]]:
    rows = await db.pool().fetch(
        """
        SELECT o.verdict, o.correct, o.checked_at,
               e.confidence, e.event_type, e.sources
        FROM accuracy_outcomes o
        LEFT JOIN events e ON e.id = o.event_id
        WHERE o.correct IS NOT NULL
        ORDER BY o.checked_at
        """
    )
    outcomes: list[dict[str, Any]] = []
    for r in rows:
        sources = []
        try:
            sources = json.loads(r["sources"]) if isinstance(r["sources"], str) else (r["sources"] or [])
        except (ValueError, TypeError):
            sources = []
        outcomes.append({
            "verdict": r["verdict"],
            "outcome": "correct" if r["correct"] else "incorrect",
            "confidence": r["confidence"],
            "source": (sources[0].split("/")[-1] if sources else "unknown"),
            "event_type": r["event_type"] or "other",
            "checked_at": r["checked_at"].isoformat() if r["checked_at"] else None,
        })
    return outcomes


@router.get("/api/reliability")
async def reliability() -> dict:
    """Reliability tables + Brier score — the audit view of prediction quality."""
    from finscrape.prediction import brier_summary, reliability_tables

    outcomes = await _outcomes_from_pool()
    return {
        "reliability": reliability_tables(outcomes),
        "brier": brier_summary(outcomes),
    }


@router.get("/api/predict/{event_id}")
async def predict_event(event_id: int) -> dict:
    """Calibrated Event-Impact Probability for one stored event, with the
    reliability evidence attached (per verdict/source/type, sample sizes)."""
    from finscrape.prediction import predict

    ev = await db.pool().fetchrow(
        """
        SELECT id, subject, verdict, signal_score, confidence, event_type,
               sources, tickers
        FROM events WHERE id = $1
        """,
        event_id,
    )
    if ev is None:
        raise HTTPException(status_code=404, detail="event not found")

    sources: list[str] = []
    try:
        raw_sources = ev["sources"]
        sources = json.loads(raw_sources) if isinstance(raw_sources, str) else (raw_sources or [])
    except (ValueError, TypeError):
        sources = []
    source = (sources[0].split("/")[-1] if sources else "local")
    tickers: list[str] = []
    try:
        raw_tickers = ev["tickers"]
        tickers = json.loads(raw_tickers) if isinstance(raw_tickers, str) else (raw_tickers or [])
    except (ValueError, TypeError):
        tickers = []

    outcomes = await _outcomes_from_pool()
    result = predict(
        text=f"{ev['subject']}. {ev['reasoning']}" if ev["reasoning"] else ev["subject"],
        verdict=ev["verdict"],
        confidence=float(ev["confidence"] or 0.5),
        source=source,
        event_type=ev["event_type"] or "other",
        outcomes=outcomes,
    )
    result["event"] = {
        "id": ev["id"],
        "subject": ev["subject"],
        "verdict": ev["verdict"],
        "signal_score": ev["signal_score"],
        "ticker": (tickers[0] if tickers else ""),
    }
    return result
