"""
NewsMap Globe Data Service for fin-scrape
Extracted from: three-js (3D globe visualization with real-time news)
Patterns: Geocoded news markers, AI location analysis, interactive globe data,
          source filtering, category management, timeline playback
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class NewsCategory(Enum):
    WORLD = "world"
    POLITICS = "politics"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    HEALTH = "health"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"


class MarkerPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    BREAKING = 4


@dataclass
class GeoPosition:
    lat: float
    lng: float
    name: str = ""


@dataclass
class GlobeMarker:
    id: str
    position: GeoPosition
    title: str
    description: str
    source: str
    url: str
    category: NewsCategory
    priority: MarkerPriority
    timestamp: datetime
    sentiment: float = 0.0  # -1 to 1
    radius: float = 1.0  # visual size on globe
    color: str = "#4CAF50"
    related_markers: list[str] = field(default_factory=list)


@dataclass
class GlobeConfig:
    rotation_speed: float = 0.001
    auto_rotate: bool = True
    show_atmosphere: bool = True
    marker_clustering: bool = True
    max_visible_markers: int = 200
    default_category: Optional[NewsCategory] = None
    time_range_hours: int = 24


# ─── Category Colors ───────────────────────────────────────────────────

CATEGORY_COLORS = {
    NewsCategory.WORLD: "#2196F3",
    NewsCategory.POLITICS: "#9C27B0",
    NewsCategory.BUSINESS: "#4CAF50",
    NewsCategory.TECHNOLOGY: "#00BCD4",
    NewsCategory.SCIENCE: "#FF9800",
    NewsCategory.HEALTH: "#E91E63",
    NewsCategory.SPORTS: "#8BC34A",
    NewsCategory.ENTERTAINMENT: "#FF5722",
}


# ─── Geocoding ─────────────────────────────────────────────────────────

def geocode_headline(headline: str, known_locations: dict[str, GeoPosition] = None) -> Optional[GeoPosition]:
    """Simple geocoding from headline text using known location database."""
    if known_locations is None:
        known_locations = DEFAULT_LOCATIONS

    headline_lower = headline.lower()
    for name, position in known_locations.items():
        if name.lower() in headline_lower:
            return position
    return None


DEFAULT_LOCATIONS = {
    "washington": GeoPosition(38.9, -77.0, "Washington DC"),
    "beijing": GeoPosition(39.9, 116.4, "Beijing"),
    "moscow": GeoPosition(55.8, 37.6, "Moscow"),
    "london": GeoPosition(51.5, -0.1, "London"),
    "paris": GeoPosition(48.9, 2.3, "Paris"),
    "tokyo": GeoPosition(35.7, 139.7, "Tokyo"),
    "new york": GeoPosition(40.7, -74.0, "New York"),
    "kyiv": GeoPosition(50.4, 30.5, "Kyiv"),
    "taipei": GeoPosition(25.0, 121.5, "Taipei"),
    "gaza": GeoPosition(31.5, 34.5, "Gaza"),
    "tel aviv": GeoPosition(32.1, 34.8, "Tel Aviv"),
    "berlin": GeoPosition(52.5, 13.4, "Berlin"),
    "delhi": GeoPosition(28.6, 77.2, "Delhi"),
    "mumbai": GeoPosition(19.1, 72.9, "Mumbai"),
    "sydney": GeoPosition(-33.9, 151.2, "Sydney"),
    "cairo": GeoPosition(30.0, 31.2, "Cairo"),
    "nairobi": GeoPosition(-1.3, 36.8, "Nairobi"),
    "sao paulo": GeoPosition(-23.5, -46.6, "São Paulo"),
    "mexico city": GeoPosition(19.4, -99.1, "Mexico City"),
    "seoul": GeoPosition(37.6, 127.0, "Seoul"),
    "taiwan": GeoPosition(23.7, 121.0, "Taiwan"),
    "ukraine": GeoPosition(49.0, 32.0, "Ukraine"),
}


# ─── Globe Data Generation ─────────────────────────────────────────────

def generate_globe_markers(
    news_items: list[dict],
    config: GlobeConfig = None,
) -> list[GlobeMarker]:
    """Generate globe markers from news items."""
    config = config or GlobeConfig()
    markers = []

    for i, item in enumerate(news_items):
        title = item.get("title", "")
        position = geocode_headline(title)
        if not position:
            continue

        category = _categorize_news(title, item.get("description", ""))
        priority = _assess_priority(title, item.get("description", ""))
        sentiment = item.get("sentiment", 0.0)

        marker = GlobeMarker(
            id=f"marker-{i}",
            position=position,
            title=title,
            description=item.get("description", ""),
            source=item.get("source", "unknown"),
            url=item.get("url", ""),
            category=category,
            priority=priority,
            timestamp=item.get("timestamp", datetime.now()),
            sentiment=sentiment,
            radius=1.0 + priority.value * 0.5,
            color=CATEGORY_COLORS.get(category, "#4CAF50"),
        )
        markers.append(marker)

    # Filter by time range
    cutoff = datetime.now().timestamp() - config.time_range_hours * 3600
    markers = [m for m in markers if m.timestamp.timestamp() >= cutoff]

    # Limit visible markers
    markers.sort(key=lambda m: m.priority.value, reverse=True)
    return markers[:config.max_visible_markers]


def _categorize_news(title: str, description: str) -> NewsCategory:
    """Simple keyword-based news categorization."""
    text = (title + " " + description).lower()
    if any(w in text for w in ["election", "parliament", "congress", "president", "minister"]):
        return NewsCategory.POLITICS
    if any(w in text for w in ["stock", "market", "economy", "trade", "gdp", "inflation"]):
        return NewsCategory.BUSINESS
    if any(w in text for w in ["ai", "tech", "software", "startup", "google", "apple"]):
        return NewsCategory.TECHNOLOGY
    if any(w in text for w in ["study", "research", "space", "climate", "discovery"]):
        return NewsCategory.SCIENCE
    if any(w in text for w in ["health", "vaccine", "hospital", "disease", "medical"]):
        return NewsCategory.HEALTH
    if any(w in text for w in ["game", "match", "tournament", "championship", "olympics"]):
        return NewsCategory.SPORTS
    if any(w in text for w in ["movie", "music", "celebrity", "album", "film"]):
        return NewsCategory.ENTERTAINMENT
    return NewsCategory.WORLD


def _assess_priority(title: str, description: str) -> MarkerPriority:
    """Assess news priority based on keywords."""
    text = (title + " " + description).lower()
    if any(w in text for w in ["breaking", "urgent", "emergency", "crisis"]):
        return MarkerPriority.BREAKING
    if any(w in text for w in ["war", "attack", "invasion", "earthquake", "tsunami"]):
        return MarkerPriority.HIGH
    if any(w in text for w in ["announce", "report", "launch", "sign"]):
        return MarkerPriority.MEDIUM
    return MarkerPriority.LOW


def filter_markers(
    markers: list[GlobeMarker],
    categories: list[NewsCategory] = None,
    sources: list[str] = None,
    min_priority: MarkerPriority = MarkerPriority.LOW,
    search_query: str = "",
) -> list[GlobeMarker]:
    """Filter globe markers by various criteria."""
    result = markers

    if categories:
        result = [m for m in result if m.category in categories]
    if sources:
        result = [m for m in result if m.source in sources]
    if min_priority:
        result = [m for m in result if m.priority.value >= min_priority.value]
    if search_query:
        query_lower = search_query.lower()
        result = [m for m in result if query_lower in m.title.lower() or query_lower in m.description.lower()]

    return result


def get_globe_summary(markers: list[GlobeMarker]) -> dict:
    """Get summary statistics for globe markers."""
    if not markers:
        return {"total": 0}

    categories = {}
    sources = {}
    priority_counts = {}
    sentiments = []

    for m in markers:
        categories[m.category.value] = categories.get(m.category.value, 0) + 1
        sources[m.source] = sources.get(m.source, 0) + 1
        priority_counts[m.priority.name] = priority_counts.get(m.priority.name, 0) + 1
        sentiments.append(m.sentiment)

    return {
        "total": len(markers),
        "categories": categories,
        "sources": sources,
        "priorities": priority_counts,
        "avg_sentiment": round(sum(sentiments) / len(sentiments), 3) if sentiments else 0,
        "time_range": {
            "earliest": min(m.timestamp.isoformat() for m in markers),
            "latest": max(m.timestamp.isoformat() for m in markers),
        },
    }
