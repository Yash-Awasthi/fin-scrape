"""Stock market news sentiment analysis and summarization.

Extracted from inspiration/fin-scrape/stock-market-news-sentiment-analysis-and-summarization.
Patterns: NLP pipeline for financial news classification, weekly sentiment summarization,
word2vec/GloVe embeddings, sentence transformers, HuggingFace fine-tuning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Sequence

# ── Sentiment labels ──────────────────────────────────────────────────────────

POSITIVE = "positive"
NEGATIVE = "negative"
NEUTRAL = "neutral"


@dataclass(frozen=True)
class NewsItem:
    date: datetime
    headline: str
    content: str = ""
    ticker: str | None = None
    source: str | None = None


@dataclass(frozen=True)
class SentimentResult:
    label: str
    confidence: float  # 0.0–1.0
    positive_score: float
    negative_score: float
    neutral_score: float


@dataclass
class WeeklySummary:
    week_start: datetime
    week_end: datetime
    top_positive: list[SentimentResult] = field(default_factory=list)
    top_negative: list[SentimentResult] = field(default_factory=list)
    avg_sentiment: float = 0.0
    article_count: int = 0


# ── Lexicon-based sentiment scorer (no external deps) ─────────────────────────

_FINANCIAL_POSITIVE_WORDS = frozenset({
    "bullish", "surge", "soar", "profit", "gain", "growth", "upgrade",
    "beat", "exceed", "strong", "robust", "outperform", "rally", "recovery",
    "dividend", "buy", "hold", "opportunity", "optimistic", "record",
    "high", "boost", "jump", "rise", "climb", "breakthrough", "expand",
})

_FINANCIAL_NEGATIVE_WORDS = frozenset({
    "bearish", "plunge", "crash", "loss", "decline", "downgrade", "miss",
    "weak", "underperform", "sell", "bear", "recession", "bankrupt", "debt",
    "crisis", "fall", "drop", "slump", "warning", "risk", "lawsuit", "fraud",
    "investigation", "layoff", "cut", "default", "volatility", "fear",
})

_NEGATION_WORDS = frozenset({"not", "no", "never", "neither", "nor", "without"})


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    import re
    return re.findall(r"[a-zA-Z]+", text.lower())


def lexicon_sentiment(text: str) -> SentimentResult:
    """Score sentiment using a financial-domain lexicon.

    Handles simple negation: a negation word before a sentiment word flips its polarity.
    """
    tokens = _tokenize(text)
    if not tokens:
        return SentimentResult(NEUTRAL, 0.0, 0.0, 0.0, 1.0)

    pos = neg = neu = 0
    neg_window = 0
    for tok in tokens:
        if tok in _NEGATION_WORDS:
            neg_window = 3
            continue
        is_pos = tok in _FINANCIAL_POSITIVE_WORDS
        is_neg = tok in _FINANCIAL_NEGATIVE_WORDS
        if neg_window > 0:
            is_pos, is_neg = is_neg, is_pos  # flip
            neg_window -= 1
        if is_pos:
            pos += 1
        elif is_neg:
            neg += 1
        else:
            neu += 1

    total = pos + neg + neu
    if total == 0:
        return SentimentResult(NEUTRAL, 0.0, 0.0, 0.0, 1.0)

    p, n, u = pos / total, neg / total, neu / total
    if p > n and p > u:
        return SentimentResult(POSITIVE, p, p, n, u)
    elif n > p and n > u:
        return SentimentResult(NEGATIVE, n, p, n, u)
    return SentimentResult(NEUTRAL, u, p, n, u)


# ── Batch classification ─────────────────────────────────────────────────────

def classify_batch(items: Sequence[NewsItem]) -> list[tuple[NewsItem, SentimentResult]]:
    """Classify a batch of news items."""
    return [(item, lexicon_sentiment(f"{item.headline} {item.content}")) for item in items]


# ── Weekly summarization ──────────────────────────────────────────────────────

def _week_bounds(dt: datetime) -> tuple[datetime, datetime]:
    start = dt - timedelta(days=dt.weekday())
    start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=7)


def weekly_summary(items: Sequence[NewsItem]) -> list[WeeklySummary]:
    """Group news items by ISO week and summarize sentiment."""
    by_week: dict[datetime, list[tuple[NewsItem, SentimentResult]]] = {}
    for item in items:
        ws, _ = _week_bounds(item.date)
        by_week.setdefault(ws, []).append((item, lexicon_sentiment(item.headline)))

    summaries: list[WeeklySummary] = []
    for ws, pairs in sorted(by_week.items()):
        positives = sorted(
            [s for _, s in pairs if s.label == POSITIVE],
            key=lambda s: s.confidence, reverse=True,
        )[:5]
        negatives = sorted(
            [s for _, s in pairs if s.label == NEGATIVE],
            key=lambda s: s.confidence, reverse=True,
        )[:5]
        avg = sum(s.positive_score - s.negative_score for _, s in pairs) / max(len(pairs), 1)
        summaries.append(WeeklySummary(
            week_start=ws, week_end=ws + timedelta(days=7),
            top_positive=positives, top_negative=negatives,
            avg_sentiment=avg, article_count=len(pairs),
        ))
    return summaries


# ── Embedding-based similarity (simplified, no external deps) ───────────────

def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = sum(a * a for a in vec_a) ** 0.5
    norm_b = sum(b * b for b in vec_b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _bow_vector(text: str) -> dict[str, int]:
    tokens = _tokenize(text)
    bow: dict[str, int] = {}
    for t in tokens:
        bow[t] = bow.get(t, 0) + 1
    return bow


def text_similarity(text_a: str, text_b: str) -> float:
    """Cosine similarity via bag-of-words vectors."""
    bow_a = _bow_vector(text_a)
    bow_b = _bow_vector(text_b)
    vocab = set(bow_a) | set(bow_b)
    if not vocab:
        return 0.0
    vec_a = [bow_a.get(w, 0) for w in vocab]
    vec_b = [bow_b.get(w, 0) for w in vocab]
    return _cosine_similarity(vec_a, vec_b)


def deduplicate_news(items: Sequence[NewsItem], threshold: float = 0.8) -> list[NewsItem]:
    """Remove near-duplicate news articles based on headline similarity."""
    seen: list[NewsItem] = []
    for item in items:
        is_dup = False
        for s in seen:
            if text_similarity(item.headline, s.headline) > threshold:
                is_dup = True
                break
        if not is_dup:
            seen.append(item)
    return seen


# ── Trading signal from sentiment ─────────────────────────────────────────────

@dataclass(frozen=True)
class SentimentSignal:
    ticker: str | None
    signal: str  # "bullish", "bearish", "neutral"
    strength: float  # 0.0–1.0
    source_count: int
    confidence: float  # 0.0–1.0


def sentiment_to_signal(
    items: Sequence[NewsItem], ticker: str | None = None
) -> SentimentSignal:
    """Aggregate sentiment across multiple news items into a single trading signal."""
    relevant = [i for i in items if ticker is None or i.ticker == ticker]
    if not relevant:
        return SentimentSignal(ticker, "neutral", 0.0, 0, 0.0)

    results = [lexicon_sentiment(i.headline) for i in relevant]
    total_score = sum(r.positive_score - r.negative_score for r in results)
    avg = total_score / len(results)

    if avg > 0.1:
        signal = "bullish"
    elif avg < -0.1:
        signal = "bearish"
    else:
        signal = "neutral"

    strength = min(abs(avg), 1.0)
    # confidence: higher with more articles and stronger sentiment
    confidence = min(strength * (1 + 0.1 * (len(results) - 1)), 1.0)

    return SentimentSignal(ticker, signal, strength, len(results), confidence)
