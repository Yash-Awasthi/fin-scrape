"""
Geopolitical risk from geopolrisk-py — country risk assessment.
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class CountryRisk:
    country: str
    political_stability: float = 0.0  # 0-100
    economic_risk: float = 0.0
    military_risk: float = 0.0
    social_risk: float = 0.0
    environmental_risk: float = 0.0
    overall_score: float = 0.0
    risk_level: str = "low"


@dataclass
class RiskAlert:
    country: str
    risk_type: str
    severity: str
    description: str
    timestamp: float = 0.0


def compute_overall_risk(country: CountryRisk) -> float:
    weights = {"political": 0.25, "economic": 0.25, "military": 0.2, "social": 0.15, "environmental": 0.15}
    score = (country.political_stability * weights["political"] + country.economic_risk * weights["economic"] +
             country.military_risk * weights["military"] + country.social_risk * weights["social"] +
             country.environmental_risk * weights["environmental"])
    return round(score, 1)


def classify_risk(score: float) -> str:
    if score >= 70: return "critical"
    elif score >= 50: return "high"
    elif score >= 30: return "moderate"
    elif score >= 10: return "low"
    return "minimal"


def assess_countries(countries: List[CountryRisk]) -> List[Dict]:
    results = []
    for country in countries:
        country.overall_score = compute_overall_risk(country)
        country.risk_level = classify_risk(country.overall_score)
        results.append({"country": country.country, "score": country.overall_score, "level": country.risk_level})
    return sorted(results, key=lambda x: x["score"], reverse=True)


def generate_risk_report(countries: List[CountryRisk]) -> Dict:
    assessed = assess_countries(countries)
    high_risk = [c for c in assessed if c["level"] in ("high", "critical")]
    return {"total_countries": len(assessed), "high_risk_count": len(high_risk), "highest_risk": assessed[0] if assessed else None, "countries": assessed}
