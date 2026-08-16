"""
Market data fetching via yfinance.
"""

from __future__ import annotations

import logging
import math
import os
import time

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

# Per-process TTL cache so the worker's per-article calls (and the correlation pass)
# don't re-hit yfinance for the same ticker every time (Phase 12 / RISKS R1 hot-path).
# Keyed by ticker → (result_dict, monotonic_ts). TTL via FINSCRAPE_MARKET_TTL (seconds).
_cache: dict[str, tuple[dict, float]] = {}

# Separate TTL cache for indicator facts (1y history per ticker, pricier fetch
# than the 2-day quote above) — same ticker → (result_dict, monotonic_ts) shape.
_indicator_cache: dict[str, tuple[dict, float]] = {}


def _ttl() -> float:
    try:
        return float(os.getenv("FINSCRAPE_MARKET_TTL", "600"))
    except ValueError:
        return 600.0


def clear_market_cache() -> None:
    """Drop the in-process market cache (used by tests)."""
    _cache.clear()


def clear_indicator_cache() -> None:
    """Drop the in-process indicator cache (used by tests)."""
    _indicator_cache.clear()


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


MIN_INDICATOR_BARS = 50  # sma50 is the binding constraint


def _rsi14(closes: list[float], period: int = 14) -> float:
    """Standard RSI over the last `period` closes. All-gains -> 100.0,
    no-change (flat) series -> 50.0 (neutral, not undefined)."""
    deltas = [closes[i] - closes[i - 1] for i in range(len(closes) - period, len(closes))]
    avg_gain = sum(d for d in deltas if d > 0) / period
    avg_loss = sum(-d for d in deltas if d < 0) / period
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


def _atr_pct(closes: list[float], highs: list[float], lows: list[float], period: int = 14) -> float:
    """Average True Range over the last `period` bars, as a % of the latest close."""
    trs = []
    for i in range(len(closes) - period, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    atr = sum(trs) / period
    return round(atr / closes[-1] * 100, 2) if closes[-1] else 0.0


def compute_indicators(closes: list[float], highs: list[float], lows: list[float]) -> dict:
    """Pure technical indicators over plain price lists — no TA-Lib, no pandas here,
    so this is testable offline with synthetic data.

    Needs at least MIN_INDICATOR_BARS closes (sma50 is the longest window); returns {}
    on short or mismatched-length input rather than crash or emit partial/misleading facts.
    """
    n = len(closes)
    if n < MIN_INDICATOR_BARS or len(highs) != n or len(lows) != n:
        return {}

    sma20 = sum(closes[-20:]) / 20
    sma50 = sum(closes[-50:]) / 50
    high_water = max(closes)

    return {
        "rsi14": _rsi14(closes),
        "sma20": round(sma20, 2),
        "sma50": round(sma50, 2),
        "atr_pct": _atr_pct(closes, highs, lows),
        "ret_5d": round((closes[-1] - closes[-6]) / closes[-6] * 100, 2),
        "pct_from_52w_high": round((closes[-1] - high_water) / high_water * 100, 2),
    }


def _fetch_indicators(tickers: list[str]) -> dict[str, dict]:
    """One batched 1y yfinance call for `tickers` → {ticker: indicator_dict}. Degrades
    to {} on any error, same as `_fetch`, so a dead yfinance never crashes the council.

    Needs the full 1y so `pct_from_52w_high` covers an actual 52 weeks, not a 6mo window
    wearing a 52-week label."""
    out: dict[str, dict] = {}
    try:
        df = yf.download(
            tickers=" ".join(tickers), period="1y", interval="1d", progress=False
        )
        if df is None or df.empty or "Close" not in df.columns:
            return out
        for t in tickers:
            try:
                if len(tickers) > 1:
                    close, high, low = df["Close"][t], df["High"][t], df["Low"][t]
                else:
                    close, high, low = df["Close"], df["High"], df["Low"]
                sub = pd.concat({"c": close, "h": high, "l": low}, axis=1).dropna()
                indicators = compute_indicators(
                    sub["c"].astype(float).tolist(),
                    sub["h"].astype(float).tolist(),
                    sub["l"].astype(float).tolist(),
                )
                if indicators:
                    out[t] = indicators
            except Exception:
                continue
    except Exception as e:
        logger.warning("Indicator fetch error: %s", e)
    return out


def get_indicators(tickers: list[str]) -> dict[str, dict]:
    """Fetch RSI/SMA/ATR/return/52w-high indicators per ticker, served from a TTL
    cache, one batched yfinance call for the tickers whose entry is missing/stale."""
    tickers = [t for t in tickers if isinstance(t, str) and t]
    if not tickers:
        return {}

    now = time.monotonic()
    ttl = _ttl()
    fresh: dict[str, dict] = {}
    stale: list[str] = []
    for t in dict.fromkeys(tickers):
        entry = _indicator_cache.get(t)
        if entry and (now - entry[1]) < ttl:
            fresh[t] = entry[0]
        else:
            stale.append(t)

    if stale:
        fetched = _fetch_indicators(stale)
        for t, result in fetched.items():
            _indicator_cache[t] = (result, now)
            fresh[t] = result

    return {t: fresh[t] for t in dict.fromkeys(tickers) if t in fresh}


def calculate_market_boost(market_data: list[dict]) -> int:
    """Calculate a score boost based on recent price movement.

    Sign follows the biggest mover: a crash pushes the boost negative,
    a rally pushes it positive.
    """
    biggest = 0
    for md in market_data:
        change = md.get("change_percent", 0)
        if abs(change) > abs(biggest):
            biggest = change

    magnitude = abs(biggest)
    if magnitude >= 10:
        return 2 if biggest > 0 else -2
    if magnitude >= 5:
        return 1 if biggest > 0 else -1
    return 0
