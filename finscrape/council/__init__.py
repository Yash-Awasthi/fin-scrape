"""
worldfin-council — Multi-agent deliberation council.

Zero-dependency pure Python package for running multiple AI agents in parallel,
computing consensus, and optionally overriding with a judge.

Usage:
    from worldfin_council import AgentCouncil, CouncilVerdict
    from worldfin_council.base import BaseAgent, AgentVerdict

    council = AgentCouncil(agents=[...], judge=True)
    verdict = council.deliberate(title, text, metadata)
"""
from finscrape.council.council import AgentCouncil
from finscrape.council.council import CouncilVerdict
from finscrape.council.base import BaseAgent, AgentVerdict

__all__ = ["AgentCouncil", "CouncilVerdict", "BaseAgent", "AgentVerdict"]
