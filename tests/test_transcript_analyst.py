"""Tests for transcript analyst — pure function tests, no AI calls."""
from finscrape.agents.transcript_analyst import (
    analyze_sentiment,
    analyze_transcript,
    detect_speaker_role,
    extract_insights,
    extract_key_quotes,
    extract_risk_factors,
    parse_speakers,
    parse_transcript,
    SpeakerRole,
)


SAMPLE_TRANSCRIPT = """
John Smith, CEO: Good morning everyone. We are very optimistic about our growth trajectory.
Revenue increased 25% year over year and we exceeded our guidance for the third consecutive quarter.
Our margins expanded significantly and we see strong momentum heading into next year.

Sarah Johnson, CFO: Thank you, John. Let me add some color to the financials.
Gross margin improved to 42%, up from 38% last quarter. We expect continued margin expansion
as we scale operations. Our guidance for next quarter is revenue of $500 million,
which represents continued strong growth.

Analyst, Goldman Sachs: Can you comment on the competitive landscape? How do you see
market share evolving against your main competitors?

John Smith, CEO: We face competition from several players but our innovation pipeline
gives us confidence. The risk of market saturation is something we monitor closely,
but we believe our technology leadership is sustainable.

Sarah Johnson, CFO: On the risk front, supply chain headwinds remain a concern.
We may face some pressure on input costs, but we have hedging strategies in place.
"""


class TestSpeakerDetection:
    def test_detect_ceo(self):
        assert detect_speaker_role("CEO, Acme Corp") == SpeakerRole.CEO

    def test_detect_cfo(self):
        assert detect_speaker_role("Chief Financial Officer") == SpeakerRole.CFO

    def test_detect_analyst(self):
        assert detect_speaker_role("Analyst, Goldman Sachs") == SpeakerRole.ANALYST

    def test_detect_moderator(self):
        assert detect_speaker_role("Moderator, Earnings Call") == SpeakerRole.MODERATOR

    def test_unknown(self):
        assert detect_speaker_role("") == SpeakerRole.UNKNOWN


class TestParseSpeakers:
    def test_finds_speakers(self):
        speakers = parse_speakers(SAMPLE_TRANSCRIPT)
        names = {s.name for s in speakers}
        assert "John Smith" in names
        assert "Sarah Johnson" in names

    def test_roles_detected(self):
        speakers = parse_speakers(SAMPLE_TRANSCRIPT)
        roles = {s.name: s.role for s in speakers}
        assert roles.get("John Smith") == SpeakerRole.CEO
        assert roles.get("Sarah Johnson") == SpeakerRole.CFO


class TestSentiment:
    def test_positive_text(self):
        label, score = analyze_sentiment("Strong growth, record revenue, optimistic outlook")
        assert label == "bullish"
        assert score > 0

    def test_negative_text(self):
        label, score = analyze_sentiment("Weak decline, risk, challenging headwinds, bearish")
        assert label == "bearish"
        assert score < 0

    def test_neutral_text(self):
        label, score = analyze_sentiment("The meeting is scheduled for tomorrow at 3pm")
        assert label == "neutral"

    def test_sample_transcript(self):
        label, score = analyze_sentiment(SAMPLE_TRANSCRIPT)
        # Mixed tone: strong positives hedged by risk/concern language
        assert label in ("bullish", "neutral")
        assert score >= -0.1  # should not be bearish


class TestInsights:
    def test_extracts_guidance(self):
        insights = extract_insights(SAMPLE_TRANSCRIPT, parse_speakers(SAMPLE_TRANSCRIPT))
        categories = {i.category for i in insights}
        assert "guidance" in categories

    def test_extracts_risks(self):
        insights = extract_insights(SAMPLE_TRANSCRIPT, parse_speakers(SAMPLE_TRANSCRIPT))
        risk_insights = [i for i in insights if i.category == "risk"]
        assert len(risk_insights) > 0

    def test_extracts_competitive(self):
        insights = extract_insights(SAMPLE_TRANSCRIPT, parse_speakers(SAMPLE_TRANSCRIPT))
        comp = [i for i in insights if i.category == "competitive"]
        assert len(comp) > 0


class TestKeyQuotes:
    def test_extracts_quotes(self):
        quotes = extract_key_quotes(SAMPLE_TRANSCRIPT, max_quotes=3)
        assert len(quotes) > 0
        assert all(len(q) > 30 for q in quotes)


class TestRiskFactors:
    def test_extracts_risks(self):
        risks = extract_risk_factors(SAMPLE_TRANSCRIPT)
        assert len(risks) > 0
        assert any("supply chain" in r.lower() or "risk" in r.lower() for r in risks)


class TestFullAnalysis:
    def test_analyze_transcript(self):
        result = analyze_transcript(
            title="Q3 Earnings",
            company="Acme Corp",
            text=SAMPLE_TRANSCRIPT,
        )
        assert result.title == "Q3 Earnings"
        assert result.company == "Acme Corp"
        assert result.total_segments > 0
        assert len(result.speakers) > 0
        assert result.overall_sentiment in ("bullish", "bearish", "neutral")
        assert isinstance(result.sentiment_score, float)
        assert len(result.key_quotes) > 0

    def test_empty_text(self):
        result = analyze_transcript(title="", company="", text="")
        assert result.total_segments == 0
        assert result.overall_sentiment == "neutral"
