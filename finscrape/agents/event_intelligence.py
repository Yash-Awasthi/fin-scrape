"""
Event intelligence — detects market-moving events and generates trading signals.

Inspired by Acuity Trading's event intelligence approach:
identify WHAT is happening, WHY it matters, and WHAT to watch next.

Pure functions for detection + assessment. No AI calls in extraction logic.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class EventType(str, Enum):
    EARNINGS = "earnings"
    MERGER_ACQUISITION = "merger_acquisition"
    REGULATORY = "regulatory"
    GEOPOLITICAL = "geopolitical"
    PRODUCT_LAUNCH = "product_launch"
    EXECUTIVE_CHANGE = "executive_change"
    IPO = "ipo"
    BANKRUPTCY = "bankruptcy"
    DIVIDEND = "dividend"
    BUYBACK = "buyback"
    PARTNERSHIP = "partnership"
    LAWSUIT = "lawsuit"
    UNKNOWN = "unknown"


class ImpactMagnitude(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ImpactTimeline(str, Enum):
    IMMEDIATE = "immediate"
    SHORT_TERM = "short_term"     # days to weeks
    LONG_TERM = "long_term"       # months to quarters
    UNCERTAIN = "uncertain"


class SignalDirection(str, Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class MarketEvent:
    """A detected market-moving event."""
    event_type: EventType
    title: str
    description: str
    companies: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)
    tickers: list[str] = field(default_factory=list)
    magnitude: ImpactMagnitude = ImpactMagnitude.MEDIUM
    timeline: ImpactTimeline = ImpactTimeline.UNCERTAIN
    confidence: float = 0.5  # 0-1


@dataclass(frozen=True)
class EventImpact:
    """Assessed impact of a market event."""
    event: MarketEvent
    affected_sectors: list[str]
    magnitude: ImpactMagnitude
    timeline: ImpactTimeline
    confidence: float
    risk_factors: list[str]
    historical_precedent: str
    recommendation: str


@dataclass(frozen=True)
class TradingSignal:
    """A trading signal generated from event analysis."""
    event_type: str
    direction: SignalDirection
    confidence: float  # 0-1
    tickers: list[str]
    rationale: str
    risk_factors: list[str]
    time_horizon: str  # "immediate", "days", "weeks", "months"
    strength: str  # "weak", "moderate", "strong"


# ── Event Detection ──────────────────────────────────────────────────────────

EVENT_PATTERNS: dict[EventType, list[str]] = {
    EventType.EARNINGS: [
        r"earnings.{0,20}(?:beat|miss|exceeded|fell|reported|release)",
        r"(?:revenue|eps|profit|loss).{0,30}(?:increase|decrease|beat|miss|exceed|fell)",
        r"(?:q[1-4]|fiscal).{0,20}(?:results|earnings|report)",
        r"(?:guided?|guidance).{0,15}(?:up|down|higher|lower|raised|lowered)",
    ],
    EventType.MERGER_ACQUISITION: [
        r"(?:acquir(?:e|ed|ing)|merg(?:e|er|ing)|buy(?:out|ing)|takeover).{0,30}(?:of|for|with|by)",
        r"\$[\d.]+\s*(?:billion|million|B|M).{0,20}(?:deal|acquisition|merger)",
        r"(?:deal|acquisition|merger).{0,20}\$[\d.]+\s*(?:billion|million)",
    ],
    EventType.REGULATORY: [
        r"(?:SEC|FDA|FTC|DOJ|EU).{0,40}(?:approv(?:e|al|ed?)|reject|investigat|fine|penalt)",
        r"(?:regulat(?:ory|ion)).{0,30}(?:change|update|rule|law|bill|action)",
        r"(?:antitrust|monopol|anticompetit)",
    ],
    EventType.GEOPOLITICAL: [
        r"(?:tariff|sanction|embargo|trade\s+war).{0,50}(?:impos|announc|escalat)",
        r"(?:war|conflict|tension).{0,30}(?:escalat|break|emerg)",
        r"(?:election|coup|regime).{0,20}(?:change|crisis|overthrow)",
    ],
    EventType.PRODUCT_LAUNCH: [
        r"(?:launch(?:es|ed|ing)?|unveil|reveal).{0,15}(?:new|its|their)",
        r"(?:product|device).{0,15}(?:announcement|release|debut)",
    ],
    EventType.EXECUTIVE_CHANGE: [
        r"(?:CEO|CFO|CTO|COO|president|chairman).{0,20}(?:step|resign|appoint|fire|replac)",
        r"(?:executive|leadership).{0,15}(?:change|transition|shuffle|departure)",
    ],
    EventType.IPO: [
        r"(?:IPO|initial\s+public\s+offering|go(?:es)?\s+public)",
        r"(?:pric(?:e|ing)).{0,15}\$[\d.]+",
    ],
    EventType.BANKRUPTCY: [
        r"(?:bankrupt(?:cy|c?y)|chapter\s+11|file.{0,10}for.{0,10}protect|insolven)",
    ],
    EventType.DIVIDEND: [
        r"dividend.{0,15}(?:increase|decrease|cut|raise|special|suspend|initiat)",
    ],
    EventType.BUYBACK: [
        r"(?:share\s+repurchase|buyback|stock\s+buyback).{0,15}\$",
    ],
    EventType.PARTNERSHIP: [
        r"(?:partner|collaborat|alliance|joint\s+venture).{0,15}(?:with|between)",
    ],
    EventType.LAWSUIT: [
        r"(?:lawsuit|litigation|class\s+action|settl(?:e|ement))",
        r"sue.{0,15}(?:over|for|regarding)",
    ],
}


def detect_events(text: str) -> list[MarketEvent]:
    """Detect market-moving events from text using pattern matching."""
    events: list[MarketEvent] = []
    text_lower = text.lower()

    for event_type, patterns in EVENT_PATTERNS.items():
        for pattern in patterns:
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
            if matches:
                # Extract the matched context (surrounding sentence)
                for match in matches[:2]:  # max 2 per pattern
                    start = max(0, text.rfind(".", 0, match.start()) + 1)
                    end = text.find(".", match.end())
                    if end == -1:
                        end = min(len(text), match.end() + 150)
                    context = text[start:end].strip()

                    # Extract tickers mentioned nearby
                    nearby_start = max(0, match.start() - 200)
                    nearby_end = min(len(text), match.end() + 200)
                    nearby = text[nearby_start:nearby_end]
                    tickers = re.findall(r"\b([A-Z]{2,5})\b", nearby)
                    # Filter out common false positives
                    tickers = [t for t in tickers if t not in {
                        "THE", "AND", "FOR", "NOT", "BUT", "HAS", "ARE", "CAN",
                        "CEO", "CFO", "CTO", "SEC", "FDA", "FTC", "NEW", "OLD",
                    }]

                    events.append(MarketEvent(
                        event_type=event_type,
                        title=context[:100],
                        description=context,
                        tickers=tickers[:5],
                    ))

    return events


# ── Impact Assessment ────────────────────────────────────────────────────────

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "technology": ["tech", "software", "semiconductor", "chip", "cloud", "ai", "saas", "data"],
    "healthcare": ["pharma", "biotech", "drug", "fda", "medical", "health", "hospital"],
    "finance": ["bank", "financial", "insurance", "credit", "lending", "fintech"],
    "energy": ["oil", "gas", "solar", "wind", "nuclear", "energy", "petroleum", "renewable"],
    "consumer": ["retail", "consumer", "brand", "shopping", "e-commerce", "grocery"],
    "industrial": ["manufacturing", "construction", "infrastructure", "aerospace", "defense"],
    "real_estate": ["real estate", "property", "housing", "mortgage", "reit"],
    "crypto": ["bitcoin", "ethereum", "crypto", "blockchain", "defi", "token"],
}

MAGNITUDE_KEYWORDS: dict[ImpactMagnitude, list[str]] = {
    ImpactMagnitude.CRITICAL: ["crisis", "collapse", "emergency", "halt", "default", "fraud", "bankruptcy"],
    ImpactMagnitude.HIGH: ["billion", "major", "significant", "massive", "unprecedented", "blockbuster"],
    ImpactMagnitude.MEDIUM: ["million", "notable", "substantial", "meaningful", "material"],
    ImpactMagnitude.LOW: ["minor", "modest", "small", "limited", "incremental"],
}


def detect_sectors(text: str) -> list[str]:
    """Detect which sectors are affected by event text."""
    text_lower = text.lower()
    sectors = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            sectors.append(sector)
    return sectors


def assess_magnitude(text: str, event_type: EventType) -> ImpactMagnitude:
    """Assess the magnitude of an event's impact."""
    text_lower = text.lower()

    # Event type defaults
    type_magnitudes = {
        EventType.MERGER_ACQUISITION: ImpactMagnitude.HIGH,
        EventType.BANKRUPTCY: ImpactMagnitude.CRITICAL,
        EventType.IPO: ImpactMagnitude.MEDIUM,
        EventType.EARNINGS: ImpactMagnitude.MEDIUM,
        EventType.REGULATORY: ImpactMagnitude.HIGH,
        EventType.GEOPOLITICAL: ImpactMagnitude.HIGH,
    }

    for mag, keywords in MAGNITUDE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return mag

    return type_magnitudes.get(event_type, ImpactMagnitude.MEDIUM)


def assess_timeline(event_type: EventType) -> ImpactTimeline:
    """Determine the typical timeline for an event type's impact."""
    return {
        EventType.EARNINGS: ImpactTimeline.IMMEDIATE,
        EventType.MERGER_ACQUISITION: ImpactTimeline.LONG_TERM,
        EventType.REGULATORY: ImpactTimeline.SHORT_TERM,
        EventType.GEOPOLITICAL: ImpactTimeline.UNCERTAIN,
        EventType.PRODUCT_LAUNCH: ImpactTimeline.SHORT_TERM,
        EventType.EXECUTIVE_CHANGE: ImpactTimeline.SHORT_TERM,
        EventType.IPO: ImpactTimeline.IMMEDIATE,
        EventType.BANKRUPTCY: ImpactTimeline.IMMEDIATE,
        EventType.DIVIDEND: ImpactTimeline.IMMEDIATE,
        EventType.BUYBACK: ImpactTimeline.SHORT_TERM,
        EventType.PARTNERSHIP: ImpactTimeline.LONG_TERM,
        EventType.LAWSUIT: ImpactTimeline.LONG_TERM,
    }.get(event_type, ImpactTimeline.UNCERTAIN)


def assess_impact(event: MarketEvent) -> EventImpact:
    """Full impact assessment of a detected market event."""
    sectors = detect_sectors(event.description)
    magnitude = assess_magnitude(event.description, event.event_type)
    timeline = assess_timeline(event.event_type)

    # Risk factors
    risk_factors = []
    if event.confidence < 0.5:
        risk_factors.append("Low detection confidence")
    if len(event.tickers) == 0:
        risk_factors.append("No specific ticker identified")
    if magnitude == ImpactMagnitude.CRITICAL:
        risk_factors.append("Critical magnitude — potential market-wide impact")
    if timeline == ImpactTimeline.UNCERTAIN:
        risk_factors.append("Impact timeline uncertain")

    # Historical precedent (simplified)
    precedents = {
        EventType.EARNINGS: "Earnings beats typically see 5-15% immediate move",
        EventType.MERGER_ACQUISITION: "Target usually rises 20-40%, acquirer may dip 5-10%",
        EventType.REGULATORY: "Regulatory actions can cause 10-30% swings depending on severity",
        EventType.GEOPOLITICAL: "Geopolitical events cause sector rotation over weeks",
        EventType.BANKRUPTCY: "Bankruptcy filings typically cause 50-90% decline",
        EventType.IPO: "IPO first-day moves average 10-20%",
    }
    precedent = precedents.get(event.event_type, "No specific historical precedent data available")

    # Recommendation
    rec = {
        ImpactMagnitude.CRITICAL: "Monitor closely — potential for significant volatility",
        ImpactMagnitude.HIGH: "Active position review recommended",
        ImpactMagnitude.MEDIUM: "Watch for follow-through signals",
        ImpactMagnitude.LOW: "Informational — no immediate action needed",
    }

    return EventImpact(
        event=event,
        affected_sectors=sectors,
        magnitude=magnitude,
        timeline=timeline,
        confidence=event.confidence,
        risk_factors=risk_factors,
        historical_precedent=precedent,
        recommendation=rec.get(magnitude, "Monitor"),
    )


# ── Signal Generation ────────────────────────────────────────────────────────

# Event type → default signal direction
EVENT_SIGNAL_DEFAULTS: dict[EventType, SignalDirection] = {
    EventType.EARNINGS: SignalDirection.NEUTRAL,  # depends on beat/miss
    EventType.MERGER_ACQUISITION: SignalDirection.BULLISH,  # target
    EventType.REGULATORY: SignalDirection.BEARISH,
    EventType.GEOPOLITICAL: SignalDirection.BEARISH,
    EventType.PRODUCT_LAUNCH: SignalDirection.BULLISH,
    EventType.EXECUTIVE_CHANGE: SignalDirection.NEUTRAL,
    EventType.IPO: SignalDirection.BULLISH,
    EventType.BANKRUPTCY: SignalDirection.BEARISH,
    EventType.DIVIDEND: SignalDirection.BULLISH,
    EventType.BUYBACK: SignalDirection.BULLISH,
    EventType.PARTNERSHIP: SignalDirection.BULLISH,
    EventType.LAWSUIT: SignalDirection.BEARISH,
}


def generate_signal(
    event: MarketEvent,
    text: str = "",
) -> TradingSignal:
    """Generate a trading signal from a detected event."""
    direction = EVENT_SIGNAL_DEFAULTS.get(event.event_type, SignalDirection.NEUTRAL)

    # Refine based on text sentiment
    text_lower = (text or event.description).lower()
    bullish_words = {"beat", "exceeded", "strong", "growth", "increase", "approved", "surge", "rally"}
    bearish_words = {"miss", "decline", "weak", "loss", "rejected", "crash", "plunge", "cut", "suspend"}

    bull_count = sum(1 for w in bullish_words if w in text_lower)
    bear_count = sum(1 for w in bearish_words if w in text_lower)

    if bull_count > bear_count + 1:
        direction = SignalDirection.BULLISH
    elif bear_count > bull_count + 1:
        direction = SignalDirection.BEARISH

    # Confidence based on event detection confidence + text clarity
    clarity = min(bull_count + bear_count, 5) / 5
    confidence = (event.confidence + clarity) / 2
    confidence = min(max(confidence, 0.1), 0.95)

    # Strength
    magnitude_strength = {
        ImpactMagnitude.CRITICAL: "strong",
        ImpactMagnitude.HIGH: "strong",
        ImpactMagnitude.MEDIUM: "moderate",
        ImpactMagnitude.LOW: "weak",
    }
    impact = assess_impact(event)
    strength = magnitude_strength.get(impact.magnitude, "moderate")

    # Time horizon
    horizon = {
        ImpactTimeline.IMMEDIATE: "immediate",
        ImpactTimeline.SHORT_TERM: "days",
        ImpactTimeline.LONG_TERM: "months",
        ImpactTimeline.UNCERTAIN: "weeks",
    }

    # Risk factors
    risk_factors = []
    if confidence < 0.4:
        risk_factors.append("Low signal confidence")
    if event.event_type == EventType.GEOPOLITICAL:
        risk_factors.append("Geopolitical events are unpredictable")
    if not event.tickers:
        risk_factors.append("No specific ticker identified")

    rationale_parts = [
        f"{event.event_type.value.replace('_', ' ').title()} event detected",
        f"Magnitude: {impact.magnitude.value}",
    ]
    if event.tickers:
        rationale_parts.append(f"Tickers: {', '.join(event.tickers)}")
    rationale_parts.append(f"Sectors: {', '.join(impact.affected_sectors) if impact.affected_sectors else 'broad market'}")

    return TradingSignal(
        event_type=event.event_type.value,
        direction=direction,
        confidence=round(confidence, 2),
        tickers=event.tickers,
        rationale=". ".join(rationale_parts),
        risk_factors=risk_factors,
        time_horizon=horizon.get(impact.timeline, "weeks"),
        strength=strength,
    )
