"""
Market Sentiment Analyzer — real-time sentiment scoring from multiple sources.

Combines:
- News headline sentiment (NLP)
- Social media sentiment (Twitter/Reddit)
- Options flow sentiment
- Institutional positioning (13F filings)
- Fear & Greed Index components

Provides:
- Composite sentiment score per asset (-100 to +100)
- Sentiment momentum (accelerating/decelerating)
- Divergence detection (price vs sentiment)
- Alert generation for sentiment extremes
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
import re
import math


class SentimentSource(Enum):
    NEWS = "news"
    SOCIAL_MEDIA = "social_media"
    OPTIONS_FLOW = "options_flow"
    INSTITUTIONAL = "institutional"
    RETAIL = "retail"


class SentimentExtreme(Enum):
    EXTREME_FEAR = "extreme_fear"
    FEAR = "fear"
    NEUTRAL = "neutral"
    GREED = "greed"
    EXTREME_GREED = "extreme_greed"


@dataclass
class SentimentSignal:
    source: SentimentSource
    timestamp: datetime
    asset: str
    text: str
    score: float          # -1.0 to +1.0
    confidence: float     # 0 to 1.0
    weight: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class SentimentSnapshot:
    asset: str
    composite_score: float    # -100 to +100
    extreme: SentimentExtreme
    momentum: float           # -1 to +1 (negative = fear growing)
    signal_count: int
    sources: Dict[str, float]  # source -> score
    divergence: Optional[str]  # "bullish_divergence" / "bearish_divergence" / None
    last_updated: datetime
    historical_scores: List[tuple] = field(default_factory=list)


class MarketSentimentAnalyzer:
    """
    Multi-source market sentiment analysis engine.
    """

    # Source weights for composite score
    SOURCE_WEIGHTS = {
        SentimentSource.NEWS: 0.30,
        SentimentSource.SOCIAL_MEDIA: 0.15,
        SentimentSource.OPTIONS_FLOW: 0.25,
        SentimentSource.INSTITUTIONAL: 0.20,
        SentimentSource.RETAIL: 0.10,
    }

    # Sentiment keywords (simplified lexicon-based approach)
    POSITIVE_WORDS = {
        "surge", "rally", "breakout", "bullish", "upgrade", "beat", "exceed",
        "growth", "profit", "innovation", "partnership", "expansion", "record",
        "strong", "outperform", "buy", "accumulate", "moon", "rocket",
        "ath", "all-time high", "dividend", "recovery", "boom", "golden",
    }

    NEGATIVE_WORDS = {
        "crash", "plunge", "bearish", "downgrade", "miss", "decline", "loss",
        "layoff", "lawsuit", "fraud", "bankruptcy", "default", "sell-off",
        "panic", "bubble", "overvalued", "short", "put", "fear", "recession",
        "tariff", "sanction", "war", "crisis", "collapse", "warning",
    }

    def __init__(self):
        self.signals: Dict[str, List[SentimentSignal]] = {}  # asset -> signals
        self.price_history: Dict[str, List[float]] = {}      # asset -> prices

    def ingest_signal(self, signal: SentimentSignal):
        """Add a new sentiment signal."""
        if signal.asset not in self.signals:
            self.signals[signal.asset] = []
        self.signals[signal.asset].append(signal)

        # Keep last 7 days
        cutoff = datetime.now() - timedelta(days=7)
        self.signals[signal.asset] = [
            s for s in self.signals[signal.asset] if s.timestamp > cutoff
        ]

    def update_price(self, asset: str, price: float):
        """Record a price point for divergence detection."""
        if asset not in self.price_history:
            self.price_history[asset] = []
        self.price_history[asset].append(price)
        # Keep last 30 days (assume daily prices)
        self.price_history[asset] = self.price_history[asset][-30:]

    def get_sentiment(self, asset: str) -> SentimentSnapshot:
        """Calculate composite sentiment for an asset."""
        signals = self.signals.get(asset, [])

        if not signals:
            return SentimentSnapshot(
                asset=asset,
                composite_score=0.0,
                extreme=SentimentExtreme.NEUTRAL,
                momentum=0.0,
                signal_count=0,
                sources={},
                divergence=None,
                last_updated=datetime.now(),
            )

        # Group by source and calculate weighted scores
        source_scores: Dict[SentimentSource, List[float]] = {}
        for signal in signals:
            if signal.source not in source_scores:
                source_scores[signal.source] = []
            source_scores[signal.source].append(signal.score * signal.confidence)

        source_avg = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for source, scores in source_scores.items():
            avg = sum(scores) / len(scores)
            source_avg[source.value] = round(avg * 100, 1)
            weight = self.SOURCE_WEIGHTS.get(source, 0.1)
            weighted_sum += avg * weight
            total_weight += weight

        composite = (weighted_sum / total_weight * 100) if total_weight > 0 else 0.0

        # Determine extreme
        if composite <= -60:
            extreme = SentimentExtreme.EXTREME_FEAR
        elif composite <= -20:
            extreme = SentimentExtreme.FEAR
        elif composite <= 20:
            extreme = SentimentExtreme.NEUTRAL
        elif composite <= 60:
            extreme = SentimentExtreme.GREED
        else:
            extreme = SentimentExtreme.EXTREME_GREED

        # Calculate momentum (compare recent vs older signals)
        momentum = self._calculate_momentum(signals)

        # Check divergence
        divergence = self._check_divergence(asset, composite)

        return SentimentSnapshot(
            asset=asset,
            composite_score=round(composite, 1),
            extreme=extreme,
            momentum=momentum,
            signal_count=len(signals),
            sources=source_avg,
            divergence=divergence,
            last_updated=datetime.now(),
            historical_scores=[(s.timestamp, s.score) for s in signals[-20:]],
        )

    def get_composite_market_sentiment(self) -> Dict[str, float]:
        """Get sentiment scores for all tracked assets."""
        return {
            asset: self.get_sentiment(asset).composite_score
            for asset in self.signals
        }

    def get_extreme_sentiments(self) -> List[SentimentSnapshot]:
        """Get assets with extreme sentiment readings."""
        extremes = []
        for asset in self.signals:
            snapshot = self.get_sentiment(asset)
            if snapshot.extreme in (SentimentExtreme.EXTREME_FEAR, SentimentExtreme.EXTREME_GREED):
                extremes.append(snapshot)
        return sorted(extremes, key=lambda s: abs(s.composite_score), reverse=True)

    def get_divergences(self) -> List[Dict]:
        """Find all assets with price-sentiment divergence."""
        divergences = []
        for asset in self.signals:
            snapshot = self.get_sentiment(asset)
            if snapshot.divergence:
                divergences.append({
                    "asset": asset,
                    "type": snapshot.divergence,
                    "sentiment_score": snapshot.composite_score,
                    "signal_count": snapshot.signal_count,
                })
        return divergences

    def analyze_text(self, text: str) -> float:
        """Simple lexicon-based sentiment scoring of text."""
        words = set(text.lower().split())
        pos_count = len(words & self.POSITIVE_WORDS)
        neg_count = len(words & self.NEGATIVE_WORDS)

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _calculate_momentum(self, signals: List[SentimentSignal]) -> float:
        """Calculate sentiment momentum (-1 to +1)."""
        if len(signals) < 4:
            return 0.0

        now = datetime.now()
        recent_cutoff = now - timedelta(hours=12)
        older_cutoff = now - timedelta(hours=48)

        recent = [s.score for s in signals if s.timestamp > recent_cutoff]
        older = [s.score for s in signals if older_cutoff < s.timestamp <= recent_cutoff]

        if not recent or not older:
            return 0.0

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        diff = recent_avg - older_avg
        return max(-1.0, min(1.0, diff))

    def _check_divergence(self, asset: str, sentiment_score: float) -> Optional[str]:
        """Check for price-sentiment divergence."""
        prices = self.price_history.get(asset, [])
        if len(prices) < 5:
            return None

        # Simple price trend
        recent_prices = prices[-5:]
        price_change = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]

        # Bullish divergence: price falling but sentiment rising
        if price_change < -0.02 and sentiment_score > 20:
            return "bullish_divergence"

        # Bearish divergence: price rising but sentiment falling
        if price_change > 0.02 and sentiment_score < -20:
            return "bearish_divergence"

        return None
