"""Auxiliary data routes for Phase 6 panels: RSS proxy, ticker rollup, suggestions.

Network calls (RSS) run in a threadpool with a short in-memory cache so they don't
block the event loop or hammer upstreams. The RSS proxy is SSRF-guarded: it only
fetches URLs from the world feed registry (no arbitrary user URLs).
"""

from __future__ import annotations

import asyncio

import requests
from fastapi import APIRouter, HTTPException, Query

from finscrape.scrapers.world.feeds import FEEDS, get_feed
from server import cache, db
from server.circuit import CircuitBreaker
from server.ssrf import assert_public_url

router = APIRouter()

_HEADERS = {"User-Agent": "finscrape-worldfin/0.1"}
_TIMEOUT = 15

# Per-upstream breakers: a dead host fails fast instead of burning a thread + 15s timeout
# on every request until its TTL cache entry would refill.
_rss_cb = CircuitBreaker("rss")


# --- RSS proxy (allowlisted by feed key — SSRF guard) ---


def _fetch_rss(url: str, limit: int) -> list[dict]:
    import feedparser

    # SSRF guard: validate before fetch, then re-validate every redirect hop so a
    # registry host that 302s to a private address is still rejected. We fetch the
    # bytes ourselves (requests) instead of letting feedparser open the socket.
    assert_public_url(url)
    resp = requests.get(url, headers=_HEADERS, timeout=_TIMEOUT, stream=False)
    for hop in (*resp.history, resp):
        assert_public_url(hop.url)
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
    items = []
    for e in feed.entries[:limit]:
        items.append(
            {
                "title": (e.get("title") or "").strip(),
                "link": (e.get("link") or "").strip(),
                "published": e.get("published", ""),
            }
        )
    return items


@router.get("/api/rss-proxy")
async def rss_proxy(
    feed: str = Query(...), limit: int = Query(20, ge=1, le=50)
) -> dict:
    f = get_feed(feed)
    if f is None:
        # only registry feeds are proxied — blocks arbitrary-URL SSRF
        raise HTTPException(status_code=400, detail="unknown feed key")
    try:
        items = await asyncio.to_thread(
            lambda: cache.get_or_set(
                f"rss:{feed}:{limit}",
                cache.MEDIUM,
                lambda: _rss_cb.call(lambda: _fetch_rss(f.url, limit)),
            )
        )
    except Exception:
        items = []
    return {"feed": feed, "name": f.name, "tier": f.tier, "items": items}


@router.get("/api/feeds")
async def feeds() -> dict:
    """The world feed registry (for the WorldNews panel's source picker)."""
    return {
        "feeds": [
            {"key": f.key, "name": f.name, "tier": f.tier, "region": f.region}
            for f in FEEDS
        ]
    }


# --- markets (ticker frequency from stored events; live quotes deferred to Phase 8) ---


@router.get("/api/markets")
async def markets(limit: int = Query(20, ge=1, le=100)) -> dict:
    """Most-mentioned tickers across recent events. Live price quotes are deferred
    (yfinance hot-path cost, RISKS R1) — this is the cheap event-derived rollup."""
    rows = await db.pool().fetch(
        """
        SELECT t.ticker, COUNT(*) AS mentions,
               AVG(signal_score)::float AS avg_score
        FROM events e, jsonb_array_elements_text(e.tickers) AS t(ticker)
        WHERE e.timestamp >= now() - interval '7 days'
        GROUP BY t.ticker ORDER BY mentions DESC LIMIT $1
        """,
        limit,
    )
    return {
        "tickers": [
            {
                "ticker": r["ticker"],
                "mentions": r["mentions"],
                "avg_score": round(r["avg_score"], 2),
            }
            for r in rows
        ]
    }


# --- suggestions (what to look at next, derived from event flow + trust) ---

_SUGGESTIONS_SQL = """
WITH recent AS (
    SELECT e.id, e.subject, e.tickers, e.signal_score, e.confidence,
           e.verdict, e.sector_impact, e.actionability, e.timestamp
    FROM events e
    WHERE e.timestamp >= now() - interval '7 days'
),
ticker_stats AS (
    SELECT t.ticker,
           COUNT(*)::float AS mentions,
           AVG(r.confidence)::float AS avg_confidence,
           AVG(r.signal_score)::float AS avg_score,
           MAX(r.timestamp) AS last_seen,
           SUM(CASE WHEN r.verdict IN ('INVEST', 'PULL_OUT') THEN 1 ELSE 0 END)::float AS directional
    FROM recent r, jsonb_array_elements_text(r.tickers) AS t(ticker)
    GROUP BY t.ticker
),
source_accuracy AS (
    SELECT s.ticker, AVG(s.hit_rate)::float AS trust
    FROM (
        SELECT jsonb_array_elements_text(e.tickers) AS ticker,
               CASE WHEN e.verdict IN ('INVEST', 'PULL_OUT') THEN 1.0 ELSE 0.5 END AS hit_rate
        FROM events e
        WHERE e.timestamp >= now() - interval '30 days'
              AND e.verdict IN ('INVEST', 'PULL_OUT')
    ) s
    GROUP BY s.ticker
)
SELECT r.ticker, r.mentions, r.avg_confidence, r.avg_score, r.last_seen,
       COALESCE(sa.trust, 0.5) AS trust,
       (r.mentions * r.avg_confidence * (0.5 + ABS(r.avg_score) / 10.0)
        * (0.5 + COALESCE(sa.trust, 0.5)))::float AS suggestion_score,
       (ARRAY_AGG(r.subject ORDER BY r.timestamp DESC))[1] AS latest_subject,
       (ARRAY_AGG(r.verdict ORDER BY r.timestamp DESC))[1] AS latest_verdict,
       (ARRAY_AGG(r.sector_impact ORDER BY r.timestamp DESC))[1] AS sector
FROM ticker_stats r
LEFT JOIN source_accuracy sa ON sa.ticker = r.ticker
GROUP BY r.ticker, r.mentions, r.avg_confidence, r.avg_score, r.last_seen, sa.trust
ORDER BY suggestion_score DESC
LIMIT $1
"""


@router.get("/api/suggestions")
async def suggestions(limit: int = Query(10, ge=1, le=50)) -> dict:
    """Rank tickers to look at next: mention volume × confidence × score magnitude
    × realized directional trust. Pure event-derived — no external calls."""
    rows = await db.pool().fetch(_SUGGESTIONS_SQL, limit)
    return {
        "suggestions": [
            {
                "ticker": r["ticker"],
                "score": round(r["suggestion_score"], 3),
                "mentions": int(r["mentions"]),
                "avg_score": round(r["avg_score"], 2),
                "avg_confidence": round(r["avg_confidence"], 2),
                "trust": round(r["trust"], 2),
                "latest_subject": r["latest_subject"],
                "latest_verdict": r["latest_verdict"],
                "sector": r["sector"],
                "last_seen": r["last_seen"].isoformat() if r["last_seen"] else None,
            }
            for r in rows
        ]
    }
