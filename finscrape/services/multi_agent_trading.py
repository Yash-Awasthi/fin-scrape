"""
Multi-Agent Trading System — 15 specialized agents for trading analysis.

Inspired by TradingAgents-MCPmode.
Provides multi-agent collaboration, parallel analysis, and debate mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


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
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Debate:
    """A debate between bull and bear researchers."""
    id: str
    ticker: str
    bullArguments: List[str]
    bearArguments: List[str]
    rounds: int
    consensus: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RiskAssessment:
    """Risk assessment result."""
    agentId: str
    ticker: str
    riskLevel: str  # low, medium, high, extreme
    riskFactors: List[str]
    mitigationSuggestions: List[str]
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# Multi-Agent Trading Manager
# ============================================================================

class MultiAgentTradingManager:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.analyses: Dict[str, List[Analysis]] = {}
        self.debates: Dict[str, Debate] = {}
        self.riskAssessments: Dict[str, List[RiskAssessment]] = {}

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
                       confidence: float, reasoning: str, metrics: Dict[str, float]) -> Analysis:
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

    def get_consensus(self, ticker: str) -> Dict:
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
                              risk_factors: List[str], mitigation: List[str], confidence: float) -> RiskAssessment:
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

    def get_risk_summary(self, ticker: str) -> Dict:
        """Get risk summary for a ticker."""
        assessments = self.risk_assessments.get(ticker, [])
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

    def get_agent_performance(self) -> List[Dict]:
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

    def get_dashboard_data(self) -> Dict:
        """Get dashboard data for all tickers."""
        return {
            "tickers": list(self.analyses.keys()),
            "totalAnalyses": sum(len(a) for a in self.analyses.values()),
            "totalDebates": len(self.debates),
            "totalRiskAssessments": sum(len(r) for r in self.riskAssessments.values()),
            "activeAgents": sum(1 for a in self.agents.values() if a.isActive),
        }
