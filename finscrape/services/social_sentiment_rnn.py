"""
Social Media Sentiment Analysis for fin-scrape
Extracted from: stocktwits-sentiment (Keras LSTM sentiment prediction)
Patterns: Text preprocessing, tokenization, LSTM model architecture,
          bullish/bearish classification, batch prediction
"""
import re
import string
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Sentiment(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass
class SentimentPrediction:
    text: str
    sentiment: Sentiment
    confidence: float  # 0-1
    raw_score: float  # -1 to 1
    source: str = ""
    timestamp: Optional[int] = None
    ticker: str = ""


@dataclass
class SentimentAggregate:
    ticker: str
    total_messages: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    bullish_ratio: float
    bearish_ratio: float
    avg_confidence: float
    sentiment_score: float  # -1 to 1
    trend: str = "stable"  # "improving", "deteriorating", "stable"


# ─── Text Preprocessing ────────────────────────────────────────────────

def preprocess_text(text: str) -> str:
    """Clean and standardize social media text for analysis."""
    text = text.lower()
    text = re.sub(r'\$[a-zA-Z0-9]+\s*', '', text)  # Remove ticker symbols
    text = text.translate(str.maketrans('', '', string.punctuation))
    text = re.sub(r'[\W_]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_tickers(text: str) -> list[str]:
    """Extract stock ticker symbols from text."""
    return re.findall(r'\$([A-Z]{1,5})\b', text.upper())


def extract_hashtags(text: str) -> list[str]:
    """Extract hashtags from social media text."""
    return re.findall(r'#(\w+)', text)


def extract_mentions(text: str) -> list[str]:
    """Extract @mentions from social media text."""
    return re.findall(r'@(\w+)', text)


# ─── Rule-Based Sentiment (No ML dependency) ───────────────────────────

BULLISH_WORDS = {
    "buy", "long", "bullish", "moon", "rocket", "calls", "up", "rising",
    "growth", "profit", "gain", "breakout", "recovery", "undervalued",
    "strong", "beat", "outperform", "upgrade", "buyback", "dividend",
    "expansion", "innovation", "partnership", "record", "surge",
}

BEARISH_WORDS = {
    "sell", "short", "bearish", "crash", "puts", "down", "falling",
    "loss", "decline", "overvalued", "weak", "miss", "underperform",
    "downgrade", "bankruptcy", "debt", "lawsuit", "investigation",
    "fraud", "bubble", "dump", "collapse", "recession", "default",
}


def rule_based_sentiment(text: str) -> SentimentPrediction:
    """Simple rule-based sentiment analysis."""
    cleaned = preprocess_text(text)
    words = set(cleaned.split())

    bullish_hits = len(words & BULLISH_WORDS)
    bearish_hits = len(words & BEARISH_WORDS)

    if bullish_hits > bearish_hits:
        score = min(1.0, 0.5 + (bullish_hits - bearish_hits) * 0.2)
        return SentimentPrediction(
            text=text,
            sentiment=Sentiment.BULLISH,
            confidence=min(0.9, 0.4 + bullish_hits * 0.1),
            raw_score=score,
        )
    elif bearish_hits > bullish_hits:
        score = max(-1.0, -0.5 - (bearish_hits - bullish_hits) * 0.2)
        return SentimentPrediction(
            text=text,
            sentiment=Sentiment.BEARISH,
            confidence=min(0.9, 0.4 + bearish_hits * 0.1),
            raw_score=score,
        )
    else:
        return SentimentPrediction(
            text=text,
            sentiment=Sentiment.NEUTRAL,
            confidence=0.3,
            raw_score=0.0,
        )


# ─── LSTM Model Architecture (reference for ML integration) ────────────

def build_lstm_model(vocabulary_size: int, max_words: int = 100, embedding_size: int = 32):
    """
    Build an LSTM model for sentiment classification.
    Reference architecture from stocktwits-sentiment.
    
    Model:
      Embedding → LSTM(200) → Dense(1, tanh)
    
    In production, this would be used with:
      - Tokenizer fitted on training data
      - pad_sequences for input normalization
      - Binary crossentropy loss
      - Adam optimizer
    """
    return {
        "architecture": "Sequential",
        "layers": [
            {"type": "Embedding", "input_dim": vocabulary_size, "output_dim": embedding_size, "input_length": max_words},
            {"type": "LSTM", "units": 200},
            {"type": "Dense", "units": 1, "activation": "tanh"},
        ],
        "loss": "binary_crossentropy",
        "optimizer": "adam",
        "metrics": ["accuracy"],
    }


# ─── Batch Analysis ────────────────────────────────────────────────────

def batch_analyze(messages: list[dict], source: str = "social") -> list[SentimentPrediction]:
    """Analyze a batch of social media messages."""
    predictions = []
    for msg in messages:
        text = msg.get("body", msg.get("text", ""))
        tickers = extract_tickers(text)

        prediction = rule_based_sentiment(text)
        prediction.source = source
        prediction.timestamp = msg.get("timestamp")
        prediction.ticker = tickers[0] if tickers else ""
        predictions.append(prediction)

    return predictions


def aggregate_by_ticker(predictions: list[SentimentPrediction]) -> dict[str, SentimentAggregate]:
    """Aggregate predictions by ticker symbol."""
    ticker_groups: dict[str, list[SentimentPrediction]] = {}
    for p in predictions:
        if p.ticker:
            ticker_groups.setdefault(p.ticker, []).append(p)

    results = {}
    for ticker, preds in ticker_groups.items():
        bullish = sum(1 for p in preds if p.sentiment == Sentiment.BULLISH)
        bearish = sum(1 for p in preds if p.sentiment == Sentiment.BEARISH)
        neutral = sum(1 for p in preds if p.sentiment == Sentiment.NEUTRAL)
        total = len(preds)
        avg_conf = sum(p.confidence for p in preds) / total if total else 0
        avg_score = sum(p.raw_score for p in preds) / total if total else 0

        results[ticker] = SentimentAggregate(
            ticker=ticker,
            total_messages=total,
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            bullish_ratio=bullish / total if total else 0,
            bearish_ratio=bearish / total if total else 0,
            avg_confidence=round(avg_conf, 3),
            sentiment_score=round(avg_score, 3),
            trend="improving" if avg_score > 0.2 else "deteriorating" if avg_score < -0.2 else "stable",
        )

    return results
