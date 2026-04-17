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
- **AI-powered expansion** — click any row for AI summary, ticker impact analysis, and verdict reasoning (free via Workers AI)
- **Dynamic ticker detection** — AI analysis identifies tickers missed by heuristic scraping, merges into feed live
- **Background AI pipeline** — new events are auto-analyzed on ingest, results cached in SQLite
- **Auto-refresh** — 30-minute countdown timer with manual refresh, WebSocket real-time updates
- **Deduplication** — URL-based (`instr()`) and subject-based filtering prevents duplicate entries
- **Responsive design** — mobile-first with progressive column disclosure and 3D card effects
- **Telegram alerts** — subscribe to INVEST/PULL_OUT signals with `/subscribe`

**Dashboard code:** [`dashboard/`](./dashboard/) — see [`dashboard/README.md`](./dashboard/README.md) for full docs

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
├── dashboard/                 # Real-time web dashboard (Cloudflare Workers)
│   ├── app/routes/home.tsx    # Main dashboard UI
│   ├── workers/app.ts         # Worker entry + API routes + Telegram bot
│   ├── workers/signals-do.ts  # Durable Object with SQLite + WebSocket
│   └── wrangler.jsonc         # Cloudflare config
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

The dashboard lives in [`dashboard/`](./dashboard/) (full docs in [`dashboard/README.md`](./dashboard/README.md)):

- **Frontend**: React 19 + React Router 7 (SSR) + Tailwind CSS 4 + shadcn/ui
- **Backend**: Cloudflare Workers + Durable Objects with SQLite storage
- **Real-time**: WebSocket streaming via Durable Objects + 30-min polling fallback
- **AI Analysis**: Workers AI (free) for on-demand event analysis — generates summaries, ticker impacts, verdict reasoning. Cached in SQLite after first request. Background analysis on ingest via `ctx.waitUntil()`.
- **Dynamic Tickers**: AI-detected tickers merge back into the events table and appear in the feed without page reload
- **Alerts**: Telegram Bot API with `/subscribe`, `/status`, `/latest`, `/portfolio` commands
- **Deduplication**: URL-based (`instr()` SQL) + subject-based duplicate filtering on ingestion
- **Responsive**: Mobile-first with progressive column disclosure, 3D hover effects

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

---

## Deployment Guide

### System Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.10+ |
| **Node.js** | 18+ (for dashboard) |
| **Bun** | 1.0+ (package manager for dashboard) |
| **Playwright** | Chromium (for stealth scrapers) |
| **Cloudflare Account** | Free tier sufficient |

### Part 1: Deploy the Scraping Pipeline

The Python pipeline runs on any server, VPS, or locally.

```bash
# 1. Clone the repository
git clone https://github.com/Yash-Awasthi/fin-scrape.git
cd fin-scrape

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Linux/Mac
# venv\Scripts\activate    # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install browser for stealth scrapers
playwright install chromium

# 5. Configure environment
cp .env.example .env
# Edit .env — add your OPENROUTER_API_KEY
```

**Run the full AI pipeline:**
```bash
python main.py
```

**Run heuristic-only mode (no AI key needed):**
```bash
python push_to_dashboard.py
```

#### Pipeline Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | For AI mode | — | OpenRouter API key for LLM inference |
| `SERPER_API_KEY` | No | — | Google SERP API for additional news |
| `FINSCRAPE_MODEL` | No | `deepseek/deepseek-chat` | LLM model to use |
| `FINSCRAPE_AI_TEMP` | No | `0.1` | LLM temperature |
| `FINSCRAPE_AI_TIMEOUT` | No | `60` | API timeout in seconds |
| `FINSCRAPE_MAX_ARTICLES` | No | `10` | Max articles per source |
| `FINSCRAPE_MAX_AGE_HOURS` | No | `24.0` | Skip articles older than this |
| `FINSCRAPE_INVEST_THRESHOLD` | No | `3` | Score >= 3 → INVEST verdict |
| `FINSCRAPE_DEDUP_SIMILARITY` | No | `0.85` | Headline dedup similarity threshold |

### Part 2: Deploy the Dashboard

The dashboard runs on Cloudflare Workers (edge deployment, globally distributed). **Workers AI is free** and included with your Cloudflare account — no separate AI key needed.

**Prerequisites:**
- [Bun](https://bun.sh) installed (`curl -fsSL https://bun.sh/install | bash`)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/) (`bun add -g wrangler`)
- A [Cloudflare account](https://dash.cloudflare.com/sign-up) (free tier works)

```bash
# 1. Navigate to dashboard
cd dashboard

# 2. Install dependencies
bun install

# 3. Login to Cloudflare
wrangler login

# 4. Configure secrets
wrangler secret put API_KEY              # Your chosen API key for event ingestion
wrangler secret put TELEGRAM_BOT_TOKEN   # Optional: Telegram bot token

# 5. Build and deploy
bun run build
wrangler deploy
```

After deployment, Wrangler outputs your URL:
`https://finscrape-dashboard.<your-subdomain>.workers.dev`

#### What's Free on Cloudflare

| Resource | Free Allowance |
|----------|---------------|
| Worker requests | 100,000/day |
| Durable Object requests | 1,000,000/month |
| Durable Object storage | 1 GB |
| Workers AI inference | 10,000 neurons/day |
| WebSocket connections | Included |

More than sufficient for personal use. No credit card required.

#### Dashboard Environment Variables

Set in `wrangler.jsonc` under `vars` or via `wrangler secret put`:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `API_KEY` | Yes | `finscrape-default-key` | Auth key for `/api/events` POST endpoint |
| `TELEGRAM_BOT_TOKEN` | No | — | Telegram Bot API token for alerts |
| `AI_VIRTUAL_MODEL` | No | `auto` | Workers AI model route |

### Part 3: Connect Pipeline to Dashboard

Once both are deployed, point the scraper at your dashboard:

```bash
python push_to_dashboard.py \
  --url https://your-dashboard.workers.dev \
  --api-key YOUR_API_KEY
```

Or set environment variables:
```bash
export DASHBOARD_URL=https://your-dashboard.workers.dev
export DASHBOARD_API_KEY=YOUR_API_KEY
python push_to_dashboard.py
```

#### Manual Event Push (Testing)
```bash
curl -X POST https://your-dashboard.workers.dev/api/events \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [{
      "subject": "Test: Apple beats Q1 expectations",
      "verdict": "INVEST",
      "signal_score": 4,
      "confidence": 0.85,
      "event_type": "earnings",
      "tickers": ["AAPL"],
      "impact_direction": "positive",
      "heuristic_impact": 3,
      "divergence_flag": false,
      "sources": ["manual"],
      "articles": [],
      "timestamp": "2026-04-15T12:00:00Z"
    }]
  }'
```

### Part 4: Telegram Alerts (Optional)

1. Create a bot via [@BotFather](https://t.me/BotFather) on Telegram
2. Copy the bot token
3. Set it: `wrangler secret put TELEGRAM_BOT_TOKEN`
4. Register the webhook:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-dashboard.workers.dev/api/telegram"
   ```
5. Message your bot `/subscribe` to receive INVEST/PULL_OUT alerts

### Automation (Cron)

Run the scraper on a schedule:

```bash
# crontab -e
# Run every 30 minutes
*/30 * * * * cd /path/to/fin-scrape && /path/to/venv/bin/python push_to_dashboard.py >> /var/log/finscrape.log 2>&1
```

Or use systemd timers, GitHub Actions, or any task scheduler.

---

## Roadmap

See **[ROADMAP.md](ROADMAP.md)** for the full strategic plan. Key milestones:

- **Q2 2026** — Multi-source scraping, internal engine, live dashboard, Telegram alerts, AI-powered analysis *(Done)*
- **Q3 2026** — Real-time monitoring, NLP pipeline, portfolio tracking *(In Progress)*
- **Q4 2026** — Multi-agent AI council, market persona simulation
- **H1 2027** — Social sentiment, alternative data, autonomous trading signals
- **H2 2027** — API platform, institutional features, global market coverage

## Contributing

This project is in active development. Issues and PRs welcome.

## License

MIT
