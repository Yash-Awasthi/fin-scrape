"""
Market data fetching via yfinance.
"""

from __future__ import annotations

import logging
import math
import os
import time

import yfinance as yf

logger = logging.getLogger(__name__)

# Per-process TTL cache so the worker's per-article calls (and the correlation pass)
# don't re-hit yfinance for the same ticker every time (Phase 12 / RISKS R1 hot-path).
# Keyed by ticker → (result_dict, monotonic_ts). TTL via FINSCRAPE_MARKET_TTL (seconds).
_cache: dict[str, tuple[dict, float]] = {}


def _ttl() -> float:
    try:
        return float(os.getenv("FINSCRAPE_MARKET_TTL", "600"))
    except ValueError:
        return 600.0


def clear_market_cache() -> None:
    """Drop the in-process market cache (used by tests)."""
    _cache.clear()


def _fetch(tickers: list[str]) -> dict[str, dict]:
    """One batched yfinance call for `tickers` → {ticker: result_dict}. Degrades to {}
    on any error so a slow/dead yfinance never crashes the cycle (it just skips boost)."""
    out: dict[str, dict] = {}
    try:
        df = yf.download(
            tickers=" ".join(tickers), period="2d", interval="1d", progress=False
        )
        if df is None or df.empty or "Close" not in df.columns:
            return out
        for t in tickers:
            try:
                close = df["Close"][t] if len(tickers) > 1 else df["Close"]
                if len(close) < 2:
                    continue
                price = float(close.iloc[-1])
                prev = float(close.iloc[-2])
                if math.isnan(price) or math.isnan(prev) or prev == 0:
                    continue
                change = ((price - prev) / prev) * 100
                out[t] = {
                    "ticker": t,
                    "price": round(price, 2),
                    "change_percent": round(change, 2),
                }
            except Exception:
                continue
    except Exception as e:
        logger.warning("Market data error: %s", e)
    return out


def get_market_data(tickers: list[str]) -> list[dict]:
    """Fetch 2-day % change per ticker, served from a TTL cache. Only tickers whose
    cache entry is missing/stale are fetched (in one batched call). Returns a list of
    {"ticker", "price", "change_percent"} for the tickers that resolved."""
    tickers = [t for t in tickers if isinstance(t, str) and t]
    if not tickers:
        return []

    now = time.monotonic()
    ttl = _ttl()
    fresh: dict[str, dict] = {}
    stale: list[str] = []
    for t in dict.fromkeys(tickers):  # de-dupe, preserve order
        entry = _cache.get(t)
        if entry and (now - entry[1]) < ttl:
            fresh[t] = entry[0]
        else:
            stale.append(t)

    if stale:
        fetched = _fetch(stale)
        for t, result in fetched.items():
            _cache[t] = (result, now)
            fresh[t] = result

    return [fresh[t] for t in dict.fromkeys(tickers) if t in fresh]


def calculate_market_boost(market_data: list[dict]) -> int:
    """Calculate a score boost based on recent price movement."""
    boost = 0
    for md in market_data:
        change = abs(md.get("change_percent", 0))
        if change >= 10:
            boost = max(boost, 2)
        elif change >= 5:
            boost = max(boost, 1)
    return boost
