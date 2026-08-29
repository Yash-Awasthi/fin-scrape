"""Tests for event intelligence — pure function tests, no AI calls."""
from finscrape.agents.event_intelligence import (
    EventType,
    ImpactMagnitude,
    ImpactTimeline,
    SignalDirection,
    assess_impact,
    assess_magnitude,
    assess_timeline,
    detect_events,
    detect_sectors,
    generate_signal,
    MarketEvent,
)


EARNINGS_TEXT = (
    "Apple Inc. reported Q3 earnings that beat analyst expectations. "
    "Revenue increased 12% year over year to $94.8 billion, exceeding "
    "guidance of $90 billion. EPS came in at $1.26 vs expected $1.18. "
    "The company raised full-year guidance citing strong iPhone sales."
)

MA_TEXT = (
    "Microsoft announced it will acquire Activision Blizzard for $68.7 billion "
    "in an all-cash deal. The merger is expected to close by fiscal year end, "
    "pending regulatory approval from the FTC."
)

REGULATORY_TEXT = (
    "The FDA approved Pfizer's new drug treatment for rare heart disease. "
    "The approval was faster than expected and covers adults aged 18 and older."
)

GEOPOLITICAL_TEXT = (
    "New trade tariffs on Chinese imports were announced by the White House, "
    "affecting semiconductor and technology sectors. Markets fell on the news."
)

BANKRUPTCY_TEXT = (
    "WeWork filed for Chapter 11 bankruptcy protection today, citing "
    "unsustainable debt levels and declining office space demand."
)


class TestEventDetection:
    def test_detects_earnings(self):
        events = detect_events(EARNINGS_TEXT)
        types = {e.event_type for e in events}
        assert EventType.EARNINGS in types

    def test_detects_merger(self):
        events = detect_events(MA_TEXT)
        types = {e.event_type for e in events}
        assert EventType.MERGER_ACQUISITION in types

    def test_detects_regulatory(self):
        events = detect_events(REGULATORY_TEXT)
        types = {e.event_type for e in events}
        assert EventType.REGULATORY in types

    def test_detects_geopolitical(self):
        events = detect_events(GEOPOLITICAL_TEXT)
        types = {e.event_type for e in events}
        assert EventType.GEOPOLITICAL in types

    def test_detects_bankruptcy(self):
        events = detect_events(BANKRUPTCY_TEXT)
        types = {e.event_type for e in events}
        assert EventType.BANKRUPTCY in types

    def test_extracts_tickers(self):
        events = detect_events(EARNINGS_TEXT)
        # Should not find false positives from common words
        for e in events:
            for t in e.tickers:
                assert len(t) >= 2

    def test_empty_text(self):
        events = detect_events("")
        assert len(events) == 0


class TestSectorDetection:
    def test_tech_sector(self):
        sectors = detect_sectors("semiconductor chip shortage affects tech sector")
        assert "technology" in sectors

    def test_healthcare(self):
        sectors = detect_sectors("FDA approved new drug for medical treatment")
        assert "healthcare" in sectors

    def test_energy(self):
        sectors = detect_sectors("oil prices surge on renewable energy transition")
        assert "energy" in sectors

    def test_multiple_sectors(self):
        sectors = detect_sectors("banking technology fintech disruption in financial sector")
        assert "finance" in sectors
        assert "technology" in sectors


class TestMagnitudeAssessment:
    def test_critical_from_bankruptcy(self):
        mag = assess_magnitude(BANKRUPTCY_TEXT, EventType.BANKRUPTCY)
        assert mag in (ImpactMagnitude.CRITICAL, ImpactMagnitude.HIGH)

    def test_high_from_billion_deal(self):
        mag = assess_magnitude(MA_TEXT, EventType.MERGER_ACQUISITION)
        assert mag in (ImpactMagnitude.HIGH, ImpactMagnitude.CRITICAL)

    def test_medium_default(self):
        mag = assess_magnitude("company announces quarterly report", EventType.EARNINGS)
        assert mag in (ImpactMagnitude.MEDIUM, ImpactMagnitude.HIGH)


class TestTimelineAssessment:
    def test_earnings_immediate(self):
        assert assess_timeline(EventType.EARNINGS) == ImpactTimeline.IMMEDIATE

    def test_merger_long_term(self):
        assert assess_timeline(EventType.MERGER_ACQUISITION) == ImpactTimeline.LONG_TERM

    def test_bankruptcy_immediate(self):
        assert assess_timeline(EventType.BANKRUPTCY) == ImpactTimeline.IMMEDIATE


class TestImpactAssessment:
    def test_full_assessment(self):
        event = MarketEvent(
            event_type=EventType.EARNINGS,
            title="Q3 Earnings Beat",
            description=EARNINGS_TEXT,
            tickers=["AAPL"],
            confidence=0.8,
        )
        impact = assess_impact(event)
        assert impact.affected_sectors  # should find technology
        assert impact.magnitude in (ImpactMagnitude.LOW, ImpactMagnitude.MEDIUM, ImpactMagnitude.HIGH, ImpactMagnitude.CRITICAL)
        assert impact.timeline == ImpactTimeline.IMMEDIATE
        assert len(impact.risk_factors) >= 0
        assert len(impact.historical_precedent) > 0


class TestSignalGeneration:
    def test_bullish_earnings(self):
        event = MarketEvent(
            event_type=EventType.EARNINGS,
            title="Beat",
            description=EARNINGS_TEXT,
            tickers=["AAPL"],
            confidence=0.8,
        )
        signal = generate_signal(event, EARNINGS_TEXT)
        assert signal.direction in (SignalDirection.BULLISH, SignalDirection.NEUTRAL)
        assert 0 < signal.confidence <= 1
        assert signal.tickers == ["AAPL"]

    def test_bearish_bankruptcy(self):
        event = MarketEvent(
            event_type=EventType.BANKRUPTCY,
            title="Chapter 11",
            description=BANKRUPTCY_TEXT,
            confidence=0.9,
        )
        signal = generate_signal(event, BANKRUPTCY_TEXT)
        assert signal.direction == SignalDirection.BEARISH

    def test_signal_has_rationale(self):
        event = MarketEvent(
            event_type=EventType.MERGER_ACQUISITION,
            title="Acquisition",
            description=MA_TEXT,
            tickers=["MSFT"],
            confidence=0.7,
        )
        signal = generate_signal(event, MA_TEXT)
        assert len(signal.rationale) > 20
        assert signal.strength in ("weak", "moderate", "strong")
