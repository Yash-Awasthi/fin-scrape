# FinScrape

AI-powered financial news intelligence engine. Scrapes news from multiple sources, runs AI inference to extract market signals, and produces actionable investment verdicts.

```
News Sources → Scraping Engine → AI Analysis → Heuristic Validation → Investment Signals
```

---

## What It Does

FinScrape monitors financial news across the web, extracts structured market events, and tells you what matters:

- **Scrapes** news from Yahoo Finance, Bloomberg, Reuters, CNBC, and more with a built-in stealth scraping engine (anti-bot, Cloudflare bypass, TLS fingerprinting)
- **Analyzes** articles with LLMs to extract event types, affected tickers, sentiment, and confidence
- **Validates** AI output against a 200+ keyword financial lexicon to catch hallucinations
- **Scores** each event with a hybrid signal combining AI inference, heuristic analysis, and live market data
- **Produces** clear investment verdicts: **INVEST**, **PULL OUT**, **OBSERVE**, **CAUTIOUS**

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

# Run
python main.py
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
├── main.py                    # Entry point
├── finscrape/                 # Core package
│   ├── engine/                # Internal scraping engine (zero external deps)
│   │   ├── page.py            # Unified Page/Element with CSS selectors
│   │   ├── fetcher.py         # Fast HTTP with stealth headers + retry
│   │   ├── stealth.py         # Playwright + anti-detection (Cloudflare, etc.)
│   │   └── dynamic.py         # Playwright for JS-heavy pages
│   ├── scrapers/              # Source-specific news scrapers
│   │   ├── yahoo.py           # Yahoo Finance
│   │   ├── bloomberg.py       # Bloomberg (stealth mode)
│   │   ├── reuters.py         # Reuters
│   │   ├── cnbc.py            # CNBC
│   │   └── rss.py             # Generic RSS feeds
│   ├── analysis/              # AI + heuristic processing
│   │   ├── ai_client.py       # LLM inference (OpenRouter)
│   │   ├── validator.py       # Keyword-based validation
│   │   ├── constants.py       # Financial lexicons & weights
│   │   └── prompts.py         # System & analysis prompts
│   ├── models/                # Data models (dataclasses)
│   ├── pipeline.py            # Orchestration pipeline
│   ├── market_data.py         # yfinance integration
│   └── storage.py             # State persistence
├── data/                      # Runtime data (gitignored)
├── tests/                     # Test suite
├── requirements.txt
└── .env.example
```

## How the Pipeline Works

### 1. Ingestion
The built-in scraping engine handles anti-bot detection, Cloudflare bypasses, stealth headers, and TLS fingerprint spoofing. Three fetch modes: fast HTTP, stealth browser, and dynamic JS rendering. Each news source has a dedicated scraper.

### 2. AI Analysis
Articles go to an LLM (DeepSeek via OpenRouter) with a financial extraction prompt. Returns structured JSON: event type, affected tickers, sentiment, impact score, confidence.

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

## Configuration

Create a `.env` file (or copy `.env.example`):

```bash
OPENROUTER_API_KEY=your_key    # Required — LLM access
FINNHUB_API_KEY=optional       # Additional news source
MARKETAUX_API_KEY=optional     # Additional news source
```

## News Sources

| Source | Method | Status |
|:-------|:-------|:------:|
| Yahoo Finance | HTTP + RSS | Active |
| Bloomberg | Stealth Browser | In Progress |
| Reuters | HTTP | In Progress |
| CNBC | HTTP + RSS | In Progress |
| Finnhub API | REST API | Optional |
| MarketAux API | REST API | Optional |

## Tech Stack

- **Python 3.10+**
- **httpx** — HTTP/2 client with stealth headers
- **BeautifulSoup** — HTML parsing and CSS selectors
- **Playwright** — Browser automation for anti-bot and JS rendering
- **OpenRouter** — LLM gateway (DeepSeek, Claude, GPT)
- **yfinance** — Live market data
- **feedparser** — RSS feed parsing

Zero external scraping framework dependencies. The engine is fully self-contained.

---

## Roadmap

See **[ROADMAP.md](ROADMAP.md)** for the full 2-year plan. Key milestones:

- **Q2 2026** — Multi-source scraping, architecture overhaul, internal engine
- **Q3 2026** — Real-time monitoring, portfolio tracking, alerts
- **Q4 2026** — Multi-agent AI council, advanced NLP pipeline
- **H1 2027** — Social sentiment, alternative data, autonomous trading signals
- **H2 2027** — API platform, institutional features, global market coverage

## Contributing

This project is in active development. Issues and PRs welcome.

## License

MIT
