"""
Multi-Agent Trading System — 15 specialized agents for trading analysis.

Inspired by TradingAgents-MCPmode.
Provides multi-agent collaboration, parallel analysis, and debate mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Agent:
    """Represents a trading agent."""
    id: str
    name: str
    role: str  # analyst, researcher, risk_manager, etc.
    specialty: str
    isActive: bool = True
    analysisCount: int = 0
    accuracy: float = 0.0


@dataclass
class Analysis:
    """An analysis result from an agent."""
    agentId: str
    ticker: str
    recommendation: str  # buy, sell, hold
    confidence: float
    reasoning: str
    metrics: dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Debate:
    """A debate between bull and bear researchers."""
    id: str
    ticker: str
    bullArguments: list[str]
    bearArguments: list[str]
    rounds: int
    consensus: str | None = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    agentId: str
    ticker: str
    riskLevel: str  # low, medium, high, extreme
    riskFactors: list[str]
    mitigationSuggestions: list[str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Multi-Agent Trading Manager
# ============================================================================

class MultiAgentTradingManager:
    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.analyses: dict[str, list[Analysis]] = {}
        self.debates: dict[str, Debate] = {}
        self.riskAssessments: dict[str, list[RiskAssessment]] = {}

    def register_agent(self, name: str, role: str, specialty: str) -> Agent:
        """Register a new trading agent."""
        import uuid
        agent = Agent(
            id=str(uuid.uuid4())[:8],
            name=name,
            role=role,
            specialty=specialty,
        )
        self.agents[agent.id] = agent
        return agent

    def submit_analysis(self, agent_id: str, ticker: str, recommendation: str,
                       confidence: float, reasoning: str, metrics: dict[str, float]) -> Analysis:
        """Submit an analysis from an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        analysis = Analysis(
            agentId=agent_id,
            ticker=ticker,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
            metrics=metrics,
        )

        agent.analysisCount += 1
        if ticker not in self.analyses:
            self.analyses[ticker] = []
        self.analyses[ticker].append(analysis)
        return analysis

    def get_consensus(self, ticker: str) -> dict:
        """Get consensus recommendation for a ticker."""
        analyses = self.analyses.get(ticker, [])
        if not analyses:
            return {"ticker": ticker, "consensus": "no_data", "confidence": 0}

        buy_count = sum(1 for a in analyses if a.recommendation == "buy")
        sell_count = sum(1 for a in analyses if a.recommendation == "sell")
        hold_count = sum(1 for a in analyses if a.recommendation == "hold")

        total = len(analyses)
        avg_confidence = sum(a.confidence for a in analyses) / total

        if buy_count > sell_count and buy_count > hold_count:
            consensus = "buy"
        elif sell_count > buy_count and sell_count > hold_count:
            consensus = "sell"
        else:
            consensus = "hold"

        return {
            "ticker": ticker,
            "consensus": consensus,
            "confidence": avg_confidence,
            "buyVotes": buy_count,
            "sellVotes": sell_count,
            "holdVotes": hold_count,
            "totalAnalyses": total,
        }

    def start_debate(self, ticker: str, bull_agent_id: str, bear_agent_id: str, rounds: int = 3) -> Debate:
        """Start a bull vs bear debate."""
        import uuid
        debate = Debate(
            id=str(uuid.uuid4())[:8],
            ticker=ticker,
            bullArguments=[],
            bearArguments=[],
            rounds=rounds,
        )
        self.debates[debate.id] = debate
        return debate

    def add_bull_argument(self, debate_id: str, argument: str) -> None:
        """Add a bull argument to a debate."""
        debate = self.debates.get(debate_id)
        if debate:
            debate.bullArguments.append(argument)

    def add_bear_argument(self, debate_id: str, argument: str) -> None:
        """Add a bear argument to a debate."""
        debate = self.debates.get(debate_id)
        if debate:
            debate.bearArguments.append(argument)

    def resolve_debate(self, debate_id: str, consensus: str, confidence: float) -> None:
        """Resolve a debate with a consensus."""
        debate = self.debates.get(debate_id)
        if debate:
            debate.consensus = consensus
            debate.confidence = confidence

    def submit_risk_assessment(self, agent_id: str, ticker: str, risk_level: str,
                              risk_factors: list[str], mitigation: list[str], confidence: float) -> RiskAssessment:
        """Submit a risk assessment."""
        assessment = RiskAssessment(
            agentId=agent_id,
            ticker=ticker,
            riskLevel=risk_level,
            riskFactors=risk_factors,
            mitigationSuggestions=mitigation,
            confidence=confidence,
        )

        if ticker not in self.riskAssessments:
            self.riskAssessments[ticker] = []
        self.riskAssessments[ticker].append(assessment)
        return assessment

    def get_risk_summary(self, ticker: str) -> dict:
        """Get risk summary for a ticker."""
        assessments = self.riskAssessments.get(ticker, [])
        if not assessments:
            return {"ticker": ticker, "riskLevel": "unknown", "confidence": 0}

        risk_levels = {"low": 1, "medium": 2, "high": 3, "extreme": 4}
        avg_risk = sum(risk_levels.get(a.riskLevel, 0) for a in assessments) / len(assessments)
        avg_confidence = sum(a.confidence for a in assessments) / len(assessments)

        if avg_risk <= 1.5:
            risk_level = "low"
        elif avg_risk <= 2.5:
            risk_level = "medium"
        elif avg_risk <= 3.5:
            risk_level = "high"
        else:
            risk_level = "extreme"

        return {
            "ticker": ticker,
            "riskLevel": risk_level,
            "confidence": avg_confidence,
            "totalAssessments": len(assessments),
        }

    def get_agent_performance(self) -> list[dict]:
        """Get performance metrics for all agents."""
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "role": agent.role,
                "analyses": agent.analysisCount,
                "accuracy": agent.accuracy,
            }
            for agent in self.agents.values()
        ]

    def get_dashboard_data(self) -> dict:
        """Get dashboard data for all tickers."""
        return {
            "tickers": list(self.analyses.keys()),
            "totalAnalyses": sum(len(a) for a in self.analyses.values()),
            "totalDebates": len(self.debates),
            "totalRiskAssessments": sum(len(r) for r in self.riskAssessments.values()),
            "activeAgents": sum(1 for a in self.agents.values() if a.isActive),
        }


# ============================================================================
# Report → consensus → risk → decision pipeline (wired API; tests pin this)
# ============================================================================

@dataclass
class AgentReport:
    """One agent's verdict on a ticker, fed into build_consensus."""

    name: str
    role: str  # analyst, researcher, trader, risk_manager
    ticker: str
    recommendation: str  # bullish, bearish, neutral
    confidence: float  # 0..1
    reasoning: str


@dataclass
class RiskLimits:
    """Guardrails for position sizing and decision gating."""

    min_confidence: float = 0.6   # below this consensus confidence: no position
    max_position_size: float = 0.10  # fraction of portfolio, hard cap


@dataclass
class Decision:
    """Final trading decision produced from agent reports."""

    ticker: str
    action: str  # BUY, SELL, HOLD
    confidence: float
    risk_assessment: dict
    position_size: float  # fraction of portfolio
    rationale: str


def get_agent_roles() -> dict[str, list[str]]:
    """Role rosters, mirroring the TradingAgents analyst→researcher→PM layout."""
    return {
        "analysts": ["market", "news", "social", "fundamentals", "technical"],
        "researchers": ["bull", "bear", "contrarian"],
        "traders": ["execution"],
        "risk_managers": ["risk", "portfolio"],
    }


def build_consensus(reports: list[AgentReport]) -> dict:
    """Aggregate agent reports into one recommendation.

    Confidence is average agreement damped by directional disagreement, so a
    split bull/bear room never yields the raw average.
    """
    if not reports:
        return {"recommendation": "neutral", "confidence": 0.0}

    bulls = [r for r in reports if r.recommendation == "bullish"]
    bears = [r for r in reports if r.recommendation == "bearish"]
    avg_confidence = sum(r.confidence for r in reports) / len(reports)
    net = (len(bulls) - len(bears)) / len(reports)

    if not bulls and not bears:
        recommendation = "neutral"
    elif net > 0:
        recommendation = "bullish"
    elif net < 0:
        recommendation = "bearish"
    else:
        # Even split: side with the higher average conviction, bulls on a tie.
        recommendation = "bullish" if _avg_conf(bulls) >= _avg_conf(bears) else "bearish"

    confidence = round(avg_confidence * (0.5 + 0.5 * abs(net)), 4)
    return {
        "recommendation": recommendation,
        "confidence": confidence,
        "bull_votes": len(bulls),
        "bear_votes": len(bears),
        "total_reports": len(reports),
    }


def _avg_conf(reports: list[AgentReport]) -> float:
    return sum(r.confidence for r in reports) / len(reports) if reports else 0.0


def assess_risk(ticker: str, consensus: dict, reports: list[AgentReport]) -> dict:
    """Score decision risk from consensus confidence and room composition.

    Each risk factor adds 0.15; base risk grows as consensus confidence falls.
    """
    confidence = float(consensus.get("confidence", 0.0))
    score = (1.0 - confidence) * 0.7
    factors: list[dict] = []

    if confidence < 0.5:
        factors.append({"factor": "low_confidence", "detail": f"consensus confidence {confidence}"})
    recommendations = {r.recommendation for r in reports}
    if "bullish" in recommendations and "bearish" in recommendations:
        factors.append({"factor": "high_disagreement", "detail": "both bullish and bearish reports present"})
    if not any(r.role == "risk_manager" for r in reports):
        factors.append({"factor": "no_risk_review", "detail": "no risk_manager signed off"})

    score = round(min(1.0, score + 0.15 * len(factors)), 4)
    risk_level = "low" if score < 0.3 else "medium" if score < 0.6 else "high"
    return {
        "ticker": ticker,
        "risk_score": score,
        "risk_level": risk_level,
        "passes_limits": risk_level != "high",
        "factors": factors,
    }


def calculate_position_size(
    portfolio_value: float,
    confidence: float,
    risk_score: float,
    limits: RiskLimits | None = None,
) -> float:
    """Position as a fraction of the portfolio: conviction scaled by inverse risk,
    capped by limits. Returns 0.0 below the confidence floor."""
    limits = limits or RiskLimits()
    if confidence < limits.min_confidence:
        return 0.0
    size = limits.max_position_size * confidence * (1.0 - min(1.0, max(0.0, risk_score)))
    return round(max(0.0, size), 4)


def generate_decision(
    ticker: str,
    reports: list[AgentReport],
    portfolio_value: float,
    limits: RiskLimits | None = None,
) -> Decision:
    """Run reports through consensus → risk → sizing and produce one decision."""
    limits = limits or RiskLimits()
    consensus = build_consensus(reports)
    risk = assess_risk(ticker, consensus, reports)
    confidence = float(consensus["confidence"])
    recommendation = consensus["recommendation"]

    size = calculate_position_size(portfolio_value, confidence, risk["risk_score"], limits)
    below_floor = confidence < limits.min_confidence
    if below_floor or not risk["passes_limits"] or recommendation == "neutral":
        action = "HOLD"
    elif recommendation == "bullish":
        action = "BUY"
    else:
        action = "SELL"

    if below_floor:
        rationale = f"consensus confidence {confidence} below floor {limits.min_confidence}"
    elif not risk["passes_limits"]:
        factor_names = ", ".join(f["factor"] for f in risk["factors"]) or "risk score"
        rationale = f"risk limits blocked the trade: {factor_names}"
    else:
        rationale = f"{recommendation} consensus at confidence {confidence}"

    return Decision(
        ticker=ticker,
        action=action,
        confidence=confidence,
        risk_assessment=risk,
        position_size=size,
        rationale=rationale,
    )
