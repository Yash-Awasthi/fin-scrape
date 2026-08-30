"""
Sentiment analyzer from praw — social media sentiment patterns.
"""
from dataclasses import dataclass
from typing import List, Dict
import math


@dataclass
class SentimentResult:
    text: str
    polarity: float  # -1 to 1
    subjectivity: float  # 0 to 1
    label: str  # positive, negative, neutral


@dataclass
class SocialSentiment:
    platform: str
    topic: str
    total_mentions: int
    avg_sentiment: float
    positive_count: int
    negative_count: int
    neutral_count: int
    top_keywords: List[str]
    trend: str  # rising, falling, stable


POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic", "love",
    "best", "awesome", "perfect", "brilliant", "outstanding", "superb", "happy",
    "joy", "success", "win", "profit", "gain", "rise", "surge", "bullish",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "poor", "fail",
    "loss", "crash", "drop", "bearish", "decline", "recession", "crisis",
    "panic", "fear", "risk", "danger", "threat", "problem", "issue", "bug",
}

INTENSIFIERS = {"very": 1.5, "extremely": 2.0, "incredibly": 2.0, "slightly": 0.5, "barely": 0.3}

NEGATORS = {"not", "no", "never", "neither", "nobody", "nothing", "nowhere", "nor", "cannot", "can't", "won't", "don't"}


def analyze_sentiment(text: str) -> SentimentResult:
    words = text.lower().split()
    score = 0.0
    negated = False
    intensifier = 1.0

    for i, word in enumerate(words):
        if word in NEGATORS:
            negated = True
            continue
        if word in INTENSIFIERS:
            intensifier = INTENSIFIERS[word]
            continue

        word_score = 0.0
        if word in POSITIVE_WORDS:
            word_score = 1.0
        elif word in NEGATIVE_WORDS:
            word_score = -1.0

        if negated:
            word_score *= -0.7
            negated = False
        if intensifier != 1.0:
            word_score *= intensifier
            intensifier = 1.0

        score += word_score

    avg = score / max(1, len(words))
    polarity = max(-1.0, min(1.0, avg))
    subjectivity = min(1.0, abs(avg) * 2)

    if polarity > 0.1:
        label = "positive"
    elif polarity < -0.1:
        label = "negative"
    else:
        label = "neutral"

    return SentimentResult(text=text, polarity=polarity, subjectivity=subjectivity, label=label)


def batch_analyze(texts: List[str]) -> Dict:
    results = [analyze_sentiment(t) for t in texts]
    positive = sum(1 for r in results if r.label == "positive")
    negative = sum(1 for r in results if r.label == "negative")
    neutral = sum(1 for r in results if r.label == "neutral")
    avg_polarity = sum(r.polarity for r in results) / len(results) if results else 0

    words = []
    for text in texts:
        words.extend(text.lower().split())
    word_freq = {}
    for w in words:
        if len(w) > 3:
            word_freq[w] = word_freq.get(w, 0) + 1
    top_words = sorted(word_freq.keys(), key=lambda x: -word_freq[x])[:10]

    return {
        "total": len(results),
        "positive": positive,
        "negative": negative,
        "neutral": neutral,
        "avg_polarity": avg_polarity,
        "top_keywords": top_words,
    }


def compute_sentiment_trend(sentiments: List[float], window: int = 5) -> str:
    if len(sentiments) < window * 2:
        return "stable"
    recent = sum(sentiments[-window:]) / window
    earlier = sum(sentiments[-window * 2:-window]) / window
    diff = recent - earlier
    if diff > 0.1:
        return "rising"
    elif diff < -0.1:
        return "falling"
    return "stable"
