# `news_ingestion.py`

Multi-source async financial news ingestion pipeline with deduplication, TTL caching, and market heatmap generation.

---

## Table of Contents

- [Sources](#sources)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Public API](#public-api)
  - [fetch\_company\_news](#fetch_company_news)
  - [fetch\_market\_heatmap\_async](#fetch_market_heatmap_async)
  - [fetch\_market\_heatmap](#fetch_market_heatmap)
- [Type Schemas](#type-schemas)
  - [NewsItem](#newsitem)
  - [HeatmapEntry](#heatmapentry)
  - [FetchMetrics](#fetchmetrics)
- [Architecture](#architecture)
  - [Concurrency model](#concurrency-model)
  - [Deduplication](#deduplication)
  - [Caching](#caching)
  - [Retry policy](#retry-policy)
  - [Rate limiting](#rate-limiting)
  - [Ticker extraction](#ticker-extraction)
- [Logging](#logging)
- [Event loop guide](#event-loop-guide)
- [Free tier limits](#free-tier-limits)
- [Tunable constants](#tunable-constants)

---

## Sources

| Source | Tag in `NewsItem.source` | Auth required |
|---|---|---|
| [Finnhub](https://finnhub.io) | `"Finnhub"` | `FINNHUB_API_KEY` |
| [Marketaux](https://www.marketaux.com) | `"Marketaux"` | `MARKETAUX_API_KEY` |
| Yahoo Finance RSS | `"YahooRSS"` | No |
| CNBC Finance RSS | `"CNBC_RSS"` | No |
| yfinance (Yahoo Finance scraper) | `"Yahoo Finance"` | No |

Missing API keys are **logged as warnings and skipped** — the pipeline never raises on a missing credential and always returns results from whatever sources are available.

---

## Requirements

Python 3.11+

```
httpx[http2]>=0.27.0
feedparser>=6.0.11
yfinance>=0.2.40
python-dateutil>=2.9.0
```

---

## Installation

```bash
pip install "httpx[http2]" feedparser yfinance python-dateutil
```

---

## Configuration

Set API keys as environment variables before running:

```bash
export FINNHUB_API_KEY="your_finnhub_key"
export MARKETAUX_API_KEY="your_marketaux_key"
```

Or load from a `.env` file with `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()
```

Free-tier registration:
- Finnhub → https://finnhub.io (60 req/min)
- Marketaux → https://www.marketaux.com (100 req/day)

---

## Quick Start

### Async context (FastAPI, Jupyter, async service)

```python
import asyncio
from news_ingestion import fetch_company_news, fetch_market_heatmap_async

async def main():
    news = await fetch_company_news("AAPL", limit=20)
    for item in news:
        print(f"[{item['source']}] {item['published_at']}  {item['headline']}")

asyncio.run(main())
```

### Sync context (script, CLI, Django)

```python
from news_ingestion import fetch_market_heatmap

heatmap = fetch_market_heatmap(["AAPL", "MSFT", "NVDA", "TSLA"], top_n=10)
for entry in heatmap:
    print(f"{entry['symbol']:6s}  mentions={entry['heat']}")
```

### With per-source metrics

```python
import asyncio
from news_ingestion import fetch_company_news

async def main():
    news, metrics = await fetch_company_news("TSLA", limit=25, return_metrics=True)
    print(metrics)
    # FetchMetrics(finnhub=8, marketaux=5, yahoo_rss=6, cnbc_rss=2, yfinance=9,
    #              total_raw=30, total_deduped=22)

asyncio.run(main())
```

---

## Public API

### `fetch_company_news`

```python
async def fetch_company_news(
    symbol: str,
    limit: int = 30,
    use_cache: bool = True,
    return_metrics: bool = False,
) -> list[NewsItem] | tuple[list[NewsItem], FetchMetrics]
```

Fetches, merges, and deduplicates news for a single equity symbol. All sources run concurrently. Per-source failures are logged and skipped without interrupting the pipeline.

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `symbol` | `str` | — | Equity ticker. Accepts `AAPL`, `BRK.B`. Raises `ValueError` on invalid format. |
| `limit` | `int` | `30` | Max items to return, sorted newest-first. |
| `use_cache` | `bool` | `True` | Serve from in-memory TTL cache if available (TTL = 300 s). |
| `return_metrics` | `bool` | `False` | If `True`, returns `(items, FetchMetrics)` tuple instead of just items. |

**Returns** `list[NewsItem]` — or `tuple[list[NewsItem], FetchMetrics]` when `return_metrics=True`.

**Raises** `ValueError` if `symbol` fails format validation.

---

### `fetch_market_heatmap_async`

```python
async def fetch_market_heatmap_async(
    symbols: list[str],
    limit_per_symbol: int = 20,
    top_n: int = 25,
) -> list[HeatmapEntry]
```

Builds a ticker mention heatmap across a universe of symbols. Counts how many times each ticker appears in `related_tickers` across all fetched articles and returns the top-N by frequency.

**Use this in async contexts** — FastAPI route handlers, Jupyter notebooks, async services. See [Event loop guide](#event-loop-guide).

**Parameters**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `symbols` | `list[str]` | — | Tickers to scan. Invalid symbols are logged and skipped. |
| `limit_per_symbol` | `int` | `20` | Max articles fetched per symbol. Cache hits count toward this. |
| `top_n` | `int` | `25` | Number of top-mentioned tickers to return. |

**Returns** `list[HeatmapEntry]` sorted by `heat` descending.

---

### `fetch_market_heatmap`

```python
def fetch_market_heatmap(
    symbols: list[str],
    limit_per_symbol: int = 20,
    top_n: int = 25,
) -> list[HeatmapEntry]
```

Synchronous wrapper around `fetch_market_heatmap_async`. Same parameters and return type.

**Use this in synchronous contexts only** — scripts, CLI tools, Django views, or any code not already running inside an event loop. See [Event loop guide](#event-loop-guide).

---

## Type Schemas

### `NewsItem`

```python
class NewsItem(TypedDict):
    headline:        str        # Article title
    published_at:    str        # ISO-8601 UTC, e.g. "2024-01-15T14:30:00+00:00"
    source:          str        # "Finnhub" | "Marketaux" | "YahooRSS" | "CNBC_RSS" | "Yahoo Finance"
    url:             str        # Canonical article URL — always non-empty
    summary:         str        # Lead paragraph or description — may be empty string
    related_tickers: list[str]  # Sorted uppercase tickers, e.g. ["AAPL", "MSFT"]
```

All fields are always present. `url` is guaranteed non-empty — items without a URL are discarded during normalisation. `summary` may be an empty string depending on the source. `related_tickers` is sorted and deduplicated.

### `HeatmapEntry`

```python
class HeatmapEntry(TypedDict):
    symbol: str   # Ticker symbol, e.g. "NVDA"
    heat:   int   # Total mention count across all scanned symbols
```

### `FetchMetrics`

```python
class FetchMetrics(TypedDict):
    finnhub:       int   # Items returned by Finnhub
    marketaux:     int   # Items returned by Marketaux
    yahoo_rss:     int   # Items returned by Yahoo Finance RSS
    cnbc_rss:      int   # Items returned by CNBC RSS
    yfinance:      int   # Items returned by yfinance scraper
    total_raw:     int   # Total before deduplication
    total_deduped: int   # Total after deduplication
```

> **Note:** When `use_cache=True` serves a cache hit, all source counts are `0` and `total_deduped` reflects the cached slice length. Source-level breakdown is only available on a live fetch.

---

## Architecture

### Concurrency model

```
fetch_company_news("AAPL")
│
├── asyncio.gather (all concurrent)
│   ├── _fetch_finnhub()      — httpx async GET        → event loop
│   ├── _fetch_marketaux()    — httpx async GET        → event loop
│   ├── _fetch_rss()
│   │   ├── YahooRSS          — feedparser.parse       → ThreadPoolExecutor (max 4)
│   │   └── CNBC_RSS          — feedparser.parse       → ThreadPoolExecutor (max 4)
│   └── _fetch_yfinance()     — yf.Ticker().news       → ThreadPoolExecutor (max 4)
│
└── _deduplicate() → sort → cache → slice to limit
```

`feedparser` and `yfinance` are synchronous blocking libraries. They run inside a named, bounded `ThreadPoolExecutor` (`max_workers=4`, prefix `news_blocking`) via `loop.run_in_executor`, keeping the event loop unblocked. The pool is registered with `atexit` for graceful shutdown on process exit.

### Deduplication

Two-pass pipeline applied to the merged results of all sources, pre-sorted newest-first so the most recent copy of a duplicate is always kept.

**Pass 1 — O(n), SHA-256 URL hash.** Removes identical articles syndicated across multiple sources. Since `url` is guaranteed non-empty by `_build_news_item`, this pass has no edge cases.

**Pass 2 — O(n²) worst case, `SequenceMatcher`.** Catches rewrites and reposts. Two articles are considered duplicates when their normalised headline similarity is ≥ `DEDUP_SIMILARITY_THRESHOLD` (0.85) **and** they were published within `DEDUP_TIME_WINDOW` (48 hours). When dates cannot be compared, the conservative choice is to treat them as duplicates. Pass 1 typically removes the bulk of cross-source duplicates, so Pass 2 operates on a much smaller working set in practice.

### Caching

Results are cached in `_NEWS_CACHE`, a `dict[str, tuple[float, list[NewsItem]]]` keyed by validated symbol. The float is a `time.monotonic()` expiry timestamp. TTL defaults to 300 seconds.

All reads and writes are protected by `threading.Lock` because the cache can be read and written from both async coroutines and thread-pool callbacks simultaneously.

On a cache hit, expired entries are evicted eagerly and the result is returned immediately with no network I/O. Pass `use_cache=False` to force a live fetch.

### Retry policy

`_get_json` retries on HTTP `{429, 500, 502, 503, 504}` with exponential backoff starting at 1 second (`1s → 2s → 4s`, up to 2 retries). Permanent 4xx errors (401, 403, 404, etc.) raise immediately without retrying.

### Rate limiting

`_API_SEMAPHORE = asyncio.Semaphore(5)` wraps every `_get_json` call. This caps the total number of concurrent outbound HTTP requests at 5 across the entire module, regardless of how many symbols `fetch_market_heatmap_async` fans out to simultaneously. This is the primary protection against 429 responses on free-tier APIs.

### Ticker extraction

Tickers are extracted from headline + summary text using the regex `(?<!\w)\$?([A-Z]{2,5})(?!\w)`. The minimum length of 2 characters eliminates single-letter false positives (`A`, `I`). Matches are filtered against a 55-entry deny-list covering common English words and financial abbreviations (`CEO`, `IPO`, `ETF`, `FED`, `GDP`, `EBITDA`, timezone codes, and more).

---

## Logging

This module uses Python's standard `logging` with logger name `news_ingestion`. It **never calls `logging.basicConfig()`** — configuring the root logger is the caller's responsibility (see Python logging HOWTO).

To enable output in your application or script:

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
```

| Level | What you see |
|---|---|
| `INFO` | Per-source item counts, dedup summary (`30 raw → 22 unique`), cache set |
| `WARNING` | Missing API keys, HTTP retries, network errors, per-source fetch failures |
| `ERROR` | Unexpected exceptions from fetcher coroutines |
| `DEBUG` | Per-item skip reasons (no headline / no URL / no date), datetime parse failures, cache hits and expiry |

---

## Event loop guide

| Calling context | Correct call |
|---|---|
| Script / CLI / Django view | `fetch_market_heatmap([...])` |
| FastAPI route handler | `await fetch_market_heatmap_async([...])` |
| Jupyter notebook | `await fetch_market_heatmap_async([...])` |
| Any `async def` function | `await fetch_market_heatmap_async([...])` |

**Why `fetch_market_heatmap` cannot be called from a running event loop:**

`asyncio.run()` creates a new event loop and blocks the calling thread until the coroutine completes. Calling it from inside an already-running loop (FastAPI, Jupyter, or any `async def`) raises:

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

A common workaround — `loop.run_until_complete(...)` — raises the same error differently:

```
RuntimeError: This event loop is already running
```

The correct solution is `await fetch_market_heatmap_async(...)`. There is no synchronous shortcut from inside a running event loop that does not involve third-party hacks like `nest_asyncio`.

---

## Free tier limits

| Source | Free tier cap | Behaviour when exceeded |
|---|---|---|
| Finnhub | 60 req/min | 429 → retried with backoff |
| Marketaux | 100 req/day | 429 → retried with backoff, then source skipped for that symbol |
| Yahoo Finance RSS | Unlimited (public feed) | — |
| CNBC RSS | Unlimited (public feed) | — |
| yfinance | Unofficial scraper | May break without notice on Yahoo-side changes |

For large heatmap scans (50+ symbols), Marketaux's 100 req/day free quota will exhaust quickly. Consider relying on Finnhub + RSS for high-volume scans and reserving Marketaux for its entity-level ticker tagging where precision matters.

---

## Tunable constants

Module-level constants can be overridden at import time:

```python
from datetime import timedelta
import news_ingestion

news_ingestion.DEFAULT_LOOKBACK_DAYS       = 14    # default: 7
news_ingestion.DEFAULT_TIMEOUT             = 20.0  # default: 12.0  (seconds)
news_ingestion.MAX_RESULTS_PER_SOURCE      = 50    # default: 25
news_ingestion.DEDUP_SIMILARITY_THRESHOLD  = 0.90  # default: 0.85  (higher = stricter, fewer merges)
news_ingestion.DEDUP_TIME_WINDOW           = timedelta(hours=24)  # default: timedelta(hours=48)
news_ingestion.CACHE_TTL                   = 600.0 # default: 300.0 (seconds)
```
