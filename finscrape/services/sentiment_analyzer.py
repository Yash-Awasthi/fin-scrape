"""
Financial Sentiment Analysis — Inspired by FinBERT, VADER, and Stock-News-Analysis patterns.

Provides text sentiment scoring for financial news, earnings calls,
and social media. Uses a lexicon-based approach with financial domain
specific adjustments. All pure functions, no external model dependencies.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums and data structures
# ---------------------------------------------------------------------------

class Sentiment(str, Enum):
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


@dataclass
class SentimentResult:
    """Sentiment analysis result for a single text."""
    text: str
    sentiment: Sentiment
    score: float  # -1.0 (bearish) to 1.0 (bullish)
    confidence: float  # 0.0 to 1.0
    positive_words: List[str] = field(default_factory=list)
    negative_words: List[str] = field(default_factory=list)
    bullish_signals: List[str] = field(default_factory=list)
    bearish_signals: List[str] = field(default_factory=list)


@dataclass
class NewsSentiment:
    """Aggregated sentiment for a news article."""
    headline: str
    overall: SentimentResult
    sentences: List[SentimentResult]
    source_credibility: float  # 0.0 to 1.0
    market_relevance: float  # 0.0 to 1.0
    urgency: float  # 0.0 to 1.0
    affected_tickers: List[str] = field(default_factory=list)


@dataclass
class EarningsSentiment:
    """Sentiment from earnings call transcript."""
    company: str
    quarter: str
    guidance_sentiment: SentimentResult
    management_tone: SentimentResult
    analyst_questions_sentiment: SentimentResult
    risk_factors_mentioned: List[str] = field(default_factory=list)
    forward_keywords: List[str] = field(default_factory=list)


@dataclass
class SentimentTrend:
    """Sentiment trend over time for a ticker."""
    ticker: str
    period: str
    data_points: List[Dict]  # [{date, score, volume}]
    trend_direction: Sentiment
    trend_strength: float  # 0.0 to 1.0
    avg_score: float
    volatility: float


# ---------------------------------------------------------------------------
# Financial sentiment lexicon
# ---------------------------------------------------------------------------

_STRONG_POSITIVE = {
    "beat", "exceeded", "outperformed", "surpass", "upgrade", "upgrade",
    "breakout", "surge", "soar", "rally", "bullish", "boom", "record",
    "profit", "growth", "surplus", "recovery", "optimistic", "strong",
    "accelerate", "expansion", "innovation", "milestone", "exceptional",
    "dividend", "buyback", "partnership", "acquisition", "approval",
}

_MODERATE_POSITIVE = {
    "rise", "gain", "increase", "up", "higher", "improve", "better",
    "positive", "steady", "stable", "support", "hold", "maintain",
    "progress", "develop", "opportunity", "potential", "favor",
    "benefit", "advantage", "strength", "resilient", "solid",
    "momentum", "uptick", "rebound", "bounce", "recover",
}

_STRONG_NEGATIVE = {
    "miss", "missed", "downgrade", "crash", "collapse", "plunge",
    "bearish", "recession", "bankruptcy", "default", "crisis",
    "fraud", "scandal", "lawsuit", "investigation", "ban",
    "bankrupt", "liquidation", "insolvency", "default", "catastrophe",
    "devastating", "catastrophic", "emergency", "panic", "collapse",
}

_MODERATE_NEGATIVE = {
    "fall", "drop", "decline", "down", "lower", "decrease", "loss",
    "negative", "risk", "concern", "worry", "weak", "weakness",
    "slow", "slowdown", "delay", "cut", "reduce", "pressure",
    "headwind", "challenge", "uncertainty", "volatile", "fluctuate",
    "cautious", "prudent", "conservative", "soft", "deteriorate",
}

_INTENSIFIERS = {
    "very", "extremely", "significantly", "substantially", "dramatically",
    "sharply", "massive", "huge", "massive", "unprecedented", "historic",
    "record-breaking", "stunning", "remarkable",
}

_NEGATORS = {
    "not", "no", "never", "neither", "nor", "hardly", "barely",
    "scarcely", "seldom", "rarely", "doesn't", "don't", "didn't",
    "won't", "wouldn't", "couldn't", "shouldn't", "isn't", "aren't",
}

_FINANCIAL_CONTEXT = {
    "revenue", "earnings", "eps", "margin", "guidance", "forecast",
    "outlook", "valuation", "market cap", "pe ratio", "dividend yield",
    "free cash flow", "debt", "leverage", "ebitda", "gross margin",
    "operating margin", "net income", "shareholder", "investor",
}

_SOURCE_CREDIBILITY = {
    "reuters": 0.9, "bloomberg": 0.9, "wsj": 0.85, "ft": 0.85,
    "cnbc": 0.7, "marketwatch": 0.7, "seeking alpha": 0.6,
    "reddit": 0.3, "twitter": 0.2, "stocktwits": 0.2,
    "sec filing": 0.95, "earnings call": 0.9, "10-k": 0.95, "10-q": 0.95,
}


# ---------------------------------------------------------------------------
# Core sentiment scoring
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Simple whitespace + punctuation tokenizer."""
    text = text.lower()
    tokens = re.findall(r'\b\w+\b', text)
    return tokens


def _has_negation(tokens: List[str], position: int, window: int = 3) -> bool:
    """Check if a word is negated within a window."""
    start = max(0, position - window)
    return any(t in _NEGATORS for t in tokens[start:position])


def _is_intensified(tokens: List[str], position: int, window: int = 2) -> bool:
    """Check if a word is intensified."""
    start = max(0, position - window)
    return any(t in _INTENSIFIERS for t in tokens[start:position])


def score_text(text: str) -> SentimentResult:
    """
    Score a piece of text for financial sentiment.
    
    Uses a lexicon-based approach with:
    - Financial domain-specific word weights
    - Negation handling (reverses sentiment within window)
    - Intensifier detection (amplifies sentiment)
    - Context awareness (financial terms amplify relevance)
    
    Returns:
        SentimentResult with score, classification, and word lists
    """
    tokens = _tokenize(text)
    if not tokens:
        return SentimentResult(
            text=text, sentiment=Sentiment.NEUTRAL,
            score=0.0, confidence=0.0,
        )
    
    positive_score = 0.0
    negative_score = 0.0
    positive_words = []
    negative_words = []
    
    for i, token in enumerate(tokens):
        weight = 1.0
        negated = _has_negation(tokens, i)
        intensified = _is_intensified(tokens, i)
        
        if intensified:
            weight = 1.5
        
        if token in _STRONG_POSITIVE:
            if negated:
                negative_score += 0.8 * weight
                negative_words.append(f"not {token}")
            else:
                positive_score += 0.8 * weight
                positive_words.append(token)
        
        elif token in _MODERATE_POSITIVE:
            if negated:
                negative_score += 0.4 * weight
                negative_words.append(f"not {token}")
            else:
                positive_score += 0.4 * weight
                positive_words.append(token)
        
        elif token in _STRONG_NEGATIVE:
            if negated:
                positive_score += 0.6 * weight
                positive_words.append(f"not {token}")
            else:
                negative_score += 0.8 * weight
                negative_words.append(token)
        
        elif token in _MODERATE_NEGATIVE:
            if negated:
                positive_score += 0.3 * weight
                positive_words.append(f"not {token}")
            else:
                negative_score += 0.4 * weight
                negative_words.append(token)
    
    # Financial context boost
    financial_hits = sum(1 for t in tokens if t in _FINANCIAL_CONTEXT)
    context_boost = 1.0 + min(0.3, financial_hits * 0.05)
    
    positive_score *= context_boost
    negative_score *= context_boost
    
    # Compute final score
    total = positive_score + negative_score
    if total == 0:
        score = 0.0
        confidence = 0.3
    else:
        score = (positive_score - negative_score) / total
        confidence = min(1.0, total / (len(tokens) * 0.1))
    
    # Classify
    if score > 0.5:
        sentiment = Sentiment.VERY_BULLISH
    elif score > 0.15:
        sentiment = Sentiment.BULLISH
    elif score < -0.5:
        sentiment = Sentiment.VERY_BEARISH
    elif score < -0.15:
        sentiment = Sentiment.BEARISH
    else:
        sentiment = Sentiment.NEUTRAL
    
    return SentimentResult(
        text=text,
        sentiment=sentiment,
        score=round(score, 3),
        confidence=round(confidence, 3),
        positive_words=list(set(positive_words))[:10],
        negative_words=list(set(negative_words))[:10],
    )


# ---------------------------------------------------------------------------
# News sentiment
# ---------------------------------------------------------------------------

def analyze_news(
    headline: str,
    body: str = "",
    source: str = "",
    tickers: Optional[List[str]] = None,
) -> NewsSentiment:
    """
    Analyze sentiment of a news article.
    
    Combines headline and body analysis with source credibility
    and market relevance scoring.
    """
    # Score headline (weighted more)
    headline_result = score_text(headline)
    
    # Score body sentences
    sentences = re.split(r'[.!?]+', body)
    sentence_results = [score_text(s.strip()) for s in sentences if len(s.strip()) > 10]
    
    # Overall score (headline weighted 60%, body 40%)
    if sentence_results:
        body_avg = sum(r.score for r in sentence_results) / len(sentence_results)
        overall_score = headline_result.score * 0.6 + body_avg * 0.4
    else:
        overall_score = headline_result.score
    
    # Source credibility
    source_lower = source.lower()
    credibility = 0.5  # default
    for key, cred in _SOURCE_CREDIBILITY.items():
        if key in source_lower:
            credibility = cred
            break
    
    # Market relevance (based on ticker mentions and financial context)
    text = f"{headline} {body}".lower()
    financial_terms = sum(1 for t in _FINANCIAL_CONTEXT if t in text)
    ticker_mentions = len(tickers or [])
    relevance = min(1.0, (financial_terms * 0.1 + ticker_mentions * 0.2))
    
    # Urgency (breaking news indicators)
    urgency_keywords = ["breaking", "just in", "urgent", "alert", "flash"]
    urgency = min(1.0, sum(0.3 for kw in urgency_keywords if kw in text))
    
    # Classify overall
    if overall_score > 0.5:
        overall_sentiment = Sentiment.VERY_BULLISH
    elif overall_score > 0.15:
        overall_sentiment = Sentiment.BULLISH
    elif overall_score < -0.5:
        overall_sentiment = Sentiment.VERY_BEARISH
    elif overall_score < -0.15:
        overall_sentiment = Sentiment.BEARISH
    else:
        overall_sentiment = Sentiment.NEUTRAL
    
    overall = SentimentResult(
        text=headline,
        sentiment=overall_sentiment,
        score=round(overall_score, 3),
        confidence=round(headline_result.confidence * credibility, 3),
        positive_words=headline_result.positive_words,
        negative_words=headline_result.negative_words,
    )
    
    return NewsSentiment(
        headline=headline,
        overall=overall,
        sentences=sentence_results,
        source_credibility=credibility,
        market_relevance=relevance,
        urgency=urgency,
        affected_tickers=tickers or [],
    )


# ---------------------------------------------------------------------------
# Earnings call sentiment
# ---------------------------------------------------------------------------

def analyze_earnings_call(
    transcript_segments: List[Dict],
    company: str = "",
    quarter: str = "",
) -> EarningsSentiment:
    """
    Analyze sentiment from earnings call transcript segments.
    
    Expects list of {speaker: str, text: str, role: str} dicts.
    Separates management commentary, guidance, and analyst questions.
    """
    guidance_texts = []
    management_texts = []
    analyst_texts = []
    
    risk_keywords = [
        "risk", "challenge", "headwind", "uncertainty", "volatile",
        "slowdown", "pressure", "concern", "investigation", "lawsuit",
    ]
    
    forward_keywords = [
        "guidance", "forecast", "outlook", "expect", "project",
        "target", "plan", "strategy", "initiative", "pipeline",
    ]
    
    risk_factors = set()
    forward_kw = set()
    
    for segment in transcript_segments:
        text = segment.get("text", "")
        role = segment.get("role", "").lower()
        
        # Categorize by role
        if "cfo" in role or "ceo" in role or "management" in role:
            management_texts.append(text)
            if "guidance" in text.lower() or "forecast" in text.lower():
                guidance_texts.append(text)
        elif "analyst" in role or "question" in role:
            analyst_texts.append(text)
        
        # Extract risk factors and forward keywords
        text_lower = text.lower()
        for kw in risk_keywords:
            if kw in text_lower:
                risk_factors.add(kw)
        for kw in forward_keywords:
            if kw in text_lower:
                forward_kw.add(kw)
    
    # Score each section
    guidance_result = score_text(" ".join(guidance_texts)) if guidance_texts else \
        SentimentResult(text="", sentiment=Sentiment.NEUTRAL, score=0, confidence=0)
    management_result = score_text(" ".join(management_texts)) if management_texts else \
        SentimentResult(text="", sentiment=Sentiment.NEUTRAL, score=0, confidence=0)
    analyst_result = score_text(" ".join(analyst_texts)) if analyst_texts else \
        SentimentResult(text="", sentiment=Sentiment.NEUTRAL, score=0, confidence=0)
    
    return EarningsSentiment(
        company=company,
        quarter=quarter,
        guidance_sentiment=guidance_result,
        management_tone=management_result,
        analyst_questions_sentiment=analyst_result,
        risk_factors_mentioned=sorted(risk_factors),
        forward_keywords=sorted(forward_kw),
    )


# ---------------------------------------------------------------------------
# Sentiment trend analysis
# ---------------------------------------------------------------------------

def analyze_trend(
    ticker: str,
    daily_scores: List[Dict],  # [{date: str, score: float, volume: int}]
    period: str = "30d",
) -> SentimentTrend:
    """
    Analyze sentiment trend for a ticker over time.
    
    Computes trend direction, strength, and volatility from
    a series of daily sentiment scores.
    """
    if not daily_scores:
        return SentimentTrend(
            ticker=ticker, period=period,
            data_points=[], trend_direction=Sentiment.NEUTRAL,
            trend_strength=0, avg_score=0, volatility=0,
        )
    
    scores = [d["score"] for d in daily_scores]
    n = len(scores)
    
    # Average score
    avg = sum(scores) / n
    
    # Volatility
    var = sum((s - avg) ** 2 for s in scores) / n
    volatility = math.sqrt(var)
    
    # Trend using linear regression
    x_mean = (n - 1) / 2
    y_mean = avg
    numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0
    
    # Trend strength (normalized slope)
    trend_strength = min(1.0, abs(slope) * 10)
    
    # Trend direction
    if slope > 0.02:
        direction = Sentiment.BULLISH
    elif slope > 0.05:
        direction = Sentiment.VERY_BULLISH
    elif slope < -0.02:
        direction = Sentiment.BEARISH
    elif slope < -0.05:
        direction = Sentiment.VERY_BEARISH
    else:
        direction = Sentiment.NEUTRAL
    
    return SentimentTrend(
        ticker=ticker,
        period=period,
        data_points=daily_scores,
        trend_direction=direction,
        trend_strength=round(trend_strength, 3),
        avg_score=round(avg, 3),
        volatility=round(volatility, 3),
    )
