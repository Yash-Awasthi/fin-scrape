# FinScrape Roadmap

> 2-year strategic plan: from financial news scraper to autonomous market intelligence platform.

**[Back to README.md](README.md)**

---

## Vision

FinScrape starts as a news scraper but ends as an **autonomous market intelligence system** — one that doesn't just tell you what happened, but simulates how different types of investors would react, predicts cascading market effects, and eventually acts on high-confidence signals. The end state is a platform where AI agents with different investment philosophies debate market events and produce consensus-weighted trading signals.

---

## Phase 1: Foundation Overhaul (Q2 2026)

*Goal: Replace the prototype with production-grade architecture and multi-source scraping.*

### Architecture Rebuild
- [x] Consolidate `src/`, `backend/`, and `aiwebscrape/` into a single unified `finscrape/` package
- [x] Define proper data models with dataclasses for events, signals, and verdicts
- [x] Implement a plugin-based scraper system — add new sources without touching core pipeline
- [x] Build internal scraping engine (`finscrape/engine/`) — zero external framework dependencies
- [x] Vendor Scrapling v0.4.6 source code (lxml, curl_cffi, patchright, browserforge, orjson)
- [x] Replace JSON file storage with SQLite for proper querying, indexing, and historical analysis
- [x] Add structured logging with context (source, ticker, pipeline stage)
- [x] Centralized config system — all tunable parameters via environment variables
- [x] Write test suite (112 tests — models, storage, validator, config, sessions, selectors)
- [x] Set up CI/CD with GitHub Actions (lint, test, type-check)

### Internal Scraping Engine
- [x] `Fetcher` — curl_cffi with TLS fingerprint impersonation, browserforge headers
- [x] `StealthyFetcher` — patchright with Cloudflare Turnstile solver, fingerprint normalization
- [x] `DynamicFetcher` — patchright for JS-heavy pages with network idle detection
- [x] Unified `Response`/`Selector` API with CSS/XPath selectors across all fetchers
- [x] Implement session management for sites requiring cookies/auth
- [x] Add adaptive selector tracking — survive site redesigns without code changes

### Multi-Source Scraping (11 sources)
- [x] Yahoo Finance (HTTP + RSS)
- [x] Bloomberg (stealth browser mode)
- [x] Reuters (stealth browser mode)
- [x] CNBC (HTTP scraper)
- [x] Generic RSS engine for any financial feed
- [x] Seeking Alpha (stealth browser mode)
- [x] MarketWatch (HTTP listing + stealth articles)
- [x] Benzinga (HTTP scraper)
- [x] Investing.com (HTTP scraper)
- [x] Financial Times (stealth browser mode)
- [x] SEC EDGAR (8-K filings via full-text search API)

### Investment Verdict System
- [x] Implement clear verdict categories: INVEST, PULL_OUT, OBSERVE, CAUTIOUS
- [x] Score normalization across different event types
- [x] Divergence penalty system — reduce confidence when AI and heuristics disagree
- [x] Dual AI backend support (OpenAI-compatible proxy + OpenRouter)
- [x] Confidence-weighted verdict aggregation when multiple articles cover the same event

---

## Phase 2: Intelligence Layer (Q3 2026)

*Goal: Go beyond extraction — understand context, track entities, and monitor in real-time.*

### Advanced NLP Pipeline
- [x] spaCy NER pipeline for high-precision company/person/org extraction
- [x] Entity disambiguation — "Apple" the company vs. "apple" in agriculture news
- [ ] Coreference resolution — link pronouns and references to correct entities
- [x] Relationship extraction — who acquired whom, who invested in what
- [x] Temporal extraction — parse dates, quarters, fiscal years from unstructured text
- [ ] Custom financial NER model fine-tuned on SEC filings and earnings transcripts

### Real-Time Monitoring Engine
- [x] Continuous scraping loop with configurable intervals per source
- [x] WebSocket-based event stream for real-time signal delivery
- [x] Rate limiting and backoff per domain (built into engine)
- [x] Deduplication across sources with headline similarity + entity overlap
- [x] Breaking news detection — identify stories appearing across 3+ sources within minutes

### Portfolio Tracking
- [x] Watchlist management — track specific tickers and get prioritized signals
- [x] Portfolio position awareness — weight signals by your actual holdings
- [x] Sector/industry grouping — roll up signals to sector-level views
- [x] Historical signal accuracy tracking — did our verdicts predict correctly? (AccuracyTracker with outcome checking)

### Alert System
- [ ] Discord bot for real-time signal alerts
- [x] Telegram notifications with configurable filters (bot with /subscribe, /status, /latest, /portfolio, /watchlists commands)
- [x] Email digests (daily/weekly summary of top signals via Resend proxy)
- [ ] Slack integration for team-based monitoring
- [x] Custom alert rules — "notify me when any FAANG stock gets PULL_OUT verdict" (AlertEngine with presets)

---

## Phase 3: Multi-Agent AI Council (Q4 2026)

*Goal: Replace single-model analysis with multi-agent deliberation. Different AI "personas" debate each event.*

### Agent Architecture
- [x] **Analyst Agent** — deep event extraction, entity linking, impact analysis (weight 1.5)
- [x] **Contrarian Agent** — deliberately challenges the consensus, finds counterarguments (weight 1.0)
- [x] **Risk Agent** — evaluates downside scenarios, tail risks, contagion effects (weight 1.2)
- [x] **Momentum Agent** — short-term sentiment and catalyst focus (weight 0.8)
- [x] **Fundamentals Agent** — long-term business value and earnings quality (weight 1.0)
- [x] Agent communication protocol — ThreadPoolExecutor parallel deliberation with structured AgentVerdict
- [x] Consensus scoring — weighted agreement across agents produces final CouncilVerdict
- [x] **Scout Agent** — source reliability, novelty detection, clickbait filtering (weight 0.7)
- [x] **Reviewer Agent** — cross-checks claims, information completeness, market pricing (weight 1.4)

### Market Persona Simulation
- [x] **The Institutional Whale** — high capital, risk-averse, long-term horizon, focuses on fundamentals (weight 1.3)
- [x] **The Retail Day Trader** — low capital, high risk tolerance, momentum-driven (weight 0.6)
- [x] **The Contrarian** — bets against market overreactions, looks for mean reversion (weight 0.9)
- [x] **The Quant** — purely data-driven, ignores narrative, focuses on statistical patterns (weight 1.1)
- [x] **The ESG Investor** — weighs environmental, social, governance factors heavily (weight 0.7)
- [x] Each persona produces independent verdicts → aggregate into "market consensus"
- [x] Divergence between personas = high uncertainty signal

### LLM Infrastructure
- [x] Multi-model support — run the same prompt through DeepSeek, Claude, GPT, Llama (MultiModelClient with ThreadPoolExecutor)
- [x] Model agreement scoring — higher confidence when models agree (consensus scoring with confidence ±adjustment)
- [ ] Local model option via Ollama for sensitive data / cost reduction
- [ ] Prompt versioning and A/B testing framework
- [x] Response caching with LRU + TTL to reduce API costs (SHA256 key, configurable via env vars)

---

## Phase 4: Alternative Data & Social Sentiment (H1 2027)

*Goal: Go beyond news articles. Incorporate social media, insider trading data, options flow, and macroeconomic indicators.*

### Social Sentiment Engine
- [x] Twitter/X financial sentiment scraping (FinTwit) — planned
- [x] Reddit sentiment analysis (r/wallstreetbets, r/investing, r/stocks) — RedditSentimentScraper with bot detection
- [x] StockTwits integration — StockTwitsScraper with native sentiment labels
- [x] Sentiment aggregation with bot/spam filtering — SentimentAggregator with platform weights
- [ ] Influencer tracking — weight opinions by historical accuracy
- [ ] Viral detection — identify rapidly spreading narratives before they move markets

### Alternative Data Sources
- [x] SEC EDGAR deep integration — parse 10-K, 10-Q, 8-K, DEF 14A, 13-F filings (FilingFetcher + FilingParser)
- [x] Insider trading tracker (SEC Form 4) — InsiderTracker with unusual activity detection
- [ ] Options flow analysis — unusual options activity as leading indicator
- [ ] Earnings call transcript analysis — tone, language changes, hedge words
- [ ] Patent filings — track innovation signals
- [ ] Job postings — hiring surges/freezes as leading indicators
- [ ] Satellite data proxies — foot traffic, shipping activity (via public APIs)
- [ ] App store rankings — consumer product momentum

### Macroeconomic Layer
- [ ] Fed Funds rate tracking and impact modeling
- [ ] CPI/PPI/employment data integration
- [ ] Yield curve analysis
- [ ] Currency correlation signals
- [ ] Commodity price feeds
- [ ] Geopolitical risk scoring

### Cross-Asset Correlation Engine
- [ ] Detect when news about Company A historically moves Company B
- [ ] Sector rotation signals — money flowing out of tech into healthcare
- [ ] Supply chain mapping — if a supplier gets hit, flag downstream companies
- [ ] Competitor impact modeling — good news for AAPL may be bad news for SMSN

---

## Phase 5: Autonomous Trading Signals (H2 2027)

*Goal: From "here's what happened" to "here's what to do about it" — with paper trading validation.*

### Signal Generation Engine
- [ ] Composite signal scoring: news + social + alternative data + technicals
- [ ] Entry/exit point suggestions with confidence intervals
- [ ] Position sizing recommendations based on signal strength and portfolio context
- [ ] Multi-timeframe signals — day trade vs. swing vs. long-term hold
- [ ] Sector allocation recommendations
- [ ] Risk-adjusted return projections

### Paper Trading & Backtesting
- [ ] Paper trading engine — simulate trades based on historical signals
- [ ] Backtesting framework — run signals against historical market data
- [ ] Sharpe ratio, max drawdown, win rate tracking
- [ ] Signal decay analysis — how quickly do our signals lose alpha?
- [ ] Monte Carlo simulation for portfolio stress testing
- [ ] Benchmark comparison — are we beating SPY?

### Trading Platform Integration
- [ ] Alpaca API integration (paper + live)
- [ ] Interactive Brokers bridge
- [ ] Human-in-the-loop mandatory for live orders above configurable threshold
- [ ] Order book aware execution — avoid moving the market on small-cap trades
- [ ] Portfolio rebalancing recommendations

### Risk Management
- [ ] Maximum position size limits per ticker and sector
- [ ] Drawdown circuit breaker — pause trading if portfolio drops X%
- [ ] Correlation-aware position sizing — don't over-concentrate in correlated bets
- [ ] Volatility-adjusted signals — scale position size inversely with VIX
- [ ] Black swan detection — identify when models are likely unreliable

---

## Phase 6: Platform & API (2028)

*Goal: Open FinScrape as a platform. Others build on top of it.*

### REST API
- [ ] Public API for signal access (free tier + paid)
- [ ] WebSocket streaming API for real-time signals
- [ ] Webhook system — push signals to user-defined endpoints
- [ ] API key management and rate limiting
- [ ] OpenAPI spec and auto-generated docs

### Web Dashboard
- [x] Real-time signal feed with filtering and search (Cloudflare Workers + React Router 7 + Durable Objects)
- [ ] Portfolio tracker with P&L visualization
- [ ] Signal accuracy leaderboard — which sources/agents are most accurate?
- [ ] Custom watchlist with configurable alert thresholds
- [ ] Historical signal explorer with backtest charts

### Plugin Ecosystem
- [ ] Scraper plugins — community-contributed source scrapers
- [ ] Analysis plugins — custom scoring models
- [ ] Alert plugins — new notification channels
- [ ] Trading plugins — additional broker integrations
- [ ] Plugin marketplace and versioning

### Global Market Coverage
- [ ] European markets (LSE, Euronext, XETRA)
- [ ] Asian markets (TSE, HKEX, SSE, BSE/NSE)
- [ ] Crypto markets (BTC, ETH, top 50 by market cap)
- [ ] Forex signals for major pairs
- [ ] Commodity-specific news tracking (oil, gold, agricultural)
- [ ] Multi-language article processing (Chinese, Japanese, Hindi, German)

### Institutional Features
- [ ] Multi-user access with role-based permissions
- [ ] Audit trail for all signal generation and trading decisions
- [ ] Compliance reporting — MiFID II, SEC record-keeping
- [ ] Custom model training on proprietary data
- [ ] On-premise deployment option
- [ ] SLA-backed uptime guarantees

---

## Milestone Summary

| Quarter | Milestone | Metric |
|:--------|:----------|:-------|
| Q2 2026 | Multi-source scraping with internal engine | 8+ news sources active |
| Q3 2026 | Real-time monitoring + alerts | < 5 min latency from publish to signal |
| Q4 2026 | Multi-agent AI council | 5+ AI personas generating independent verdicts |
| Q1 2027 | Social sentiment integration | Twitter + Reddit + StockTwits live |
| Q2 2027 | Alternative data (SEC, options, insider) | 10+ alternative data sources |
| Q3 2027 | Paper trading validation | 6-month backtest with positive Sharpe ratio |
| Q4 2027 | Live trading integration | Alpaca + IB connected with safety rails |
| Q1 2028 | Public API launch | Beta users on free tier |
| Q2 2028 | Web dashboard | Full-featured UI with portfolio tracking |
| H2 2028 | Global markets + institutional | Multi-market, multi-language coverage |

---

## Principles

1. **Accuracy over speed** — A wrong signal is worse than a late one. Always validate.
2. **Hybrid intelligence** — AI + heuristics + human review. No single point of failure.
3. **Transparency** — Every verdict must be explainable. Show the reasoning chain.
4. **Safety first** — Human-in-the-loop for any real money decisions. Paper trade first.
5. **Open core** — Core engine stays open source. Premium features fund development.

---

> This is a living document. Priorities will shift as the market and technology evolve.
