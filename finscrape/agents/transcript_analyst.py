"""
Transcript analyst — analyzes earnings calls, expert interviews, analyst discussions.

Inspired by AlphaSense's moat: transcript intelligence is what separates
enterprise tools from open-source alternatives. This agent extracts
actionable insights from financial transcripts.

Pure functions for parsing + extraction. AI calls go through the agent's
_base.run() pattern (inherited from BaseAgent).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SpeakerRole(str, Enum):
    CEO = "ceo"
    CFO = "cfo"
    ANALYST = "analyst"
    EXPERT = "expert"
    MODERATOR = "moderator"
    UNKNOWN = "unknown"


class SentimentShift(str, Enum):
    BULLISH_SHIFT = "bullish_shift"
    BEARISH_SHIFT = "bearish_shift"
    NEUTRAL = "neutral"
    DEFENSIVE = "defensive"
    OPTIMISTIC = "optimistic"


@dataclass(frozen=True)
class Speaker:
    name: str
    role: SpeakerRole
    title: str = ""


@dataclass(frozen=True)
class TranscriptSegment:
    speaker: Speaker
    text: str
    timestamp: str | None = None


@dataclass(frozen=True)
class TranscriptInsight:
    """A single extracted insight from a transcript."""
    category: str  # "guidance", "margin", "competitive", "outlook", "risk", "growth"
    quote: str
    speaker: str
    speaker_role: str
    sentiment: str  # "positive", "negative", "neutral"
    confidence: float  # 0-1
    impact: str  # "high", "medium", "low"
    summary: str


@dataclass(frozen=True)
class TranscriptAnalysis:
    """Full analysis of a transcript."""
    title: str
    company: str
    total_segments: int
    speakers: list[Speaker]
    insights: list[TranscriptInsight]
    overall_sentiment: str  # "bullish", "bearish", "neutral"
    sentiment_score: float  # -1 to 1
    key_quotes: list[str]
    guidance_changes: list[str]
    risk_factors: list[str]
    competitive_mentions: list[str]


# ── Speaker Detection ────────────────────────────────────────────────────────

# Common earnings call patterns
CEO_TITLES = {"ceo", "chief executive", "president", "founder", "co-founder"}
CFO_TITLES = {"cfo", "chief financial", "finance", "financial officer"}
ANALYST_KEYWORDS = {"analyst", "question", "from:", "question:"}
MODERATOR_KEYWORDS = {"moderator", "operator", "facilitator", "welcome"}


def detect_speaker_role(text_before: str) -> SpeakerRole:
    """Detect speaker role from text context (name/title line before their speech)."""
    lower = text_before.lower()
    for kw in MODERATOR_KEYWORDS:
        if kw in lower:
            return SpeakerRole.MODERATOR
    for kw in CEO_TITLES:
        if kw in lower:
            return SpeakerRole.CEO
    for kw in CFO_TITLES:
        if kw in lower:
            return SpeakerRole.CFO
    for kw in ANALYST_KEYWORDS:
        if kw in lower:
            return SpeakerRole.ANALYST
    return SpeakerRole.UNKNOWN


def parse_speakers(text: str) -> list[Speaker]:
    """Extract unique speakers from transcript text."""
    # Pattern: "Name, Title" or "Name (Title)" before a colon or paragraph
    patterns = [
        r"([A-Z][a-z]+ [A-Z][a-z]+),?\s*(?:—|–|-)?\s*(CEO|CFO|President|Chief\w*(?:\s+\w+)*|Analyst|Moderator|Operator)",
        r"([A-Z][a-z]+ [A-Z][a-z]+)\s*\(([^)]+)\)",
    ]

    speakers: dict[str, Speaker] = {}
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.MULTILINE):
            name = match.group(1).strip()
            title = match.group(2).strip()
            role = detect_speaker_role(title)
            if name not in speakers:
                speakers[name] = Speaker(name=name, role=role, title=title)

    return list(speakers.values())


# ── Transcript Parsing ───────────────────────────────────────────────────────


def parse_transcript(text: str) -> list[TranscriptSegment]:
    """Parse raw transcript text into structured segments."""
    segments: list[TranscriptSegment] = []

    # Split by speaker blocks (pattern: "Name, Title:" or "Name:")
    blocks = re.split(r"\n(?=[A-Z][a-z]+ [A-Z][a-z]+(?:,|\s*\(|\s*[–—-])|[A-Z][a-z]+:)", text)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Extract speaker line
        speaker_match = re.match(
            r"^([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*(?:[,–—-]\s*([^:\n]+))?\s*:\s*(.*)",
            block,
            re.DOTALL,
        )

        if speaker_match:
            name = speaker_match.group(1).strip()
            title = (speaker_match.group(2) or "").strip()
            body = speaker_match.group(3).strip()
            role = detect_speaker_role(title)
            speaker = Speaker(name=name, role=role, title=title)
        else:
            # No speaker detected — treat as continuation
            speaker = Speaker(name="Unknown", role=SpeakerRole.UNKNOWN)
            body = block

        segments.append(TranscriptSegment(speaker=speaker, text=body))

    return segments


# ── Sentiment Analysis ───────────────────────────────────────────────────────

POSITIVE_WORDS = {
    "strong", "growth", "increase", "beat", "exceeded", "optimistic",
    "confident", "expansion", "improvement", "record", "breakthrough",
    "accelerate", "outperform", "upgrade", "recovery", "momentum",
    "bullish", "upside", "opportunity", "innovative", "leading",
}

NEGATIVE_WORDS = {
    "weak", "decline", "decrease", "miss", "below", "cautious",
    "challenging", "headwinds", "risk", "uncertainty", "slowdown",
    "downside", "concern", "pressure", "volatile", "disruption",
    "bearish", "recession", "layoff", "restructuring", "impairment",
}

HEDGING_WORDS = {
    "may", "might", "could", "potentially", "uncertain", "challenging",
    "cautiously", "modest", "gradual", "some", "certain",
}


def analyze_sentiment(text: str) -> tuple[str, float]:
    """
    Simple lexicon-based sentiment analysis.
    Returns (label, score) where score is -1 to 1.
    """
    words = set(re.findall(r"\b\w+\b", text.lower()))
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    hedge = len(words & HEDGING_WORDS)

    total = pos + neg + hedge
    if total == 0:
        return "neutral", 0.0

    score = (pos - neg) / max(total, 1)
    # Dampen by hedging
    score *= (1 - hedge * 0.1)

    if score > 0.15:
        return "bullish", min(score, 1.0)
    elif score < -0.15:
        return "bearish", max(score, -1.0)
    return "neutral", score


def detect_sentiment_shift(segments: list[TranscriptSegment]) -> SentimentShift:
    """Detect if sentiment shifted during the transcript."""
    if len(segments) < 4:
        return SentimentShift.NEUTRAL

    mid = len(segments) // 2
    first_half = " ".join(s.text for s in segments[:mid])
    second_half = " ".join(s.text for s in segments[mid:])

    _, first_score = analyze_sentiment(first_half)
    _, second_score = analyze_sentiment(second_half)

    diff = second_score - first_score
    if diff > 0.2:
        return SentimentShift.BULLISH_SHIFT
    elif diff < -0.2:
        return SentimentShift.BEARISH_SHIFT
    elif second_score < -0.3:
        return SentimentShift.DEFENSIVE
    return SentimentShift.NEUTRAL


# ── Insight Extraction ───────────────────────────────────────────────────────


GUIDANCE_PATTERNS = [
    r"(?:guid(?:ance|e)|forecast|outlook|expect|project|target|plan)\w*\s+(?:is|are|to|for|of)?\s*(.{10,100})",
    r"(?:revenue|sales|earnings|eps|profit)\s+(?:guidance|forecast|outlook)\s+(?:of|is|are)?\s*(.{10,80})",
]

MARGIN_PATTERNS = [
    r"(?:margin|gross|operating|ebitda)\s+(?:is|are|will|should|improve|expand|compress|contract)\s*(.{10,100})",
    r"(?:margin|gross|operating)\s+(?:of|at|around|approximately)\s*(\d+\.?\d*%?)",
]

COMPETITIVE_PATTERNS = [
    r"(?:competitor|competition|rival|vs\.?|versus|compared to|market share)\s*(.{10,100})",
    r"(?:compete|disrupt|threat|challenge)\w*\s+(?:from|by|with)\s*(.{10,100})",
]

RISK_PATTERNS = [
    r"(?:risk|risk factor|headwind|challenge|threat|concern|uncertainty)\s*(.{10,120})",
    r"(?:may|could|might)\s+(?:be|face|experience|encounter)\s*(.{10,100})",
]


def extract_insights(text: str, speakers: list[Speaker]) -> list[TranscriptInsight]:
    """Extract structured insights from transcript text."""
    insights: list[TranscriptInsight] = []
    text_lower = text.lower()

    # Guidance changes
    for pattern in GUIDANCE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            quote = match.group(0).strip()
            if len(quote) > 15:
                sentiment, conf = ("positive", 0.6) if any(w in quote for w in POSITIVE_WORDS) else ("negative", 0.6) if any(w in quote for w in NEGATIVE_WORDS) else ("neutral", 0.5)
                insights.append(TranscriptInsight(
                    category="guidance",
                    quote=quote[:200],
                    speaker=speakers[0].name if speakers else "Unknown",
                    speaker_role=speakers[0].role.value if speakers else "unknown",
                    sentiment=sentiment,
                    confidence=conf,
                    impact="high",
                    summary=f"Forward guidance: {quote[:80]}",
                ))

    # Margin commentary
    for pattern in MARGIN_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            quote = match.group(0).strip()
            if len(quote) > 10:
                insights.append(TranscriptInsight(
                    category="margin",
                    quote=quote[:200],
                    speaker=speakers[0].name if speakers else "Unknown",
                    speaker_role=speakers[0].role.value if speakers else "unknown",
                    sentiment="positive" if any(w in quote for w in ["improve", "expand", "increase"]) else "negative" if any(w in quote for w in ["compress", "contract", "decline"]) else "neutral",
                    confidence=0.6,
                    impact="medium",
                    summary=f"Margin commentary: {quote[:80]}",
                ))

    # Competitive mentions
    for pattern in COMPETITIVE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            quote = match.group(0).strip()
            if len(quote) > 15:
                insights.append(TranscriptInsight(
                    category="competitive",
                    quote=quote[:200],
                    speaker=speakers[0].name if speakers else "Unknown",
                    speaker_role=speakers[0].role.value if speakers else "unknown",
                    sentiment="neutral",
                    confidence=0.5,
                    impact="medium",
                    summary=f"Competitive landscape: {quote[:80]}",
                ))

    # Risk factors
    for pattern in RISK_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            quote = match.group(0).strip()
            if len(quote) > 15:
                insights.append(TranscriptInsight(
                    category="risk",
                    quote=quote[:200],
                    speaker=speakers[0].name if speakers else "Unknown",
                    speaker_role=speakers[0].role.value if speakers else "unknown",
                    sentiment="negative",
                    confidence=0.6,
                    impact="high" if any(w in quote for w in ["significant", "material", "major"]) else "medium",
                    summary=f"Risk factor: {quote[:80]}",
                ))

    return insights


def extract_key_quotes(text: str, max_quotes: int = 5) -> list[str]:
    """Extract the most impactful quotes from a transcript."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    scored: list[tuple[float, str]] = []

    for s in sentences:
        if len(s) < 30 or len(s) > 300:
            continue
        # Score by keyword density
        words = set(re.findall(r"\b\w+\b", s.lower()))
        score = len(words & POSITIVE_WORDS) + len(words & NEGATIVE_WORDS)
        if any(w in s.lower() for w in ["guidance", "forecast", "outlook", "record"]):
            score += 2
        if any(w in s.lower() for w in ["margin", "revenue", "earnings"]):
            score += 1
        if score > 0:
            scored.append((score, s.strip()))

    scored.sort(key=lambda x: -x[0])
    return [s for _, s in scored[:max_quotes]]


def extract_guidance_changes(text: str) -> list[str]:
    """Extract forward guidance changes."""
    changes: list[str] = []
    for pattern in GUIDANCE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            change = match.group(0).strip()
            if len(change) > 15 and change not in changes:
                changes.append(change[:200])
    return changes


def extract_risk_factors(text: str) -> list[str]:
    """Extract risk factors mentioned in the transcript."""
    risks: list[str] = []
    for pattern in RISK_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            risk = match.group(0).strip()
            if len(risk) > 15 and risk not in risks:
                risks.append(risk[:200])
    return risks


# ── Full Analysis ────────────────────────────────────────────────────────────


def analyze_transcript(
    title: str,
    company: str,
    text: str,
) -> TranscriptAnalysis:
    """Run full transcript analysis. Pure functions only — no AI calls."""
    speakers = parse_speakers(text)
    segments = parse_transcript(text)
    insights = extract_insights(text, speakers)
    overall_sentiment, sentiment_score = analyze_sentiment(text)
    key_quotes = extract_key_quotes(text)
    guidance = extract_guidance_changes(text)
    risks = extract_risk_factors(text)

    # Competitive mentions
    competitive = []
    for insight in insights:
        if insight.category == "competitive" and insight.quote not in competitive:
            competitive.append(insight.quote)

    return TranscriptAnalysis(
        title=title,
        company=company,
        total_segments=len(segments),
        speakers=speakers,
        insights=insights,
        overall_sentiment=overall_sentiment,
        sentiment_score=round(sentiment_score, 3),
        key_quotes=key_quotes,
        guidance_changes=guidance,
        risk_factors=risks,
        competitive_mentions=competitive[:5],
    )
