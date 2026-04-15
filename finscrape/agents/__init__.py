"""
Multi-Agent AI Council for financial news analysis.

Provides multiple AI personas that independently analyze articles and
produce a consensus verdict through weighted deliberation.

Quick start:
    from finscrape.agents import AgentCouncil, DEFAULT_AGENTS

    council = AgentCouncil(agents=DEFAULT_AGENTS)
    verdict = council.deliberate(title, text, metadata)
"""

from finscrape.agents.base import BaseAgent, AgentVerdict
from finscrape.agents.council import AgentCouncil, CouncilVerdict
from finscrape.agents.personas import (
    AnalystAgent,
    ContrarianAgent,
    RiskAgent,
    MomentumAgent,
    FundamentalsAgent,
    ScoutAgent,
    ReviewerAgent,
    DEFAULT_AGENTS,
)
from finscrape.agents.market_personas import (
    InstitutionalWhaleAgent,
    RetailDayTraderAgent,
    ContrarianInvestorAgent,
    QuantAgent,
    ESGInvestorAgent,
    MARKET_PERSONAS,
)

__all__ = [
    "BaseAgent",
    "AgentVerdict",
    "AgentCouncil",
    "CouncilVerdict",
    "AnalystAgent",
    "ContrarianAgent",
    "RiskAgent",
    "MomentumAgent",
    "FundamentalsAgent",
    "ScoutAgent",
    "ReviewerAgent",
    "DEFAULT_AGENTS",
    "InstitutionalWhaleAgent",
    "RetailDayTraderAgent",
    "ContrarianInvestorAgent",
    "QuantAgent",
    "ESGInvestorAgent",
    "MARKET_PERSONAS",
]
