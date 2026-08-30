"""
Geopolitical Intelligence Monitor for fin-scrape
Extracted from: worldview-intelligence (3D globe intelligence dashboard)
Patterns: Conflict zone monitoring, situation reports, escalation prediction,
          threat assessment, multi-source intelligence fusion
"""
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Severity(Enum):
    GREEN = "green"
    ORANGE = "orange"
    RED = "red"
    CRITICAL = "critical"


class EventType(Enum):
    BATTLE = "battle"
    EXPLOSION = "explosion"
    PROTEST = "protest"
    SANCTIONS = "sanctions"
    DIPLOMATIC = "diplomatic"
    CYBER = "cyber"
    ECONOMIC = "economic"
    HUMANITARIAN = "humanitarian"
    MISSILE = "missile"
    NAVAL = "naval"
    AIRSPACE = "airspace"
    NUCLEAR = "nuclear"


class IntelSource(Enum):
    GDELT = "gdelt"
    ACLED = "acled"
    OSINT = "osint"
    RSS = "rss"
    SOCIAL_MEDIA = "social_media"
    GOVERNMENT = "government"
    SATELLITE = "satellite"
    SIGNALS = "signals"


@dataclass
class GeoPosition:
    lat: float
    lng: float


@dataclass
class ConflictEvent:
    id: str
    timestamp: datetime
    position: GeoPosition
    country: str
    region: str
    event_type: EventType
    severity: Severity
    fatalities: int = 0
    displaced: int = 0
    source: IntelSource = IntelSource.OSINT
    description: str = ""
    actors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class ThreatIndicator:
    name: str
    score: float  # 0-1
    weight: float
    description: str
    trend: str = "stable"  # "rising", "falling", "stable"


@dataclass
class SituationReport:
    region: str
    timestamp: datetime
    threats: list[ThreatIndicator]
    escalation_score: float  # 0-1
    summary: str
    recommendations: list[str]
    events_count: int
    severity: Severity


@dataclass
class NewsItem:
    id: str
    title: str
    source: str
    timestamp: datetime
    sentiment: float  # -1 to 1
    relevance: float  # 0 to 1
    region: str = ""
    categories: list[str] = field(default_factory=list)


# ─── Distance Calculation ───────────────────────────────────────────────

def haversine_distance(a: GeoPosition, b: GeoPosition) -> float:
    """Great-circle distance between two points in km."""
    R = 6371
    d_lat = math.radians(b.lat - a.lat)
    d_lng = math.radians(b.lng - a.lng)
    a_val = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(a.lat)) * math.cos(math.radians(b.lat)) * math.sin(d_lng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a_val), math.sqrt(1 - a_val))


def point_in_radius(point: GeoPosition, center: GeoPosition, radius_km: float) -> bool:
    """Check if a point is within a radius of a center point."""
    return haversine_distance(point, center) <= radius_km


# ─── Conflict Zone Database ────────────────────────────────────────────

CONFLICT_ZONES = [
    {"country": "Ukraine", "region": "Donetsk", "center": GeoPosition(48.0, 37.8), "radius_km": 80, "severity": Severity.RED, "base_intensity": 8},
    {"country": "Gaza", "region": "Gaza Strip", "center": GeoPosition(31.4, 34.4), "radius_km": 20, "severity": Severity.CRITICAL, "base_intensity": 9},
    {"country": "Sudan", "region": "Khartoum", "center": GeoPosition(15.6, 32.5), "radius_km": 30, "severity": Severity.RED, "base_intensity": 7},
    {"country": "Syria", "region": "Idlib", "center": GeoPosition(35.9, 36.6), "radius_km": 50, "severity": Severity.ORANGE, "base_intensity": 5},
    {"country": "Yemen", "region": "Red Sea", "center": GeoPosition(13.0, 43.5), "radius_km": 150, "severity": Severity.ORANGE, "base_intensity": 5},
    {"country": "Myanmar", "region": "Sagaing", "center": GeoPosition(22.0, 95.5), "radius_km": 80, "severity": Severity.ORANGE, "base_intensity": 5},
    {"country": "Somalia", "region": "Mogadishu", "center": GeoPosition(2.0, 45.3), "radius_km": 100, "severity": Severity.ORANGE, "base_intensity": 4},
    {"country": "Ethiopia", "region": "Amhara", "center": GeoPosition(11.6, 38.0), "radius_km": 100, "severity": Severity.ORANGE, "base_intensity": 5},
]


# ─── Intelligence Analysis Functions ───────────────────────────────────

def assess_event_severity(event: ConflictEvent) -> ThreatIndicator:
    """Convert a single event into a threat indicator."""
    severity_weights = {
        Severity.GREEN: 0.1,
        Severity.ORANGE: 0.5,
        Severity.RED: 0.8,
        Severity.CRITICAL: 1.0,
    }
    type_weights = {
        EventType.BATTLE: 0.7,
        EventType.EXPLOSION: 0.8,
        EventType.MISSILE: 0.9,
        EventType.NUCLEAR: 1.0,
        EventType.NAVAL: 0.7,
        EventType.CYBER: 0.5,
        EventType.SANCTIONS: 0.3,
        EventType.DIPLOMATIC: 0.2,
        EventType.PROTEST: 0.3,
        EventType.HUMANITARIAN: 0.4,
        EventType.ECONOMIC: 0.3,
        EventType.AIRSPACE: 0.6,
    }
    base = severity_weights.get(event.severity, 0.5) * type_weights.get(event.event_type, 0.5)
    fatality_factor = min(1.0, event.fatalities / 100)
    score = min(1.0, base + fatality_factor * 0.3)
    return ThreatIndicator(
        name=f"{event.event_type.value} in {event.region}",
        score=score,
        weight=1.0,
        description=f"{event.event_type.value} event: {event.description}",
        trend="rising" if event.fatalities > 10 else "stable",
    )


def calculate_escalation_score(events: list[ConflictEvent], region: str = "") -> float:
    """Calculate overall escalation probability (0-1) from a set of events."""
    if not events:
        return 0.0

    regional_events = [e for e in events if not region or e.region == region]
    if not regional_events:
        return 0.0

    indicators = [assess_event_severity(e) for e in regional_events]
    total_weight = sum(i.weight for i in indicators)
    if total_weight == 0:
        return 0.0

    weighted_score = sum(i.score * i.weight for i in indicators) / total_weight

    # Event count factor (more events = higher escalation)
    count_factor = min(1.0, len(regional_events) / 20.0)

    # Recency factor (recent events weight more)
    now = datetime.now()
    recency_scores = []
    for e in regional_events:
        hours_ago = (now - e.timestamp).total_seconds() / 3600
        recency_scores.append(max(0.1, 1.0 - hours_ago / 72))
    avg_recency = sum(recency_scores) / len(recency_scores)

    escalation = (weighted_score * 0.5 + count_factor * 0.3 + avg_recency * 0.2)
    return min(1.0, escalation)


def generate_situation_report(
    region: str,
    events: list[ConflictEvent],
    news: list[NewsItem] = None,
) -> SituationReport:
    """Generate a comprehensive situation report for a region."""
    threats = []
    recommendations = []
    news = news or []

    # Analyze conflict events
    regional_events = [e for e in events if e.region == region or e.country == region]
    escalation = calculate_escalation_score(events, region)

    if regional_events:
        red_events = [e for e in regional_events if e.severity in (Severity.RED, Severity.CRITICAL)]
        total_fatalities = sum(e.fatalities for e in regional_events)

        if red_events:
            threats.append(ThreatIndicator(
                name="High-severity events",
                score=min(1.0, len(red_events) * 0.2),
                weight=1.5,
                description=f"{len(red_events)} high-severity events in {region}",
                trend="rising",
            ))
            recommendations.append("Increase monitoring frequency for conflict zones")

        if total_fatalities > 50:
            threats.append(ThreatIndicator(
                name="Significant casualties",
                score=min(1.0, total_fatalities / 200),
                weight=1.2,
                description=f"{total_fatalities} fatalities reported in {region}",
            ))
            recommendations.append("Assess humanitarian impact and displacement risk")

        missile_events = [e for e in regional_events if e.event_type == EventType.MISSILE]
        if missile_events:
            threats.append(ThreatIndicator(
                name="Missile activity",
                score=0.9,
                weight=2.0,
                description=f"{len(missile_events)} missile/launch events detected",
                trend="rising",
            ))
            recommendations.append("Activate air-defense monitoring protocols")

    # Analyze negative news
    regional_news = [n for n in news if n.region == region]
    negative_news = [n for n in regional_news if n.sentiment < -0.3]
    if len(negative_news) > 3:
        threats.append(ThreatIndicator(
            name="Negative media sentiment",
            score=min(1.0, len(negative_news) * 0.1),
            weight=0.8,
            description=f"Elevated negative sentiment across {len(negative_news)} reports",
        ))

    if not recommendations:
        recommendations.append("Continue standard monitoring procedures")

    severity = Severity.GREEN
    if escalation > 0.7:
        severity = Severity.CRITICAL
    elif escalation > 0.5:
        severity = Severity.RED
    elif escalation > 0.3:
        severity = Severity.ORANGE

    summary = f"Situation report for {region}. "
    if threats:
        summary += f"{len(threats)} threat indicator(s). Escalation probability: {escalation:.0%}."
    else:
        summary += "No significant threats detected."

    return SituationReport(
        region=region,
        timestamp=datetime.now(),
        threats=threats,
        escalation_score=escalation,
        summary=summary,
        recommendations=recommendations,
        events_count=len(regional_events),
        severity=severity,
    )


def analyze_news_sentiment_batch(news: list[NewsItem]) -> dict:
    """Analyze batch sentiment for a region and return aggregates."""
    region_sentiment: dict[str, list[float]] = {}
    for item in news:
        if item.region:
            region_sentiment.setdefault(item.region, []).append(item.sentiment)

    results = {}
    for region, sentiments in region_sentiment.items():
        avg = sum(sentiments) / len(sentiments)
        negative = sum(1 for s in sentiments if s < -0.3)
        positive = sum(1 for s in sentiments if s > 0.3)
        results[region] = {
            "avg_sentiment": round(avg, 3),
            "total_reports": len(sentiments),
            "negative_reports": negative,
            "positive_reports": positive,
            "sentiment_trend": "deteriorating" if negative > positive * 2 else "improving" if positive > negative * 2 else "stable",
        }
    return results


def detect_anomalies(events: list[ConflictEvent], baseline_window_hours: int = 168) -> list[dict]:
    """Detect anomalous spikes in conflict activity."""
    now = datetime.now()
    recent = [e for e in events if (now - e.timestamp).total_seconds() / 3600 <= 24]
    baseline = [e for e in events if baseline_window_hours >= (now - e.timestamp).total_seconds() / 3600 > 24]

    if not baseline:
        return []

    daily_baseline = len(baseline) / (baseline_window_hours / 24)
    baseline_fatalities = sum(e.fatalities for e in baseline) / (baseline_window_hours / 24)

    anomalies = []
    if len(recent) > daily_baseline * 2:
        anomalies.append({
            "type": "event_spike",
            "severity": "high",
            "description": f"Event count {len(recent)} exceeds baseline {daily_baseline:.1f}/day by {len(recent)/max(daily_baseline,1):.1f}x",
            "recent_count": len(recent),
            "baseline_daily": round(daily_baseline, 1),
        })

    recent_fatalities = sum(e.fatalities for e in recent)
    if recent_fatalities > baseline_fatalities * 3 and baseline_fatalities > 0:
        anomalies.append({
            "type": "fatality_spike",
            "severity": "critical",
            "description": f"Fatalities {recent_fatalities} exceed baseline {baseline_fatalities:.1f}/day",
            "recent_fatalities": recent_fatalities,
            "baseline_daily": round(baseline_fatalities, 1),
        })

    return anomalies


def forecast_escalation(events: list[ConflictEvent], region: str, hours_ahead: int = 72) -> dict:
    """Simple escalation forecast based on recent trends."""
    now = datetime.now()
    regional = [e for e in events if e.region == region]
    if not regional:
        return {"region": region, "forecast": "stable", "confidence": 0.3, "factors": []}

    # Trend analysis: compare last 12h vs previous 12h
    recent_12h = [e for e in regional if (now - e.timestamp).total_seconds() / 3600 <= 12]
    prev_12h = [e for e in regional if 24 >= (now - e.timestamp).total_seconds() / 3600 > 12]

    recent_rate = len(recent_12h) / 12
    prev_rate = len(prev_12h) / 12 if prev_12h else 0

    factors = []
    trend = "stable"

    if recent_rate > prev_rate * 1.5 and prev_rate > 0:
        trend = "escalating"
        factors.append(f"Event rate increasing: {recent_rate:.2f}/hr vs {prev_rate:.2f}/hr baseline")
    elif recent_rate < prev_rate * 0.7 and prev_rate > 0:
        trend = "de-escalating"
        factors.append(f"Event rate decreasing: {recent_rate:.2f}/hr vs {prev_rate:.2f}/hr baseline")

    recent_fatalities = sum(e.fatalities for e in recent_12h)
    if recent_fatalities > 20:
        factors.append(f"High casualty count: {recent_fatalities} in last 12h")

    current_escalation = calculate_escalation_score(regional, region)

    return {
        "region": region,
        "forecast": trend,
        "current_escalation": round(current_escalation, 3),
        "projected_escalation": round(min(1.0, current_escalation * (1.2 if trend == "escalating" else 0.8 if trend == "de-escalating" else 1.0)), 3),
        "confidence": min(0.9, 0.3 + len(regional) * 0.05),
        "factors": factors,
        "hours_ahead": hours_ahead,
    }
