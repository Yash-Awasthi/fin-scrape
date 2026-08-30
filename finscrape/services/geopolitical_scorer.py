"""
Geopolitical risk scoring and location-based risk assessment.

Extracted from argus-system — event-based risk scoring patterns.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import math


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GeopoliticalEvent:
    location: str
    goldstein: float  # -10 to 10 (negative = negative event)
    tone: float  # -10 to 10 (negative = negative tone)
    mentions: int
    quad_class: int  # 1=Verbal Cooperation, 2=Material Cooperation, 3=Verbal Conflict, 4=Material Conflict
    date: str
    source: str = ""
    summary: str = ""


@dataclass
class LocationRisk:
    location: str
    risk_score: float  # 0-100
    confidence: RiskLevel
    n_events: int
    avg_goldstein: float
    avg_tone: float
    conflict_share: float
    trending: str = "stable"  # improving, declining, stable


@dataclass
class RouteRisk:
    origin: str
    destination: str
    waypoints: List[str]
    overall_risk: float  # 0-100
    location_risks: List[LocationRisk]
    recommendation: str


def compute_location_risk(events: List[GeopoliticalEvent]) -> Optional[LocationRisk]:
    """Compute risk score for a location based on events."""
    if not events:
        return None

    weights = [max(1, e.mentions) for e in events]
    total_weight = sum(weights)

    avg_goldstein = sum(e.goldstein * w for e, w in zip(events, weights)) / total_weight
    avg_tone = sum(e.tone * w for e, w in zip(events, weights)) / total_weight
    conflict_events = sum(1 for e in events if e.quad_class in (3, 4))
    conflict_share = conflict_events / len(events)

    goldstein_risk = max(0, min(1, (10 - avg_goldstein) / 20))
    tone_risk = max(0, min(1, (10 - max(-10, min(10, avg_tone))) / 20))

    risk_score = (0.40 * goldstein_risk + 0.30 * tone_risk + 0.30 * conflict_share) * 100

    n = len(events)
    if n < 20:
        confidence = RiskLevel.LOW
    elif n < 100:
        confidence = RiskLevel.MEDIUM
    else:
        confidence = RiskLevel.HIGH

    return LocationRisk(
        location=events[0].location,
        risk_score=round(risk_score, 1),
        confidence=confidence,
        n_events=n,
        avg_goldstein=round(avg_goldstein, 2),
        avg_tone=round(avg_tone, 2),
        conflict_share=round(conflict_share, 2),
    )


def compute_route_risk(
    location_risks: List[LocationRisk],
    origin: str,
    destination: str,
    waypoints: Optional[List[str]] = None,
) -> RouteRisk:
    """Compute overall route risk from individual location risks."""
    if not location_risks:
        return RouteRisk(
            origin=origin,
            destination=destination,
            waypoints=waypoints or [],
            overall_risk=0.0,
            location_risks=[],
            recommendation="No data available — proceed with caution",
        )

    risks = [lr.risk_score for lr in location_risks]
    overall = max(risks)  # Worst case for route

    if overall >= 80:
        rec = "CRITICAL: Avoid this route. High conflict risk."
    elif overall >= 60:
        rec = "HIGH: Consider alternative routes. Significant risk detected."
    elif overall >= 40:
        rec = "MODERATE: Proceed with enhanced monitoring and contingency plans."
    elif overall >= 20:
        rec = "LOW: Normal operations with standard monitoring."
    else:
        rec = "MINIMAL: Route appears safe for normal operations."

    return RouteRisk(
        origin=origin,
        destination=destination,
        waypoints=waypoints or [],
        overall_risk=round(overall, 1),
        location_risks=location_risks,
        recommendation=rec,
    )


def detect_risk_trends(
    current: LocationRisk, previous: LocationRisk
) -> str:
    """Detect if risk is improving, declining, or stable."""
    diff = current.risk_score - previous.risk_score
    if diff > 5:
        return "declining"
    elif diff < -5:
        return "improving"
    return "stable"


def generate_risk_alert(
    location_risk: LocationRisk,
    threshold: float = 60.0,
) -> Optional[Dict]:
    """Generate an alert if risk exceeds threshold."""
    if location_risk.risk_score >= threshold:
        severity = "CRITICAL" if location_risk.risk_score >= 80 else "HIGH" if location_risk.risk_score >= 60 else "MEDIUM"
        return {
            "location": location_risk.location,
            "severity": severity,
            "risk_score": location_risk.risk_score,
            "message": f"Risk score {location_risk.risk_score:.1f} exceeds threshold {threshold:.1f} for {location_risk.location}",
            "conflict_share": location_risk.conflict_share,
            "n_events": location_risk.n_events,
        }
    return None


def batch_score_locations(
    events_by_location: Dict[str, List[GeopoliticalEvent]],
    threshold: float = 60.0,
) -> Dict[str, Optional[LocationRisk]]:
    """Score multiple locations and generate alerts."""
    results = {}
    for location, events in events_by_location.items():
        risk = compute_location_risk(events)
        results[location] = risk
    return results
