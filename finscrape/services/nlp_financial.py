"""
NLP Financial Text Analysis — Industrial-strength NLP for financial text.

Inspired by spaCy.
Provides tokenization, named entity recognition, sentiment analysis,
and text classification for financial documents.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Token:
    """Represents a tokenized word."""
    text: str
    lemma: str
    pos: str  # part of speech
    isStop: bool
    isAlpha: bool
    isNumeric: bool
    index: int


@dataclass
class Entity:
    """Represents a named entity."""
    text: str
    label: str  # ORG, PERSON, MONEY, DATE, etc.
    start: int
    end: int
    confidence: float


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    text: str
    polarity: float  # -1.0 to 1.0
    subjectivity: float  # 0.0 to 1.0
    label: str  # positive, negative, neutral


@dataclass
class ClassificationResult:
    """Text classification result."""
    text: str
    label: str
    confidence: float
    probabilities: Dict[str, float]


# ============================================================================
# Financial NLP Pipeline
# ============================================================================

class FinancialNLPPipeline:
    """NLP pipeline for financial text analysis."""

    # Financial entity patterns
    ENTITY_PATTERNS = {
        "MONEY": r'\$[\d,]+\.?\d*|€[\d,]+\.?\d*|£[\d,]+\.?\d*|¥[\d,]+\.?\d*',
        "PERCENT": r'\d+\.?\d*%|\d+\.?\d* percent',
        "TICKER": r'\b[A-Z]{1,5}\b',
        "DATE": r'\b\d{1,2}/\d{1,2}/\d{2,4}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b',
    }

    # Financial sentiment lexicon
    POSITIVE_WORDS = {
        "profit", "gain", "increase", "growth", "bullish", "outperform",
        "upgrade", "beat", "exceed", "surge", "rally", "boom", "recovery",
        "strong", "positive", "optimistic", "buy", "accumulate",
    }

    NEGATIVE_WORDS = {
        "loss", "decrease", "decline", "bearish", "underperform", "downgrade",
        "miss", "miss", "slump", "crash", "recession", "weak", "negative",
        "pessimistic", "sell", "dump", "bankruptcy", "default", "risk",
    }

    def __init__(self):
        self.stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "could",
            "should", "may", "might", "can", "shall", "to", "of", "in", "for",
            "on", "with", "at", "by", "from", "as", "into", "through", "during",
            "before", "after", "above", "below", "between", "out", "off", "over",
            "under", "again", "further", "then", "once", "here", "there", "when",
            "where", "why", "how", "all", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own", "same",
            "so", "than", "too", "very", "just", "don", "now",
        }

    def tokenize(self, text: str) -> List[Token]:
        """Tokenize text into tokens."""
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        tokens = []
        for i, word in enumerate(words):
            tokens.append(Token(
                text=word,
                lemma=word.lower(),
                pos=self._guess_pos(word),
                isStop=word.lower() in self.stop_words,
                isAlpha=word.isalpha(),
                isNumeric=word.replace('.', '').replace(',', '').isdigit(),
                index=i,
            ))
        return tokens

    def _guess_pos(self, word: str) -> str:
        """Simple POS tagger (in production, use a trained model)."""
        if word.endswith(('ing', 'ed', 'ly')):
            return 'VERB'
        elif word.endswith(('tion', 'ment', 'ness', 'ity')):
            return 'NOUN'
        elif word.endswith(('ous', 'ive', 'able', 'ible')):
            return 'ADJ'
        elif word.lower() in self.stop_words:
            return 'DET'
        else:
            return 'NOUN'

    def extract_entities(self, text: str) -> List[Entity]:
        """Extract named entities from text."""
        entities = []

        for label, pattern in self.ENTITY_PATTERNS.items():
            for match in re.finditer(pattern, text):
                entities.append(Entity(
                    text=match.group(),
                    label=label,
                    start=match.start(),
                    end=match.end(),
                    confidence=0.85,
                ))

        return entities

    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of financial text."""
        words = set(text.lower().split())
        positive_count = len(words & self.POSITIVE_WORDS)
        negative_count = len(words & self.NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            polarity = 0.0
            label = "neutral"
        else:
            polarity = (positive_count - negative_count) / total
            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"

        return SentimentResult(
            text=text,
            polarity=polarity,
            subjectivity=min(total / 10, 1.0),
            label=label,
        )

    def classify_text(self, text: str) -> ClassificationResult:
        """Classify text into financial categories."""
        words = set(text.lower().split())

        categories = {
            "earnings": {"revenue", "earnings", "profit", "loss", "quarterly", "annual"},
            "merger": {"merger", "acquisition", "buyout", "takeover", "deal"},
            "regulation": {"regulation", "compliance", "sec", "filing", "disclosure"},
            "market": {"market", "stock", "trading", "volume", "price"},
            "economic": {"gdp", "inflation", "interest", "rate", "economic"},
        }

        scores = {}
        for category, keywords in categories.items():
            scores[category] = len(words & keywords)

        best_category = max(scores, key=scores.get)
        confidence = scores[best_category] / max(len(keywords), 1)

        return ClassificationResult(
            text=text[:100],
            label=best_category,
            confidence=min(confidence, 1.0),
            probabilities=scores,
        )

    def extract_key_phrases(self, text: str, top_k: int = 5) -> List[str]:
        """Extract key phrases from text."""
        # Simple TF-based extraction
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        for word in words:
            if word not in self.stop_words and len(word) > 2:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top phrases (bigrams)
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in self.stop_words and words[i + 1] not in self.stop_words:
                bigrams.append(f"{words[i]} {words[i + 1]}")

        bigram_freq = {}
        for bigram in bigrams:
            bigram_freq[bigram] = bigram_freq.get(bigram, 0) + 1

        # Combine unigrams and bigrams
        all_phrases = {}
        all_phrases.update(word_freq)
        all_phrases.update(bigram_freq)

        sorted_phrases = sorted(all_phrases.items(), key=lambda x: x[1], reverse=True)
        return [phrase for phrase, _ in sorted_phrases[:top_k]]
