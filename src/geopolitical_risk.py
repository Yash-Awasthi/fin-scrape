"""
Geopolitical Risk Assessment — AI-powered geopolitical intelligence for financial analysis.

Extracted from GeoPulseWebApp: analyzes geopolitical relations, trade routes,
and commodity risks using LLM orchestration for strategic decision-making.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GeopoliticalEvent:
    """A geopolitical event that may impact markets."""
    title: str
    description: str
    region: str
    category: str  # "conflict", "sanctions", "trade", "election", "policy", "disaster"
    risk_level: RiskLevel
    affected_sectors: list
    affected_tickers: list
    timestamp: str
    source: Optional[str] = None


@dataclass
class RiskAssessment:
    """Assessment of geopolitical risk for a region or sector."""
    region: str
    overall_risk: RiskLevel
    risk_score: float  # 0.0 to 1.0
    key_risks: list
    affected_sectors: list
    recommendations: list
    events: list = field(default_factory=list)


@dataclass
class TradeRouteRisk:
    """Risk assessment for a trade route."""
    route_name: str
    origin: str
    destination: str
    risk_level: RiskLevel
    disruption_probability: float
    alternative_routes: list
    impact_on_shipping_cost: float  # percentage increase
    key_threats: list


# Risk scoring weights
SECTOR_RISK_WEIGHTS = {
    "energy": {"oil": 0.9, "gas": 0.85, "renewables": 0.3},
    "technology": {"semiconductors": 0.8, "software": 0.4, "hardware": 0.6},
    "finance": {"banking": 0.7, "insurance": 0.6, "fintech": 0.5},
    "agriculture": {"grain": 0.7, "livestock": 0.5, "fertilizer": 0.8},
    "defense": {"aerospace": 0.9, "cybersecurity": 0.8, "ordnance": 0.95},
}

# Regional risk baselines
REGIONAL_RISK_BASELINES = {
    "middle_east": 0.7,
    "east_asia": 0.5,
    "eastern_europe": 0.6,
    "south_asia": 0.4,
    "sub_saharan_africa": 0.5,
    "latin_america": 0.35,
    "western_europe": 0.2,
    "north_america": 0.15,
    "oceania": 0.1,
}


class GeopoliticalRiskAnalyzer:
    """
    Geopolitical risk analyzer for financial intelligence.
    
    Usage:
        analyzer = GeopoliticalRiskAnalyzer()
        assessment = analyzer.assess_region("middle_east")
        print(assessment.overall_risk)  # RiskLevel
        print(assessment.risk_score)    # 0.0-1.0
    """
    
    def __init__(self, events: list = None):
        self.events = events or []
    
    def add_event(self, event: GeopoliticalEvent):
        """Add a geopolitical event to the analyzer."""
        self.events.append(event)
    
    def assess_region(self, region: str) -> RiskAssessment:
        """Assess geopolitical risk for a region."""
        baseline = REGIONAL_RISK_BASELINES.get(region, 0.5)
        
        # Filter events for this region
        region_events = [e for e in self.events if e.region.lower() == region.lower()]
        
        # Calculate risk score from events
        event_risk = 0.0
        if region_events:
            risk_scores = {
                RiskLevel.LOW: 0.2,
                RiskLevel.MEDIUM: 0.5,
                RiskLevel.HIGH: 0.8,
                RiskLevel.CRITICAL: 1.0,
            }
            event_risk = sum(risk_scores.get(e.risk_level, 0.5) for e in region_events) / len(region_events)
        
        # Combine baseline and event risk
        overall_score = (baseline * 0.4 + event_risk * 0.6) if region_events else baseline
        overall_score = min(1.0, overall_score)
        
        # Determine risk level
        if overall_score >= 0.8:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 0.6:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        # Collect affected sectors
        affected_sectors = list(set(
            sector for e in region_events for sector in e.affected_sectors
        ))
        
        # Generate key risks
        key_risks = [e.title for e in region_events if e.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_level, affected_sectors, region_events)
        
        return RiskAssessment(
            region=region,
            overall_risk=risk_level,
            risk_score=round(overall_score, 4),
            key_risks=key_risks,
            affected_sectors=affected_sectors,
            recommendations=recommendations,
            events=region_events,
        )
    
    def assess_sector(self, sector: str) -> dict:
        """Assess risk for a specific sector across all regions."""
        sector_events = [
            e for e in self.events
            if sector.lower() in [s.lower() for s in e.affected_sectors]
        ]
        
        if not sector_events:
            return {"sector": sector, "risk_score": 0.0, "event_count": 0}
        
        risk_scores = {
            RiskLevel.LOW: 0.2,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 1.0,
        }
        
        avg_risk = sum(risk_scores.get(e.risk_level, 0.5) for e in sector_events) / len(sector_events)
        
        return {
            "sector": sector,
            "risk_score": round(avg_risk, 4),
            "event_count": len(sector_events),
            "affected_regions": list(set(e.region for e in sector_events)),
        }
    
    def get_affected_tickers(self, region: str = None, sector: str = None) -> list:
        """Get tickers affected by geopolitical events."""
        events = self.events
        
        if region:
            events = [e for e in events if e.region.lower() == region.lower()]
        if sector:
            events = [e for e in events if sector.lower() in [s.lower() for s in e.affected_sectors]]
        
        tickers = set()
        for e in events:
            tickers.update(e.affected_tickers)
        
        return sorted(tickers)
    
    def _generate_recommendations(self, risk_level: RiskLevel, sectors: list, events: list) -> list:
        """Generate risk management recommendations."""
        recommendations = []
        
        if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            recommendations.append("Consider reducing exposure to affected sectors")
            recommendations.append("Hedge currency and commodity positions")
            recommendations.append("Review supply chain dependencies")
        
        if risk_level == RiskLevel.CRITICAL:
            recommendations.append("Implement defensive portfolio positioning")
            recommendations.append("Increase cash reserves")
            recommendations.append("Monitor real-time news feeds")
        
        if "energy" in sectors:
            recommendations.append("Monitor oil futures and energy ETFs")
        if "technology" in sectors:
            recommendations.append("Review semiconductor supply chain exposure")
        if "finance" in sectors:
            recommendations.append("Monitor banking sector stability")
        
        if not recommendations:
            recommendations.append("Continue standard monitoring")
        
        return recommendations
