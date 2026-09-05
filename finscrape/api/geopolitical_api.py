"""
Geopolitical Dashboard API endpoints.
Provides REST access to the geopolitical risk dashboard and market sentiment.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(
    tags=["Geopolitical Intelligence", "Market Sentiment"],
    responses={
        422: {"description": "Validation Error"},
        500: {"description": "Internal Server Error"},
    },
)

# Singleton instances
_dashboard = None
_sentiment = None


def _get_dashboard():
    global _dashboard
    if _dashboard is None:
        from finscrape.analysis.geopolitical_dashboard import GeopoliticalDashboard
        _dashboard = GeopoliticalDashboard()
    return _dashboard


def _get_sentiment():
    global _sentiment
    if _sentiment is None:
        from finscrape.analysis.market_sentiment import MarketSentimentAnalyzer
        _sentiment = MarketSentimentAnalyzer()
    return _sentiment


class SignalInput(BaseModel):
    source: str = "news"
    region: str = "east_asia"
    threat_type: str = "military_conflict"
    headline: str = ""
    summary: str = ""
    severity: float = 0.5
    confidence: float = 0.7
    market_impact: float = 0.0
    affected_assets: list[str] = []


class SentimentInput(BaseModel):
    source: str = "news"
    asset: str = "SPY"
    text: str = ""
    score: float = 0.0
    confidence: float = 0.7


# ── Geopolitical Dashboard Endpoints ─────────────────────────────────────────

@router.get(
    "/geopolitical/dashboard",
    summary="Get full geopolitical risk dashboard",
    description="Returns the complete geopolitical risk state including global risk score, region profiles, active threats, and recent alerts.",
    responses={
        200: {
            "description": "Dashboard state",
            "content": {
                "application/json": {
                    "example": {
                        "global_risk": 42.5,
                        "regions": {
                            "east_asia": {"risk_score": 65.0, "trend": "rising", "active_threats": 3},
                            "europe": {"risk_score": 35.0, "trend": "stable", "active_threats": 1},
                        },
                        "recent_alerts": [],
                    }
                }
            },
        }
    },
)
async def get_dashboard():
    """Get the full geopolitical risk dashboard state."""
    dashboard = _get_dashboard()
    return dashboard.to_dict()


@router.get(
    "/geopolitical/regions",
    summary="Get risk scores for all regions",
    description="Returns risk scores, trends, active threats, and signal counts for every tracked geopolitical region.",
    responses={
        200: {
            "description": "Regional risk profiles",
            "content": {
                "application/json": {
                    "example": {
                        "east_asia": {
                            "risk_score": 65.0,
                            "trend": "rising",
                            "active_threats": 3,
                            "signal_count": 12,
                        },
                        "europe": {
                            "risk_score": 35.0,
                            "trend": "stable",
                            "active_threats": 1,
                            "signal_count": 5,
                        },
                    }
                }
            },
        }
    },
)
async def get_region_risks():
    """Get risk scores for all regions."""
    dashboard = _get_dashboard()
    return {
        region.value: {
            "risk_score": round(profile.risk_score, 1),
            "trend": profile.trend.value,
            "active_threats": profile.active_threats,
            "signal_count": len(profile.signals),
        }
        for region, profile in dashboard.regions.items()
    }


@router.get(
    "/geopolitical/top-risks",
    summary="Get highest-risk regions",
    description="Returns the top N regions sorted by risk score (descending).",
    responses={
        200: {
            "description": "Top risk regions",
            "content": {
                "application/json": {
                    "example": [
                        {"region": "east_asia", "risk_score": 65.0, "trend": "rising", "active_threats": 3},
                        {"region": "middle_east", "risk_score": 55.0, "trend": "stable", "active_threats": 2},
                    ]
                }
            },
        }
    },
)
async def get_top_risks(n: int = 5):
    """Get the N highest-risk regions."""
    dashboard = _get_dashboard()
    top = dashboard.get_top_risks(n)
    return [
        {
            "region": p.region.value,
            "risk_score": round(p.risk_score, 1),
            "trend": p.trend.value,
            "active_threats": p.active_threats,
        }
        for p in top
    ]


@router.get(
    "/geopolitical/alerts",
    summary="Get recent alerts",
    description="Returns geopolitical alerts generated in the last N hours, sorted by severity.",
    responses={
        200: {
            "description": "Recent alerts",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "alert-1",
                            "timestamp": "2025-01-15T10:30:00Z",
                            "severity": "high",
                            "region": "east_asia",
                            "title": "Military tension escalation",
                            "description": "Naval exercises reported near contested waters.",
                        }
                    ]
                }
            },
        }
    },
)
async def get_alerts(hours: int = 24):
    """Get alerts from the last N hours."""
    dashboard = _get_dashboard()
    alerts = dashboard.get_recent_alerts(hours)
    return [
        {
            "id": a.id,
            "timestamp": a.timestamp.isoformat(),
            "severity": a.severity,
            "region": a.region.value,
            "title": a.title,
            "description": a.description,
        }
        for a in alerts
    ]


@router.get(
    "/geopolitical/global-risk",
    summary="Get global risk score",
    description="Returns the aggregate global geopolitical risk score (0-100).",
    responses={
        200: {
            "description": "Global risk score",
            "content": {
                "application/json": {
                    "example": {"global_risk": 42.5}
                }
            },
        }
    },
)
async def get_global_risk():
    """Get the global risk score."""
    dashboard = _get_dashboard()
    return {"global_risk": round(dashboard.get_global_risk(), 1)}


@router.post(
    "/geopolitical/signal",
    summary="Ingest a geopolitical signal",
    description="Submit a new geopolitical signal (news event, intelligence report) to update risk calculations.",
    responses={
        200: {
            "description": "Signal ingested, updated dashboard returned",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "dashboard": {"global_risk": 43.0}}
                }
            },
        }
    },
)
async def ingest_signal(signal: SignalInput):
    """Ingest a new geopolitical signal."""
    from finscrape.analysis.geopolitical_dashboard import (
        GeopoliticalSignal, Region, ThreatType,
    )
    dashboard = _get_dashboard()

    geo_signal = GeopoliticalSignal(
        id=f"sig-{datetime.now().timestamp()}",
        timestamp=datetime.now(),
        source=signal.source,
        region=Region(signal.region),
        threat_type=ThreatType(signal.threat_type),
        headline=signal.headline,
        summary=signal.summary,
        severity=signal.severity,
        confidence=signal.confidence,
        market_impact=signal.market_impact,
        affected_assets=signal.affected_assets,
    )
    dashboard.ingest_signal(geo_signal)
    return {"status": "ok", "dashboard": dashboard.to_dict()}


# ── Market Sentiment Endpoints ────────────────────────────────────────────────

@router.get(
    "/sentiment/{asset}",
    summary="Get sentiment for an asset",
    description="Returns composite sentiment score, momentum, and extreme status for a specific asset (e.g. BTC, SPY, TSLA).",
    responses={
        200: {
            "description": "Sentiment analysis",
            "content": {
                "application/json": {
                    "example": {
                        "asset": "BTC",
                        "composite_score": 72.0,
                        "extreme": "bullish",
                        "momentum": 0.025,
                        "signal_count": 8,
                        "sources": ["news", "social"],
                        "divergence": False,
                    }
                }
            },
        }
    },
)
async def get_sentiment(asset: str):
    """Get composite sentiment for an asset."""
    analyzer = _get_sentiment()
    snapshot = analyzer.get_sentiment(asset)
    return {
        "asset": snapshot.asset,
        "composite_score": round(snapshot.composite_score, 1),
        "extreme": snapshot.extreme.value,
        "momentum": round(snapshot.momentum, 3),
        "signal_count": snapshot.signal_count,
        "sources": snapshot.sources,
        "divergence": snapshot.divergence,
    }


@router.get(
    "/sentiment/market/overview",
    summary="Get market sentiment overview",
    description="Returns composite sentiment scores for all tracked assets.",
    responses={
        200: {
            "description": "Market sentiment overview",
            "content": {
                "application/json": {
                    "example": {"BTC": 72.0, "ETH": 65.0, "SPY": 55.0, "TSLA": 48.0}
                }
            },
        }
    },
)
async def get_market_overview():
    """Get sentiment for all tracked assets."""
    analyzer = _get_sentiment()
    return analyzer.get_composite_market_sentiment()


@router.get(
    "/sentiment/extremes",
    summary="Get extreme sentiment readings",
    description="Returns assets with extreme bullish or bearish sentiment that may indicate overbought/oversold conditions.",
    responses={
        200: {
            "description": "Extreme sentiment assets",
            "content": {
                "application/json": {
                    "example": [{"asset": "BTC", "composite_score": 85.0, "extreme": "bullish", "signal_count": 12}]
                }
            },
        }
    },
)
async def get_extreme_sentiments():
    """Get assets with extreme sentiment readings."""
    analyzer = _get_sentiment()
    extremes = analyzer.get_extreme_sentiments()
    return [
        {
            "asset": s.asset,
            "composite_score": round(s.composite_score, 1),
            "extreme": s.extreme.value,
            "signal_count": s.signal_count,
        }
        for s in extremes
    ]


@router.get(
    "/sentiment/divergences",
    summary="Find price-sentiment divergences",
    description="Identifies assets where price movement contradicts sentiment (potential contrarian signals).",
    responses={
        200: {
            "description": "Divergence signals",
            "content": {
                "application/json": {
                    "example": [{"asset": "TSLA", "type": "bearish_divergence", "price_change": 0.05, "sentiment_change": -0.02}]
                }
            },
        }
    },
)
async def get_divergences():
    """Find assets with price-sentiment divergence."""
    analyzer = _get_sentiment()
    return analyzer.get_divergences()


@router.post(
    "/sentiment/signal",
    summary="Ingest a sentiment signal",
    description="Submit a new sentiment signal (news, social media, analyst report) for an asset.",
    responses={
        200: {
            "description": "Signal ingested",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "asset": "BTC"}
                }
            },
        }
    },
)
async def ingest_sentiment(signal: SentimentInput):
    """Ingest a new sentiment signal."""
    from finscrape.analysis.market_sentiment import SentimentSource
    analyzer = _get_sentiment()

    from finscrape.analysis.market_sentiment import SentimentSignal
    sig = SentimentSignal(
        source=SentimentSource(signal.source),
        timestamp=datetime.now(),
        asset=signal.asset,
        text=signal.text,
        score=signal.score,
        confidence=signal.confidence,
    )
    analyzer.ingest_signal(sig)
    return {"status": "ok", "asset": signal.asset}
