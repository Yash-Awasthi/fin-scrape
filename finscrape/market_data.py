"""
Market data fetching via yfinance.
"""

from __future__ import annotations

import logging
import math

import yfinance as yf

logger = logging.getLogger(__name__)


def get_market_data(tickers: list[str]) -> list[dict]:
    """
    Fetch 2-day OHLC data for tickers and calculate % change.

    Returns a list of dicts: {"ticker", "price", "change_percent"}
    """
    if not tickers:
        return []

    data = []
    tickers = [t for t in tickers if isinstance(t, str) and t]

    try:
        df = yf.download(
            tickers=" ".join(tickers),
            period="2d",
            interval="1d",
            progress=False,
        )

        if df is None or df.empty or "Close" not in df.columns:
            return data

        for t in tickers:
            try:
                close = df["Close"][t] if len(tickers) > 1 else df["Close"]

                if len(close) < 2:
                    continue

                price = float(close.iloc[-1])
                prev = float(close.iloc[-2])

                if math.isnan(price) or math.isnan(prev):
                    continue

                change = ((price - prev) / prev) * 100
                data.append({
                    "ticker": t,
                    "price": round(price, 2),
                    "change_percent": round(change, 2),
                })
            except Exception:
                continue

    except Exception as e:
        logger.warning("Market data error: %s", e)

    return data


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
