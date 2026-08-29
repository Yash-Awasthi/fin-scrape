"""Event intelligence API endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class TextInput(BaseModel):
    text: str
    title: str = ""


class EventInput(BaseModel):
    event_type: str = "unknown"
    title: str = ""
    description: str = ""
    tickers: list[str] = []
    confidence: float = 0.5


@router.post("/events/detect")
def detect_events(body: TextInput):
    from finscrape.agents.event_intelligence import detect_events
    events = detect_events(body.text)
    return {
        "count": len(events),
        "events": [
            {
                "event_type": e.event_type.value,
                "title": e.title,
                "description": e.description,
                "tickers": e.tickers,
                "magnitude": e.magnitude.value,
                "timeline": e.timeline.value,
                "confidence": e.confidence,
            }
            for e in events
        ],
    }


@router.post("/events/impact")
def assess_impact(body: EventInput):
    from finscrape.agents.event_intelligence import assess_impact, MarketEvent, EventType, ImpactMagnitude, ImpactTimeline
    try:
        event_type = EventType(body.event_type)
    except ValueError:
        event_type = EventType.UNKNOWN
    event = MarketEvent(
        event_type=event_type,
        title=body.title,
        description=body.description,
        tickers=body.tickers,
        confidence=body.confidence,
    )
    impact = assess_impact(event)
    return {
        "affected_sectors": impact.affected_sectors,
        "magnitude": impact.magnitude.value,
        "timeline": impact.timeline.value,
        "confidence": impact.confidence,
        "risk_factors": impact.risk_factors,
        "historical_precedent": impact.historical_precedent,
        "recommendation": impact.recommendation,
    }


@router.post("/events/signals")
def generate_signals(body: TextInput):
    from finscrape.agents.event_intelligence import detect_events, generate_signal
    events = detect_events(body.text)
    signals = [generate_signal(e, body.text) for e in events]
    return {
        "count": len(signals),
        "signals": [
            {
                "event_type": s.event_type,
                "direction": s.direction.value,
                "confidence": s.confidence,
                "tickers": s.tickers,
                "rationale": s.rationale,
                "risk_factors": s.risk_factors,
                "time_horizon": s.time_horizon,
                "strength": s.strength,
            }
            for s in signals
        ],
    }
