"""Multi-Agent Trading Orchestration.

Extracted from alpacatradingagent (inspiration).
Agent roles (analyst, researcher, trader, risk manager), consensus building,
and structured trading decisions.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentReport:
    """Report from a single agent."""
    agent_name: str
    agent_role: str  # "analyst", "researcher", "trader", "risk_manager"
    ticker: str
    recommendation: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0-1
    reasoning: str
    timestamp: str = ""


@dataclass
class TradingDecision:
    """Final trading decision with all supporting data."""
    ticker: str
    action: str  # "BUY", "HOLD", "SELL", "LONG", "SHORT", "NEUTRAL"
    confidence: float
    reasoning: str
    agent_reports: list[AgentReport] = field(default_factory=list)
    risk_assessment: Optional[dict] = None
    position_size_pct: float = 0.0


@dataclass
class RiskLimits:
    """Risk management constraints."""
    max_position_pct: float = 0.10
    max_daily_trades: int = 10
    max_drawdown_pct: float = 0.15
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.10
    max_correlated_positions: int = 3
    min_confidence: float = 0.6


# --- Agent Roles ---

ANALYST_AGENTS = [
    {"name": "Market Analyst", "role": "analyst", "focus": "overall market conditions and trends"},
    {"name": "Social Sentiment Analyst", "role": "analyst", "focus": "social media sentiment and public opinion"},
    {"name": "News Analyst", "role": "analyst", "focus": "financial news and events"},
    {"name": "Fundamentals Analyst", "role": "analyst", "focus": "company financials and intrinsic value"},
    {"name": "Macro Analyst", "role": "analyst", "focus": "macroeconomic indicators and Fed data"},
]

RESEARCH_AGENTS = [
    {"name": "Bull Researcher", "role": "researcher", "focus": "bullish case and upside catalysts"},
    {"name": "Bear Researcher", "role": "researcher", "focus": "bearish case and downside risks"},
    {"name": "Research Manager", "role": "researcher", "focus": "synthesize bull and bear cases"},
]

TRADING_AGENTS = [
    {"name": "Trader", "role": "trader", "focus": "execute trading strategy"},
]

RISK_AGENTS = [
    {"name": "Risky Analyst", "role": "risk_manager", "focus": "aggressive risk tolerance"},
    {"name": "Neutral Analyst", "role": "risk_manager", "focus": "balanced risk approach"},
    {"name": "Safe Analyst", "role": "risk_manager", "focus": "conservative risk approach"},
]


def get_agent_roles() -> dict:
    """Get all agent roles and their descriptions."""
    return {
        "analysts": ANALYST_AGENTS,
        "researchers": RESEARCH_AGENTS,
        "traders": TRADING_AGENTS,
        "risk_managers": RISK_AGENTS,
    }


# --- Consensus Building ---

def build_consensus(reports: list[AgentReport]) -> dict:
    """Build consensus from multiple agent reports.

    Uses weighted voting based on agent role and confidence.

    Args:
        reports: List of agent reports

    Returns:
        Consensus result with recommendation, confidence, and breakdown
    """
    if not reports:
        return {"recommendation": "neutral", "confidence": 0.0, "votes": {}}

    # Role weights
    role_weights = {
        "analyst": 1.0,
        "researcher": 1.5,  # Research has more weight
        "trader": 2.0,      # Trader has highest weight
        "risk_manager": 1.2,
    }

    # Count weighted votes
    votes = {"bullish": 0.0, "bearish": 0.0, "neutral": 0.0}
    for report in reports:
        weight = role_weights.get(report.agent_role, 1.0) * report.confidence
        rec = report.recommendation.lower()
        if rec in votes:
            votes[rec] += weight

    total = sum(votes.values())
    if total == 0:
        return {"recommendation": "neutral", "confidence": 0.0, "votes": votes}

    # Normalize
    normalized = {k: v / total for k, v in votes.items()}

    # Find winner
    winner = max(normalized, key=normalized.get)
    vote_confidence = normalized[winner]

    # Factor in average report confidence
    avg_report_confidence = sum(r.confidence for r in reports) / len(reports)
    confidence = vote_confidence * avg_report_confidence

    return {
        "recommendation": winner,
        "confidence": round(confidence, 3),
        "votes": {k: round(v, 3) for k, v in normalized.items()},
        "total_reports": len(reports),
    }


# --- Risk Assessment ---

def assess_risk(
    ticker: str,
    consensus: dict,
    reports: list[AgentReport],
    limits: RiskLimits = RiskLimits(),
) -> dict:
    """Assess risk for a trading decision.

    Args:
        ticker: Stock ticker
        consensus: Consensus result
        reports: Agent reports
        limits: Risk limits

    Returns:
        Risk assessment with factors and score
    """
    risk_factors = []

    # Confidence risk
    if consensus["confidence"] < limits.min_confidence:
        risk_factors.append({
            "factor": "low_confidence",
            "severity": "high",
            "description": f"Consensus confidence {consensus['confidence']:.2f} below minimum {limits.min_confidence}",
        })

    # Disagreement risk
    bullish_count = sum(1 for r in reports if r.recommendation == "bullish")
    bearish_count = sum(1 for r in reports if r.recommendation == "bearish")
    total = len(reports)

    if total > 0:
        disagreement = abs(bullish_count - bearish_count) / total
        if disagreement < 0.3:
            risk_factors.append({
                "factor": "high_disagreement",
                "severity": "medium",
                "description": f"Agents disagree: {bullish_count} bullish vs {bearish_count} bearish",
            })

    # Role-specific risks
    risk_reports = [r for r in reports if r.agent_role == "risk_manager"]
    if risk_reports:
        risk_confidence = sum(r.confidence for r in risk_reports) / len(risk_reports)
        if risk_confidence < 0.5:
            risk_factors.append({
                "factor": "risk_managers_concerned",
                "severity": "high",
                "description": "Risk management agents have low confidence",
            })

    # Calculate overall risk score (0 = low risk, 1 = high risk)
    severity_map = {"low": 0.2, "medium": 0.5, "high": 0.8, "critical": 1.0}
    if risk_factors:
        risk_score = sum(severity_map.get(f["severity"], 0.5) for f in risk_factors) / len(risk_factors)
    else:
        risk_score = 0.1

    return {
        "ticker": ticker,
        "risk_score": round(risk_score, 3),
        "risk_level": "low" if risk_score < 0.3 else "medium" if risk_score < 0.6 else "high",
        "factors": risk_factors,
        "passes_limits": risk_score < 0.7 and consensus["confidence"] >= limits.min_confidence,
    }


# --- Position Sizing ---

def calculate_position_size(
    capital: float,
    confidence: float,
    risk_score: float,
    limits: RiskLimits = RiskLimits(),
) -> float:
    """Calculate position size based on confidence and risk.

    Uses Kelly-inspired sizing with risk adjustment.

    Args:
        capital: Available capital
        confidence: Consensus confidence (0-1)
        risk_score: Overall risk score (0-1)
        limits: Risk limits

    Returns:
        Position size as percentage of capital
    """
    if confidence < limits.min_confidence:
        return 0.0

    # Kelly-inspired sizing
    win_rate = confidence
    avg_win = limits.take_profit_pct
    avg_loss = limits.stop_loss_pct

    if avg_loss == 0:
        return 0.0

    kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
    kelly = max(0, min(kelly, 1.0))

    # Risk adjustment
    risk_adjustment = 1.0 - (risk_score * 0.5)

    # Apply limits
    position_pct = kelly * risk_adjustment * limits.max_position_pct
    position_pct = min(position_pct, limits.max_position_pct)

    return round(position_pct, 4)


# --- Decision Generation ---

def generate_decision(
    ticker: str,
    reports: list[AgentReport],
    capital: float,
    limits: RiskLimits = RiskLimits(),
) -> TradingDecision:
    """Generate a complete trading decision from agent reports.

    Args:
        ticker: Stock ticker
        reports: List of agent reports
        capital: Available capital
        limits: Risk limits

    Returns:
        Complete trading decision
    """
    # Build consensus
    consensus = build_consensus(reports)

    # Assess risk
    risk = assess_risk(ticker, consensus, reports, limits)

    # Determine action
    if not risk["passes_limits"]:
        action = "HOLD"
        confidence = 0.0
        reasoning = f"Risk assessment failed: {risk['risk_level']} risk"
    elif consensus["recommendation"] == "bullish":
        if consensus["confidence"] > 0.7:
            action = "BUY"
        else:
            action = "LONG"
        confidence = consensus["confidence"]
        reasoning = f"Bullish consensus with {confidence:.0%} confidence"
    elif consensus["recommendation"] == "bearish":
        if consensus["confidence"] > 0.7:
            action = "SELL"
        else:
            action = "SHORT"
        confidence = consensus["confidence"]
        reasoning = f"Bearish consensus with {confidence:.0%} confidence"
    else:
        action = "HOLD"
        confidence = consensus["confidence"]
        reasoning = "Neutral consensus"

    # Calculate position size
    position_size = calculate_position_size(capital, confidence, risk["risk_score"], limits)

    return TradingDecision(
        ticker=ticker,
        action=action,
        confidence=round(confidence, 3),
        reasoning=reasoning,
        agent_reports=reports,
        risk_assessment=risk,
        position_size_pct=position_size,
    )
