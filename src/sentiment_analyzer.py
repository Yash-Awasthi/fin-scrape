"""
Financial News Sentiment Analyzer — NLP-based sentiment scoring for financial headlines.

Extracted from FinNews-Sentiment-Stock-Correlation-Analysis: performs sentiment analysis
on financial news headlines using VADER/FinBERT, quantifies sentiment scores, and
correlates with stock price movements.
"""

from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class SentimentResult:
    """Result of sentiment analysis on a piece of text."""
    text: str
    sentiment_score: float  # -1.0 (very negative) to 1.0 (very positive)
    label: str  # "positive", "negative", "neutral"
    confidence: float  # 0.0 to 1.0
    magnitude: float  # 0.0 to 1.0 (strength of sentiment)
    tokens: list = field(default_factory=list)


@dataclass
class StockSentimentCorrelation:
    """Correlation between sentiment and stock movement."""
    ticker: str
    sentiment_score: float
    price_change_pct: float
    correlation: float
    sample_size: int
    p_value: Optional[float] = None


# Financial sentiment lexicon (VADER-inspired with finance-specific terms)
POSITIVE_WORDS = {
    "surge", "rally", "gain", "profit", "bullish", "upgrade", "beat", "exceed",
    "growth", "increase", "rise", "outperform", "strong", "positive", "boom",
    "record", "high", "optimistic", "recovery", "breakthrough", "innovation",
    "dividend", "acquisition", "partnership", "expansion", "milestone",
}

NEGATIVE_WORDS = {
    "crash", "plunge", "loss", "deficit", "bearish", "downgrade", "miss",
    "decline", "decrease", "fall", "underperform", "weak", "negative", "bust",
    "low", "pessimistic", "recession", "bankruptcy", "layoff", "lawsuit",
    "fraud", "investigation", "recall", "debt", "default", "crisis",
}

INTENSIFIERS = {
    "very", "extremely", "significantly", "sharply", "dramatically", "massive",
    "huge", "substantial", "notably", "remarkably",
}

NEGATORS = {
    "not", "no", "never", "neither", "nobody", "nothing", "nowhere",
    "nor", "cannot", "can't", "don't", "won't", "isn't", "aren't",
}


def _tokenize(text: str) -> list:
    """Simple tokenization."""
    return re.findall(r'\b\w+\b', text.lower())


def _compute_sentiment(text: str) -> SentimentResult:
    """Compute sentiment using lexicon-based approach."""
    tokens = _tokenize(text)
    
    pos_count = 0
    neg_count = 0
    intensifier_count = 0
    negator_present = False
    
    for i, token in enumerate(tokens):
        if token in POSITIVE_WORDS:
            # Check for preceding negator
            if i > 0 and tokens[i - 1] in NEGATORS:
                neg_count += 1
            else:
                pos_count += 1
        elif token in NEGATIVE_WORDS:
            if i > 0 and tokens[i - 1] in NEGATORS:
                pos_count += 1
            else:
                neg_count += 1
        elif token in INTENSIFIERS:
            intensifier_count += 1
        elif token in NEGATORS:
            negator_present = True
    
    total = pos_count + neg_count
    if total == 0:
        score = 0.0
        label = "neutral"
        confidence = 0.5
    else:
        raw_score = (pos_count - neg_count) / total
        # Apply intensifier boost
        intensity_boost = min(0.3, intensifier_count * 0.1)
        score = raw_score * (1 + intensity_boost)
        score = max(-1.0, min(1.0, score))
        
        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        confidence = min(1.0, total / max(3, len(tokens)))
    
    magnitude = abs(score)
    
    return SentimentResult(
        text=text,
        sentiment_score=round(score, 4),
        label=label,
        confidence=round(confidence, 4),
        magnitude=round(magnitude, 4),
        tokens=tokens,
    )


class SentimentAnalyzer:
    """
    Financial news sentiment analyzer.
    
    Usage:
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze("Stock surges on strong earnings beat")
        print(result.sentiment_score)  # > 0
        print(result.label)  # "positive"
    """
    
    def __init__(self, custom_positive: set = None, custom_negative: set = None):
        self.positive_words = POSITIVE_WORDS | (custom_positive or set())
        self.negative_words = NEGATIVE_WORDS | (custom_negative or set())
    
    def analyze(self, text: str) -> SentimentResult:
        """Analyze sentiment of a single text."""
        return _compute_sentiment(text)
    
    def batch_analyze(self, texts: list) -> list:
        """Analyze sentiment of multiple texts."""
        return [self.analyze(text) for text in texts]
    
    def aggregate_sentiment(self, texts: list) -> dict:
        """Aggregate sentiment across multiple texts."""
        results = self.batch_analyze(texts)
        
        if not results:
            return {"average": 0.0, "positive_pct": 0.0, "negative_pct": 0.0, "neutral_pct": 0.0}
        
        scores = [r.sentiment_score for r in results]
        labels = [r.label for r in results]
        
        return {
            "average": round(sum(scores) / len(scores), 4),
            "median": round(sorted(scores)[len(scores) // 2], 4),
            "positive_pct": round(labels.count("positive") / len(labels) * 100, 1),
            "negative_pct": round(labels.count("negative") / len(labels) * 100, 1),
            "neutral_pct": round(labels.count("neutral") / len(labels) * 100, 1),
            "count": len(results),
        }
    
    def correlate_with_price(self, sentiment_scores: list, price_changes: list) -> StockSentimentCorrelation:
        """Compute correlation between sentiment and price changes."""
        n = min(len(sentiment_scores), len(price_changes))
        if n < 2:
            return StockSentimentCorrelation("", 0.0, 0.0, 0.0, n)
        
        s = sentiment_scores[:n]
        p = price_changes[:n]
        
        mean_s = sum(s) / n
        mean_p = sum(p) / n
        
        cov = sum((s[i] - mean_s) * (p[i] - mean_p) for i in range(n)) / n
        std_s = (sum((x - mean_s) ** 2 for x in s) / n) ** 0.5
        std_p = (sum((x - mean_p) ** 2 for x in p) / n) ** 0.5
        
        if std_s == 0 or std_p == 0:
            correlation = 0.0
        else:
            correlation = cov / (std_s * std_p)
        
        return StockSentimentCorrelation(
            ticker="",
            sentiment_score=round(mean_s, 4),
            price_change_pct=round(mean_p, 4),
            correlation=round(correlation, 4),
            sample_size=n,
        )
