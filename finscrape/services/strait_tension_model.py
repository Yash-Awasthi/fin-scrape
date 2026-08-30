"""
Strait Tension & Geopolitical Risk Model for fin-scrape
Extracted from: taiwan-situation (Taiwan Strait tension monitoring)
Patterns: Cumulative decay risk model, real-time monitoring,
          automated risk assessment, trend visualization
"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class RiskLevel(Enum):
    MINIMAL = "minimal"
    LOW = "low"
    ELEVATED = "elevated"
    HIGH = "high"
    SEVERE = "severe"
    CRITICAL = "critical"


class TensionSource(Enum):
    MILITARY = "military"
    DIPLOMATIC = "diplomatic"
    ECONOMIC = "economic"
    CYBER = "cyber"
    NAVAL = "naval"
    AIRSPACE = "airspace"


@dataclass
class TensionEvent:
    id: str
    timestamp: datetime
    source: TensionSource
    severity: float  # 0-1
    description: str
    region: str = ""
    actors: list[str] = field(default_factory=list)


@dataclass
class RiskAssessment:
    region: str
    timestamp: datetime
    risk_score: float  # 0-100
    risk_level: RiskLevel
    components: dict[str, float]
    trend: str  # "rising", "falling", "stable"
    decay_adjusted_score: float
    events_count: int
    recommendations: list[str]


# ─── V4 Cumulative Decay Model ─────────────────────────────────────────

def cumulative_decay_score(
    events: list[TensionEvent],
    decay_half_life_days: float = 7.0,
    max_lookback_days: float = 90.0,
) -> float:
    """
    V4 cumulative decay model: recent events weight more, old events decay exponentially.
    """
    now = datetime.now()
    total_score = 0.0
    max_possible = 0.0

    source_weights = {
        TensionSource.MILITARY: 1.5,
        TensionSource.NAVAL: 1.3,
        TensionSource.AIRSPACE: 1.2,
        TensionSource.CYBER: 0.8,
        TensionSource.DIPLOMATIC: 0.7,
        TensionSource.ECONOMIC: 0.6,
    }

    for event in events:
        days_ago = (now - event.timestamp).total_seconds() / 86400
        if days_ago > max_lookback_days:
            continue

        decay_factor = math.exp(-0.693 * days_ago / decay_half_life_days)
        source_weight = source_weights.get(event.source, 1.0)
        weighted = event.severity * decay_factor * source_weight

        total_score += weighted
        max_possible += source_weight

    if max_possible == 0:
        return 0.0

    normalized = (total_score / max_possible) * 100
    return min(100, max(0, normalized))


def risk_level_from_score(score: float) -> RiskLevel:
    """Convert numeric risk score to risk level."""
    if score >= 80:
        return RiskLevel.CRITICAL
    elif score >= 60:
        return RiskLevel.SEVERE
    elif score >= 40:
        return RiskLevel.HIGH
    elif score >= 25:
        return RiskLevel.ELEVATED
    elif score >= 10:
        return RiskLevel.LOW
    else:
        return RiskLevel.MINIMAL


# ─── Component Analysis ────────────────────────────────────────────────

def analyze_components(events: list[TensionEvent]) -> dict[str, float]:
    """Break down risk into component sources."""
    components: dict[str, list[float]] = {}
    for event in events:
        components.setdefault(event.source.value, []).append(event.severity)

    return {
        source: round(sum(values) / len(values) * 100, 1)
        for source, values in components.items()
        if values
    }


def compute_trend(events: list[TensionEvent], window_days: int = 14) -> str:
    """Determine if tension is rising, falling, or stable."""
    now = datetime.now()
    recent = [e for e in events if (now - e.timestamp).total_seconds() / 86400 <= window_days]
    older = [e for e in events if window_days < (now - e.timestamp).total_seconds() / 86400 <= window_days * 2]

    if not recent and not older:
        return "stable"

    recent_avg = sum(e.severity for e in recent) / len(recent) if recent else 0
    older_avg = sum(e.severity for e in older) / len(older) if older else 0

    diff = recent_avg - older_avg
    if diff > 0.1:
        return "rising"
    elif diff < -0.1:
        return "falling"
    return "stable"


# ─── Full Assessment ───────────────────────────────────────────────────

def assess_risk(
    region: str,
    events: list[TensionEvent],
    decay_half_life_days: float = 7.0,
) -> RiskAssessment:
    """Generate a comprehensive risk assessment for a region."""
    regional_events = [e for e in events if e.region == region or not e.region]
    score = cumulative_decay_score(regional_events, decay_half_life_days)
    components = analyze_components(regional_events)
    trend = compute_trend(regional_events)
    risk_level = risk_level_from_score(score)

    recommendations = []
    if score >= 60:
        recommendations.append("Increase monitoring frequency to hourly")
        recommendations.append("Activate early warning systems")
    elif score >= 40:
        recommendations.append("Monitor situation closely")
        recommendations.append("Review contingency plans")
    elif score >= 25:
        recommendations.append("Continue standard monitoring")
    else:
        recommendations.append("Routine monitoring sufficient")

    return RiskAssessment(
        region=region,
        timestamp=datetime.now(),
        risk_score=round(score, 1),
        risk_level=risk_level,
        components=components,
        trend=trend,
        decay_adjusted_score=round(score, 1),
        events_count=len(regional_events),
        recommendations=recommendations,
    )
