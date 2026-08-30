"""Tests for trading metrics service."""

import pytest
from finscrape.services.trading_metrics import (
    AgentMetrics,
    calculate_competition_metrics,
    calculate_cooperation_metrics,
    calculate_content_metrics,
    evaluate_agent,
    calculate_risk_metrics,
)


class TestCompetitionMetrics:
    def test_calculate(self):
        agents = [
            AgentMetrics("a1", challenges_participated=10, challenges_won=3, avg_rank=2.5, max_drawdown=0.1, total_return=0.15),
            AgentMetrics("a2", challenges_participated=8, challenges_won=2, avg_rank=3.0, max_drawdown=0.2, total_return=0.10),
        ]
        result = calculate_competition_metrics(agents, 20)
        assert result.participation_rate > 0
        assert result.win_rate > 0
        assert result.rank_stability > 0

    def test_empty(self):
        result = calculate_competition_metrics([], 10)
        assert result.participation_rate == 0.0


class TestCooperationMetrics:
    def test_calculate(self):
        edges = [{"edge_type": "citation"}, {"edge_type": "adoption"}, {"edge_type": "reply"}]
        team_results = [{"quality_score": "0.8", "consensus_gain": "0.5"}]
        replies = [{"text": "reply1"}, {"text": "reply2"}]
        result = calculate_cooperation_metrics(edges, team_results, replies, 10)
        assert result.citation_count == 1
        assert result.adoption_count == 1
        assert result.discussion_gain == 2


class TestContentMetrics:
    def test_calculate(self):
        scores = [
            {"verifiability_score": "0.9", "evidence_score": "0.8", "specificity_score": "0.7", "novelty_score": "0.6", "review_score": "0.5"},
        ]
        result = calculate_content_metrics(scores)
        assert result.verifiability == pytest.approx(0.9, abs=0.01)
        assert result.evidence_score == pytest.approx(0.8, abs=0.01)


class TestAgentEvaluation:
    def test_evaluate(self):
        agent = AgentMetrics("a1", avg_rank=2.0, total_return=0.15, max_drawdown=0.1)
        peers = [
            AgentMetrics("a2", avg_rank=3.0, total_return=0.10, max_drawdown=0.2),
            AgentMetrics("a3", avg_rank=4.0, total_return=0.05, max_drawdown=0.3),
        ]
        result = evaluate_agent(agent, 10, peers)
        assert result["score"] > 0
        assert result["peer_rank"] > 0


class TestRiskMetrics:
    def test_calculate(self):
        returns = [0.01, -0.005, 0.02, -0.01, 0.015]
        result = calculate_risk_metrics(returns)
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert "win_rate" in result

    def test_empty(self):
        assert calculate_risk_metrics([]) == {}
