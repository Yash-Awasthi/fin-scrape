"""Auxiliary data routes for Phase 6 panels: crypto, RSS proxy, ticker rollup.

Network calls (CoinGecko, RSS) run in a threadpool with a short in-memory cache so
they don't block the event loop or hammer upstreams. The RSS proxy is SSRF-guarded:
it only fetches URLs from the world feed registry (no arbitrary user URLs).
"""
from __future__ import annotations

import asyncio
import time

import requests
from fastapi import APIRouter, HTTPException, Query

from finscrape.scrapers.world.feeds import FEEDS, get_feed
from server import db

router = APIRouter()

_HEADERS = {"User-Agent": "finscrape-worldfin/0.1"}
_TIMEOUT = 15

# tiny TTL cache: key -> (expires_at, value)
_cache: dict[str, tuple[float, object]] = {}


def _cached(key: str, ttl: float, produce):
    hit = _cache.get(key)
    now = time.time()
    if hit and hit[0] > now:
        return hit[1]
    value = produce()
    _cache[key] = (now + ttl, value)
    return value


# --- crypto (CoinGecko passthrough) ---


def _fetch_crypto(per_page: int) -> list[dict]:
    resp = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": per_page,
            "page": 1,
            "price_change_percentage": "24h",
        },
        headers=_HEADERS,
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return [
        {
            "symbol": (c.get("symbol") or "").upper(),
            "name": c.get("name"),
            "price": c.get("current_price"),
            "change_24h": c.get("price_change_percentage_24h"),
        }
        for c in resp.json()
    ]


@router.get("/api/crypto")
async def crypto(limit: int = Query(20, ge=1, le=100)) -> dict:
    try:
        coins = await asyncio.to_thread(
            lambda: _cached(f"crypto:{limit}", 60, lambda: _fetch_crypto(limit))
        )
    except requests.RequestException:
        coins = []
    return {"coins": coins}


# --- RSS proxy (allowlisted by feed key — SSRF guard) ---


def _fetch_rss(url: str, limit: int) -> list[dict]:
    import feedparser

    feed = feedparser.parse(url)
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
async def rss_proxy(feed: str = Query(...), limit: int = Query(20, ge=1, le=50)) -> dict:
    f = get_feed(feed)
    if f is None:
        # only registry feeds are proxied — blocks arbitrary-URL SSRF
        raise HTTPException(status_code=400, detail="unknown feed key")
    try:
        items = await asyncio.to_thread(
            lambda: _cached(f"rss:{feed}:{limit}", 120, lambda: _fetch_rss(f.url, limit))
        )
    except Exception:
        items = []
    return {"feed": feed, "name": f.name, "tier": f.tier, "items": items}


@router.get("/api/feeds")
async def feeds() -> dict:
    """The world feed registry (for the WorldNews panel's source picker)."""
    return {
        "feeds": [
            {"key": f.key, "name": f.name, "tier": f.tier, "region": f.region} for f in FEEDS
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
            {"ticker": r["ticker"], "mentions": r["mentions"], "avg_score": round(r["avg_score"], 2)}
            for r in rows
        ]
    }
