"""Financial Sentiment Analyzer Service.

Extracted from fintwit-bot (inspiration).
Financial text sentiment analysis: bullish/bearish/neutral classification,
text preprocessing, and sentiment aggregation.
"""

from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Sentiment(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    text: str
    sentiment: Sentiment
    confidence: float
    score: float  # -1 to 1
    keywords: list[str] = field(default_factory=list)


@dataclass
class SentimentAggregation:
    overall: Sentiment
    bullish_pct: float
    bearish_pct: float
    neutral_pct: float
    avg_score: float
    total_texts: int
    dominant_keywords: list[str]
    trend: str  # "improving", "declining", "stable"


BULLISH_WORDS = {
    "bullish", "buy", "long", "moon", "pump", "rally", "surge", "breakout",
    "accumulate", "hold", "strong", "growth", "profit", "upgrade", "beat",
    "outperform", "overweight", "target", "momentum", "uptrend", "rocket",
}

BEARISH_WORDS = {
    "bearish", "sell", "short", "crash", "dump", "decline", "breakdown",
    "fear", "weak", "loss", "downgrade", "miss", "underperform", "underweight",
    "risk", "downtrend", "bubble", "overvalued", "recession", "inflation",
}

SENTIMENT_MODIFIERS = {
    "very": 1.5, "extremely": 2.0, "slightly": 0.5, "somewhat": 0.5,
    "highly": 1.5, "incredibly": 2.0, "absolutely": 2.0, "barely": 0.3,
}


def preprocess_text(text: str) -> str:
    """Preprocess text for sentiment analysis."""
    text = re.sub(r"http\S+", "[URL]", text)
    text = re.sub(r"@\S+", "@USER", text)
    text = re.sub(r"#(\S+)", r"\1", text)
    text = re.sub(r"\$\w+", "[TICKER]", text)
    text = re.sub(r"[^\w\s]", " ", text)
    return text.lower().strip()


def analyze_sentiment(text: str) -> SentimentResult:
    """Analyze sentiment of financial text."""
    processed = preprocess_text(text)
    words = processed.split()
    bullish_count = sum(1 for w in words if w in BULLISH_WORDS)
    bearish_count = sum(1 for w in words if w in BEARISH_WORDS)
    modifier = 1.0
    for i, w in enumerate(words):
        if w in SENTIMENT_MODIFIERS and i + 1 < len(words):
            if words[i + 1] in BULLISH_WORDS or words[i + 1] in BEARISH_WORDS:
                modifier = SENTIMENT_MODIFIERS[w]
    bullish_score = bullish_count * modifier
    bearish_score = bearish_count * modifier
    total = bullish_score + bearish_score
    if total == 0:
        sentiment = Sentiment.NEUTRAL
        confidence = 0.5
        score = 0.0
    elif bullish_score > bearish_score:
        sentiment = Sentiment.BULLISH
        confidence = min(0.9, bullish_score / total * 0.7 + 0.3)
        score = (bullish_score - bearish_score) / total
    elif bearish_score > bullish_score:
        sentiment = Sentiment.BEARISH
        confidence = min(0.9, bearish_score / total * 0.7 + 0.3)
        score = -(bearish_score - bullish_score) / total
    else:
        sentiment = Sentiment.NEUTRAL
        confidence = 0.5
        score = 0.0
    keywords = [w for w in words if w in BULLISH_WORDS or w in BEARISH_WORDS]
    return SentimentResult(
        text=text, sentiment=sentiment, confidence=round(confidence, 3),
        score=round(score, 3), keywords=keywords,
    )


def aggregate_sentiments(results: list[SentimentResult]) -> SentimentAggregation:
    """Aggregate multiple sentiment results."""
    if not results:
        return SentimentAggregation(Sentiment.NEUTRAL, 0, 0, 0, 0, 0, [], "stable")
    bullish = sum(1 for r in results if r.sentiment == Sentiment.BULLISH)
    bearish = sum(1 for r in results if r.sentiment == Sentiment.BEARISH)
    neutral = sum(1 for r in results if r.sentiment == Sentiment.NEUTRAL)
    total = len(results)
    bullish_pct = bullish / total * 100
    bearish_pct = bearish / total * 100
    neutral_pct = neutral / total * 100
    avg_score = statistics.mean(r.score for r in results)
    all_keywords = []
    for r in results:
        all_keywords.extend(r.keywords)
    keyword_counts = {}
    for kw in all_keywords:
        keyword_counts[kw] = keyword_counts.get(kw, 0) + 1
    dominant_keywords = sorted(keyword_counts.keys(), key=lambda k: keyword_counts[k], reverse=True)[:10]
    if avg_score > 0.1:
        overall = Sentiment.BULLISH
        trend = "improving"
    elif avg_score < -0.1:
        overall = Sentiment.BEARISH
        trend = "declining"
    else:
        overall = Sentiment.NEUTRAL
        trend = "stable"
    return SentimentAggregation(
        overall=overall, bullish_pct=round(bullish_pct, 1),
        bearish_pct=round(bearish_pct, 1), neutral_pct=round(neutral_pct, 1),
        avg_score=round(avg_score, 3), total_texts=total,
        dominant_keywords=dominant_keywords, trend=trend,
    )


def analyze_conversation(texts: list[str]) -> dict[str, Any]:
    """Analyze a conversation/thread of financial texts."""
    results = [analyze_sentiment(text) for text in texts]
    aggregation = aggregate_sentiments(results)
    return {
        "individual_results": [
            {"text": r.text[:100], "sentiment": r.sentiment.value,
             "confidence": r.confidence, "score": r.score}
            for r in results
        ],
        "aggregation": {
            "overall": aggregation.overall.value,
            "bullish_pct": aggregation.bullish_pct,
            "bearish_pct": aggregation.bearish_pct,
            "neutral_pct": aggregation.neutral_pct,
            "avg_score": aggregation.avg_score,
            "total_texts": aggregation.total_texts,
            "dominant_keywords": aggregation.dominant_keywords,
            "trend": aggregation.trend,
        },
    }
