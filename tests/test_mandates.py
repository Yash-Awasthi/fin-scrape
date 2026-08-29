"""Tests for mandate system."""
import pytest
from finscrape.council.mandates import (
    Mandate, MandateStatus, RiskTolerance, Position,
    validate_recommendation, allocate_risk_budgets, track_compliance,
    ComplianceRecord,
)


def _default_mandate():
    return Mandate(
        name="Test Fund",
        risk_tolerance=RiskTolerance.MODERATE,
        max_position_pct=25.0,
        max_sector_pct=40.0,
        max_positions=10,
        min_confidence=0.3,
        min_score=-2,
    )


class TestMandate:
    def test_defaults(self):
        m = _default_mandate()
        assert m.status == MandateStatus.ACTIVE
        assert m.max_position_pct == 25.0

    def test_to_dict(self):
        m = _default_mandate()
        d = m.to_dict()
        assert d["name"] == "Test Fund"
        assert d["risk_tolerance"] == "moderate"
        assert d["status"] == "active"


class TestValidateRecommendation:
    def test_approve_valid(self):
        m = _default_mandate()
        r = validate_recommendation(
            m, "AAPL", "technology", score=3, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is True
        assert r["breach_count"] == 0

    def test_reject_low_score(self):
        m = _default_mandate()
        r = validate_recommendation(
            m, "AAPL", "technology", score=-5, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is False
        assert any(v["rule"] == "min_score" for v in r["violations"])

    def test_reject_low_confidence(self):
        m = _default_mandate()
        r = validate_recommendation(
            m, "AAPL", "technology", score=2, confidence=0.1,
            current_positions=[], portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is False
        assert any(v["rule"] == "min_confidence" for v in r["violations"])

    def test_reject_excluded_ticker(self):
        m = _default_mandate()
        m.excluded_tickers = ["TSLA"]
        r = validate_recommendation(
            m, "TSLA", "technology", score=3, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is False

    def test_reject_excluded_sector(self):
        m = _default_mandate()
        m.excluded_sectors = ["tobacco"]
        r = validate_recommendation(
            m, "MO", "tobacco", score=3, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is False

    def test_reject_max_positions(self):
        m = _default_mandate()
        m.max_positions = 2
        positions = [
            Position(ticker="A", shares=10, avg_cost=100, current_price=100, sector="tech"),
            Position(ticker="B", shares=10, avg_cost=100, current_price=100, sector="tech"),
        ]
        r = validate_recommendation(
            m, "C", "tech", score=3, confidence=0.8,
            current_positions=positions, portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is False
        assert any(v["rule"] == "max_positions" for v in r["violations"])

    def test_reject_position_size(self):
        m = _default_mandate()
        r = validate_recommendation(
            m, "AAPL", "tech", score=3, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=30_000,
        )
        assert r["approved"] is False
        assert any(v["rule"] == "max_position_pct" for v in r["violations"])

    def test_reject_sector_concentration(self):
        m = _default_mandate()
        positions = [
            Position(ticker="A", shares=200, avg_cost=100, current_price=100, sector="tech"),
            Position(ticker="B", shares=200, avg_cost=100, current_price=100, sector="tech"),
        ]
        r = validate_recommendation(
            m, "C", "tech", score=3, confidence=0.8,
            current_positions=positions, portfolio_value=100_000, proposed_value=10_000,
        )
        assert r["approved"] is False

    def test_warning_not_breach(self):
        m = _default_mandate()
        r = validate_recommendation(
            m, "AAPL", "tech", score=3, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=23_000,
        )
        # 23% is close to 25% limit → warning, not breach
        assert r["approved"] is True
        assert r["warning_count"] > 0

    def test_reject_trade_frequency(self):
        m = _default_mandate()
        m.max_daily_trades = 3
        r = validate_recommendation(
            m, "AAPL", "tech", score=3, confidence=0.8,
            current_positions=[], portfolio_value=100_000, proposed_value=10_000,
            daily_trades_today=3,
        )
        assert r["approved"] is False


class TestAllocateRiskBudgets:
    def test_allocation(self):
        mandates = [
            Mandate("Conservative", risk_tolerance=RiskTolerance.CONSERVATIVE),
            Mandate("Moderate", risk_tolerance=RiskTolerance.MODERATE),
            Mandate("Aggressive", risk_tolerance=RiskTolerance.AGGRESSIVE),
        ]
        budgets = allocate_risk_budgets(mandates)
        assert len(budgets) == 3
        assert budgets[0].risk_allocation_pct < budgets[1].risk_allocation_pct < budgets[2].risk_allocation_pct

    def test_var_limit(self):
        mandates = [Mandate("Test", max_drawdown_pct=10)]
        budgets = allocate_risk_budgets(mandates, portfolio_value=200_000)
        assert budgets[0].var_limit == 20_000.0

    def test_headroom(self):
        budgets = allocate_risk_budgets([Mandate("T", risk_tolerance=RiskTolerance.MODERATE)])
        assert budgets[0].risk_remaining == budgets[0].risk_allocation_pct


class TestTrackCompliance:
    def test_empty(self):
        r = track_compliance([])
        assert r["total_checks"] == 0

    def test_with_records(self):
        records = [
            ComplianceRecord("2026-01-01", "Fund", "AAPL", "buy", True, []),
            ComplianceRecord("2026-01-01", "Fund", "TSLA", "buy", False,
                            [{"rule": "excluded_ticker", "description": "TSLA excluded", "severity": "breach"}]),
        ]
        r = track_compliance(records)
        assert r["total_checks"] == 2
        assert r["approved"] == 1
        assert r["rejected"] == 1
        assert r["approval_rate"] == 50.0
