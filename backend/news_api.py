"""
news_ingestion.py
=================
Multi-source financial news ingestion pipeline.

Sources
-------
Structured APIs  : Finnhub, Marketaux
Free feeds       : Yahoo Finance (yfinance), RSS (Yahoo Finance RSS, CNBC)

Missing API keys are skipped with a log warning — the pipeline always
returns a (possibly partial) result rather than hard-failing.

Architecture
------------
- Fully async fetch layer (httpx + asyncio)
- Normalised, typed schema (NewsItem, HeatmapEntry, FetchMetrics TypedDicts)
- Two-pass deduplication: URL hash → headline similarity (SequenceMatcher)
- Bounded thread-pool for blocking I/O (feedparser, yfinance)
- Structured logging throughout — zero silent failures
- Exponential-backoff retry on transient HTTP errors (429 / 5xx)
- Global asyncio.Semaphore to prevent 429s on heatmap scans
- In-memory TTL cache (thread-safe) to avoid redundant fetches
- Client-level + request-level timeout enforcement
- Ticker extraction with common-word deny-list + min-length filter
- Graceful thread-pool shutdown via atexit

Public API
----------
    fetch_company_news(symbol, limit, use_cache)    →  list[NewsItem]       (async)
    fetch_market_heatmap_async(symbols, ...)        →  list[HeatmapEntry]   (async — FastAPI / Jupyter / async services)
    fetch_market_heatmap(symbols, ...)              →  list[HeatmapEntry]   (sync  — scripts / Django / CLI)

Environment Variables
---------------------
    FINNHUB_API_KEY     – https://finnhub.io       (60 req/min free)
    MARKETAUX_API_KEY   – https://www.marketaux.com (100 req/day free)
    (Yahoo Finance and RSS require no keys)

Logging
-------
Library code never configures the root logger. To see output:

    import logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
"""

from __future__ import annotations

import asyncio
import atexit
import hashlib
import logging
import os
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from typing import Any, TypedDict

import feedparser
import httpx
import yfinance as yf
from dateutil import parser as date_parser

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

class NewsItem(TypedDict):
    headline:        str          # Article title
    published_at:    str          # ISO-8601 UTC — "2024-01-15T14:30:00+00:00"
    source:          str          # "Finnhub" | "Marketaux" | "YahooRSS" | "CNBC_RSS" | "Yahoo Finance"
    url:             str          # Canonical article URL (always non-empty)
    summary:         str          # Lead paragraph / description (may be empty)
    related_tickers: list[str]    # Sorted uppercase tickers, e.g. ["AAPL", "MSFT"]


class HeatmapEntry(TypedDict):
    symbol: str
    heat:   int


class FetchMetrics(TypedDict):
    """Per-source item counts returned alongside news when return_metrics=True."""
    finnhub:       int
    marketaux:     int
    yahoo_rss:     int
    cnbc_rss:      int
    yfinance:      int
    total_raw:     int
    total_deduped: int


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------

__all__ = [
    "fetch_company_news",
    "fetch_market_heatmap",
    "fetch_market_heatmap_async",
    "NewsItem",
    "HeatmapEntry",
    "FetchMetrics",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_LOOKBACK_DAYS:      int       = 7
DEFAULT_TIMEOUT:            float     = 12.0
MAX_RESULTS_PER_SOURCE:     int       = 25
DEDUP_SIMILARITY_THRESHOLD: float     = 0.85
DEDUP_TIME_WINDOW:          timedelta = timedelta(hours=48)
CACHE_TTL:                  float     = 300.0   # seconds (5 min)

# Global semaphore: caps concurrent outbound API requests across all coroutines.
# Prevents 429s when fetch_market_heatmap fans out across many symbols.
_API_SEMAPHORE = asyncio.Semaphore(5)

# Bounded thread-pool for blocking I/O (feedparser, yfinance).
# Named threads aid debugging in thread dumps / profilers.
_THREAD_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="news_blocking")
atexit.register(_THREAD_POOL.shutdown, wait=False)

# ---------------------------------------------------------------------------
# In-memory TTL cache (thread-safe)
#
# Keyed by symbol. Value is (expiry_monotonic_timestamp, items).
# threading.Lock used because cache may be read/written from sync contexts
# (e.g. inside run_in_executor callbacks) as well as async ones.
# ---------------------------------------------------------------------------

_NEWS_CACHE: dict[str, tuple[float, list[NewsItem]]] = {}
_CACHE_LOCK = threading.Lock()


def _cache_get(symbol: str) -> list[NewsItem] | None:
    with _CACHE_LOCK:
        entry = _NEWS_CACHE.get(symbol)
        if entry is None:
            return None
        expiry, items = entry
        if time.monotonic() < expiry:
            logger.debug("Cache HIT for %s", symbol)
            return items
        del _NEWS_CACHE[symbol]   # expired — evict eagerly
        logger.debug("Cache EXPIRED for %s", symbol)
    return None


def _cache_set(symbol: str, items: list[NewsItem]) -> None:
    with _CACHE_LOCK:
        _NEWS_CACHE[symbol] = (time.monotonic() + CACHE_TTL, items)
        logger.debug("Cache SET for %s (%d items, TTL=%.0fs)", symbol, len(items), CACHE_TTL)


# ---------------------------------------------------------------------------
# Ticker extraction
# ---------------------------------------------------------------------------

# Deny-list: common short uppercase words and financial abbreviations
# that are NOT ticker symbols.
_TICKER_DENYLIST: frozenset[str] = frozenset({
    "AM", "AN", "AS", "AT", "BE", "BY", "DO", "GO", "IF",
    "IN", "IS", "IT", "MY", "NO", "OF", "OK", "ON", "OR",
    "SO", "TO", "UP", "US", "WE", "AI", "CEO", "CFO", "CTO",
    "COO", "IPO", "ETF", "GDP", "CPI", "FED", "SEC", "NYSE",
    "NASDAQ", "SPX", "DOW", "EU", "UK", "UN", "WHO", "IMF",
    "ECB", "VC", "PE", "EPS", "YOY", "QOQ", "TTM", "EBITDA",
    "EST", "EDT", "PST", "PDT", "UTC", "GMT",
})

# Minimum 2 chars eliminates single-letter false positives (A, I, etc.)
_TICKER_RE = re.compile(r"(?<!\w)\$?([A-Z]{2,5})(?!\w)")


def _extract_tickers(text: str) -> list[str]:
    """Extract plausible ticker symbols from free text."""
    if not text:
        return []
    return sorted({t for t in _TICKER_RE.findall(text) if t not in _TICKER_DENYLIST})


# ---------------------------------------------------------------------------
# Date utilities
# ---------------------------------------------------------------------------

def _date_window(days_back: int = DEFAULT_LOOKBACK_DAYS) -> tuple[str, str]:
    today = datetime.now(timezone.utc).date()
    return (today - timedelta(days=days_back)).isoformat(), today.isoformat()


def _parse_datetime(raw: Any) -> str | None:
    """
    Coerce any datetime representation to an ISO-8601 UTC string.

    Accepts: Unix timestamp (int/float), ISO string, datetime object.
    Returns None on failure (logged at DEBUG).
    """
    if raw is None:
        return None
    try:
        if isinstance(raw, (int, float)):
            dt = datetime.fromtimestamp(raw, tz=timezone.utc)
        elif isinstance(raw, str):
            dt = date_parser.parse(raw)
        elif isinstance(raw, datetime):
            dt = raw
        else:
            logger.debug("Unrecognised datetime type %s: %r", type(raw).__name__, raw)
            return None

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError) as exc:
        logger.debug("Could not parse datetime %r: %s", raw, exc)
        return None


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _normalize_text(text: str) -> str:
    """Lowercase, collapse whitespace, strip non-alphanumeric characters."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)          # collapse runs of whitespace
    text = re.sub(r"[^a-z0-9 ]", "", text)
    return text.strip()


def _validate_symbol(symbol: str) -> str:
    """
    Normalise and strictly validate an equity ticker symbol.

    Accepts standard symbols (AAPL) and share-class variants (BRK.B).

    Raises
    ------
    ValueError
        If the symbol does not match the expected pattern.
    """
    symbol = symbol.strip().upper()
    if not re.fullmatch(r"[A-Z]{1,5}(\.[A-Z])?", symbol):
        raise ValueError(
            f"Invalid ticker symbol {symbol!r}. "
            "Expected 1–5 uppercase letters, optionally followed by '.' "
            "and one letter (e.g. 'AAPL', 'BRK.B')."
        )
    return symbol


def _build_news_item(
    raw: dict[str, Any],
    source: str,
    fallback_tickers: list[str] | None = None,
) -> NewsItem | None:
    """
    Build a validated NewsItem from a raw fetcher dict.

    Returns None (with DEBUG log) when:
    - headline is empty or missing
    - no parseable publication date  (required for deduplication + ranking)
    - no URL                         (required for deduplication integrity)
    """
    headline = (raw.get("headline") or raw.get("title") or "").strip()
    if not headline:
        logger.debug("[%s] Skipping item — empty headline", source)
        return None

    raw_date = (
        raw.get("published_at")
        or raw.get("datetime")
        or raw.get("publishedDate")
        or raw.get("time_published")
        or raw.get("published")
        or raw.get("providerPublishTime")
    )
    published_at = _parse_datetime(raw_date)
    if not published_at:
        logger.debug("[%s] Skipping %r — no parseable date", source, headline[:60])
        return None

    url = (raw.get("url") or raw.get("link") or "").strip()
    if not url:
        logger.debug("[%s] Skipping %r — missing URL", source, headline[:60])
        return None

    summary = (
        raw.get("summary") or raw.get("description") or raw.get("text") or ""
    ).strip()

    tickers: list[str] = list(raw.get("related_tickers") or fallback_tickers or [])
    if not tickers:
        tickers = _extract_tickers(f"{headline} {summary}")

    return NewsItem(
        headline=headline,
        published_at=published_at,
        source=source,
        url=url,
        summary=summary,
        related_tickers=sorted({t.upper() for t in tickers if t.strip()}),
    )


# ---------------------------------------------------------------------------
# HTTP helper — semaphore-guarded GET with exponential backoff
# ---------------------------------------------------------------------------

async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, Any] | None = None,
    *,
    source: str,
    retries: int = 2,
) -> Any:
    """
    Semaphore-guarded GET with exponential backoff.

    - Max concurrent requests: bounded by _API_SEMAPHORE
    - Retries on: 429, 500, 502, 503, 504
    - Raises immediately on permanent 4xx (non-429) errors
    """
    delay = 1.0
    last_exc: Exception | None = None

    async with _API_SEMAPHORE:
        for attempt in range(retries + 1):
            try:
                r = await client.get(url, params=params)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in {429, 500, 502, 503, 504}:
                    logger.warning(
                        "[%s] HTTP %d — attempt %d/%d, retrying in %.1fs",
                        source, exc.response.status_code,
                        attempt + 1, retries + 1, delay,
                    )
                    last_exc = exc
                    await asyncio.sleep(delay)
                    delay *= 2
                else:
                    raise   # permanent 4xx — do not retry
            except httpx.RequestError as exc:
                logger.warning(
                    "[%s] Network error — attempt %d/%d: %s",
                    source, attempt + 1, retries + 1, exc,
                )
                last_exc = exc
                await asyncio.sleep(delay)
                delay *= 2

    raise last_exc  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Source fetchers
# ---------------------------------------------------------------------------

async def _fetch_finnhub(symbol: str, client: httpx.AsyncClient) -> list[NewsItem]:
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        logger.warning("[Finnhub] FINNHUB_API_KEY not set — skipping source")
        return []

    start, end = _date_window()
    try:
        data = await _get_json(
            client,
            "https://finnhub.io/api/v1/company-news",
            {"symbol": symbol, "from": start, "to": end, "token": api_key},
            source="Finnhub",
        )
    except Exception as exc:
        logger.warning("[Finnhub] Fetch failed for %s: %s", symbol, exc)
        return []

    items: list[NewsItem] = []
    for raw in data:
        related_raw = raw.get("related") or ""
        tickers = [t.strip().upper() for t in related_raw.split(",") if t.strip()]
        item = _build_news_item(raw, "Finnhub", fallback_tickers=tickers or [symbol])
        if item:
            items.append(item)

    logger.info("[Finnhub] %d items for %s", len(items), symbol)
    return items


async def _fetch_marketaux(symbol: str, client: httpx.AsyncClient) -> list[NewsItem]:
    api_key = os.getenv("MARKETAUX_API_KEY")
    if not api_key:
        logger.warning("[Marketaux] MARKETAUX_API_KEY not set — skipping source")
        return []

    try:
        payload = await _get_json(
            client,
            "https://api.marketaux.com/v1/news/all",
            {
                "symbols": symbol,
                "filter_entities": "true",
                "language": "en",
                "limit": 10,          # conservative: free tier is 100 req/day
                "api_token": api_key,
            },
            source="Marketaux",
        )
    except Exception as exc:
        logger.warning("[Marketaux] Fetch failed for %s: %s", symbol, exc)
        return []

    items: list[NewsItem] = []
    for raw in payload.get("data", []):
        tickers = [e["symbol"] for e in raw.get("entities", []) if e.get("symbol")]
        item = _build_news_item(
            {**raw, "related_tickers": tickers},
            "Marketaux",
            fallback_tickers=[symbol],
        )
        if item:
            items.append(item)

    logger.info("[Marketaux] %d items for %s", len(items), symbol)
    return items


async def _fetch_rss(symbol: str) -> tuple[list[NewsItem], list[NewsItem]]:
    """
    Fetch from Yahoo Finance RSS and CNBC RSS in parallel.

    Returns (yahoo_rss_items, cnbc_rss_items) so the caller can track
    per-source metrics independently.

    feedparser.parse is blocking; offloaded to the bounded thread pool.
    Non-symbol-specific feeds (CNBC) are filtered by symbol mention.
    """
    feeds: list[tuple[str, str, bool]] = [
        # (url,  source_tag,  is_symbol_specific)
        (
            f"https://feeds.finance.yahoo.com/rss/2.0/headline"
            f"?s={symbol}&region=US&lang=en-US",
            "YahooRSS",
            True,
        ),
        (
            "https://www.cnbc.com/id/10000664/device/rss/rss.html",
            "CNBC_RSS",
            False,
        ),
    ]

    loop = asyncio.get_running_loop()
    yahoo_items: list[NewsItem] = []
    cnbc_items:  list[NewsItem] = []
    bucket_map = {"YahooRSS": yahoo_items, "CNBC_RSS": cnbc_items}

    async def _parse_feed(url: str, tag: str, specific: bool) -> None:
        try:
            feed = await loop.run_in_executor(_THREAD_POOL, feedparser.parse, url)
        except Exception as exc:
            logger.warning("[%s] feedparser failed (%s): %s", tag, url, exc)
            return

        bucket = bucket_map[tag]
        for entry in feed.entries[:MAX_RESULTS_PER_SOURCE]:
            raw_text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            if not specific and symbol.upper() not in raw_text.upper():
                continue
            item = _build_news_item(
                {
                    "headline":  entry.get("title"),
                    "published": entry.get("published"),
                    "url":       entry.get("link"),
                    "summary":   entry.get("summary", ""),
                },
                tag,
                fallback_tickers=[symbol],
            )
            if item:
                bucket.append(item)

    await asyncio.gather(*(_parse_feed(url, tag, spec) for url, tag, spec in feeds))
    logger.info(
        "[YahooRSS] %d items | [CNBC_RSS] %d items for %s",
        len(yahoo_items), len(cnbc_items), symbol,
    )
    return yahoo_items, cnbc_items


def _yfinance_blocking(symbol: str) -> list[NewsItem]:
    """Synchronous yfinance fetch — must run inside a thread executor."""
    ticker = yf.Ticker(symbol)
    items: list[NewsItem] = []
    for raw in (ticker.news or [])[:MAX_RESULTS_PER_SOURCE]:
        item = _build_news_item(raw, "Yahoo Finance", fallback_tickers=[symbol])
        if item:
            items.append(item)
    return items


async def _fetch_yfinance(symbol: str) -> list[NewsItem]:
    loop = asyncio.get_running_loop()
    try:
        items = await loop.run_in_executor(_THREAD_POOL, _yfinance_blocking, symbol)
        logger.info("[YFinance] %d items for %s", len(items), symbol)
        return items
    except Exception as exc:
        logger.warning("[YFinance] Fetch failed for %s: %s", symbol, exc)
        return []


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------

def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def _are_duplicates(a: NewsItem, b: NewsItem) -> bool:
    """
    Two articles are duplicates when either:
      1. They share the same URL  (exact cross-source syndication), OR
      2. Their headlines are >= DEDUP_SIMILARITY_THRESHOLD similar AND
         they were published within DEDUP_TIME_WINDOW of each other.
    """
    if a["url"] == b["url"]:
        return True

    sim = SequenceMatcher(
        None,
        _normalize_text(a["headline"]),
        _normalize_text(b["headline"]),
    ).ratio()

    if sim < DEDUP_SIMILARITY_THRESHOLD:
        return False

    try:
        dt_a = datetime.fromisoformat(a["published_at"])
        dt_b = datetime.fromisoformat(b["published_at"])
        return abs(dt_a - dt_b) <= DEDUP_TIME_WINDOW
    except (ValueError, KeyError):
        return True   # conservative: can't compare dates → treat as duplicate


def _deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    """
    Two-pass deduplication, newest-first.

    Pass 1 — O(n)    : SHA-256 URL hash — removes cross-source syndication.
    Pass 2 — O(n²) wc: SequenceMatcher headline similarity — removes rewrites
                       and reposts. Pass 1 eliminates the bulk of duplicates
                       so pass 2 operates on a much smaller set in practice.
    """
    sorted_items = sorted(items, key=lambda x: x["published_at"], reverse=True)

    seen_urls: set[str] = set()
    url_deduped: list[NewsItem] = []
    for item in sorted_items:
        h = _url_hash(item["url"])
        if h not in seen_urls:
            seen_urls.add(h)
            url_deduped.append(item)

    unique: list[NewsItem] = []
    for candidate in url_deduped:
        if not any(_are_duplicates(candidate, existing) for existing in unique):
            unique.append(candidate)

    logger.info("Dedup: %d raw → %d unique", len(items), len(unique))
    return unique


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_company_news(
    symbol: str,
    limit: int = 30,
    use_cache: bool = True,
    return_metrics: bool = False,
) -> list[NewsItem] | tuple[list[NewsItem], FetchMetrics]:
    
    symbol = _validate_symbol(symbol)

    if use_cache:
        cached = _cache_get(symbol)
        if cached is not None:
            result = cached[:limit]
            if return_metrics:
                return result, FetchMetrics(
                    finnhub=0, marketaux=0, yahoo_rss=0, cnbc_rss=0, yfinance=0,
                    total_raw=0, total_deduped=len(result),
                )
            return result

    logger.info("Fetching news for %s (limit=%d)", symbol, limit)

    async with httpx.AsyncClient(
        http2=True,
        timeout=httpx.Timeout(DEFAULT_TIMEOUT),   # enforced at client level too
    ) as client:
        finnhub_r, marketaux_r, rss_r, yfinance_r = await asyncio.gather(
            _fetch_finnhub(symbol, client),
            _fetch_marketaux(symbol, client),
            _fetch_rss(symbol),
            _fetch_yfinance(symbol),
            return_exceptions=True,
        )

    def _safe(result: Any, name: str) -> list[NewsItem]:
        if isinstance(result, Exception):
            logger.error("%s fetcher raised unexpectedly: %s", name, result)
            return []
        return result

    finnhub_items   = _safe(finnhub_r,   "Finnhub")
    marketaux_items = _safe(marketaux_r, "Marketaux")
    yfinance_items  = _safe(yfinance_r,  "YFinance")

    yahoo_rss_items: list[NewsItem] = []
    cnbc_rss_items:  list[NewsItem] = []
    if isinstance(rss_r, Exception):
        logger.error("RSS fetcher raised unexpectedly: %s", rss_r)
    else:
        yahoo_rss_items, cnbc_rss_items = rss_r

    all_items = finnhub_items + marketaux_items + yahoo_rss_items + cnbc_rss_items + yfinance_items

    deduped = _deduplicate(all_items)
    deduped.sort(key=lambda x: x["published_at"], reverse=True)  # defensive sort

    _cache_set(symbol, deduped)
    result = deduped[:limit]

    if return_metrics:
        return result, FetchMetrics(
            finnhub       = len(finnhub_items),
            marketaux     = len(marketaux_items),
            yahoo_rss     = len(yahoo_rss_items),
            cnbc_rss      = len(cnbc_rss_items),
            yfinance      = len(yfinance_items),
            total_raw     = len(all_items),
            total_deduped = len(deduped),
        )

    return result


async def fetch_market_heatmap_async(
    symbols: list[str],
    limit_per_symbol: int = 20,
    top_n: int = 25,
) -> list[HeatmapEntry]:
   
    validated: list[str] = []
    for sym in symbols:
        try:
            validated.append(_validate_symbol(sym))
        except ValueError as exc:
            logger.warning("Heatmap: skipping invalid symbol — %s", exc)

    mentions: Counter[str] = Counter()

    results = await asyncio.gather(
        *(fetch_company_news(sym, limit_per_symbol) for sym in validated),
        return_exceptions=True,
    )

    for sym, result in zip(validated, results):
        if isinstance(result, Exception):
            logger.error("Heatmap: fetch failed for %s: %s", sym, result)
            continue
        for item in result:
            for ticker in item["related_tickers"]:
                mentions[ticker] += 1

    return [
        HeatmapEntry(symbol=ticker, heat=count)
        for ticker, count in mentions.most_common(top_n)
    ]


def fetch_market_heatmap(
    symbols: list[str],
    limit_per_symbol: int = 20,
    top_n: int = 25,
) -> list[HeatmapEntry]:
   
    return asyncio.run(
        fetch_market_heatmap_async(symbols, limit_per_symbol, top_n)
    )
    """
    Synchronous wrapper around ``fetch_market_heatmap_async``.

    **Use this in synchronous contexts only**: scripts, Django views, CLI tools,
    or any code that is NOT already running inside an event loop.

    If you are inside an async context (FastAPI, Jupyter, async service), use
    ``await fetch_market_heatmap_async(...)`` instead. Calling this wrapper
    from a running event loop raises ``RuntimeError: asyncio.run() cannot be
    called from a running event loop`` — that is intentional and correct
    behaviour, not a bug to work around.

    Parameters
    ----------
    symbols : list[str]
        Universe of tickers to scan. Invalid symbols are logged and skipped.
    limit_per_symbol : int
        Max articles fetched per symbol (cached results satisfy this).
    top_n : int
        Number of top-mentioned tickers to return.

    Returns
    -------
    list[HeatmapEntry]
        Sorted by mention count, descending.

    Examples
    --------
    Script / CLI::

        if __name__ == "__main__":
            heatmap = fetch_market_heatmap(["AAPL", "MSFT", "NVDA"])
            for entry in heatmap:
                print(entry["symbol"], entry["heat"])
    """