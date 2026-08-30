"""
Multi-agent debate from multi-agent-debates-langgraph patterns.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import math


@dataclass
class DebateAgent:
    name: str
    role: str
    stance: str = "neutral"
    arguments: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class DebateRound:
    round_num: int
    statements: List[Dict[str, str]]
    dominant_view: str = ""
    consensus_score: float = 0.0


@dataclass
class DebateResult:
    topic: str
    agents: List[DebateAgent]
    rounds: List[DebateRound]
    final_consensus: str
    consensus_score: float
    winning_stance: str
    dissenting_views: List[str]


class DebateOrchestrator:
    def __init__(self):
        self.agents: List[DebateAgent] = []

    def add_agent(self, agent: DebateAgent):
        self.agents.append(agent)

    def conduct_debate(self, topic: str, num_rounds: int = 3) -> DebateResult:
        rounds = []
        for r in range(num_rounds):
            statements = []
            for agent in self.agents:
                stance = "agree" if r > 0 and agent.confidence > 0.6 else "disagree" if r > 0 else "neutral"
                statements.append({"agent": agent.name, "statement": f"Round {r+1}: {agent.role} perspective on {topic}", "stance": stance})
            dominant = max(set(s["stance"] for s in statements), key=lambda x: sum(1 for s in statements if s["stance"] == x))
            consensus = sum(1 for s in statements if s["stance"] == dominant) / len(statements) if statements else 0
            rounds.append(DebateRound(round_num=r+1, statements=statements, dominant_view=dominant, consensus_score=consensus))
        final_consensus = rounds[-1].dominant_view if rounds else "undecided"
        final_score = rounds[-1].consensus_score if rounds else 0
        dissenting = [s["statement"] for r in rounds for s in r.statements if s["stance"] != final_consensus]
        return DebateResult(topic=topic, agents=self.agents, rounds=rounds, final_consensus=final_consensus, consensus_score=final_score, winning_stance=final_consensus, dissenting_views=dissenting[:3])
