"""
Tension Pipeline — Extracted from tensionr patterns.

Real-time intelligence pipeline with:
- Multi-domain signal fetching
- NLP emotion classification
- Strategic insight generation
- Global Threat Index scoring
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class Article:
    title: str
    url: str = ""
    source: str = ""
    source_country: str = ""
    published_at: str = ""
    narrative_emotion: str = "neutral"
    manipulation_score: int = 0
    keywords: List[str] = field(default_factory=list)


@dataclass
class FlightTrack:
    icao24: str
    callsign: str
    origin_country: str
    latitude: float
    longitude: float
    altitude: float
    velocity: float
    is_military: bool = False


@dataclass
class MarketSignal:
    vix: float = 0.0
    gold_price: float = 0.0
    dxy: float = 0.0
    oil_price: float = 0.0
    btc_price: float = 0.0
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class IntelligenceReport:
    articles: List[Article]
    flight_tracks: List[FlightTrack]
    market_signals: MarketSignal
    gti_score: float = 0.0
    sitrep: str = ""
    strategic_insight: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class StageTimer:
    """Track timing for pipeline stages."""

    def __init__(self) -> None:
        self.start = time.monotonic()
        self.last = self.start
        self.stages: Dict[str, float] = {}

    def lap(self, stage: str) -> None:
        now = time.monotonic()
        self.stages[stage] = now - self.last
        self.last = now

    def elapsed(self) -> float:
        return time.monotonic() - self.start


def classify_emotion(title: str) -> str:
    """Simple emotion classification (placeholder for ML model)."""
    fear_words = ["war", "attack", "crisis", "threat", "danger", "bomb", "missile"]
    anger_words = ["protest", "riots", "unrest", "violence", "clash"]
    positive_words = ["peace", "agreement", "deal", "cooperation", "summit"]

    title_lower = title.lower()
    if any(w in title_lower for w in fear_words):
        return "fear"
    if any(w in title_lower for w in anger_words):
        return "anger"
    if any(w in title_lower for w in positive_words):
        return "positive"
    return "neutral"


def calculate_manipulation_score(title: str) -> int:
    """Estimate manipulation/bias risk (0-10)."""
    score = 0
    sensational = ["shocking", "unbelievable", "breaking", "urgent", "exclusive"]
    for word in sensational:
        if word in title.lower():
            score += 2
    return min(score, 10)


def deduce_country(title: str) -> str:
    """Deduce country from article title."""
    countries = {
        "china": "China", "russia": "Russia", "ukraine": "Ukraine",
        "iran": "Iran", "north korea": "North Korea", "taiwan": "Taiwan",
        "israel": "Israel", "gaza": "Palestine", "syria": "Syria",
    }
    title_lower = title.lower()
    for keyword, country in countries.items():
        if keyword in title_lower:
            return country
    return "Unknown"


def calculate_gti(
    articles: List[Article],
    market: MarketSignal,
    flights: List[FlightTrack],
) -> float:
    """Calculate Global Threat Index (0-100)."""
    # Article sentiment component
    fear_count = sum(1 for a in articles if a.narrative_emotion == "fear")
    anger_count = sum(1 for a in articles if a.narrative_emotion == "anger")
    total_articles = max(len(articles), 1)
    sentiment_score = (fear_count * 2 + anger_count) / total_articles * 20

    # Market volatility component
    vix_score = min(market.vix / 50 * 30, 30) if market.vix > 0 else 10
    gold_score = min((market.gold_price - 2000) / 500 * 10, 10) if market.gold_price > 0 else 5

    # Military flight component
    military_flights = sum(1 for f in flights if f.is_military)
    military_score = min(military_flights / 50 * 15, 15)

    gti = sentiment_score + vix_score + gold_score + military_score
    return min(max(gti, 0), 100)


def generate_sitrep(report: IntelligenceReport) -> str:
    """Generate a situation report summary."""
    parts = []
    if report.articles:
        top_emotions = {}
        for a in report.articles:
            top_emotions[a.narrative_emotion] = top_emotions.get(a.narrative_emotion, 0) + 1
        dominant = max(top_emotions, key=top_emotions.get) if top_emotions else "neutral"
        parts.append(f"Overall narrative tone: {dominant}")

    if report.flight_tracks:
        military = sum(1 for f in report.flight_tracks if f.is_military)
        parts.append(f"{len(report.flight_tracks)} flight tracks ({military} military)")

    if report.market_signals.vix > 30:
        parts.append(f"Elevated VIX at {report.market_signals.vix:.1f}")

    gti = report.gti_score
    if gti > 70:
        parts.append(f"HIGH THREAT LEVEL (GTI: {gti:.1f})")
    elif gti > 40:
        parts.append(f"ELEVATED THREAT LEVEL (GTI: {gti:.1f})")
    else:
        parts.append(f"Baseline threat level (GTI: {gti:.1f})")

    return " | ".join(parts)


class IntelligencePipeline:
    """Orchestrate the intelligence gathering pipeline."""

    def __init__(self) -> None:
        self.articles: List[Article] = []
        self.flights: List[FlightTrack] = []
        self.market = MarketSignal()

    def process_articles(self, raw_articles: List[Dict[str, Any]], max_articles: int = 200) -> List[Article]:
        """Process raw articles with NLP enrichment."""
        processed = []
        for raw in raw_articles[:max_articles]:
            title = raw.get("title", "")
            article = Article(
                title=title,
                url=raw.get("url", ""),
                source=raw.get("source", ""),
                source_country=deduce_country(title),
                published_at=raw.get("seendate", ""),
                narrative_emotion=classify_emotion(title),
                manipulation_score=calculate_manipulation_score(title),
                keywords=title.lower().split()[:5],
            )
            processed.append(article)
        self.articles = processed
        return processed

    def update_market(self, signals: MarketSignal) -> None:
        self.market = signals

    def update_flights(self, tracks: List[FlightTrack]) -> None:
        self.flights = tracks

    def generate_report(self) -> IntelligenceReport:
        """Generate a complete intelligence report."""
        gti = calculate_gti(self.articles, self.market, self.flights)

        report = IntelligenceReport(
            articles=self.articles,
            flight_tracks=self.flights,
            market_signals=self.market,
            gti_score=gti,
        )
        report.sitrep = generate_sitrep(report)
        return report
