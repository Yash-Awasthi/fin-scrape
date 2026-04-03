"""
signal_extractor.py — Stage 4: Signal Extraction & Market Impact Analysis

Input : EventDetectionResult  (event_detector.py — Stage 3)
Output: SignalExtractionResult

Python 3.10+
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Iterator

from event_detector import (  # type: ignore[import]
    DetectedEvent,
    EventDetectionResult,
    EventType,
)


# ── Output types ──────────────────────────────────────────────────────────────

class Sentiment(str, Enum):
    STRONGLY_POSITIVE = "STRONGLY_POSITIVE"
    POSITIVE          = "POSITIVE"
    NEUTRAL           = "NEUTRAL"
    NEGATIVE          = "NEGATIVE"
    STRONGLY_NEGATIVE = "STRONGLY_NEGATIVE"

    @property
    def is_positive(self) -> bool:
        return self in (Sentiment.POSITIVE, Sentiment.STRONGLY_POSITIVE)

    @property
    def is_negative(self) -> bool:
        return self in (Sentiment.NEGATIVE, Sentiment.STRONGLY_NEGATIVE)


class MarketCategory(str, Enum):
    CORPORATE_ACTION      = "CORPORATE_ACTION"
    FINANCIAL_PERFORMANCE = "FINANCIAL_PERFORMANCE"
    MARKET_REACTION       = "MARKET_REACTION"
    DISTRESS              = "DISTRESS"
    STRATEGIC_MOVE        = "STRATEGIC_MOVE"
    LEADERSHIP            = "LEADERSHIP"
    REGULATORY            = "REGULATORY"
    WORKFORCE             = "WORKFORCE"
    CAPITAL_MARKETS       = "CAPITAL_MARKETS"
    LEGAL                 = "LEGAL"
    UNKNOWN               = "UNKNOWN"


@dataclass(frozen=True)
class Signal:
    entity:       str
    event_type:   EventType
    category:     MarketCategory
    sentiment:    Sentiment
    impact_score: float     # logistic-squashed in (0,1); never saturates
    confidence:   float     # in [0, 1]
    trigger:      str
    sentence:     str
    is_verified:  bool      # propagated from Stage 1 entity verification chain
    timestamp:    datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )

    def __post_init__(self) -> None:
        for attr in ("impact_score", "confidence"):
            v = getattr(self, attr)
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"Signal.{attr}={v!r} outside [0, 1]")


@dataclass
class EntityDivergence:
    # divergence_score = distinct polarity buckets (positive/negative/neutral).
    # Score >= 2 means contradictory signals — flag for risk monitoring.
    entity:           str
    signals:          list[Signal]
    divergence_score: int


@dataclass
class AggregateStats:
    total_signals:         int
    positive_count:        int
    negative_count:        int
    neutral_count:         int
    avg_impact:            float
    avg_confidence:        float
    top_signals:           list[Signal]
    entities_multi_signal: dict[str, list[Signal]]
    category_distribution: dict[str, int]
    entity_divergence:     dict[str, EntityDivergence]


@dataclass
class SignalExtractionResult:
    signals: list[Signal]
    stats:   AggregateStats

    def __iter__(self) -> Iterator[Signal]:
        return iter(self.signals)

    def __len__(self) -> int:
        return len(self.signals)

    def by_entity(self, name: str) -> list[Signal]:
        lower = name.lower()
        return [s for s in self.signals if s.entity.lower() == lower]

    def by_category(self, cat: MarketCategory) -> list[Signal]:
        return [s for s in self.signals if s.category == cat]

    def verified_only(self) -> list[Signal]:
        return [s for s in self.signals if s.is_verified]


# ── Scoring constants ─────────────────────────────────────────────────────────

# Entries above _BASE_CAP (0.85) are anchored there by ImpactScorer.
# They are kept at conceptual weights for readability and recalibration.
_BASE_IMPACT: dict[EventType, float] = {
    EventType.BANKRUPTCY:         0.95,
    EventType.MERGER_ACQUISITION: 0.90,
    EventType.EARNINGS_REPORT:    0.80,
    EventType.IPO:                0.75,
    EventType.REGULATORY_ACTION:  0.70,
    EventType.LEGAL_ACTION:       0.65,
    EventType.RESTRUCTURING:      0.65,
    EventType.DEBT_ISSUANCE:      0.60,
    EventType.EXECUTIVE_CHANGE:   0.60,
    EventType.FUNDING_ROUND:      0.60,
    EventType.SHARE_BUYBACK:      0.58,
    EventType.STOCK_MOVEMENT:     0.55,
    EventType.LAYOFF:             0.50,
    EventType.ANALYST_RATING:     0.50,
    EventType.DIVIDEND:           0.45,
    EventType.CONTRACT_WIN:       0.45,
    EventType.PRODUCT_LAUNCH:     0.40,
    EventType.PARTNERSHIP:        0.30,
}

_CATEGORY_MAP: dict[EventType, MarketCategory] = {
    EventType.MERGER_ACQUISITION: MarketCategory.CORPORATE_ACTION,
    EventType.EARNINGS_REPORT:    MarketCategory.FINANCIAL_PERFORMANCE,
    EventType.BANKRUPTCY:         MarketCategory.DISTRESS,
    EventType.STOCK_MOVEMENT:     MarketCategory.MARKET_REACTION,
    EventType.ANALYST_RATING:     MarketCategory.MARKET_REACTION,
    EventType.PRODUCT_LAUNCH:     MarketCategory.STRATEGIC_MOVE,
    EventType.PARTNERSHIP:        MarketCategory.STRATEGIC_MOVE,
    EventType.CONTRACT_WIN:       MarketCategory.STRATEGIC_MOVE,
    EventType.EXECUTIVE_CHANGE:   MarketCategory.LEADERSHIP,
    EventType.REGULATORY_ACTION:  MarketCategory.REGULATORY,
    EventType.LEGAL_ACTION:       MarketCategory.LEGAL,
    EventType.LAYOFF:             MarketCategory.WORKFORCE,
    EventType.RESTRUCTURING:      MarketCategory.WORKFORCE,
    EventType.IPO:                MarketCategory.CAPITAL_MARKETS,
    EventType.FUNDING_ROUND:      MarketCategory.CAPITAL_MARKETS,
    EventType.DEBT_ISSUANCE:      MarketCategory.CAPITAL_MARKETS,
    EventType.DIVIDEND:           MarketCategory.FINANCIAL_PERFORMANCE,
    EventType.SHARE_BUYBACK:      MarketCategory.FINANCIAL_PERFORMANCE,
}

_POSITIVE_STRONG: frozenset[str] = frozenset({
    "record", "blowout", "blockbuster", "landmark", "historic",
    "unprecedented", "beat expectations", "beat estimates", "smashed",
    "crushes", "soared", "surged", "skyrocketed", "jumped", "rallied",
    "all-time high", "massive deal", "transformative", "profit jumped",
    "revenue grew", "raised guidance", "record revenue", "record profit",
})
_POSITIVE_WEAK: frozenset[str] = frozenset({
    "beat", "exceeded", "above", "growth", "gain", "rose", "up",
    "improved", "strong", "positive", "agreed to acquire", "partnership",
    "launched", "increased", "expanded", "upgraded", "raised", "gained",
    "higher", "approved", "secured", "won", "awarded",
    "upgrade", "raised target", "price target raised", "initiated buy",
    "initiated coverage with buy", "reiterated buy", "reaffirmed buy",
})
_NEGATIVE_STRONG: frozenset[str] = frozenset({
    "bankrupt", "bankruptcy", "collapse", "defaulted", "insolvent",
    "catastrophic", "plunged", "crashed", "imploded", "wiped out",
    "fraud", "scandal", "indicted", "missed estimates", "missed expectations",
    "cut guidance", "profit declined", "revenue declined",
})
_NEGATIVE_WEAK: frozenset[str] = frozenset({
    "miss", "missed", "below", "fell", "dropped", "declined", "loss",
    "cut", "layoffs", "laid off", "job cuts", "restructuring", "fine",
    "penalty", "downgraded", "lowered", "warning", "concern", "lawsuit",
    "investigation", "probe", "deficit", "shortfall", "suspended",
    "resignation", "stepped down", "antitrust", "class action",
    "downgrade", "cut target", "price target cut", "initiated sell",
    "initiated underperform", "lowered target", "rating cut",
})

_SENTIMENT_PRIOR: dict[EventType, Sentiment] = {
    EventType.MERGER_ACQUISITION: Sentiment.POSITIVE,
    EventType.EARNINGS_REPORT:    Sentiment.NEUTRAL,
    EventType.BANKRUPTCY:         Sentiment.STRONGLY_NEGATIVE,
    EventType.STOCK_MOVEMENT:     Sentiment.NEUTRAL,
    EventType.ANALYST_RATING:     Sentiment.NEUTRAL,
    EventType.PRODUCT_LAUNCH:     Sentiment.POSITIVE,
    EventType.PARTNERSHIP:        Sentiment.POSITIVE,
    EventType.EXECUTIVE_CHANGE:   Sentiment.NEUTRAL,
    EventType.REGULATORY_ACTION:  Sentiment.NEGATIVE,
    EventType.LAYOFF:             Sentiment.NEGATIVE,
    EventType.RESTRUCTURING:      Sentiment.NEGATIVE,
    EventType.IPO:                Sentiment.POSITIVE,
    EventType.FUNDING_ROUND:      Sentiment.POSITIVE,
    EventType.DIVIDEND:           Sentiment.POSITIVE,
    EventType.SHARE_BUYBACK:      Sentiment.POSITIVE,
    EventType.DEBT_ISSUANCE:      Sentiment.NEUTRAL,
    EventType.LEGAL_ACTION:       Sentiment.NEGATIVE,
    EventType.CONTRACT_WIN:       Sentiment.POSITIVE,
}

_MAGNITUDE_WORDS: frozenset[str] = frozenset({
    "record", "massive", "major", "huge", "giant", "enormous",
    "landmark", "historic", "unprecedented", "transformative",
    "biggest", "largest", "biggest ever", "largest ever",
})

# Non-linear dollar-tier log-scale deltas: million->0.10, billion->0.30, trillion->0.50
_DOLLAR_UNIT_DELTA: dict[str, float] = {
    "m": 0.10, "million": 0.10,
    "b": 0.30, "billion": 0.30,
    "t": 0.50, "trillion": 0.50,
}
_DOLLAR_VAL_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(billion|trillion|million|[Bb]|[Tt]|[Mm])?\b",
    re.IGNORECASE,
)

_NEGATION_WINDOW = 3
_NEGATION_DAMP   = 0.50

_HIGH_CONF_RE = re.compile(
    r"\b(agreed to acquire|filed for bankruptcy|reported earnings|"
    r"announced acquisition|ipo priced|declared dividend|signed agreement|"
    r"regulatory approval|court ruling|merger completed|beat estimates|"
    r"beat expectations|raised guidance|series [a-e] funding|filed for chapter)\b",
    re.IGNORECASE,
)
_LOW_CONF_RE = re.compile(
    r"\b(reportedly|sources say|rumored|may|could|might|speculated|"
    r"whisper|unconfirmed|according to sources|said to be)\b",
    re.IGNORECASE,
)

_DELTA_MAGNITUDE_PER_HIT = 0.15
_DELTA_MULTI_ENTITY      = 0.10
_DELTA_VERIFIED          = 0.08   # log-scale boost for Stage-1-verified entities
_MAX_MAGNITUDE_HITS      = 3

# Require two consecutive Title-Case tokens — excludes Monday, Federal, President.
_MULTI_ENTITY_RE = re.compile(
    r"\b([A-Z]{3,}|[A-Z][A-Za-z&\-]+\s[A-Z][A-Za-z&\-]+)\b"
)

_NOISE_BIGRAMS: frozenset[str] = frozenset({
    "United States", "Federal Reserve", "Wall Street", "New York",
    "White House", "European Union", "World Bank", "Chief Executive",
    "Chief Financial", "Vice President", "Prime Minister",
    "San Francisco", "Los Angeles", "Hong Kong",
})


# ── Internal helpers ──────────────────────────────────────────────────────────

def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _logistic(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _build_lexicon_pattern(lexicon: frozenset[str]) -> re.Pattern[str]:
    # Longest-first so multi-word phrases shadow their single-word substrings.
    alts = "|".join(re.escape(t) for t in sorted(lexicon, key=len, reverse=True))
    return re.compile(rf"\b(?:{alts})\b", re.IGNORECASE)


# Pre-compiled once at module load — single-pass O(M) scan per call
# instead of O(N) separate re.compile + findall calls per lexicon.
_RE_POS_STRONG = _build_lexicon_pattern(_POSITIVE_STRONG)
_RE_POS_WEAK   = _build_lexicon_pattern(_POSITIVE_WEAK)
_RE_NEG_STRONG = _build_lexicon_pattern(_NEGATIVE_STRONG)
_RE_NEG_WEAK   = _build_lexicon_pattern(_NEGATIVE_WEAK)
_RE_MAGNITUDE  = _build_lexicon_pattern(_MAGNITUDE_WORDS)


def _count_occurrences(text: str, pattern: re.Pattern[str]) -> int:
    return len(pattern.findall(text))


def _negation_dampened_score(
    tokens: list[str],
    raw_hits: int,
    positive_lexicon: frozenset[str],
    negative_lexicon: frozenset[str],
) -> float:
    if raw_hits == 0:
        return 0.0
    effective = 0.0
    for pos_term in positive_lexicon:
        pt     = pos_term.split()       # split once per term
        pt_len = len(pt)
        for i in range(len(tokens) - pt_len + 1):
            if tokens[i : i + pt_len] == pt:
                ws     = max(0, i - _NEGATION_WINDOW)
                we     = min(len(tokens), i + pt_len + _NEGATION_WINDOW)
                window = " ".join(tokens[ws:we])
                effective += _NEGATION_DAMP if any(neg in window for neg in negative_lexicon) else 1.0
    return min(effective, float(raw_hits))


# ── Scoring classes ───────────────────────────────────────────────────────────

class SentimentScorer:
    """
    5-tier polarity via weighted occurrence counts with negation dampening.

    raw = (2*SP_eff + WP_eff) - (2*SN + WN)
    raw >= 3  -> STRONGLY_POSITIVE   raw > 0 -> POSITIVE
    raw <= -3 -> STRONGLY_NEGATIVE   raw < 0 -> NEGATIVE
    raw == 0  -> structural prior (_SENTIMENT_PRIOR)
    """

    def score(self, event: DetectedEvent) -> Sentiment:
        corpus = f"{event.trigger} {event.sentence}".lower()
        tokens = re.findall(r"[a-zA-Z]+", corpus)

        sp_raw = _count_occurrences(corpus, _RE_POS_STRONG)
        wp_raw = _count_occurrences(corpus, _RE_POS_WEAK)
        sn     = _count_occurrences(corpus, _RE_NEG_STRONG)
        wn     = _count_occurrences(corpus, _RE_NEG_WEAK)

        sp_eff = _negation_dampened_score(tokens, sp_raw, _POSITIVE_STRONG, _NEGATIVE_STRONG)
        wp_eff = _negation_dampened_score(tokens, wp_raw, _POSITIVE_WEAK,   _NEGATIVE_STRONG)

        raw = (2 * sp_eff + wp_eff) - (2 * sn + wn)

        if raw >= 3:  return Sentiment.STRONGLY_POSITIVE
        if raw > 0:   return Sentiment.POSITIVE
        if raw <= -3: return Sentiment.STRONGLY_NEGATIVE
        if raw < 0:   return Sentiment.NEGATIVE
        return _SENTIMENT_PRIOR.get(event.event_type, Sentiment.NEUTRAL)


class ImpactScorer:
    """
    Logistic-squashed impact score in (0, 1).

    log_score  = log(base) + Σ modifiers
    impact     = sigmoid(log_score + logit(base))

    logit(base) anchors sigmoid so an unmodified event maps to exactly its
    base value. Modifiers (magnitude, dollar tier, multi-entity, verified)
    push smoothly above/below without saturation.
    """

    _BASE_CAP = 0.85  # logit diverges as base->1; cap preserves headroom for modifiers

    def score(self, event: DetectedEvent) -> float:
        base = min(_BASE_IMPACT.get(event.event_type, 0.10), self._BASE_CAP)
        if base <= 0:
            return 0.0

        corpus    = f"{event.trigger} {event.sentence}".lower()
        log_score = math.log(base)
        log_score += min(_count_occurrences(corpus, _RE_MAGNITUDE), _MAX_MAGNITUDE_HITS) * _DELTA_MAGNITUDE_PER_HIT
        log_score += self._best_dollar_delta(event.sentence)
        if self._has_second_entity(event):
            log_score += _DELTA_MULTI_ENTITY
        if getattr(event, "is_verified", False):
            log_score += _DELTA_VERIFIED

        logit_base = math.log(base / (1.0 - base))
        return round(_logistic(log_score + logit_base), 4)

    @staticmethod
    def _best_dollar_delta(sentence: str) -> float:
        best = 0.0
        for m in _DOLLAR_VAL_RE.finditer(sentence):
            unit = (m.group(2) or "").lower()
            delta = _DOLLAR_UNIT_DELTA.get(unit, 0.0)
            if delta > best:
                best = delta
        return best

    @staticmethod
    def _has_second_entity(event: DetectedEvent) -> bool:
        primary = event.entity.lower()
        for m in _MULTI_ENTITY_RE.finditer(event.sentence):
            bigram = m.group(0)
            if bigram.lower() != primary and bigram not in _NOISE_BIGRAMS:
                return True
        return False


class ConfidenceScorer:
    """
    base=0.50 + trigger_quality  in {+0.25, 0, -0.20}
             + sentence_length   in {+0.10, 0, -0.10}
             + verified_bonus      +0.15  if is_verified
             - 0.05 * hedge_count

    High-conf patterns are searched over the full sentence because declarative
    evidence may appear anywhere in the sentence body, not just the trigger.
    """

    _BASE             = 0.50
    _HIGH_TRIG_BONUS  = 0.25
    _LOW_TRIG_PENALTY = 0.20
    _LEN_MAX_BONUS    = 0.10
    _LEN_SHORT_PEN    = 0.10
    _VERIFIED_BONUS   = 0.15
    _HEDGE_PEN_EACH   = 0.05

    def score(self, event: DetectedEvent) -> float:
        conf = self._BASE

        if _HIGH_CONF_RE.search(event.sentence.lower()):
            conf += self._HIGH_TRIG_BONUS
        elif _LOW_CONF_RE.search(event.trigger.lower()):
            conf -= self._LOW_TRIG_PENALTY

        token_count = len(event.sentence.split())
        if token_count >= 15:
            conf += self._LEN_MAX_BONUS
        elif token_count < 5:
            conf -= self._LEN_SHORT_PEN

        if getattr(event, "is_verified", False):
            conf += self._VERIFIED_BONUS

        conf -= len(_LOW_CONF_RE.findall(event.sentence)) * self._HEDGE_PEN_EACH
        return _clamp(conf)


# ── Main processor ────────────────────────────────────────────────────────────

class SignalExtractor:
    """Stateless after construction; safe to share across threads."""

    def __init__(self) -> None:
        self._sentiment  = SentimentScorer()
        self._impact     = ImpactScorer()
        self._confidence = ConfidenceScorer()

    def extract(self, detection_result: EventDetectionResult) -> SignalExtractionResult:
        signals = [self._process(ev) for ev in detection_result.events]
        return SignalExtractionResult(signals=signals, stats=self._stats(signals))

    def _process(self, event: DetectedEvent) -> Signal:
        return Signal(
            entity       = event.entity,
            event_type   = event.event_type,
            category     = _CATEGORY_MAP.get(event.event_type, MarketCategory.UNKNOWN),
            sentiment    = self._sentiment.score(event),
            impact_score = self._impact.score(event),
            confidence   = self._confidence.score(event),
            trigger      = event.trigger,
            sentence     = event.sentence,
            is_verified  = getattr(event, "is_verified", False),
        )

    @staticmethod
    def _divergence(entity: str, sigs: list[Signal]) -> EntityDivergence:
        buckets: set[str] = set()
        for s in sigs:
            buckets.add(
                "positive" if s.sentiment.is_positive else
                "negative" if s.sentiment.is_negative else
                "neutral"
            )
        return EntityDivergence(entity=entity, signals=sigs, divergence_score=len(buckets))

    @staticmethod
    def _stats(signals: list[Signal]) -> AggregateStats:
        if not signals:
            return AggregateStats(
                total_signals=0, positive_count=0, negative_count=0,
                neutral_count=0, avg_impact=0.0, avg_confidence=0.0,
                top_signals=[], entities_multi_signal={},
                category_distribution={}, entity_divergence={},
            )

        pos = sum(1 for s in signals if s.sentiment.is_positive)
        neg = sum(1 for s in signals if s.sentiment.is_negative)

        entity_map: dict[str, list[Signal]] = {}
        for sig in signals:
            entity_map.setdefault(sig.entity, []).append(sig)

        cat_dist: dict[str, int] = {}
        for sig in signals:
            cat_dist[sig.category.value] = cat_dist.get(sig.category.value, 0) + 1

        return AggregateStats(
            total_signals=len(signals),
            positive_count=pos,
            negative_count=neg,
            neutral_count=len(signals) - pos - neg,
            avg_impact=round(sum(s.impact_score for s in signals) / len(signals), 4),
            avg_confidence=round(sum(s.confidence for s in signals) / len(signals), 4),
            top_signals=sorted(signals, key=lambda s: s.impact_score, reverse=True)[:5],
            entities_multi_signal={e: v for e, v in entity_map.items() if len(v) > 1},
            category_distribution=cat_dist,
            entity_divergence={
                e: SignalExtractor._divergence(e, v)
                for e, v in entity_map.items() if len(v) > 1
            },
        )


def extract_signals(detection_result: EventDetectionResult) -> SignalExtractionResult:
    return SignalExtractor().extract(detection_result)