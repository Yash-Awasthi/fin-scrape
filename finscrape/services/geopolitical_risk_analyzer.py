"""Geopolitical Risk Analyzer Service.

Extracted from geopolitics-ml (inspiration).
Event classification, exposure scoring, and impact estimation
for geopolitical events affecting companies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GeopoliticalCategory(Enum):
    TRADE_WAR = "trade_war"
    SANCTIONS = "sanctions"
    MILITARY_CONFLICT = "military_conflict"
    REGULATORY = "regulatory"
    CYBER_ATTACK = "cyber_attack"
    RESOURCE_DISRUPTION = "resource_disruption"
    POLITICAL_INSTABILITY = "political_instability"
    ALLIANCE_SHIFT = "alliance_shift"


class ImpactChannel(Enum):
    SUPPLY_CHAIN = "supply_chain"
    REVENUE = "revenue"
    ASSETS = "assets"
    REPUTATION = "reputation"
    REGULATORY = "regulatory"
    CURRENCY = "currency"
    ENERGY = "energy"
    TALENT = "talent"
    CAPITAL = "capital"
    MARKET_ACCESS = "market_access"


class ImpactDirection(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


@dataclass
class EventClassification:
    category: GeopoliticalCategory
    confidence: float
    subcategory: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass
class ExposureScore:
    channel: ImpactChannel
    severity: float  # 0-1
    confidence: float
    reasoning: str = ""


@dataclass
class ImpactEstimate:
    direction: ImpactDirection
    revenue_impact_pct: float
    dollar_impact: float
    timeframe: str  # "immediate", "short_term", "long_term"
    confidence: float
    risk_level: str  # "low", "medium", "high", "critical"
    reasoning: str = ""


@dataclass
class GeopoliticalRiskReport:
    event_text: str
    classification: EventClassification
    exposures: list[ExposureScore]
    impacts: list[ImpactEstimate]
    overall_risk: str
    summary: str = ""


CATEGORY_KEYWORDS = {
    GeopoliticalCategory.TRADE_WAR: ["tariff", "trade", "import", "export", "duties", "quota", "embargo"],
    GeopoliticalCategory.SANCTIONS: ["sanction", "restrict", "ban", "blacklist", "entity list", "OFAC"],
    GeopoliticalCategory.MILITARY_CONFLICT: ["war", "invasion", "military", "missile", "conflict", "attack"],
    GeopoliticalCategory.REGULATORY: ["regulation", "compliance", "antitrust", "GDPR", "fine", "penalty"],
    GeopoliticalCategory.CYBER_ATTACK: ["hack", "breach", "ransomware", "cyber", "data leak", "vulnerability"],
    GeopoliticalCategory.RESOURCE_DISRUPTION: ["oil", "gas", "rare earth", "chip", "supply", "shortage"],
    GeopoliticalCategory.POLITICAL_INSTABILITY: ["coup", "election", "protest", "sanctions", "coup", "revolution"],
    GeopoliticalCategory.ALLIANCE_SHIFT: ["NATO", "BRICS", "treaty", "alliance", "partnership", "deal"],
}


def classify_event(text: str) -> EventClassification:
    """Classify geopolitical event from text."""
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[category] = score
    if not scores:
        return EventClassification(category=GeopoliticalCategory.POLITICAL_INSTABILITY,
                                   confidence=0.3, keywords=[])
    best_category = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = scores[best_category] / total if total > 0 else 0.3
    matched_keywords = [kw for kw in CATEGORY_KEYWORDS[best_category] if kw in text_lower]
    return EventClassification(
        category=best_category, confidence=min(0.9, confidence + 0.2),
        keywords=matched_keywords,
    )


def score_exposure(
    event_category: GeopoliticalCategory,
    sector: str,
    revenue_usd: float,
    global_exposure_pct: float = 0.5,
) -> list[ExposureScore]:
    """Score exposure across impact channels."""
    channel_weights = {
        ImpactChannel.SUPPLY_CHAIN: 0.8 if "manufacturing" in sector.lower() else 0.3,
        ImpactChannel.REVENUE: 0.7 if global_exposure_pct > 0.5 else 0.4,
        ImpactChannel.ASSETS: 0.5,
        ImpactChannel.REGULATORY: 0.6 if event_category in (GeopoliticalCategory.REGULATORY, GeopoliticalCategory.SANCTIONS) else 0.2,
        ImpactChannel.CURRENCY: 0.4 if global_exposure_pct > 0.3 else 0.1,
    }
    scores = []
    for channel, base_weight in channel_weights.items():
        severity = min(1.0, base_weight * global_exposure_pct)
        scores.append(ExposureScore(
            channel=channel, severity=round(severity, 2),
            confidence=0.6, reasoning=f"Sector={sector}, Global={global_exposure_pct:.0%}",
        ))
    return sorted(scores, key=lambda s: s.severity, reverse=True)


def estimate_impact(
    event_category: GeopoliticalCategory,
    channel: ImpactChannel,
    revenue_usd: float,
    severity: float,
) -> ImpactEstimate:
    """Estimate financial impact from event."""
    base_impact_pct = {
        GeopoliticalCategory.TRADE_WAR: 5.0,
        GeopoliticalCategory.SANCTIONS: 8.0,
        GeopoliticalCategory.MILITARY_CONFLICT: 12.0,
        GeopoliticalCategory.REGULATORY: 3.0,
        GeopoliticalCategory.CYBER_ATTACK: 4.0,
        GeopoliticalCategory.RESOURCE_DISRUPTION: 6.0,
        GeopoliticalCategory.POLITICAL_INSTABILITY: 7.0,
        GeopoliticalCategory.ALLIANCE_SHIFT: 2.0,
    }
    pct = base_impact_pct.get(event_category, 5.0) * severity
    dollar_impact = revenue_usd * pct / 100
    if pct > 10:
        direction = ImpactDirection.NEGATIVE
        risk_level = "critical"
    elif pct > 5:
        direction = ImpactDirection.NEGATIVE
        risk_level = "high"
    elif pct > 2:
        direction = ImpactDirection.NEGATIVE
        risk_level = "medium"
    else:
        direction = ImpactDirection.LOW
        risk_level = "low"
    return ImpactEstimate(
        direction=direction, revenue_impact_pct=round(pct, 2),
        dollar_impact=round(dollar_impact), timeframe="short_term",
        confidence=0.6, risk_level=risk_level,
        reasoning=f"{event_category.value} via {channel.value}",
    )


def analyze_geopolitical_risk(
    event_text: str,
    company_name: str,
    sector: str,
    revenue_usd: float,
    global_exposure_pct: float = 0.5,
) -> GeopoliticalRiskReport:
    """Complete geopolitical risk analysis."""
    classification = classify_event(event_text)
    exposures = score_exposure(classification.category, sector, revenue_usd, global_exposure_pct)
    impacts = []
    for exp in exposures[:3]:
        impact = estimate_impact(classification.category, exp.channel, revenue_usd, exp.severity)
        impacts.append(impact)
    max_risk = "low"
    risk_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    for imp in impacts:
        if risk_order.get(imp.risk_level, 0) > risk_order.get(max_risk, 0):
            max_risk = imp.risk_level
    summary = f"Event classified as {classification.category.value} ({classification.confidence:.0%}). "
    summary += f"Top impact: {impacts[0].channel.value if impacts else 'none'}. "
    summary += f"Overall risk: {max_risk}."
    return GeopoliticalRiskReport(
        event_text=event_text, classification=classification,
        exposures=exposures, impacts=impacts,
        overall_risk=max_risk, summary=summary,
    )
