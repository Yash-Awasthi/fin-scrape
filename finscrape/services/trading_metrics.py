"""Trading Metrics Service.

Extracted from ai-trader (inspiration).
Calculates competition, cooperation, and content metrics
for trading agent evaluation.

All pure functions — no DB, no async.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentMetrics:
    """Metrics for a single trading agent."""
    agent_id: str
    challenges_participated: int = 0
    challenges_won: int = 0
    avg_rank: float = 0.0
    max_drawdown: float = 0.0
    total_return: float = 0.0


@dataclass
class CompetitionMetrics:
    """Competition-wide metrics."""
    participation_rate: float = 0.0
    win_rate: float = 0.0
    rank_stability: float = 0.0
    risk_escalation: float = 0.0
    strategy_convergence: float = 0.0
    return_distribution_mean: float = 0.0
    max_drawdown_mean: float = 0.0


@dataclass
class CooperationMetrics:
    """Cooperation metrics for agent networks."""
    citation_count: int = 0
    adoption_count: int = 0
    team_contribution_score: float = 0.0
    team_consensus_gain: float = 0.0
    reply_graph_centrality: float = 0.0
    cross_community_bridge_score: int = 0
    discussion_gain: int = 0


@dataclass
class ContentMetrics:
    """Content quality metrics."""
    verifiability: float = 0.0
    evidence_score: float = 0.0
    specificity: float = 0.0
    novelty: float = 0.0
    review_score: float = 0.0
    duplicate_content_rate: float = 0.0


# --- Helper Functions ---

def mean(values: list[float]) -> float:
    """Calculate mean of a list of values."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def stddev(values: list[float]) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0
    avg = mean(values)
    variance = sum((x - avg) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


# --- Competition Metrics ---

def calculate_competition_metrics(
    agents: list[AgentMetrics],
    total_agents: int,
) -> CompetitionMetrics:
    """Calculate competition metrics from agent data.

    Args:
        agents: List of agent metrics
        total_agents: Total number of agents in competition

    Returns:
        Competition metrics
    """
    if not agents:
        return CompetitionMetrics()

    participants = [a for a in agents if a.challenges_participated > 0]
    winners = [a for a in agents if a.challenges_won > 0]

    participation_rate = len(participants) / max(total_agents, 1)
    win_rate = len(winners) / max(len(participants), 1)

    # Rank stability: lower stddev = more stable ranks
    ranks = [a.avg_rank for a in participants if a.avg_rank > 0]
    rank_stability = 1 / (1 + stddev(ranks)) if ranks else 0.0

    # Risk escalation: average max drawdown
    drawdowns = [a.max_drawdown for a in participants if a.max_drawdown > 0]
    risk_escalation = mean(drawdowns)

    # Strategy convergence: inverse of unique strategies (simplified)
    returns = [a.total_return for a in participants]
    return_mean = mean(returns)

    return CompetitionMetrics(
        participation_rate=round(participation_rate, 6),
        win_rate=round(win_rate, 6),
        rank_stability=round(rank_stability, 6),
        risk_escalation=round(risk_escalation, 6),
        strategy_convergence=round(1 / max(1, len(set(returns))), 6),
        return_distribution_mean=round(return_mean, 6),
        max_drawdown_mean=round(risk_escalation, 6),
    )


# --- Cooperation Metrics ---

def calculate_cooperation_metrics(
    edges: list[dict],
    team_results: list[dict],
    replies: list[dict],
    total_agents: int,
) -> CooperationMetrics:
    """Calculate cooperation metrics from network data.

    Args:
        edges: List of network edges (citation, adoption, follow, reply, same_team)
        team_results: List of team results
        replies: List of signal replies
        total_agents: Total number of agents

    Returns:
        Cooperation metrics
    """
    edge_types = {}
    for edge in edges:
        et = edge.get("edge_type", "unknown")
        edge_types[et] = edge_types.get(et, 0) + 1

    citation_count = edge_types.get("citation", 0)
    adoption_count = edge_types.get("adoption", 0) + edge_types.get("follow", 0)

    team_scores = [float(r.get("quality_score", 0)) for r in team_results if r.get("quality_score")]
    consensus_gains = [float(r.get("consensus_gain", 0)) for r in team_results if r.get("consensus_gain")]

    return CooperationMetrics(
        citation_count=citation_count,
        adoption_count=adoption_count,
        team_contribution_score=round(mean(team_scores), 6),
        team_consensus_gain=round(mean(consensus_gains), 6),
        reply_graph_centrality=round(edge_types.get("reply", 0) / max(total_agents, 1), 6),
        cross_community_bridge_score=edge_types.get("same_team", 0),
        discussion_gain=len(replies),
    )


# --- Content Metrics ---

def calculate_content_metrics(
    quality_scores: list[dict],
) -> ContentMetrics:
    """Calculate content quality metrics.

    Args:
        quality_scores: List of quality score dicts

    Returns:
        Content metrics
    """
    if not quality_scores:
        return ContentMetrics()

    def safe_float(d: dict, key: str) -> float:
        try:
            return float(d.get(key, 0))
        except (ValueError, TypeError):
            return 0.0

    return ContentMetrics(
        verifiability=round(mean([safe_float(q, "verifiability_score") for q in quality_scores]), 6),
        evidence_score=round(mean([safe_float(q, "evidence_score") for q in quality_scores]), 6),
        specificity=round(mean([safe_float(q, "specificity_score") for q in quality_scores]), 6),
        novelty=round(mean([safe_float(q, "novelty_score") for q in quality_scores]), 6),
        review_score=round(mean([safe_float(q, "review_score") for q in quality_scores]), 6),
        duplicate_content_rate=0.0,
    )


# --- Agent Evaluation ---

def evaluate_agent(
    agent: AgentMetrics,
    total_agents: int,
    peer_agents: list[AgentMetrics],
) -> dict:
    """Evaluate a single agent's performance.

    Args:
        agent: Agent to evaluate
        total_agents: Total agents in competition
        peer_agents: Other agents for comparison

    Returns:
        Evaluation summary
    """
    if not peer_agents:
        return {"agent_id": agent.agent_id, "score": 0, "rank": 1}

    peer_returns = [p.total_return for p in peer_agents]
    peer_ranks = [p.avg_rank for p in peer_agents if p.avg_rank > 0]

    # Percentile ranking
    better_count = sum(1 for r in peer_returns if r < agent.total_return)
    percentile = better_count / max(len(peer_returns), 1) * 100

    # Score: weighted combination
    rank_score = (1 - agent.avg_rank / max(total_agents, 1)) * 40
    return_score = min(100, max(0, agent.total_return * 100)) * 0.3
    consistency_score = (1 - agent.max_drawdown) * 30

    total_score = rank_score + return_score + consistency_score

    return {
        "agent_id": agent.agent_id,
        "score": round(total_score, 2),
        "percentile": round(percentile, 1),
        "peer_rank": better_count + 1,
        "total_peers": len(peer_agents),
    }


# --- Risk Metrics ---

def calculate_risk_metrics(returns: list[float]) -> dict:
    """Calculate risk metrics from return series.

    Args:
        returns: List of returns

    Returns:
        Risk metrics
    """
    if not returns:
        return {}

    avg_return = mean(returns)
    volatility = stddev(returns)

    # Sharpe ratio (assuming risk-free rate = 0)
    sharpe = avg_return / volatility if volatility > 0 else 0.0

    # Sortino ratio (downside deviation only)
    downside = [r for r in returns if r < 0]
    downside_std = stddev(downside) if len(downside) > 1 else 0.0
    sortino = avg_return / downside_std if downside_std > 0 else 0.0

    # Max drawdown
    cumulative = 1.0
    peak = 1.0
    max_dd = 0.0
    for r in returns:
        cumulative *= (1 + r)
        peak = max(peak, cumulative)
        dd = (peak - cumulative) / peak
        max_dd = max(max_dd, dd)

    # Win rate
    wins = sum(1 for r in returns if r > 0)
    win_rate = wins / len(returns)

    return {
        "mean_return": round(avg_return, 6),
        "volatility": round(volatility, 6),
        "sharpe_ratio": round(sharpe, 4),
        "sortino_ratio": round(sortino, 4),
        "max_drawdown": round(max_dd, 4),
        "win_rate": round(win_rate, 4),
        "total_trades": len(returns),
    }
