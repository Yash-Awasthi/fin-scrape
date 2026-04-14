"""
Heuristic validation layer.

Provides keyword-based sentiment scoring as a sanity check
against AI model output.
"""

from __future__ import annotations

import math
import re

from finscrape.analysis.constants import (
    POSITIVE_STRONG, POSITIVE_WEAK,
    NEGATIVE_STRONG, NEGATIVE_WEAK,
    MAGNITUDE_WORDS, EVENT_BASE_IMPACT,
    TICKER_STOPWORDS,
)


def calculate_heuristic_score(text: str, event_type: str) -> tuple[str, float]:
    """
    Calculate a heuristic sentiment and impact score from text.

    Returns: (sentiment_label, impact_score)
        sentiment_label: "positive", "negative", or "neutral"
        impact_score: float in [0, 1]
    """
    text_lower = text.lower()

    sp = sum(1 for w in POSITIVE_STRONG if w in text_lower)
    wp = sum(1 for w in POSITIVE_WEAK if w in text_lower)
    sn = sum(1 for w in NEGATIVE_STRONG if w in text_lower)
    wn = sum(1 for w in NEGATIVE_WEAK if w in text_lower)

    raw_sentiment = (2 * sp + wp) - (2 * sn + wn)

    if raw_sentiment >= 2:
        sentiment = "positive"
    elif raw_sentiment <= -2:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    # Impact calculation (logistic weighting)
    base_impact = EVENT_BASE_IMPACT.get(event_type, 0.3)
    mag_boost = sum(1 for w in MAGNITUDE_WORDS if w in text_lower) * 0.1

    dollar_boost = 0.0
    if re.search(r'\$\d+\s*(?:billion|b|bn)', text_lower):
        dollar_boost = 0.3
    elif re.search(r'\$\d+\s*(?:million|m|mn)', text_lower):
        dollar_boost = 0.1

    logit_base = math.log(base_impact / (1.0 - base_impact + 1e-9))
    total_log = math.log(base_impact) + mag_boost + dollar_boost
    heuristic_impact = 1.0 / (1.0 + math.exp(-(total_log + logit_base)))

    return sentiment, round(heuristic_impact, 2)


def check_divergence(ai_sentiment: str, heuristic_sentiment: str) -> bool:
    """Flag if AI and heuristics disagree on polarity."""
    if ai_sentiment == "neutral" or heuristic_sentiment == "neutral":
        return False
    return ai_sentiment != heuristic_sentiment


def clean_tickers(tickers: list[str]) -> list[str]:
    """Remove noise tickers using the stopword list."""
    return [t for t in tickers if t.upper() not in TICKER_STOPWORDS]
