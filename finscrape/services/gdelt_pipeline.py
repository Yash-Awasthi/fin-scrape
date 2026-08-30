"""
GDELT data pipeline from gdelt-data-pipeline — news event analysis.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math
import time


@dataclass
class GDELTEvent:
    event_id: str
    date: str
    source_url: str
    source_name: str
    headline: str
    tone: float = 0.0
    goldstein: float = 0.0
    mentions: int = 0
    shares: int = 0
    theme: str = ""
    location: str = ""
    actor1: str = ""
    actor2: str = ""
    event_type: str = ""


@dataclass
class EventCluster:
    theme: str
    events: List[GDELTEvent]
    avg_tone: float = 0.0
    total_mentions: int = 0
    sentiment: str = "neutral"
    impact_score: float = 0.0


@dataclass
class PipelineResult:
    events_processed: int
    clusters: List[EventCluster]
    top_themes: List[Dict]
    global_sentiment: float
    alerts: List[Dict]


def cluster_events(events: List[GDELTEvent], theme_field: str = "theme") -> List[EventCluster]:
    clusters: Dict[str, List[GDELTEvent]] = {}
    for event in events:
        key = getattr(event, theme_field) or "unknown"
        clusters.setdefault(key, []).append(event)

    result = []
    for theme, cluster_events in clusters.items():
        tones = [e.tone for e in cluster_events]
        avg_tone = sum(tones) / len(tones) if tones else 0
        total_mentions = sum(e.mentions for e in cluster_events)
        sentiment = "positive" if avg_tone > 1 else "negative" if avg_tone < -1 else "neutral"
        impact = min(1.0, total_mentions / 1000) * min(1.0, len(cluster_events) / 10)
        result.append(EventCluster(theme=theme, events=cluster_events, avg_tone=avg_tone, total_mentions=total_mentions, sentiment=sentiment, impact_score=impact))

    return sorted(result, key=lambda c: c.impact_score, reverse=True)


def compute_global_sentiment(events: List[GDELTEvent]) -> float:
    if not events:
        return 0.0
    weights = [max(1, e.mentions) for e in events]
    total_weight = sum(weights)
    return sum(e.tone * w for e, w in zip(events, weights)) / total_weight if total_weight > 0 else 0.0


def detect_breaking_events(events: List[GDELTEvent], threshold: float = 5.0) -> List[Dict]:
    alerts = []
    for event in events:
        if abs(event.tone) > threshold or event.mentions > 500:
            alerts.append({"event_id": event.event_id, "headline": event.headline, "tone": event.tone, "mentions": event.mentions, "severity": "critical" if abs(event.tone) > 8 else "high"})
    return alerts


def analyze_themes(events: List[GDELTEvent]) -> List[Dict]:
    themes: Dict[str, Dict] = {}
    for event in events:
        theme = event.theme or "unknown"
        if theme not in themes:
            themes[theme] = {"count": 0, "total_tone": 0, "total_mentions": 0}
        themes[theme]["count"] += 1
        themes[theme]["total_tone"] += event.tone
        themes[theme]["total_mentions"] += event.mentions
    result = []
    for theme, data in themes.items():
        result.append({"theme": theme, "events": data["count"], "avg_tone": data["total_tone"] / data["count"], "total_mentions": data["total_mentions"]})
    return sorted(result, key=lambda x: x["total_mentions"], reverse=True)


def run_pipeline(events: List[GDELTEvent]) -> PipelineResult:
    clusters = cluster_events(events)
    top_themes = analyze_themes(events)
    global_sentiment = compute_global_sentiment(events)
    alerts = detect_breaking_events(events)
    return PipelineResult(events_processed=len(events), clusters=clusters, top_themes=top_themes, global_sentiment=global_sentiment, alerts=alerts)
