"""
Financial sentiment analysis (lexicon-based, zero dependencies).

Implements the sentiment feature distilled from the absorbed sentiment repos
(FinNews-Sentiment-Stock-Correlation-Analysis, Stock-News-Analysis-with-BERT):
VADER-style scoring with finance-specific lexicon, negation handling,
intensifiers and a financial-context boost. `src/sentiment_analyzer.py` holds the
VADER/FinBERT-flavored variant; this module is the pure-python engine whose API
(`Sentiment` / `SentimentResult` / `SentimentAnalyzer`) the test suite pins.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum


class Sentiment(str, Enum):
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


@dataclass
class SentimentResult:
    """Sentiment verdict for one piece of text."""

    text: str
    sentiment: Sentiment
    score: float  # -1.0 (very bearish) .. 1.0 (very bullish)
    confidence: float  # 0.0 .. 1.0, coverage of sentiment-bearing words
    positive_words: list[str] = field(default_factory=list)
    negative_words: list[str] = field(default_factory=list)
    word_count: int = 0


@dataclass
class SentimentTrend:
    """Aggregate sentiment over a labeled window of results."""

    period: str
    avg_score: float
    volatility: float
    count: int


POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic", "love",
    "best", "awesome", "perfect", "brilliant", "outstanding", "superb",
    "success", "successful", "win", "wins", "profit", "profits", "profitable",
    "gain", "gains", "rise", "rises", "rising", "rose", "surge", "surges",
    "surged", "soar", "soars", "soared", "rally", "rallies", "bullish",
    "beat", "beats", "beating", "revenue", "revenues", "earnings", "growth",
    "grow", "grows", "grew", "exceptional", "strong", "stronger", "strongest",
    "upgrade", "upgraded", "outperform", "outperforms", "record", "recovery",
    "breakthrough", "innovation", "dividend", "acquisition", "partnership",
    "expansion", "milestone", "optimistic", "rallying", "boom", "booming",
    "exceed", "exceeds", "exceeding", "increase", "increases", "increased",
    "positive", "top", "high", "favorable",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "horrible", "worst", "hate", "poor", "fail",
    "failing", "failure", "loss", "losses", "lose", "crash", "crashes",
    "crashed", "drop", "drops", "dropped", "bearish", "decline", "declines",
    "declined", "recession", "crisis", "panic", "fear", "danger", "threat",
    "problem", "problems", "plunge", "plunges", "plunged", "plummet",
    "plummets", "collapse", "bankruptcy", "bankrupt", "lawsuit", "fraud",
    "investigation", "downgrade", "downgraded", "miss", "misses", "missed",
    "weak", "weaker", "weakest", "pessimistic", "bust", "default", "layoff",
    "layoffs", "low", "negative", "tumble", "tumbles", "slump", "concern",
    "concerns", "risk", "risks", "risky",
}

INTENSIFIERS = {
    "extremely": 2.0, "incredibly": 2.0, "very": 1.5, "massive": 1.5,
    "massively": 1.5, "sharply": 1.5, "significantly": 1.5, "huge": 1.5,
    "dramatically": 1.5, "substantially": 1.5, "slightly": 0.5,
    "barely": 0.3, "marginally": 0.5,
}

NEGATORS = {
    "not", "no", "never", "neither", "nobody", "nothing", "nowhere", "nor",
    "cannot", "can't", "won't", "don't", "isn't", "aren't", "doesn't",
}

# Words that mark the text as finance-related; their presence boosts confidence
# in the lexicon verdict (a "strong" in an earnings note means more than in prose).
FINANCIAL_CONTEXT = {
    "revenue", "revenues", "earnings", "profit", "profits", "stock", "stocks",
    "shares", "market", "markets", "ticker", "investors", "company",
    "companies", "fiscal", "quarter", "guidance", "estimates", "analyst",
    "analysts", "trading", "ipo",
}

_TOKEN_RE = re.compile(r"[a-z']+")


def _classify(score: float) -> Sentiment:
    if score >= 0.4:
        return Sentiment.VERY_BULLISH
    if score > 0.05:
        return Sentiment.BULLISH
    if score <= -0.4:
        return Sentiment.VERY_BEARISH
    if score < -0.05:
        return Sentiment.BEARISH
    return Sentiment.NEUTRAL


def _analyze(text: str) -> SentimentResult:
    tokens = _TOKEN_RE.findall((text or "").lower())
    positives: list[str] = []
    negatives: list[str] = []
    score = 0.0
    negated = False  # flips the next sentiment-bearing word
    intensifier = 1.0

    for token in tokens:
        if token in NEGATORS:
            negated = True
            intensifier = 1.0
            continue
        if token in INTENSIFIERS:
            intensifier = INTENSIFIERS[token]
            continue

        word_score = 0.0
        if token in POSITIVE_WORDS:
            word_score = 1.0
            positives.append(token)
        elif token in NEGATIVE_WORDS:
            word_score = -1.0
            negatives.append(token)

        if word_score:
            if negated:
                word_score *= -0.7
                negated = False
            word_score *= intensifier
            intensifier = 1.0
            score += word_score

    word_count = len(tokens)
    if word_count:
        score /= word_count
        if any(t in FINANCIAL_CONTEXT for t in tokens):
            score = min(1.0, score * 1.15)
    score = round(max(-1.0, min(1.0, score)), 4)

    hits = len(positives) + len(negatives)
    confidence = round(min(1.0, 0.3 + 0.5 * hits / max(1, word_count)), 4) if word_count else 0.0

    return SentimentResult(
        text=text or "",
        sentiment=_classify(score),
        score=score,
        confidence=confidence,
        positive_words=positives,
        negative_words=negatives,
        word_count=word_count,
    )


class SentimentAnalyzer:
    """Lexicon-based financial sentiment engine (static API)."""

    @classmethod
    def analyze_text(cls, text: str) -> SentimentResult:
        """Score a body of text; -1..1 score with word-level evidence."""
        return _analyze(text)

    @classmethod
    def analyze_headline(cls, headline: str) -> SentimentResult:
        """Score a headline — same engine, headlines are short enough that the
        per-word signals dominate, so no separate weighting is needed."""
        return _analyze(headline)

    @classmethod
    def calculate_sentiment_trend(cls, results: Sequence[SentimentResult], period: str) -> SentimentTrend:
        """Average score + volatility across a labeled window of results."""
        scores = [r.score for r in results]
        if not scores:
            return SentimentTrend(period=period, avg_score=0.0, volatility=0.0, count=0)
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return SentimentTrend(
            period=period,
            avg_score=round(mean, 4),
            volatility=round(variance ** 0.5, 4),
            count=len(scores),
        )

    @classmethod
    def extract_sentiment_keywords(cls, text: str) -> list[tuple[str, int]]:
        """Sentiment-bearing words in `text` with frequencies, most frequent first."""
        tokens = _TOKEN_RE.findall((text or "").lower())
        hits = [t for t in tokens if t in POSITIVE_WORDS or t in NEGATIVE_WORDS]
        return sorted(Counter(hits).items(), key=lambda kv: (-kv[1], kv[0]))


# ── Legacy helpers (kept for callers predating the class API) ────────────────

@dataclass
class SocialSentiment:
    platform: str
    topic: str
    total_mentions: int
    avg_sentiment: float
    positive_count: int
    negative_count: int
    neutral_count: int
    top_keywords: list[str]
    trend: str  # rising, falling, stable


def analyze_sentiment(text: str) -> SentimentResult:
    """Backward-compatible alias for SentimentAnalyzer.analyze_text."""
    return _analyze(text)


def batch_analyze(texts: list[str]) -> dict:
    results = [_analyze(t) for t in texts]
    positive = sum(1 for r in results if r.score > 0.05)
    negative = sum(1 for r in results if r.score < -0.05)
    avg_score = sum(r.score for r in results) / len(results) if results else 0.0

    keyword_freq: Counter = Counter()
    for text in texts:
        keyword_freq.update(t for t in _TOKEN_RE.findall(text.lower()) if len(t) > 3)
    top_words = [w for w, _ in keyword_freq.most_common(10)]

    return {
        "total": len(results),
        "positive": positive,
        "negative": negative,
        "neutral": len(results) - positive - negative,
        "avg_score": round(avg_score, 4),
        "top_keywords": top_words,
    }


def compute_sentiment_trend(sentiments: list[float], window: int = 5) -> str:
    if len(sentiments) < window * 2:
        return "stable"
    recent = sum(sentiments[-window:]) / window
    earlier = sum(sentiments[-window * 2:-window]) / window
    diff = recent - earlier
    if diff > 0.1:
        return "rising"
    if diff < -0.1:
        return "falling"
    return "stable"
