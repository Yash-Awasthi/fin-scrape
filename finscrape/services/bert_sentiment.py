"""
Financial sentiment analysis using BERT-like scoring patterns.

Extracted from Stock-News-Analysis-with-BERT — multi-class sentiment analysis
for financial news with sector-specific scoring.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple
import re
import math


class SentimentLabel(Enum):
    VERY_BEARISH = -2
    BEARISH = -1
    NEUTRAL = 0
    BULLISH = 1
    VERY_BULLISH = 2


@dataclass
class SentimentResult:
    text: str
    label: SentimentLabel
    score: float  # -1.0 (very bearish) to 1.0 (very bullish)
    confidence: float  # 0.0 to 1.0
    tokens: List[str] = field(default_factory=list)
    entity_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class StockSentiment:
    ticker: str
    overall_sentiment: float  # -1.0 to 1.0
    confidence: float
    results: List[SentimentResult]
    sector_impact: Dict[str, float] = field(default_factory=dict)
    trend: str = "stable"  # improving, declining, stable


# Financial lexicon with sentiment scores
FINANCIAL_LEXICON = {
    # Strongly bullish
    "surge": 0.9, "soar": 0.9, "breakthrough": 0.85, "beat expectations": 0.85,
    "outperform": 0.8, "upgrade": 0.8, "buyback": 0.75, "dividend increase": 0.8,
    "record high": 0.85, "bullish": 0.8, "rally": 0.75, "boom": 0.8,
    "exceed": 0.7, "growth": 0.6, "profit": 0.5, "gain": 0.5,
    "revenue increase": 0.7, "market share": 0.4, "innovation": 0.5,

    # Moderately bullish
    "positive": 0.4, "improve": 0.4, "recovery": 0.35, "stable": 0.2,
    "hold": 0.1, "maintain": 0.1, "opportunity": 0.4, "expansion": 0.5,
    "partnership": 0.3, "launch": 0.35, "approval": 0.5, "acquisition": 0.3,

    # Strongly bearish
    "crash": -0.9, "plunge": -0.85, "bankruptcy": -0.95, "default": -0.9,
    "downgrade": -0.8, "sell": -0.6, "short": -0.5, "bearish": -0.8,
    "recession": -0.7, "crisis": -0.75, "collapse": -0.9, "fraud": -0.85,
    "investigation": -0.6, "lawsuit": -0.55, "recall": -0.6, "layoff": -0.5,

    # Moderately bearish
    "decline": -0.4, "drop": -0.35, "loss": -0.4, "miss expectations": -0.6,
    "warning": -0.4, "risk": -0.3, "concern": -0.35, "uncertainty": -0.3,
    "volatility": -0.2, "slowdown": -0.4, "weakness": -0.35, "pressure": -0.3,
}

NEGATION_WORDS = {"not", "no", "never", "neither", "nobody", "nothing",
                  "nowhere", "nor", "cannot", "can't", "won't", "don't",
                  "doesn't", "isn't", "aren't", "wasn't", "weren't",
                  "hasn't", "haven't", "hadn't", "wouldn't", "shouldn't",
                  "couldn't", "without", "barely", "hardly", "scarcely"}

INTENSIFIERS = {
    "very": 1.5, "extremely": 1.8, "significantly": 1.4, "sharply": 1.5,
    "dramatically": 1.6, "massive": 1.5, "huge": 1.4, "substantially": 1.3,
    "slightly": 0.5, "marginally": 0.4, "somewhat": 0.6, "barely": 0.3,
}

# Sector-specific sentiment modifiers
SECTOR_MODIFIERS = {
    "technology": {"ai": 0.3, "cloud": 0.2, "semiconductor": 0.15, "chip": 0.1},
    "healthcare": {"fda approval": 0.5, "trial": 0.2, "drug": 0.1, "patient": 0.1},
    "energy": {"oil": 0.1, "renewable": 0.2, "solar": 0.2, "crude": 0.1},
    "finance": {"rate": 0.2, "fed": 0.3, "inflation": -0.2, "yield": 0.1},
    "consumer": {"retail": 0.1, "brand": 0.15, "holiday": 0.2, "sales": 0.15},
}


def tokenize_financial_text(text: str) -> List[str]:
    """Tokenize financial text, preserving multi-word expressions."""
    text = text.lower().strip()
    # Handle multi-word expressions first
    tokens = []
    remaining = text
    expressions = sorted(FINANCIAL_LEXICON.keys(), key=len, reverse=True)

    for expr in expressions:
        if " " in expr and expr in remaining:
            tokens.append(expr)
            remaining = remaining.replace(expr, " ")

    # Single word tokenization
    words = re.findall(r'\b[a-z]+\b', remaining)
    tokens.extend(words)
    return tokens


def detect_negation(tokens: List[str], position: int, window: int = 3) -> bool:
    """Check if a token is negated within a window of preceding words."""
    start = max(0, position - window)
    for i in range(start, position):
        if tokens[i] in NEGATION_WORDS:
            return True
    return False


def detect_intensifier(tokens: List[str], position: int) -> float:
    """Check for intensifier words before the target token."""
    if position > 0:
        prev = tokens[position - 1]
        if prev in INTENSIFIERS:
            return INTENSIFIERS[prev]
    return 1.0


def analyze_sentiment(
    text: str,
    sector: Optional[str] = None,
) -> SentimentResult:
    """
    Analyze financial sentiment of text using lexicon-based scoring
    with negation handling and intensifier detection.

    Returns sentiment from -1.0 (very bearish) to 1.0 (very bullish).
    """
    tokens = tokenize_financial_text(text)
    total_score = 0.0
    matched_count = 0
    entity_scores = {}

    for i, token in enumerate(tokens):
        score = FINANCIAL_LEXICON.get(token)
        if score is None:
            continue

        # Apply negation
        if detect_negation(tokens, i):
            score *= -0.7  # Negation flips but dampens

        # Apply intensifier
        multiplier = detect_intensifier(tokens, i)
        score *= multiplier

        # Apply sector modifier
        if sector and sector.lower() in SECTOR_MODIFIERS:
            for keyword, modifier in SECTOR_MODIFIERS[sector.lower()].items():
                if keyword in " ".join(tokens[max(0, i-3):i+3]):
                    score += modifier * 0.3

        entity_scores[token] = score
        total_score += score
        matched_count += 1

    if matched_count == 0:
        final_score = 0.0
        confidence = 0.2
    else:
        avg_score = total_score / matched_count
        final_score = max(-1.0, min(1.0, avg_score))
        confidence = min(1.0, matched_count / max(len(tokens), 1) * 2)

    # Map to label
    if final_score > 0.5:
        label = SentimentLabel.VERY_BULLISH
    elif final_score > 0.15:
        label = SentimentLabel.BULLISH
    elif final_score > -0.15:
        label = SentimentLabel.NEUTRAL
    elif final_score > -0.5:
        label = SentimentLabel.BEARISH
    else:
        label = SentimentLabel.VERY_BEARISH

    return SentimentResult(
        text=text,
        label=label,
        score=final_score,
        confidence=confidence,
        tokens=tokens,
        entity_scores=entity_scores,
    )


def analyze_stock_sentiment(
    ticker: str,
    headlines: List[str],
    descriptions: Optional[List[str]] = None,
    sector: Optional[str] = None,
) -> StockSentiment:
    """
    Aggregate sentiment across multiple news items for a stock.
    Uses weighted averaging (headlines weighted more than descriptions).
    """
    results = []
    weighted_sum = 0.0
    total_weight = 0.0

    for headline in headlines:
        result = analyze_sentiment(headline, sector)
        weight = 2.0  # Headlines get higher weight
        weighted_sum += result.score * weight * result.confidence
        total_weight += weight * result.confidence
        results.append(result)

    if descriptions:
        for desc in descriptions:
            result = analyze_sentiment(desc, sector)
            weight = 1.0
            weighted_sum += result.score * weight * result.confidence
            total_weight += weight * result.confidence
            results.append(result)

    overall = weighted_sum / total_weight if total_weight > 0 else 0.0
    avg_confidence = (
        sum(r.confidence for r in results) / len(results) if results else 0.0
    )

    # Compute trend from recent items
    trend = "stable"
    if len(results) >= 3:
        recent = [r.score for r in results[-3:]]
        older = [r.score for r in results[:3]]
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        if recent_avg - older_avg > 0.2:
            trend = "improving"
        elif older_avg - recent_avg > 0.2:
            trend = "declining"

    # Sector impact
    sector_impact = {}
    if sector and sector.lower() in SECTOR_MODIFIERS:
        sector_impact = {
            k: v * overall for k, v in SECTOR_MODIFIERS[sector.lower()].items()
        }

    return StockSentiment(
        ticker=ticker,
        overall_sentiment=overall,
        confidence=avg_confidence,
        results=results,
        sector_impact=sector_impact,
        trend=trend,
    )


def batch_analyze(
    items: List[Dict[str, str]],
    sector: Optional[str] = None,
) -> List[StockSentiment]:
    """
    Batch analyze multiple stocks.
    items: [{"ticker": "AAPL", "headline": "...", "description": "..."}]
    """
    by_ticker = {}
    for item in items:
        ticker = item.get("ticker", "UNKNOWN")
        if ticker not in by_ticker:
            by_ticker[ticker] = {"headlines": [], "descriptions": []}
        if "headline" in item:
            by_ticker[ticker]["headlines"].append(item["headline"])
        if "description" in item:
            by_ticker[ticker]["descriptions"].append(item["description"])

    return [
        analyze_stock_sentiment(
            ticker,
            data["headlines"],
            data["descriptions"] or None,
            sector,
        )
        for ticker, data in by_ticker.items()
    ]
