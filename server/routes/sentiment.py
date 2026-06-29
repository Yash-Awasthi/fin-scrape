"""GET /api/sentiment?ticker= — social sentiment (Reddit + StockTwits) via finscrape.

The scrapers hit public, unauthenticated, and FLAKY endpoints with blocking `requests`,
so the call runs in a threadpool, behind a circuit breaker, with a medium TTL cache.
Any failure (timeout, rate-limit, open breaker) degrades to an empty result — the panel
shows "no data", never an error.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Query

from server import cache
from server.circuit import CircuitBreaker

router = APIRouter()

_sentiment_cb = CircuitBreaker("sentiment")


def _empty(ticker: str) -> dict:
    return {
        "ticker": ticker,
        "sentiment_score": 0.0,
        "bullish_count": 0,
        "bearish_count": 0,
        "neutral_count": 0,
        "total_posts": 0,
        "bullish_pct": 0.0,
        "volume_spike": False,
        "platforms": [],
        "top_posts": [],
    }


def _fetch(ticker: str) -> dict:
    """Blocking: scrape both platforms, aggregate to one result dict."""
    from finscrape.sentiment.aggregator import SentimentAggregator

    agg = SentimentAggregator()
    results = agg.scrape_all([ticker]).get(ticker, [])
    r = agg.aggregate(results)
    return {
        "ticker": ticker,
        "sentiment_score": round(r.sentiment_score, 4),
        "bullish_count": r.bullish_count,
        "bearish_count": r.bearish_count,
        "neutral_count": r.neutral_count,
        "total_posts": r.total_posts,
        "bullish_pct": round(r.bullish_pct, 4),
        "volume_spike": r.volume_spike,
        "platforms": [x.platform for x in results if x.total_posts > 0],
        "top_posts": [
            {
                "text": (p.text or "")[:280],
                "author": p.author,
                "platform": p.platform,
                "url": p.url,
            }
            for p in r.top_posts[:8]
        ],
    }


@router.get("/api/sentiment")
async def sentiment(ticker: str = Query(..., min_length=1, max_length=10)) -> dict:
    sym = ticker.upper().strip()
    try:
        result = await asyncio.to_thread(
            lambda: cache.get_or_set(
                f"sentiment:{sym}",
                cache.MEDIUM,
                lambda: _sentiment_cb.call(lambda: _fetch(sym)),
            )
        )
    except Exception:  # noqa: BLE001 - any upstream failure (incl. CircuitOpen) → empty
        return _empty(sym)
    return result if isinstance(result, dict) else _empty(sym)
