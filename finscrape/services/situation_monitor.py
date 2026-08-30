"""
Situation Monitor — Geopolitical intelligence aggregation and monitoring.

Extracted from situation-monitor inspiration repo.
Provides RSS feed aggregation, geographic classification, and crisis detection.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class NewsArticle:
    """Represents a single news article."""
    title: str
    summary: str
    source: str
    location: Optional[str] = None
    url: str = ""
    published: Optional[datetime] = None
    categories: List[str] = field(default_factory=list)
    sentiment_score: float = 0.0
    relevance_score: float = 0.0
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    keywords: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.published:
            self.published = datetime.now()

    @property
    def article_id(self) -> str:
        raw = f"{self.title}:{self.source}:{self.url}"
        return hashlib.md5(raw.encode()).hexdigest()


@dataclass
class FeedConfig:
    """RSS feed configuration."""
    url: str
    source: str
    location: Optional[str] = None
    category: str = "general"
    enabled: bool = True
    fetch_interval_minutes: int = 30


@dataclass
class CrisisAlert:
    """Detected crisis or escalation event."""
    alert_type: str  # escalation, de_escalation, breaking, update
    severity: str  # low, medium, high, critical
    headline: str
    source: str
    region: str
    timestamp: datetime
    related_articles: List[str] = field(default_factory=list)
    confidence: float = 0.0


# Default feed configurations — geopolitics and crisis monitoring
DEFAULT_FEEDS: Dict[str, List[FeedConfig]] = {
    "US Policy Watch": [
        FeedConfig(url="https://www.whitehouse.gov/feed/", source="White House", location="United States", category="policy"),
        FeedConfig(url="https://rss.politico.com/playbook.xml", source="POLITICO", location="United States", category="policy"),
        FeedConfig(url="https://feeds.axios.com/api/feed", source="Axios", location="United States", category="policy"),
        FeedConfig(url="https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", source="NYT Politics", location="United States", category="policy"),
    ],
    "Geopolitics": [
        FeedConfig(url="https://www.cfr.org/rss.xml", source="CFR", category="geopolitics"),
        FeedConfig(url="https://feeds.bbci.co.uk/news/world/rss.xml", source="BBC World", category="geopolitics"),
    ],
    "Conflict Zones": [
        FeedConfig(url="https://feeds.bbci.co.uk/news/world/middle_east/rss.xml", source="BBC Middle East", location="Middle East", category="conflict"),
    ],
    "Defence & Intel": [
        FeedConfig(url="https://www.janes.com/feeds/news", source="Janes", category="defence"),
    ],
    "Economic Warfare": [
        FeedConfig(url="https://www.reuters.com/arc/outboundfeeds/v3/all/rss.xml?outputType=xml", source="Reuters", category="economic"),
    ],
}


# Location → coordinates mapping for geo-visualization
GEOLOCATIONS: Dict[str, Tuple[float, float]] = {
    "United States": (38.9072, -77.0369),
    "Russia": (55.7558, 37.6173),
    "China": (39.9042, 116.4074),
    "Ukraine": (50.4501, 30.5234),
    "Israel": (31.7683, 35.2137),
    "Taiwan": (25.0330, 121.5654),
    "Iran": (35.6892, 51.3890),
    "North Korea": (39.0392, 125.7625),
    "Middle East": (29.3759, 47.9774),
    "NATO": (50.8503, 4.3517),
    "Europe": (50.1109, 8.6821),
    "Asia": (34.0522, 118.2437),
    "Africa": (-1.2921, 36.8219),
    "South America": (-14.2350, -51.9253),
}

# Crisis keywords for severity classification
CRISIS_KEYWORDS = {
    "critical": ["nuclear", "declaration of war", "invasion", "coup", "mass casualty", "bioweapon"],
    "high": ["military strike", "sanctions imposed", "embassy closed", "troops deployed", "missile launch"],
    "medium": ["tensions rise", "diplomatic crisis", "trade war", "sanctions threatened", "military exercise"],
    "low": ["protest", "diplomatic meeting", "trade talks", "policy change", "election"],
}

# Region keywords for auto-classification
REGION_KEYWORDS: Dict[str, List[str]] = {
    "United States": ["washington", "white house", "congress", "pentagon", "us ", "america", "biden", "trump"],
    "Russia": ["moscow", "kremlin", "putin", "russia", "russian"],
    "China": ["beijing", "xi jinping", "china", "chinese", "taiwan strait"],
    "Ukraine": ["kyiv", "zelensky", "ukraine", "ukrainian", "donbas"],
    "Middle East": ["gaza", "hamas", "hezbollah", "iran", "israel", "idf"],
    "Europe": ["brussels", "eu ", "european union", "nato", "berlin", "paris"],
}


def classify_region(title: str, summary: str = "") -> Optional[str]:
    """Auto-classify article region from title and summary."""
    text = f"{title} {summary}".lower()
    for region, keywords in REGION_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return region
    return None


def extract_geo_coordinates(region: Optional[str] = None, location: Optional[str] = None) -> Optional[Tuple[float, float]]:
    """Get lat/lon for a region or location string."""
    if location and location in GEOLOCATIONS:
        return GEOLOCATIONS[location]
    if region and region in GEOLOCATIONS:
        return GEOLOCATIONS[region]
    return None


def detect_crisis(title: str, summary: str = "") -> Optional[CrisisAlert]:
    """Detect crisis events from article text and assign severity."""
    text = f"{title} {summary}".lower()
    for severity in ["critical", "high", "medium", "low"]:
        for keyword in CRISIS_KEYWORDS[severity]:
            if keyword in text:
                region = classify_region(title, summary)
                return CrisisAlert(
                    alert_type="breaking" if severity in ("critical", "high") else "update",
                    severity=severity,
                    headline=title,
                    source="",
                    region=region or "Global",
                    timestamp=datetime.now(),
                    confidence=0.8 if severity in ("critical", "high") else 0.5,
                )
    return None


def compute_relevance(title: str, summary: str = "", focus_regions: Optional[Set[str]] = None) -> float:
    """Compute relevance score based on focus regions and keywords."""
    text = f"{title} {summary}".lower()
    score = 0.3  # base relevance
    if focus_regions:
        region = classify_region(title, summary)
        if region and region in focus_regions:
            score += 0.4
    crisis = detect_crisis(title, summary)
    if crisis:
        severity_map = {"critical": 0.3, "high": 0.25, "medium": 0.15, "low": 0.05}
        score += severity_map.get(crisis.severity, 0.0)
    return min(score, 1.0)


def deduplicate_articles(articles: List[NewsArticle]) -> List[NewsArticle]:
    """Remove duplicate articles by ID."""
    seen: Set[str] = set()
    unique: List[NewsArticle] = []
    for article in articles:
        if article.article_id not in seen:
            seen.add(article.article_id)
            unique.append(article)
    return unique


def filter_by_age(articles: List[NewsArticle], max_age_days: int = 7) -> List[NewsArticle]:
    """Filter out articles older than max_age_days."""
    cutoff = datetime.now() - timedelta(days=max_age_days)
    return [a for a in articles if a.published and a.published > cutoff]


def sort_by_relevance(articles: List[NewsArticle]) -> List[NewsArticle]:
    """Sort articles by relevance score descending."""
    return sorted(articles, key=lambda a: a.relevance_score, reverse=True)


def aggregate_by_region(articles: List[NewsArticle]) -> Dict[str, List[NewsArticle]]:
    """Group articles by region."""
    result: Dict[str, List[NewsArticle]] = {}
    for article in articles:
        region = article.location or classify_region(article.title, article.summary) or "Unknown"
        result.setdefault(region, []).append(article)
    return result


def count_crisis_events(articles: List[NewsArticle]) -> Dict[str, int]:
    """Count crisis events by severity."""
    counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for article in articles:
        crisis = detect_crisis(article.title, article.summary)
        if crisis:
            counts[crisis.severity] = counts.get(crisis.severity, 0) + 1
    return counts


def generate_situation_summary(articles: List[NewsArticle]) -> Dict[str, object]:
    """Generate a summary of the current situation."""
    filtered = filter_by_age(articles, max_age_days=1)
    by_region = aggregate_by_region(filtered)
    crisis_counts = count_crisis_events(filtered)
    total_crisis = sum(crisis_counts.values())
    top_regions = sorted(by_region.keys(), key=lambda r: len(by_region[r]), reverse=True)[:5]
    return {
        "total_articles": len(filtered),
        "total_crisis_events": total_crisis,
        "crisis_by_severity": crisis_counts,
        "top_regions": top_regions,
        "articles_by_region": {r: len(arts) for r, arts in by_region.items()},
        "generated_at": datetime.now().isoformat(),
    }
