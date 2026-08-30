"""Tests for geopolitical_risk.py — geopolitical risk analysis."""

import pytest
from finscrape.services.geopolitical_risk import (
    EventCategory, RiskLevel, MarketDirection,
    GeopoliticalEvent, SectorImpact, GeopoliticalRiskIndex,
    detect_event_category, extract_countries, calculate_event_risk_score,
    analyze_event, assess_sector_impact, calculate_risk_index,
)


class TestEventDetection:
    def test_conflict_detection(self):
        cats = detect_event_category("Russian troops launch military offensive in Ukraine")
        assert cats[0][0] == EventCategory.CONFLICT
        assert cats[0][1] > 0

    def test_sanctions_detection(self):
        cats = detect_event_category("US imposes new sanctions and embargo on Russian banks")
        assert any(c[0] == EventCategory.SANCTIONS for c in cats)

    def test_energy_detection(self):
        cats = detect_event_category("OPEC announces oil production cut amid energy crisis")
        assert any(c[0] == EventCategory.ENERGY for c in cats)

    def test_no_event(self):
        cats = detect_event_category("The weather is nice today")
        assert len(cats) == 0

    def test_multiple_categories(self):
        cats = detect_event_category(
            "Trade war escalation with new tariffs and sanctions on technology exports"
        )
        assert len(cats) >= 2


class TestCountryExtraction:
    def test_us_mention(self):
        countries = extract_countries("The United States announces new policy")
        assert any("united states" in c.lower() or c.upper() == "US" for c in countries)

    def test_multiple_countries(self):
        countries = extract_countries("China and Japan agree with European Union")
        assert len(countries) >= 2

    def test_no_countries(self):
        countries = extract_countries("The stock market rose today")
        assert len(countries) == 0


class TestRiskScoring:
    def test_nuclear_high_risk(self):
        score = calculate_event_risk_score(
            EventCategory.NUCLEAR, ["IRAN"], "Nuclear enrichment program"
        )
        assert score > 0.5

    def test_diplomatic_low_risk(self):
        score = calculate_event_risk_score(
            EventCategory.DIPLOMATIC, ["LUXEMBOURG"], "Bilateral meeting"
        )
        assert score < 0.5

    def test_major_economy_boost(self):
        score_major = calculate_event_risk_score(
            EventCategory.CONFLICT, ["US", "CHINA"], "Military tension"
        )
        score_minor = calculate_event_risk_score(
            EventCategory.CONFLICT, ["LUXEMBOURG"], "Military tension"
        )
        assert score_major > score_minor


class TestEventAnalysis:
    def test_full_analysis(self):
        event = analyze_event(
            text="Breaking: Military offensive launched in Ukraine, NATO responds with urgent meeting",
            title="Ukraine Crisis Escalates",
            source="Reuters",
            timestamp="2024-01-15",
        )
        assert event is not None
        assert event.category in (EventCategory.CONFLICT, EventCategory.DIPLOMATIC)
        assert event.risk_score > 0
        assert len(event.countries) > 0 or len(event.keywords) > 0

    def test_no_event(self):
        event = analyze_event(text="Beautiful sunny day in the park")
        assert event is None


class TestSectorImpact:
    def test_conflict_impact(self):
        event = GeopoliticalEvent(
            event_id="test",
            category=EventCategory.CONFLICT,
            title="Test conflict",
            description="Military conflict",
            countries=["US"],
            risk_level=RiskLevel.HIGH,
            risk_score=0.8,
            confidence=0.7,
            timestamp="2024-01-01",
        )
        impacts = assess_sector_impact(event)
        assert len(impacts) > 0
        # Defense should be bullish in conflict
        defense = next((i for i in impacts if i.sector == "defense"), None)
        assert defense is not None
        assert defense.direction == MarketDirection.BULLISH

    def test_trade_war_impact(self):
        event = GeopoliticalEvent(
            event_id="test",
            category=EventCategory.TRADE_WAR,
            title="Trade war",
            description="Tariffs imposed",
            countries=["US", "CHINA"],
            risk_level=RiskLevel.HIGH,
            risk_score=0.7,
            confidence=0.6,
            timestamp="2024-01-01",
        )
        impacts = assess_sector_impact(event)
        industrial = next((i for i in impacts if i.sector == "industrial"), None)
        assert industrial is not None
        assert industrial.direction == MarketDirection.BEARISH


class TestRiskIndex:
    def test_empty_events(self):
        index = calculate_risk_index([])
        assert index.overall_level == RiskLevel.LOW
        assert index.active_events == 0

    def test_multiple_events(self):
        events = [
            GeopoliticalEvent(
                event_id=f"e{i}",
                category=EventCategory.CONFLICT,
                title=f"Conflict {i}",
                description="",
                countries=["US"],
                risk_level=RiskLevel.HIGH,
                risk_score=0.8,
                confidence=0.7,
                timestamp="2024-01-01",
            )
            for i in range(5)
        ]
        index = calculate_risk_index(events)
        assert index.active_events == 5
        assert index.overall_score > 0
        assert "conflict" in index.component_scores

    def test_market_outlook(self):
        events = [
            GeopoliticalEvent(
                event_id="e1",
                category=EventCategory.NUCLEAR,
                title="Nuclear",
                description="",
                countries=["US", "RUSSIA", "CHINA"],
                risk_level=RiskLevel.CRITICAL,
                risk_score=0.95,
                confidence=0.8,
                timestamp="2024-01-01",
            )
        ]
        index = calculate_risk_index(events)
        assert index.market_outlook in (MarketDirection.BEARISH, MarketDirection.VOLATILE)
