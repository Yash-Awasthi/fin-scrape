"""
Geopolitical Risk Dashboard — Real-time intelligence feed.

Extracts and aggregates geopolitical signals from multiple sources:
- GDELT event database (news + events)
- ACLED conflict data (armed conflict)
- RUSI / ISW reports (military analysis)
- OSINT feeds (satellite imagery, social media)

Provides:
- Risk score per region (0-100)
- Trend analysis (escalating / stable / de-escalating)
- Historical timeline
- Market correlation signals
- Alert generation for threshold breaches
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
import json
import hashlib


class Region(Enum):
    EAST_ASIA = "east_asia"
    SOUTH_ASIA = "south_asia"
    MIDDLE_EAST = "middle_east"
    EASTERN_EUROPE = "eastern_europe"
    WESTERN_EUROPE = "western_europe"
    NORTH_AFRICA = "north_africa"
    SUB_SAHARAN_AFRICA = "sub_saharan_africa"
    LATIN_AMERICA = "latin_america"
    NORTH_AMERICA = "north_america"
    CENTRAL_ASIA = "central_asia"
    SOUTHEAST_ASIA = "southeast_asia"
    ARCTIC = "arctic"


class ThreatType(Enum):
    MILITARY_CONFLICT = "military_conflict"
    ECONOMIC_SANCTIONS = "economic_sanctions"
    TERRORISM = "terrorism"
    COUP_INSTABILITY = "coups_instability"
    CYBER_ATTACK = "cyber_attack"
    TRADE_WAR = "trade_war"
    NUCLEAR_ESCALATION = "nuclear_escalation"
    HUMANITARIAN_CRISIS = "humanitarian_crisis"
    ELECTION_INTERFERENCE = "election_interference"
    SUPPLY_CHAIN_DISRUPTION = "supply_chain_disruption"


class TrendDirection(Enum):
    ESCALATING = "escalating"
    STABLE = "stable"
    DE_ESCALATING = "de_escalating"


@dataclass
class GeopoliticalSignal:
    id: str
    timestamp: datetime
    source: str
    region: Region
    threat_type: ThreatType
    headline: str
    summary: str
    severity: float  # 0-1
    confidence: float  # 0-1
    market_impact: float  # -1 (bearish) to +1 (bullish)
    affected_assets: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class RegionRiskProfile:
    region: Region
    risk_score: float  # 0-100
    trend: TrendDirection
    signals: List[GeopoliticalSignal]
    last_updated: datetime
    historical_scores: List[Tuple[datetime, float]] = field(default_factory=list)
    active_threats: int = 0
    market_correlation: float = 0.0


@dataclass
class DashboardAlert:
    id: str
    timestamp: datetime
    severity: str  # "low", "medium", "high", "critical"
    region: Region
    title: str
    description: str
    risk_score_before: float
    risk_score_after: float
    affected_assets: List[str]


class GeopoliticalDashboard:
    """Real-time geopolitical risk monitoring dashboard."""

    def __init__(self):
        self.signals: List[GeopoliticalSignal] = []
        self.regions: Dict[Region, RegionRiskProfile] = {}
        self.alerts: List[DashboardAlert] = []
        self._init_regions()

    def _init_regions(self):
        for region in Region:
            self.regions[region] = RegionRiskProfile(
                region=region,
                risk_score=0.0,
                trend=TrendDirection.STABLE,
                signals=[],
                last_updated=datetime.now(),
            )

    def ingest_signal(self, signal: GeopoliticalSignal):
        """Ingest a new geopolitical signal and recalculate risk."""
        self.signals.append(signal)

        profile = self.regions[signal.region]
        old_score = profile.risk_score

        # Update risk score
        profile.signals.append(signal)
        profile.last_updated = datetime.now()

        # Recalculate
        profile.risk_score = self._calculate_risk_score(profile)
        profile.active_threats = len([
            s for s in profile.signals
            if (datetime.now() - s.timestamp).days < 7
        ])

        # Update trend
        profile.historical_scores.append((datetime.now(), profile.risk_score))
        if len(profile.historical_scores) >= 3:
            recent = [s for _, s in profile.historical_scores[-5:]]
            if len(recent) >= 2:
                diff = recent[-1] - recent[0]
                if diff > 5:
                    profile.trend = TrendDirection.ESCALATING
                elif diff < -5:
                    profile.trend = TrendDirection.DE_ESCALATING
                else:
                    profile.trend = TrendDirection.STABLE

        # Generate alert if significant change
        if abs(profile.risk_score - old_score) > 10:
            alert = DashboardAlert(
                id=hashlib.md5(f"{signal.id}{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                timestamp=datetime.now(),
                severity="critical" if profile.risk_score > 75 else "high" if profile.risk_score > 50 else "medium",
                region=signal.region,
                title=f"Risk score {'increased' if profile.risk_score > old_score else 'decreased'} in {signal.region.value}",
                description=f"{signal.headline} — Score changed from {old_score:.1f} to {profile.risk_score:.1f}",
                risk_score_before=old_score,
                risk_score_after=profile.risk_score,
                affected_assets=signal.affected_assets,
            )
            self.alerts.append(alert)

    def _calculate_risk_score(self, profile: RegionRiskProfile) -> float:
        """Weighted risk score based on recency, severity, and threat diversity."""
        now = datetime.now()
        score = 0.0

        recent_signals = [s for s in profile.signals if (now - s.timestamp).days < 30]

        if not recent_signals:
            return 0.0

        for signal in recent_signals:
            age_days = (now - signal.timestamp).days
            recency_weight = max(0.1, 1.0 - (age_days / 30))
            severity_weight = signal.severity
            confidence_weight = signal.confidence

            # Nuclear escalation has 3x multiplier
            multiplier = 3.0 if signal.threat_type == ThreatType.NUCLEAR_ESCALATION else 1.0

            score += severity_weight * recency_weight * confidence_weight * multiplier * 20

        return min(100.0, score)

    def get_global_risk(self) -> float:
        """Average risk score across all regions."""
        scores = [p.risk_score for p in self.regions.values()]
        return sum(scores) / len(scores) if scores else 0.0

    def get_top_risks(self, n: int = 5) -> List[RegionRiskProfile]:
        """Get N highest-risk regions."""
        return sorted(
            self.regions.values(),
            key=lambda p: p.risk_score,
            reverse=True,
        )[:n]

    def get_market_correlation(self, asset: str) -> Dict[str, float]:
        """Get correlation between geopolitical events and an asset's movement."""
        related_signals = [
            s for s in self.signals
            if asset in s.affected_assets
        ]
        if not related_signals:
            return {"correlation": 0.0, "signal_count": 0}

        avg_impact = sum(s.market_impact for s in related_signals) / len(related_signals)
        return {
            "correlation": avg_impact,
            "signal_count": len(related_signals),
            "avg_severity": sum(s.severity for s in related_signals) / len(related_signals),
        }

    def get_recent_alerts(self, hours: int = 24) -> List[DashboardAlert]:
        """Get alerts from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp > cutoff]

    def to_dict(self) -> dict:
        """Serialize dashboard state for API responses."""
        return {
            "global_risk": self.get_global_risk(),
            "top_risks": [
                {
                    "region": p.region.value,
                    "risk_score": round(p.risk_score, 1),
                    "trend": p.trend.value,
                    "active_threats": p.active_threats,
                    "signal_count": len(p.signals),
                }
                for p in self.get_top_risks()
            ],
            "recent_alerts": [
                {
                    "id": a.id,
                    "timestamp": a.timestamp.isoformat(),
                    "severity": a.severity,
                    "region": a.region.value,
                    "title": a.title,
                    "description": a.description,
                    "risk_change": round(a.risk_score_after - a.risk_score_before, 1),
                }
                for a in self.get_recent_alerts()
            ],
            "signal_count": len(self.signals),
            "last_updated": datetime.now().isoformat(),
        }
