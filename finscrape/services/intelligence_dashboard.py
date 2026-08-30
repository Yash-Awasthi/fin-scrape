"""
Intelligence Dashboard — Multi-topic intelligence tracking and visualization.

Inspired by three-globe and watchboard.
Provides data aggregation, trend analysis, and visualization data
for financial and geopolitical intelligence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class IntelligenceEvent:
    """Represents a tracked intelligence event."""
    id: str
    title: str
    category: str
    severity: str  # low, medium, high, critical
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: str = ""
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class Tracker:
    """Represents a topic tracker."""
    id: str
    name: str
    category: str
    description: str
    keywords: List[str]
    isActive: bool = True
    eventCount: int = 0
    lastEvent: Optional[datetime] = None


@dataclass
class DashboardMetric:
    """A metric for the dashboard."""
    name: str
    value: float
    change: float  # percentage change
    trend: str  # up, down, stable
    period: str  # 24h, 7d, 30d


# ============================================================================
# Intelligence Dashboard Manager
# ============================================================================

class IntelligenceDashboardManager:
    def __init__(self):
        self.events: Dict[str, IntelligenceEvent] = {}
        self.trackers: Dict[str, Tracker] = {}
        self.metrics: Dict[str, DashboardMetric] = {}

    def create_tracker(
        self,
        name: str,
        category: str,
        description: str,
        keywords: List[str]
    ) -> Tracker:
        """Create a new topic tracker."""
        import uuid
        tracker = Tracker(
            id=str(uuid.uuid4())[:8],
            name=name,
            category=category,
            description=description,
            keywords=keywords,
        )
        self.trackers[tracker.id] = tracker
        return tracker

    def add_event(self, event: IntelligenceEvent) -> None:
        """Add an intelligence event."""
        self.events[event.id] = event

        # Update tracker counts
        for tracker in self.trackers.values():
            if any(kw.lower() in event.title.lower() or kw.lower() in event.description.lower()
                   for kw in tracker.keywords):
                tracker.eventCount += 1
                tracker.lastEvent = event.timestamp

    def get_events_by_category(self, category: str) -> List[IntelligenceEvent]:
        """Get events filtered by category."""
        return [e for e in self.events.values() if e.category == category]

    def get_events_by_location(self, location: str) -> List[IntelligenceEvent]:
        """Get events filtered by location."""
        return [e for e in self.events.values() if e.location and location.lower() in e.location.lower()]

    def get_events_by_severity(self, severity: str) -> List[IntelligenceEvent]:
        """Get events filtered by severity."""
        return [e for e in self.events.values() if e.severity == severity]

    def get_timeline(self, hours: int = 24) -> List[IntelligenceEvent]:
        """Get recent events as a timeline."""
        cutoff = datetime.now().timestamp() - hours * 3600
        return sorted(
            [e for e in self.events.values() if e.timestamp.timestamp() > cutoff],
            key=lambda e: e.timestamp,
            reverse=True
        )

    def get_globe_data(self) -> List[Dict]:
        """Get data formatted for globe visualization."""
        return [
            {
                "lat": e.latitude,
                "lng": e.longitude,
                "size": {"low": 0.5, "medium": 1.0, "high": 1.5, "critical": 2.0}.get(e.severity, 0.5),
                "color": {"low": "#4CAF50", "medium": "#FF9800", "high": "#F44336", "critical": "#9C27B0"}.get(e.severity, "#4CAF50"),
                "title": e.title,
                "category": e.category,
            }
            for e in self.events.values()
            if e.latitude and e.longitude
        ]

    def get_category_stats(self) -> Dict[str, int]:
        """Get event count by category."""
        stats: Dict[str, int] = {}
        for event in self.events.values():
            stats[event.category] = stats.get(event.category, 0) + 1
        return stats

    def get_severity_stats(self) -> Dict[str, int]:
        """Get event count by severity."""
        stats: Dict[str, int] = {}
        for event in self.events.values():
            stats[event.severity] = stats.get(event.severity, 0) + 1
        return stats

    def get_top_keywords(self, limit: int = 10) -> List[tuple]:
        """Get most common keywords across events."""
        keyword_counts: Dict[str, int] = {}
        for event in self.events.values():
            for tag in event.tags:
                keyword_counts[tag] = keyword_counts.get(tag, 0) + 1
        return sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def get_active_trackers(self) -> List[Tracker]:
        """Get all active trackers."""
        return [t for t in self.trackers.values() if t.isActive]

    def get_dashboard_summary(self) -> Dict:
        """Get a summary for the dashboard."""
        return {
            "totalEvents": len(self.events),
            "totalTrackers": len(self.trackers),
            "activeTrackers": len([t for t in self.trackers.values() if t.isActive]),
            "severityDistribution": self.get_severity_stats(),
            "categoryDistribution": self.get_category_stats(),
            "recentEvents": len(self.get_timeline(24)),
            "topKeywords": self.get_top_keywords(5),
        }
