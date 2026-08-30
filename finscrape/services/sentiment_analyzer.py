"""
Sentiment Analyzer — Financial text sentiment analysis
Inspired by Stock-News-Analysis-with-BERT, FinNews-Sentiment
"""

import math
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class Sentiment(Enum):
    VERY_BEARISH = "very_bearish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    VERY_BULLISH = "very_bullish"


@dataclass
class SentimentResult:
    text: str
    sentiment: Sentiment
    score: float
    confidence: float
    positive_words: List[str]
    negative_words: List[str]
    word_count: int


@dataclass
class SentimentTrend:
    period: str
    avg_score: float
    sentiment_distribution: Dict[str, int]
    trend_direction: str
    volatility: float


class SentimentAnalyzer:
    """Pure function sentiment analysis for financial text."""

    POSITIVE_WORDS = {
        "gain", "gains", "profit", "profits", "profitable", "growth", "growing",
        "increase", "increased", "rising", "rise", "rises", "surge", "surges",
        "surging", "soar", "soars", "soaring", "rally", "rallies", "bullish",
        "outperform", "outperforms", "upgrade", "upgrades", "beat", "beats",
        "exceed", "exceeds", "exceeded", "strong", "stronger", "robust",
        "positive", "optimistic", "recovery", "recovering", "improvement",
        "improving", "record", "innovation", "breakthrough", "milestone",
        "dividend", "buyback", "expansion", "expanding", "opportunity",
        "momentum", "acceleration", "accelerating", "boom", "thriving",
    }

    NEGATIVE_WORDS = {
        "loss", "losses", "lose", "loses", "decline", "declines", "declining",
        "decrease", "decreased", "drop", "drops", "dropping", "fall", "falls",
        "falling", "crash", "crashes", "plunge", "plunges", "bearish",
        "underperform", "underperforms", "downgrade", "downgrades", "miss",
        "misses", "missed", "weak", "weaker", "weakness", "negative",
        "pessimistic", "recession", "recessionary", "crisis", "risk", "risks",
        "risky", "volatile", "volatility", "uncertainty", "uncertain",
        "concern", "concerns", "worrisome", "warning", "debt", "deficit",
        "bankruptcy", "default", "layoff", "layoffs", "restructuring",
        "downturn", "slowdown", "inflation", "deflation", "stagnation",
    }

    INTENSIFIERS = {
        "very", "extremely", "significantly", "substantially", "dramatically",
        "sharply", "massive", "huge", "massively", "tremendously",
    }

    NEGATORS = {
        "not", "no", "never", "neither", "nor", "barely", "hardly",
        "doesn't", "don't", "didn't", "wasn't", "weren't", "won't",
    }

    @classmethod
    def analyze_text(cls, text: str) -> SentimentResult:
        words = re.findall(r'\b\w+\b', text.lower())
        positive_found = []
        negative_found = []
        score = 0.0
        negate = False
        intensify = 1.0
        for word in words:
            if word in cls.NEGATORS:
                negate = True
                continue
            if word in cls.INTENSIFIERS:
                intensify = 1.5
                continue
            if word in cls.POSITIVE_WORDS:
                if negate:
                    negative_found.append(f"not_{word}")
                    score -= 0.1 * intensify
                else:
                    positive_found.append(word)
                    score += 0.1 * intensify
                negate = False
                intensify = 1.0
            elif word in cls.NEGATIVE_WORDS:
                if negate:
                    positive_found.append(f"not_{word}")
                    score += 0.05 * intensify
                else:
                    negative_found.append(word)
                    score -= 0.1 * intensify
                negate = False
                intensify = 1.0
            else:
                negate = False
                intensify = 1.0
        if score > 0.3:
            sentiment = Sentiment.VERY_BULLISH
        elif score > 0.1:
            sentiment = Sentiment.BULLISH
        elif score < -0.3:
            sentiment = Sentiment.VERY_BEARISH
        elif score < -0.1:
            sentiment = Sentiment.BEARISH
        else:
            sentiment = Sentiment.NEUTRAL
        total_sentiment_words = len(positive_found) + len(negative_found)
        confidence = min(1.0, total_sentiment_words / max(len(words) * 0.1, 1))
        return SentimentResult(
            text=text[:200],
            sentiment=sentiment,
            score=round(max(-1.0, min(1.0, score)), 3),
            confidence=round(confidence, 3),
            positive_words=positive_found,
            negative_words=negative_found,
            word_count=len(words),
        )

    @classmethod
    def analyze_headline(cls, headline: str) -> SentimentResult:
        result = cls.analyze_text(headline)
        if any(w in headline.lower() for w in ["surges", "soars", "record high"]):
            result.score = min(1.0, result.score + 0.2)
        elif any(w in headline.lower() for w in ["crashes", "plunges", "record low"]):
            result.score = max(-1.0, result.score - 0.2)
        return result

    @staticmethod
    def calculate_sentiment_trend(results: List[SentimentResult],
                                   period_label: str = "period") -> SentimentTrend:
        if not results:
            return SentimentTrend(
                period=period_label,
                avg_score=0.0,
                sentiment_distribution={},
                trend_direction="neutral",
                volatility=0.0,
            )
        scores = [r.score for r in results]
        avg_score = sum(scores) / len(scores)
        distribution = {}
        for r in results:
            s = r.sentiment.value
            distribution[s] = distribution.get(s, 0) + 1
        if len(scores) >= 2:
            first_half = scores[:len(scores) // 2]
            second_half = scores[len(scores) // 2:]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            diff = avg_second - avg_first
            if diff > 0.1:
                trend = "improving"
            elif diff < -0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        volatility = math.sqrt(variance)
        return SentimentTrend(
            period=period_label,
            avg_score=round(avg_score, 3),
            sentiment_distribution=distribution,
            trend_direction=trend,
            volatility=round(volatility, 3),
        )

    @staticmethod
    def extract_sentiment_keywords(text: str, top_n: int = 5) -> List[Tuple[str, float]]:
        words = re.findall(r'\b\w+\b', text.lower())
        word_scores = {}
        all_sentiment = SentimentAnalyzer.POSITIVE_WORDS | SentimentAnalyzer.NEGATIVE_WORDS
        for word in words:
            if word in all_sentiment:
                if word not in word_scores:
                    word_scores[word] = 0
                word_scores[word] += 1
        sorted_words = sorted(word_scores.items(), key=lambda x: -x[1])
        return sorted_words[:top_n]
