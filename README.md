# FinScrape

AI-powered financial news intelligence engine with a real-time dashboard. Scrapes 11+ news sources with stealth anti-bot bypass, runs AI inference to extract market signals, and produces actionable investment verdicts — all streamed to a live web dashboard.

```
News Sources → Stealth Scraping → AI Analysis → Heuristic Validation → Live Dashboard
     11+          Anti-bot           LLM +           200+ keywords       Real-time
   sources       Cloudflare       Multi-Agent        Divergence         WebSocket
                  bypass           Council            Detection           Feed
```

---

## What It Does

FinScrape monitors financial news across the web, extracts structured market events, and tells you what matters:

- **Scrapes** news from 11 sources (Bloomberg, Reuters, CNBC, FT, Yahoo, Google News, etc.) with a vendored stealth engine — Cloudflare bypass, TLS fingerprinting, browser automation
- **Analyzes** articles with LLMs to extract event types, affected tickers, sentiment, and confidence
- **Validates** AI output against a 200+ keyword financial lexicon to catch hallucinations
- **Scores** each event with a hybrid signal combining AI inference, heuristic analysis, and divergence detection
- **Produces** clear investment verdicts: **INVEST**, **PULL OUT**, **OBSERVE**, **CAUTIOUS**
- **Streams** signals to a live dashboard with WebSocket updates, date navigation, sorting, and filtering
- **Alerts** via Telegram bot with configurable filters and portfolio tracking

## Live Dashboard

Real-time signal feed deployed on Cloudflare Workers with Durable Objects + SQLite:

- **Date-based pagination** — navigate by day with calendar picker
- **Sortable columns** — sort by score, confidence, or time
- **Filterable feed** — by verdict, event type, or ticker
- **AI-powered expansion** — click any row for AI summary, ticker impact analysis, and verdict reasoning
- **Auto-refresh** — 30-minute countdown timer with manual refresh
- **Deduplication** — URL and subject-based filtering prevents duplicate entries

## Quick Start

```bash
# Clone
git clone https://github.com/Yash-Awasthi/fin-scrape.git
cd fin-scrape

# Install
pip install -r requirements.txt
playwright install chromium  # Required for stealth/dynamic fetchers

# Configure
cp .env.example .env
# Add your OPENROUTER_API_KEY to .env

# Run the pipeline
python main.py

# Or push directly to the live dashboard (no AI key needed — uses heuristic scoring)
python push_to_dashboard.py
```

## Sample Output

```json
{
  "subject": "Apple beats Q1 expectations with record services revenue",
  "event_type": "earnings",
  "tickers": ["AAPL"],
  "verdict": "INVEST",
  "signal_score": 4,
  "confidence": 0.92,
  "impact_direction": "positive",
  "sources": ["yahoo", "reuters"],
  "timestamp": "2026-04-14T10:30:45Z"
}
```

---

## Architecture

```
fin-scrape/
├── main.py                    # Full pipeline entry point (AI scoring)
├── push_to_dashboard.py       # Dashboard push (heuristic scoring, no AI key needed)
├── finscrape/                 # Core package
│   ├── engine/                # Vendored Scrapling v0.4.6 engine
│   │   └── scrapling/         # Full Scrapling source (lxml, curl_cffi, patchright)
│   │       ├── parser.py      # C-speed HTML parsing (lxml + cssselect)
│   │       ├── fetchers/      # Fetcher, StealthyFetcher, DynamicFetcher
│   │       ├── engines/       # curl_cffi TLS fingerprinting, patchright stealth
│   │       └── core/          # Custom types, orjson, browserforge headers
│   ├── scrapers/              # Source-specific news scrapers
│   │   ├── yahoo.py           # Yahoo Finance
│   │   ├── bloomberg.py       # Bloomberg (stealth mode)
│   │   ├── reuters.py         # Reuters (stealth mode)
│   │   ├── cnbc.py            # CNBC
│   │   ├── marketwatch.py     # MarketWatch
│   │   ├── seekingalpha.py    # Seeking Alpha (stealth mode)
│   │   ├── benzinga.py        # Benzinga
│   │   ├── investingcom.py    # Investing.com
│   │   ├── ft.py              # Financial Times (stealth mode)
│   │   ├── google_news.py     # Google News (Scrapling-based)
│   │   └── rss.py             # Generic RSS feeds
│   ├── analysis/              # AI + heuristic processing
│   │   ├── ai_client.py       # LLM inference (OpenRouter / OpenAI proxy)
│   │   ├── validator.py       # Keyword-based validation & heuristic scoring
│   │   ├── constants.py       # Financial lexicons & weights
│   │   ├── ticker_map.py      # 200+ company name → ticker mappings
│   │   └── prompts.py         # System & analysis prompts
│   ├── edgar/                 # SEC EDGAR integration
│   │   ├── fetcher.py         # EDGAR API client (8-K, 10-K, 10-Q, Form 4)
│   │   └── parser.py          # Filing parser with insider trading detection
│   ├── models/                # Data models (dataclasses)
│   ├── pipeline.py            # Orchestration pipeline
│   ├── market_data.py         # yfinance integration
│   └── storage.py             # SQLite state persistence
├── tests/                     # Test suite (112+ tests)
├── data/                      # Runtime data (gitignored)
├── requirements.txt
└── .env.example
```

## How the Pipeline Works

### 1. Ingestion
The vendored Scrapling engine (v0.4.6) provides C-speed HTML parsing via lxml, TLS fingerprint impersonation via curl_cffi, and stealth browser automation via patchright with Cloudflare Turnstile solving. Eleven news sources supported plus Google News Business topic scraping.

### 2. AI Analysis
Articles go to an LLM (DeepSeek via OpenRouter, or any OpenAI-compatible API) with a financial extraction prompt. Returns structured JSON: event type, affected tickers, sentiment, impact score, confidence. AI-detected tickers are merged back into the event for display.

### 3. Heuristic Validation
A keyword-based scoring system independently evaluates each article against 200+ financial terms. If the AI says "positive" but the keywords say "negative" — divergence flag raised.

### 4. Signal Scoring
Final score combines:
- AI signal score (-5 to +5)
- Heuristic impact (0 to 1)
- Live market data boost (via yfinance)
- Divergence penalties

### 5. Verdict

| Score Range | Verdict | Action |
|:-----------:|:-------:|:-------|
| +3 to +5 | **INVEST** | Strong positive signal — consider buying |
| +1 to +2 | **OBSERVE** | Mildly positive — watch closely |
| -1 to +1 | **CAUTIOUS** | Mixed signals — proceed with care |
| -2 to -3 | **CAUTIOUS** | Negative trend forming |
| -4 to -5 | **PULL OUT** | Strong negative signal — consider selling |

---

## News Sources

| Source | Method | Stealth | Status |
|:-------|:-------|:-------:|:------:|
| Yahoo Finance | HTTP + RSS | No | Active |
| Bloomberg | Playwright | Yes | Active |
| Reuters | Playwright | Yes | Active |
| CNBC | HTTP + RSS | No | Active |
| MarketWatch | HTTP + Stealth | Yes | Active |
| Seeking Alpha | Playwright | Yes | Active |
| Benzinga | HTTP | No | Active |
| Investing.com | HTTP | No | Active |
| Financial Times | Playwright | Yes | Active |
| Google News | Scrapling | No | Active |
| SEC EDGAR | REST API | No | Active |

## Dashboard Architecture

The dashboard is a separate Cloudflare Workers application:

- **Frontend**: React 19 + React Router 7 (SSR) + Tailwind CSS 4 + shadcn/ui
- **Backend**: Cloudflare Workers + Durable Objects with SQLite storage
- **Real-time**: WebSocket streaming via Durable Objects + 30-min polling fallback
- **AI Analysis**: Workers AI for on-demand event analysis with caching
- **Alerts**: Telegram Bot API with `/subscribe`, `/status`, `/latest`, `/portfolio` commands
- **Deduplication**: URL-based + subject-based duplicate filtering on ingestion

### Dashboard API

| Endpoint | Method | Description |
|:---------|:------:|:------------|
| `/api/events` | POST | Ingest events (API key required) |
| `/api/events` | GET | Query events with filters, date, sort |
| `/api/stats` | GET | Dashboard statistics |
| `/api/dates` | GET | Available dates with event counts |
| `/api/ai/analyze` | GET | AI analysis for a specific event |
| `/api/ws` | WS | Real-time WebSocket stream |
| `/api/portfolio` | GET | Portfolio positions and watchlists |

## Tech Stack

- **Python 3.10+** — Core scraping and analysis engine
- **Scrapling v0.4.6** (vendored) — lxml, curl_cffi, patchright, browserforge
- **OpenRouter / OpenAI** — LLM gateway for AI analysis
- **yfinance** — Live market data
- **Cloudflare Workers** — Dashboard deployment (Durable Objects + SQLite)
- **React Router 7** — SSR frontend with shadcn/ui components
- **Telegram Bot API** — Real-time alert system

Zero external scraping framework dependencies. The engine is fully self-contained.

---

## Configuration

Create a `.env` file (or copy `.env.example`):

```bash
OPENROUTER_API_KEY=your_key    # Required for AI analysis pipeline
SERPER_API_KEY=your_key        # Optional — Google SERP news (rate-limited)
```

The `push_to_dashboard.py` script works without any API keys — it uses heuristic scoring.

## Roadmap

See **[ROADMAP.md](ROADMAP.md)** for the full strategic plan. Key milestones:

- **Q2 2026** — Multi-source scraping, internal engine, live dashboard, Telegram alerts *(Done)*
- **Q3 2026** — Real-time monitoring, NLP pipeline, portfolio tracking *(In Progress)*
- **Q4 2026** — Multi-agent AI council, market persona simulation
- **H1 2027** — Social sentiment, alternative data, autonomous trading signals
- **H2 2027** — API platform, institutional features, global market coverage

## Contributing

This project is in active development. Issues and PRs welcome.

## License

MIT
