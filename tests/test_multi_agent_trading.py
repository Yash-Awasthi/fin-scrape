"""Tests for Multi-Agent Trading Orchestration."""
import pytest
from finscrape.services.multi_agent_trading import (
    build_consensus,
    assess_risk,
    calculate_position_size,
    generate_decision,
    get_agent_roles,
    AgentReport,
    RiskLimits,
)


class TestAgentRoles:
    def test_has_all_roles(self):
        roles = get_agent_roles()
        assert "analysts" in roles
        assert "researchers" in roles
        assert "traders" in roles
        assert "risk_managers" in roles
        assert len(roles["analysts"]) == 5
        assert len(roles["researchers"]) == 3


class TestConsensus:
    def test_unanimous_bullish(self):
        reports = [
            AgentReport("Market", "analyst", "AAPL", "bullish", 0.8, "Good"),
            AgentReport("News", "analyst", "AAPL", "bullish", 0.7, "Positive"),
            AgentReport("Trader", "trader", "AAPL", "bullish", 0.9, "Strong"),
        ]
        result = build_consensus(reports)
        assert result["recommendation"] == "bullish"
        assert result["confidence"] > 0.7

    def test_mixed_signals(self):
        reports = [
            AgentReport("Bull", "researcher", "AAPL", "bullish", 0.8, "Upside"),
            AgentReport("Bear", "researcher", "AAPL", "bearish", 0.8, "Downside"),
        ]
        result = build_consensus(reports)
        assert result["recommendation"] in ("bullish", "bearish")
        assert result["confidence"] < 0.8

    def test_empty_reports(self):
        result = build_consensus([])
        assert result["recommendation"] == "neutral"
        assert result["confidence"] == 0.0

    def test_neutral_consensus(self):
        reports = [
            AgentReport("Market", "analyst", "AAPL", "neutral", 0.5, "Mixed"),
        ]
        result = build_consensus(reports)
        assert result["recommendation"] == "neutral"


class TestRiskAssessment:
    def test_low_risk(self):
        consensus = {"recommendation": "bullish", "confidence": 0.8}
        reports = [
            AgentReport("Risk", "risk_manager", "AAPL", "bullish", 0.7, "OK"),
        ]
        result = assess_risk("AAPL", consensus, reports)
        assert result["risk_level"] == "low"
        assert result["passes_limits"] is True

    def test_high_risk_low_confidence(self):
        consensus = {"recommendation": "bullish", "confidence": 0.3}
        reports = []
        result = assess_risk("AAPL", consensus, reports)
        assert result["risk_level"] == "high"
        assert result["passes_limits"] is False

    def test_disagreement_risk(self):
        consensus = {"recommendation": "bullish", "confidence": 0.5}
        reports = [
            AgentReport("Bull", "analyst", "AAPL", "bullish", 0.6, "Up"),
            AgentReport("Bear", "analyst", "AAPL", "bearish", 0.6, "Down"),
            AgentReport("Neutral", "analyst", "AAPL", "neutral", 0.5, "Flat"),
        ]
        result = assess_risk("AAPL", consensus, reports)
        assert any(f["factor"] == "high_disagreement" for f in result["factors"])


class TestPositionSizing:
    def test_high_confidence(self):
        size = calculate_position_size(100000, 0.8, 0.2)
        assert size > 0
        assert size <= 0.10

    def test_low_confidence(self):
        limits = RiskLimits(min_confidence=0.6)
        size = calculate_position_size(100000, 0.3, 0.5, limits)
        assert size == 0.0

    def test_high_risk(self):
        size = calculate_position_size(100000, 0.8, 0.9)
        assert size < calculate_position_size(100000, 0.8, 0.1)


class TestGenerateDecision:
    def test_bullish_decision(self):
        reports = [
            AgentReport("Market", "analyst", "AAPL", "bullish", 0.8, "Good"),
            AgentReport("Trader", "trader", "AAPL", "bullish", 0.9, "Strong"),
        ]
        decision = generate_decision("AAPL", reports, 100000)
        assert decision.action in ("BUY", "LONG")
        assert decision.confidence > 0.5

    def test_bearish_decision(self):
        reports = [
            AgentReport("Market", "analyst", "AAPL", "bearish", 0.8, "Bad"),
            AgentReport("Trader", "trader", "AAPL", "bearish", 0.9, "Weak"),
        ]
        decision = generate_decision("AAPL", reports, 100000)
        assert decision.action in ("SELL", "SHORT")
        assert decision.confidence > 0.5

    def test_hold_on_risk(self):
        limits = RiskLimits(min_confidence=0.9)
        reports = [
            AgentReport("Market", "analyst", "AAPL", "bullish", 0.5, "Maybe"),
        ]
        decision = generate_decision("AAPL", reports, 100000, limits)
        assert decision.action == "HOLD"

    def test_has_risk_assessment(self):
        reports = [
            AgentReport("Market", "analyst", "AAPL", "bullish", 0.8, "Good"),
        ]
        decision = generate_decision("AAPL", reports, 100000)
        assert decision.risk_assessment is not None
        assert "risk_score" in decision.risk_assessment
