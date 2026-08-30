"""
Geopolitical Risk Service — Extracted from geopolitics-ml and GDELT patterns.

Provides geopolitical event detection, risk scoring, sector impact assessment,
and market impact prediction using pure functions. Inspired by the geopolitics-ml
framework's event taxonomy and risk quantification approach.

All functions are pure — no DB, no async, just analysis math.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    CONFLICT = "conflict"
    SANCTIONS = "sanctions"
    ELECTION = "election"
    TRADE_WAR = "trade_war"
    TERRORISM = "terrorism"
    NATURAL_DISASTER = "natural_disaster"
    PANDEMIC = "pandemic"
    REGULATORY = "regulatory"
    DIPLOMATIC = "diplomatic"
    ENERGY = "energy"
    CYBER = "cyber"
    NUCLEAR = "nuclear"


class MarketDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"


@dataclass
class GeopoliticalEvent:
    """Detected geopolitical event."""
    event_id: str
    category: EventCategory
    title: str
    description: str
    countries: List[str]
    risk_level: RiskLevel
    risk_score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    timestamp: str
    source: str = ""
    keywords: List[str] = field(default_factory=list)


@dataclass
class SectorImpact:
    """Impact assessment for a market sector."""
    sector: str
    direction: MarketDirection
    magnitude: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    reasoning: str = ""
    timeframe: str = "short_term"  # short_term, medium_term, long_term


@dataclass
class GeopoliticalRiskIndex:
    """Composite geopolitical risk index."""
    overall_score: float  # 0.0-100.0
    overall_level: RiskLevel
    component_scores: Dict[str, float]  # category -> score
    active_events: int
    trending_categories: List[str]
    market_outlook: MarketDirection
    volatility_forecast: float  # expected VIX impact


# ---------------------------------------------------------------------------
# Keyword dictionaries (simplified — production would use NLP models)
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: Dict[EventCategory, List[str]] = {
    EventCategory.CONFLICT: [
        "war", "invasion", "military", "troops", "missile", "bombing",
        "ceasefire", "conflict", "battle", "air strike", "offensive",
        "nato", "army", "navy", "combat", "casualties",
    ],
    EventCategory.SANCTIONS: [
        "sanction", "embargo", "trade restriction", "blacklist",
        "asset freeze", "tariff", "import ban", "export control",
        "ofac", "sanctions list", "economic pressure",
    ],
    EventCategory.ELECTION: [
        "election", "vote", "poll", "ballot", "campaign", "candidate",
        "primary", "caucus", "electoral", "democrat", "republican",
        "parliament", "referendum", "impeach",
    ],
    EventCategory.TRADE_WAR: [
        "trade war", "tariff", "import duty", "trade deficit",
        "trade agreement", "free trade", "protectionist", "retaliation",
        "supply chain", "decouple", "reshoring",
    ],
    EventCategory.TERRORISM: [
        "terrorist", "attack", "bombing", "extremist", "radical",
        "isis", "al-qaeda", "insurgency", "bomb", "hostage",
    ],
    EventCategory.NATURAL_DISASTER: [
        "earthquake", "hurricane", "typhoon", "flood", "tsunami",
        "volcano", "wildfire", "drought", "cyclone", "disaster",
    ],
    EventCategory.PANDEMIC: [
        "pandemic", "outbreak", "virus", "epidemic", "quarantine",
        "lockdown", "vaccine", "infection", "mortality", "variant",
    ],
    EventCategory.REGULATORY: [
        "regulation", "compliance", "antitrust", "monopoly",
        "data privacy", "gdpr", "sec ruling", "fda approval",
        "ban", "investigation", "lawsuit",
    ],
    EventCategory.DIPLOMATIC: [
        "summit", "negotiation", "treaty", "alliance", "embassy",
        "diplomatic", "bilateral", "multilateral", "accord",
        "relationship", "dialogue",
    ],
    EventCategory.ENERGY: [
        "oil", "opec", "natural gas", "pipeline", "energy crisis",
        "petroleum", "crude", "lng", "energy security", "renewable",
        "nuclear energy", "power grid",
    ],
    EventCategory.CYBER: [
        "cyber attack", "hack", "data breach", "ransomware",
        "espionage", "cybersecurity", "vulnerability", "exploit",
        "ddos", "phishing", "state-sponsored",
    ],
    EventCategory.NUCLEAR: [
        "nuclear", "warhead", "uranium", "enrichment", "radiation",
        "npt", "non-proliferation", "test", "deterrent", "arsenal",
    ],
}

_SECTOR_SENSITIVITY: Dict[EventCategory, Dict[str, float]] = {
    EventCategory.CONFLICT: {
        "defense": 0.9, "energy": 0.7, "insurance": 0.6,
        "aerospace": 0.5, "technology": -0.3, "consumer": -0.2,
    },
    EventCategory.SANCTIONS: {
        "energy": 0.6, "finance": 0.5, "agriculture": 0.4,
        "technology": -0.4, "consumer": -0.3, "industrial": -0.2,
    },
    EventCategory.ELECTION: {
        "healthcare": 0.5, "energy": 0.4, "finance": 0.3,
        "technology": 0.3, "defense": 0.2, "consumer": 0.1,
    },
    EventCategory.TRADE_WAR: {
        "industrial": -0.6, "technology": -0.5, "consumer": -0.4,
        "agriculture": -0.3, "domestic_retail": 0.2, "defense": 0.1,
    },
    EventCategory.ENERGY: {
        "energy": 0.8, "utilities": 0.5, "transportation": -0.4,
        "industrial": -0.3, "consumer": -0.2, "renewable": 0.6,
    },
    EventCategory.CYBER: {
        "technology": -0.5, "finance": -0.4, "healthcare": -0.3,
        "defense": 0.3, "insurance": -0.2, "consumer": -0.2,
    },
    EventCategory.NUCLEAR: {
        "defense": 0.8, "energy": 0.5, "nuclear": 0.7,
        "insurance": -0.6, "consumer": -0.4, "real_estate": -0.3,
    },
    EventCategory.PANDEMIC: {
        "healthcare": 0.6, "technology": 0.4, "pharma": 0.5,
        "travel": -0.8, "entertainment": -0.7, "consumer": -0.5,
    },
}


# ---------------------------------------------------------------------------
# Event detection
# ---------------------------------------------------------------------------

def detect_event_category(text: str) -> List[Tuple[EventCategory, float]]:
    """
    Detect geopolitical event categories from text using keyword matching.
    
    Returns list of (category, confidence) sorted by confidence descending.
    
    Args:
        text: Event description text
    
    Returns:
        List of (EventCategory, confidence_score) pairs
    """
    text_lower = text.lower()
    scores: Dict[EventCategory, float] = {}
    
    for category, keywords in _CATEGORY_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text_lower)
        if matches > 0:
            # Confidence based on keyword density
            confidence = min(1.0, matches / max(3, len(keywords) * 0.2))
            scores[category] = confidence
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def extract_countries(text: str) -> List[str]:
    """
    Extract country mentions from text.
    
    Simplified implementation — production would use NER models.
    """
    # Common country names and short forms
    countries = [
        "united states", "us", "usa", "america", "china", "russia",
        "ukrussia", "ukraine", "european union", "eu", "india",
        "japan", "south korea", "korea", "iran", "israel", "saudi arabia",
        "turkey", "brazil", "mexico", "canada", "australia", "germany",
        "france", "uk", "united kingdom", "britain", "nato", "taiwan",
        "pakistan", "north korea", "dprk", "cuba", "venezuela", "syria",
        "iraq", "afghanistan", "libya", "egypt", "south africa",
    ]
    
    text_lower = text.lower()
    found = []
    
    for country in countries:
        if country in text_lower:
            # Normalize
            name = country.upper() if len(country) <= 3 else country.title()
            if name not in found:
                found.append(name)
    
    return found


def calculate_event_risk_score(
    category: EventCategory,
    countries: List[str],
    text: str,
) -> float:
    """
    Calculate a risk score for a geopolitical event.
    
    Risk factors:
    - Category base risk (conflict > diplomatic)
    - Country involvement (major economies = higher impact)
    - Urgency indicators in text
    - Multiplicity of categories
    
    Returns:
        Risk score between 0.0 and 1.0
    """
    # Category base risk weights
    category_weights = {
        EventCategory.NUCLEAR: 0.95,
        EventCategory.CONFLICT: 0.85,
        EventCategory.TERRORISM: 0.80,
        EventCategory.PANDEMIC: 0.75,
        EventCategory.CYBER: 0.70,
        EventCategory.SANCTIONS: 0.65,
        EventCategory.TRADE_WAR: 0.60,
        EventCategory.ENERGY: 0.55,
        EventCategory.REGULATORY: 0.45,
        EventCategory.NATURAL_DISASTER: 0.50,
        EventCategory.ELECTION: 0.40,
        EventCategory.DIPLOMATIC: 0.35,
    }
    
    base_risk = category_weights.get(category, 0.5)
    
    # Country impact multiplier
    major_economies = {"US", "CHINA", "EU", "JAPAN", "GERMANY", "UK", "INDIA", "FRANCE"}
    country_multiplier = 1.0
    if any(c.upper() in major_economies for c in countries):
        country_multiplier = 1.3
    if len(countries) > 3:
        country_multiplier *= 1.2  # Multi-country events are more impactful
    
    # Urgency indicators
    urgency_keywords = [
        "immediate", "urgent", "breaking", "escalat", "crisis",
        "emergency", "emergency", "alert", "severe", "devastating",
    ]
    text_lower = text.lower()
    urgency_boost = sum(0.05 for kw in urgency_keywords if kw in text_lower)
    
    score = base_risk * country_multiplier + urgency_boost
    return min(1.0, max(0.0, score))


def analyze_event(
    text: str,
    title: str = "",
    source: str = "",
    timestamp: str = "",
) -> Optional[GeopoliticalEvent]:
    """
    Full event analysis pipeline.
    
    Args:
        text: Event description
        title: Event title
        source: News source
        timestamp: Event timestamp
    
    Returns:
        GeopoliticalEvent if detected, None if no event found
    """
    categories = detect_event_category(text)
    if not categories:
        return None
    
    primary_category, confidence = categories[0]
    countries = extract_countries(text)
    risk_score = calculate_event_risk_score(primary_category, countries, text)
    
    # Map risk score to level
    if risk_score >= 0.8:
        level = RiskLevel.CRITICAL
    elif risk_score >= 0.6:
        level = RiskLevel.HIGH
    elif risk_score >= 0.3:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW
    
    # Extract keywords
    keywords = []
    for cat, _ in categories[:3]:
        cat_keywords = _CATEGORY_KEYWORDS.get(cat, [])
        text_lower = text.lower()
        keywords.extend([kw for kw in cat_keywords if kw in text_lower][:3])
    
    event_id = f"geo_{abs(hash(title + timestamp)) % 10**8:08d}"
    
    return GeopoliticalEvent(
        event_id=event_id,
        category=primary_category,
        title=title or text[:100],
        description=text,
        countries=countries,
        risk_level=level,
        risk_score=risk_score,
        confidence=confidence,
        timestamp=timestamp,
        source=source,
        keywords=keywords[:10],
    )


# ---------------------------------------------------------------------------
# Sector impact assessment
# ---------------------------------------------------------------------------

def assess_sector_impact(
    event: GeopoliticalEvent,
) -> List[SectorImpact]:
    """
    Assess impact of a geopolitical event on market sectors.
    
    Uses pre-defined sensitivity matrices to estimate how each
    sector is likely affected.
    """
    sensitivities = _SECTOR_SENSITIVITY.get(event.category, {})
    
    impacts = []
    for sector, base_sensitivity in sensitivities.items():
        direction = MarketDirection.BULLISH if base_sensitivity > 0 else MarketDirection.BEARISH
        magnitude = abs(base_sensitivity) * event.risk_score
        
        # Adjust for country involvement
        if event.countries:
            magnitude *= (1.0 + len(event.countries) * 0.05)
        magnitude = min(1.0, magnitude)
        
        impacts.append(SectorImpact(
            sector=sector,
            direction=direction,
            magnitude=magnitude,
            confidence=event.confidence * 0.8,
            reasoning=f"{event.category.value} event affecting {', '.join(event.countries)}",
            timeframe="short_term" if event.risk_score > 0.7 else "medium_term",
        ))
    
    return sorted(impacts, key=lambda x: x.magnitude, reverse=True)


# ---------------------------------------------------------------------------
# Composite risk index
# ---------------------------------------------------------------------------

def calculate_risk_index(
    events: List[GeopoliticalEvent],
) -> GeopoliticalRiskIndex:
    """
    Calculate composite geopolitical risk index from active events.
    
    Inspired by the Global Geopolitical Risk Index (GGRI) methodology.
    """
    if not events:
        return GeopoliticalRiskIndex(
            overall_score=10.0,
            overall_level=RiskLevel.LOW,
            component_scores={},
            active_events=0,
            trending_categories=[],
            market_outlook=MarketDirection.NEUTRAL,
            volatility_forecast=15.0,
        )
    
    # Category scores
    category_scores: Dict[str, List[float]] = {}
    for event in events:
        cat = event.category.value
        if cat not in category_scores:
            category_scores[cat] = []
        category_scores[cat].append(event.risk_score)
    
    component_scores = {}
    for cat, scores in category_scores.items():
        component_scores[cat] = max(scores) * (1 + math.log(len(scores) + 1) * 0.1)
    
    # Overall score (weighted max with event count boost)
    max_category_score = max(component_scores.values()) if component_scores else 0
    event_count_boost = math.log(len(events) + 1) * 5
    overall_score = min(100, max_category_score * 80 + event_count_boost)
    
    # Overall level
    if overall_score >= 80:
        level = RiskLevel.CRITICAL
    elif overall_score >= 60:
        level = RiskLevel.HIGH
    elif overall_score >= 30:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW
    
    # Trending categories (most frequent)
    cat_counts = {}
    for event in events:
        cat = event.category.value
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    trending = sorted(cat_counts.keys(), key=lambda c: cat_counts[c], reverse=True)[:3]
    
    # Market outlook
    avg_risk = sum(e.risk_score for e in events) / len(events)
    if avg_risk > 0.7:
        outlook = MarketDirection.BEARISH
    elif avg_risk > 0.5:
        outlook = MarketDirection.VOLATILE
    elif avg_risk < 0.2:
        outlook = MarketDirection.BULLISH
    else:
        outlook = MarketDirection.NEUTRAL
    
    # VIX forecast (baseline 15, +5 per 0.1 risk above 0.5)
    vix_forecast = 15.0 + max(0, (avg_risk - 0.5) * 100)
    
    return GeopoliticalRiskIndex(
        overall_score=round(overall_score, 1),
        overall_level=level,
        component_scores={k: round(v, 3) for k, v in component_scores.items()},
        active_events=len(events),
        trending_categories=trending,
        market_outlook=outlook,
        volatility_forecast=round(vix_forecast, 1),
    )
