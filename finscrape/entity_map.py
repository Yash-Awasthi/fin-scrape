"""Sector/geopolitics keyword → ticker resolution (Phase 12).

The gap this fills: a geopolitics headline ("Iran closes the Strait of Hormuz") resolves
role-tagged affected_entities but the LLM often leaves the per-entity `ticker` blank
(it emits sector *names*, not symbols), so `_analyze_article` drops the event at the
"No valid tickers found" gate. This module maps the sector/region words that ARE in the
text to liquid ticker proxies, so the event keeps tickers and survives the gate.

Two consumers:
  - `resolve_tickers(text)` — forward map, added to the pipeline's ticker fusion.
  - `keywords_for_ticker(symbol)` — reverse map, powers
    `server.correlate.find_news_for_market_symbol` → `explained_market_move`.

Pure + data-driven (finscrape/data/entity_index.json); no network, no DB. Matching is
case-insensitive: single alnum tokens match on word boundaries, multi-word phrases as
substrings.
"""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path

_DATA_FILE = Path(__file__).with_name("data") / "entity_index.json"


@functools.lru_cache(maxsize=1)
def _forward() -> dict[str, tuple[str, ...]]:
    """keyword(lowercased) → tuple of uppercase tickers. Ignores `_`-prefixed meta keys."""
    raw = json.loads(_DATA_FILE.read_text())
    out: dict[str, tuple[str, ...]] = {}
    for keyword, tickers in raw.items():
        if keyword.startswith("_") or not isinstance(tickers, list):
            continue
        syms = tuple(sorted({str(t).upper() for t in tickers if str(t).strip()}))
        if syms:
            out[keyword.lower()] = syms
    return out


@functools.lru_cache(maxsize=1)
def _reverse() -> dict[str, tuple[str, ...]]:
    """ticker → tuple of keywords that map to it (for find_news_for_market_symbol)."""
    rev: dict[str, set[str]] = {}
    for keyword, tickers in _forward().items():
        for t in tickers:
            rev.setdefault(t, set()).add(keyword)
    return {t: tuple(sorted(kws)) for t, kws in rev.items()}


def _matches(keyword: str, text_lower: str) -> bool:
    """Word-boundary match for single alnum tokens; substring for multi-word phrases."""
    if " " in keyword:
        return keyword in text_lower
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text_lower) is not None


def resolve_tickers(text: str) -> list[str]:
    """Tickers implied by any sector/region keyword present in `text`. Sorted, unique."""
    text_lower = (text or "").lower()
    if not text_lower:
        return []
    found: set[str] = set()
    for keyword, tickers in _forward().items():
        if _matches(keyword, text_lower):
            found.update(tickers)
    return sorted(found)


def keywords_for_ticker(symbol: str) -> list[str]:
    """Keywords/phrases associated with a ticker — the reverse of resolve_tickers."""
    return list(_reverse().get((symbol or "").upper(), ()))
