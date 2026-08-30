"""
OSINT Intelligence Engine — Open-Source Intelligence for geopolitical analysis.

Inspired by war-probability-osint.
Provides GDELT integration, conflict monitoring, and escalation prediction.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class OSINTArticle:
    """Represents a news article from OSINT sources."""
    title: str
    source: str
    url: str
    timestamp: datetime
    tone: float = 0.0  # Sentiment tone (-10 to +10)
    theme: str = ""
    locations: List[str] = field(default_factory=list)
    language: str = "english"
    keywords: List[str] = field(default_factory=list)


@dataclass
class ConflictIndicator:
    """A conflict/escalation indicator."""
    indicator_type: str  # military, diplomatic, economic, nuclear
    severity: str  # low, medium, high, critical
    description: str
    source: str
    timestamp: datetime
    confidence: float = 0.0


@dataclass
class EscalationPrediction:
    """Prediction of conflict escalation probability."""
    region: str
    probability: float  # 0.0 to 1.0
    timeframe: str  # "24h", "7d", "30d"
    contributing_factors: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


# Conflict-related search themes
CONFLICT_QUERIES = [
    "military escalation",
    "troop deployment",
    "missile strike",
    "naval blockade",
    "airspace closure",
    "diplomatic expulsion",
    "sanctions threat",
    "nuclear threat",
    "carrier strike group",
    "defense readiness",
]

# Country pairs monitored for bilateral tension
COUNTRY_PAIRS = [
    ("United States", "Iran"),
    ("United States", "China"),
    ("United States", "Russia"),
    ("United States", "North Korea"),
    ("Israel", "Iran"),
    ("NATO", "Russia"),
    ("India", "Pakistan"),
    ("China", "Taiwan"),
]

# Severity keywords
SEVERITY_KEYWORDS = {
    "critical": ["nuclear", "declaration of war", "invasion", "mass casualty", "bioweapon"],
    "high": ["military strike", "sanctions imposed", "troops deployed", "missile launch"],
    "medium": ["tensions rise", "diplomatic crisis", "trade war", "military exercise"],
    "low": ["protest", "diplomatic meeting", "trade talks", "policy change"],
}


def classify_severity(text: str) -> str:
    """Classify conflict severity from text."""
    text_lower = text.lower()
    for severity in ["critical", "high", "medium", "low"]:
        for keyword in SEVERITY_KEYWORDS[severity]:
            if keyword in text_lower:
                return severity
    return "low"


def detect_conflict_indicators(articles: List[OSINTArticle]) -> List[ConflictIndicator]:
    """Detect conflict indicators from articles."""
    indicators: List[ConflictIndicator] = []
    for article in articles:
        severity = classify_severity(f"{article.title} {article.theme}")
        if severity != "low":
            indicators.append(ConflictIndicator(
                indicator_type="military" if "military" in article.theme.lower() else "diplomatic",
                severity=severity,
                description=article.title,
                source=article.source,
                timestamp=article.timestamp,
                confidence=0.7 if severity in ("critical", "high") else 0.4,
            ))
    return indicators


def calculate_tension_score(indicators: List[ConflictIndicator]) -> float:
    """Calculate overall tension score from indicators (0.0 to 1.0)."""
    if not indicators:
        return 0.0

    severity_scores = {"critical": 1.0, "high": 0.75, "medium": 0.5, "low": 0.25}
    total = sum(severity_scores.get(i.severity, 0) * i.confidence for i in indicators)
    return min(total / len(indicators), 1.0)


def analyze_tone_sentiment(articles: List[OSINTArticle]) -> Dict[str, float]:
    """Analyze sentiment tone across articles."""
    if not articles:
        return {"average_tone": 0.0, "positive_ratio": 0.5, "negative_ratio": 0.5}

    tones = [a.tone for a in articles]
    avg_tone = sum(tones) / len(tones)
    positive = sum(1 for t in tones if t > 0) / len(tones)
    negative = sum(1 for t in tones if t < 0) / len(tones)

    return {
        "average_tone": avg_tone,
        "positive_ratio": positive,
        "negative_ratio": negative,
    }


def predict_escalation(
    region: str,
    indicators: List[ConflictIndicator],
    tension_score: float,
    timeframe: str = "7d"
) -> EscalationPrediction:
    """Predict escalation probability for a region."""
    # Simple model: tension score * indicator density
    relevant = [i for i in indicators if region.lower() in i.description.lower()]
    density = len(relevant) / max(len(indicators), 1)

    probability = min(tension_score * (1 + density), 1.0)

    factors = [
        f"Tension score: {tension_score:.2f}",
        f"Relevant indicators: {len(relevant)}",
        f"Indicator density: {density:.2f}",
    ]

    return EscalationPrediction(
        region=region,
        probability=probability,
        timeframe=timeframe,
        contributing_factors=factors,
        confidence=0.6 if len(relevant) > 3 else 0.3,
    )


def generate_intelligence_report(
    articles: List[OSINTArticle],
    region: str = "Global"
) -> Dict[str, object]:
    """Generate a comprehensive intelligence report."""
    indicators = detect_conflict_indicators(articles)
    tension = calculate_tension_score(indicators)
    sentiment = analyze_tone_sentiment(articles)
    prediction = predict_escalation(region, indicators, tension)

    return {
        "region": region,
        "total_articles": len(articles),
        "conflict_indicators": len(indicators),
        "tension_score": tension,
        "sentiment": sentiment,
        "escalation_prediction": {
            "probability": prediction.probability,
            "timeframe": prediction.timeframe,
            "confidence": prediction.confidence,
            "factors": prediction.contributing_factors,
        },
        "generated_at": datetime.now().isoformat(),
    }
