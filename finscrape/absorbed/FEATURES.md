# Absorbed Features — what each reference repo contributes

Reference code lives in `finscrape/absorbed/<domain>/<repo>/` — core source only,
no git history, docs or tests. Upstream URLs for every repo are recorded in
[`UPSTREAM_MANIFEST.md`](UPSTREAM_MANIFEST.md) (copied from the inspiration
collection's MANIFEST.md before that folder was retired). Mechanical details
(what was copied, file counts) are in [`ABSORBED.md`](ABSORBED.md).

Wiring rule of thumb: absorbed code is vendored material — import it, distill it,
or lift the pattern into the real `finscrape` modules, then delete what you don't keep.

---

## geo — geopolitical risk & world monitoring (38)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `geopolrisk-py` | Geopolitical Risk (GPR) index computation pipeline following the academic GPR methodology (event weights → country risk series) | `src/geopolitical_risk.py` upgrade path |
| `gpr-zero` | GPR index from scratch: ingestion → scoring → analysis scripts | same |
| `gpr-equity-observatory` | Monitoring GPR vs equity-sector performance | accuracy / dashboard analytics |
| `geopolitics-ml` | ML models over geopolitical datasets (WEF study code) | risk model reference |
| `india-geopolitical-risk-monitor` | Country-specific GPR monitor (India) | regional specialization example |
| `real-time-geopolitical-instability-prediction` | Real-time instability prediction models | ML risk model in analysis/ |
| `war-probability-osint` | OSINT-driven conflict probability estimation | event scoring methodology |
| `anteroom-oracle` | Oracle brain: correlation engine, crisis replay, regime detector, news brain, sanity validator | `server/correlate.py` + regime detection — highly relevant, read first |
| `tensionr` | Tension scoring between state pairs | event tension scoring |
| `trendradar` | TrendRadar: keyword-alert hot-news aggregator (multi-source, Telegram push) | trend alerting feature |
| `scenario-lab` | Scenario simulation lab with adapter pattern | scenario generation for second-order impact |
| `global-affairs-simulation-platform` | Global affairs simulation platform | simulation reference |
| `hermes-geopolitical-market-sim` | Geopolitical → market simulation harness | backtest simulation |
| `supplychain` | Supply-chain disruption world simulation (Next.js) | second-order impact modeling |
| `moneyfeel-macro-risk-index` | Macro risk index construction | macro indicator set |
| `macropulse` | Macro news pulse scoring | macro event scoring |
| `canairy` | Climate/geohazard monitoring app | monitor UI patterns |
| `sentinel` | Intel sentinel dashboard | monitor reference |
| `situation-monitor` | Situation monitoring dashboards | monitor reference |
| `watchboard` | Self-hosted event watchboard with 60MB+ of tracker configs for many sources | tracker config pattern for `worker/sources.py` |
| `worldview-intelligence` | World intel dashboard | dashboard reference |
| `world-intel-mcp` | MCP server exposing world-intel APIs to agents | agent tool |
| `world-monitor` | World event monitor (Convex backend, event data model) | data modeling reference |
| `worldmonitor` | World monitor variant (Convex + API) | reference |
| `newsglobe` | Next.js news globe (globe.gl components) | `web/` globe components |
| `news-globe` | Single-file news globe page | minimal globe embed |
| `GeoPulseWebApp` | Streamlit geo-pulse dashboard | quick dashboard reference |
| `argus-intel` | Argus intel platform | platform reference |
| `argus-system` | Argus monitoring system | reference |
| `fusion-center` | Multi-source intel fusion center | data fusion reference |
| `crisismap` | Crisis mapping app (Next.js) | map UI reference |
| `realpolitik` | Geopolitics news reader (Next.js) | UI reference |
| `taiwan-situation` | Taiwan-strait situation tracker | regional tracker example |
| `terra-watch` | CesiumJS-based 3D globe intel viewer | alternative to globe.gl |
| `libcomcat` | USGS earthquake catalog library | keyless natural-event source (USGS) |
| `mahoraga` | Geopolitical event impact dashboard (TS, Cloudflare) | impact-scoring UI reference |
| `OracleX` | Crypto/stock "lens" with MCP server + agent-skill packaging | agent-skill packaging pattern (market_data domain) |

## agents — councils, debates, trading agents (29)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `trading-agents` | TauricResearch TradingAgents: analyst team → bull/bear researcher debate → risk debate → PM decision. The flagship agent architecture | `finscrape/agents/` + `src/trading_agents.py` — primary reference |
| `tradingagents-ashare` | TradingAgents adapted to China A-shares (data adapters) | localized data adapters |
| `tradingagents-astock` | TradingAgents A-stock variant | same |
| `tradingagents-mcpmode` | TradingAgents with MCP tool calls | MCP tool integration |
| `ai-hedge-fund` | virattt's investor-persona agents (Buffett, Burry…) with financial-facts feeding and backtest | persona library for council |
| `ai-trader` | HKUDS AI-Trader: autonomous trader with skills/tool use + news ingestion | skills/tool design |
| `ai-colosseum-debate` | LLM debate arena producing verdicts | debate mechanics |
| `ai-investment-advisor` | FastAPI investment advisor service | API shape reference |
| `ai-investment-goatlens` | Multi-agent investment "lens" analysis | agent roles |
| `autogen-financial-analysis` | AutoGen-based financial analysis teams | AutoGen orchestration patterns |
| `financial-analysis--multi-agent-open-source-llm` | Multi-agent analysis on open-source LLMs | prompt library |
| `berkshire-agent-council` | Warren/Munger persona council | persona prompts |
| `claude-council` | Parallel Claude perspectives + synthesis workflow (JS) | council orchestration script |
| `claude-equity-research` | Claude plugin: equity research command workflows | command/skill design |
| `debatrix` | Debate evaluation/judging framework | judge metrics for `agents/judge.py` |
| `deepfund` | HKUSTDial DeepFund: tool-calling analyst agents + fund benchmark | evaluation harness |
| `contesttrade` | Trading-agent competition arena | benchmark design |
| `cryptoagents` | Multi-agent crypto fund analysis | crypto personas |
| `llm-deliberate` | Structured multi-LLM deliberation with consensus/dissent tracking | deliberation pattern |
| `multi-agent-debates-langgraph` | LangGraph debate graph | graph orchestration |
| `multi-agent-investment` | Investment discussion agents | prompts |
| `multi-agent-trading-system` | Notebook-built multi-agent trading pipeline | educational walkthrough |
| `multi-agents-debate` | Classic MAD: debate improves factuality/reasoning | debate theory + code |
| `multi_agent_llm_debater` | Socratic-circle debate with prompt sets | prompt patterns |
| `geopol-forecast-council` | Prompt-framework council for geopolitical forecasting | forecast council design |
| `magi` | MAGI council: LLMs vote, threshold agreement decides | agreement-threshold council logic |
| `romancer` | RAND ROMANCER: case-based reasoning for scenario forecasting | forecast-by-analogy feature |
| `helm-agents` | Agent evaluation harness (multi-app monorepo) | eval harness reference |
| `valuecell` | ValueCell open-source AI investment platform (agents + portfolio + UI) | app architecture reference |

## quant — backtesting, metrics, optimization, indicators (19)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `backtesting.py` | Vectorized backtester with rich charts (`backtesting/`) | council-signal backtesting |
| `backtrader` | Event-driven backtest engine (`backtrader/`) | alternative engine |
| `alphalens` | Factor analysis tear sheets | signal-as-factor evaluation |
| `empyrical` | Sharpe/Sortino/max-drawdown metric library | `finscrape/accuracy.py` metric extension |
| `pyfolio` | Portfolio analytics tear sheets | reporting |
| `quantstats` | Portfolio stats + HTML reports | equity-curve reporting |
| `pyportfolioopt` | Portfolio optimization (MVO, HRP, risk parity) (`pypfopt/`) | position sizing |
| `riskfolio-lib` | Advanced portfolio optimization (`riskfolio/`) | alternative optimizer |
| `ta` | Pandas technical-indicator library (`ta/`) | indicator computation for market_facts |
| `ta-lib-python` | TA-Lib wrapper (`talib/`, needs native C lib) | indicators if C lib available |
| `pandas-ta-classic` | 130+ pure-pandas indicators (`pandas_ta_classic/`) | dependency-light indicators |
| `talipp` | Incremental/streaming indicators | live-quote indicator updates |
| `properscoring` | Proper scoring rules (Brier, CRPS) | calibration scoring |
| `reliability-diagrams` | Reliability-diagram plotting | confidence calibration plots |
| `ml-calibration` | Apple's calibration methods library | calibration methods |
| `calibration-framework` | EFS calibration framework | alternative calibration |
| `python-financial-technical-indicators-pandas` | Vectorized MyTT-style indicator math | fast indicator formulas |
| `machine-learning-for-trading` | ML-for-trading course code | educational reference |
| `artha-analytics` | Artha analytics platform (backend + frontend) | dashboard reference |

## trading — bots, execution, benchmarks (17)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `QuantDinger` | Multi-market quant trading platform (stocks/crypto/futures) | bot architecture reference |
| `Real-Time-Financial-Analysis-Trading-System` | Microservice decomposition: ingest → stream → signal → notify → viz | service topology reference |
| `ai-auto-trader-ahh` | Auto-trader web app incl. strategy JSON configs | strategy config schema |
| `ai-kline` | AI candlestick (K-line) chart analysis | chart-reading prompts |
| `alpacatradingagent` | Alpaca broker LLM trading agent | broker execution adapter (roadmap Phase 16) |
| `fenixai_tradingbot` | ML trading bot with risk module | risk module reference |
| `intelligent-trading-bot` | Signal generation + Telegram notification bot | signal/alert engine |
| `invest-alert-bot` | Personal invest alert bot | alert rules |
| `layeredmemorytrader` | Layered memory (episodic/semantic) for trading agents | agent memory design |
| `live-trade-bench` | Live-trading benchmark for LLM agents | evaluation harness |
| `llm_trading_sim` | LLM trading simulator + parameter sweeps | council simulation |
| `lumibot` | Lumiwealth bot framework with broker integrations (Alpaca/IBKR) | execution layer candidate |
| `orallexa-ai-trading-agent` | AI trading agent app | reference |
| `pantheon-trades` | Trade journal/analytics | trade logging schema |
| `mats` | Terminal trading-ops agent + PNL multiplier planning | ops-agent design |
| `hodget` | Hedge-fund JS monorepo (apps + packages) | UI component reference |
| `pixiu` | FinAI PIXIU financial LLM benchmark (notebooks; FinMem lives in an unfetched submodule — clone upstream if needed) | benchmark tasks |

## market_data — price, filings, prediction markets (15)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `edgartools` | Pythonic SEC EDGAR API: filings, company facts (`edgar/`) | `finscrape/edgar/` deepening |
| `sec-edgar-downloader` | Bulk SEC filing downloads by ticker/CIK (`sec_edgar_downloader/`) | filing archival jobs |
| `sec-edgar-mcp` | MCP server over SEC EDGAR | agent tool |
| `pycoingecko` | CoinGecko API client (`pycoingecko/`) | crypto quotes |
| `coingecko_py` | CoinGecko client with rate-limit handling | alternative client — keep one |
| `reliefweb-python` | ReliefWeb humanitarian/disaster API client (`reliefweb/`) | keyless disaster-event source |
| `financemcp` | MCP server aggregating financial data | agent tool |
| `opennews-mcp` | MCP server for news data | agent tool |
| `maverick-mcp` | MCP server: TA + stock screening | agent tool |
| `manifold` | Manifold prediction-markets platform | market-probability signal via API |
| `openinvest` | Financial data provider connectors (`connectors/`) | provider adapters |
| `clearmarket` | Prediction-market resolution/canonicalization toolchain | forecast-resolution benchmarking |
| `unified-marco-markets` | MARCO markets aggregation backend | market aggregation reference |
| `company_name_to_ticker` | SEC company→ticker JSON maps + matcher script | direct feed for `finscrape/entity_map.py` / `data/` |
| `OracleX` | (see geo) | — |

## gdelt — GDELT ingestion pipelines (8)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `py-gdelt` | GDELT 2.0 events/graphs → pandas (`gdelt/`) | primary GDELT ingester |
| `gdeltpyr` | gdeltPyR: parallel/async GDELT pulls (`gdelt/`, `utils/`) | alternative fetcher |
| `gdelt-doc-api` | GDELT DOC 2.0 full-text article search API wrapper | article backfill search |
| `gdelt-data-pipeline` | dbt + airflow GDELT warehouse modeling | table modeling for our GDELT store |
| `gdelt-events-data-eng-project` | Mage-based GDELT events pipeline | pipeline reference |
| `gdelt-pulse` | FastAPI service over GDELT trends | API shape reference |
| `gdelt_distributed_architecture` | Distributed GDELT acquisition design | architecture reference |
| `gdeltdataacquisition` | GDELT acquisition scripts (`src/`) | reference |

## nlp — financial NLP & sentiment (8)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `fingpt` | FinGPT: open financial LLMs — sentiment/headline classifiers + LoRA training (`fingpt/`) | sentiment model candidates |
| `finrobot` | FinRobot: AutoGen-based financial agent platform + FinNLP utils (`FinNLP/`) | agent design + NLP utils |
| `deepear` | HKUSTDial DeepEar: deep-research audio/news intelligence app (`src/`, `skills/`) | skills pattern |
| `FinNews-Sentiment-Stock-Correlation-Analysis` | Sentiment ↔ stock correlation study notebooks | analysis methodology |
| `NLP_Fnews` | Finance-news LLM fine-tuning notebooks (LLaMA3) | training reference |
| `Stock-News-Analysis-with-BERT` | BERT headline sentiment classification | baseline model |
| `sentiment-analysis-in-event-driven-stock-price-movement-prediction` | Event-driven price-movement prediction from sentiment | methodology + feature engineering |
| `stock-market-news-sentiment-analysis-and-summarization` | News sentiment + summarization pipeline + labeled dataset (stock_news.csv) | dataset + summarization prompts |

## social — Reddit / StockTwits / X (4)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `mslive_public` | MarketSentiment live: Reddit/Twitter streams, ticker counting, live sentiment | social ingestion patterns |
| `stocktwits-sentiment` | StockTwits sentiment pipeline (ML) | StockTwits feature |
| `fintwit-bot` | Fintwit digest bot with influence scoring | account scoring reference |
| `redditstocksdiscordbot` | Reddit ticker-mention → Discord alerts | alert channel reference |

## scraping — crawling & extraction (7)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `crawl4ai` | LLM-oriented async crawler producing clean markdown/structured output (`crawl4ai/`) | stealth-fetch layer alternative |
| `newspaper` | News article extraction (title/text/summary) (`newspaper/`) | article body extraction |
| `trafilatura` | Best-in-class main-content extraction + metadata (`trafilatura/`) | primary text extractor |
| `readability` | Mozilla Readability.js (DOM reader-mode extraction) | JS-side extraction fallback |
| `fastfeedparser` | Fast RSS/Atom/JSON-Feed parser (`fastfeedparser/`) | RSS ingestion upgrade over feedparser |
| `pyscrappy` | Scraping utility library | utility reference |
| `abrasio-sdk` | SDK for the Abrasio scraping service | optional provider adapter |

## security — SSRF & prompt-injection defenses (6)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `advocate` | AdBlock-style WebView-proxy SSRF protection (`advocate/`) | fetch URL guard — compare with `server/ssrf.py` |
| `safeurl-python` | SSRF-safe URL validation (`safeurl/`) | alternative guard |
| `rebuff` | Prompt-injection detection API + Python SDK (`python-sdk/`, `server/`) | injection defense for scraped content |
| `open-prompt-injection` | Prompt-injection research toolkit | attack corpus for tests |
| `bipia` | Microsoft BIPIA: indirect prompt-injection benchmark | defense eval benchmark |
| `pantheon-ssrf-guard` | SSRF guard middleware | compare with `server/ssrf.py` |

## llm — judging & evaluation (5)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `evals` | OpenAI evals framework (`evals/`) | council prompt eval harness |
| `prometheus-eval` | Prometheus open judge model + eval lib (`eval/`, `libs/`) | judge-model candidate |
| `verdict` | Composable LLM judging library | judge patterns |
| `snowglobe` | Multi-agent LLM simulation sandbox (`src/`, `config/`) | agent simulation |
| `finance-skills` | Finance agent skill plugins (`plugins/`, `opencli-plugins/`) | skill definitions |

## misc — to classify at wiring time (3)

| Repo | Feature it implements | Wire into |
|---|---|---|
| `aird` | Small single-script utility (`run.py`) — low confidence, review before using | triage |
| `homerun` | Backend/tools app with agent docs — review before using | triage |
| `neuberg` | JS client/server app — review before using | triage |

---

## Skipped on purpose (code lives only upstream)

These were **not** absorbed — the reason and how to get the feature back:

**Already pip dependencies (wired via pyproject.toml — nothing to copy):**
`yfinance`, `feedparser`, `spacy`, `curl_cffi`, `browserforge`, `lxml`, `asyncpg`,
`apscheduler`, `rapidfuzz`, `dedupe`, `praw`, `python-telegram-bot`, `broadcaster`,
`fastapi_websocket_pubsub`, `pybreaker`, `circuitbreaker`, `client_python`,
`purgatory`, `openai-python`

**Already vendored:** `scrapling` → `finscrape/engine/scrapling`

**Platforms — install, never vendor:** `airbyte`, `airflow`, `dbt-core`, `meltano`,
`dify`, `ollama`, `scrapy`, `playwright`, `SeleniumBase`/`seleniumbase`, `yt-dlp`,
`qlib`, `nautilus_trader`, `freqtrade`, `octobot`, `zipline`, `curl-impersonate`

**npm libraries — web/ already consumes them:** `ai` (vercel), `globe.gl`,
`react-globe.gl`, `three-globe`, `three-js`, `react-router`

**Knowledge-only (no code to absorb):** the five `awesome-*` lists,
`EventExtractionPapers`, `event-extraction-paper`, `cameo-codebook`,
`anti-detect-browser-tools-tech-comparison`, `AI-Geopol-Projects`,
`prompt-injection-defenses` (README-only), `tickertick-api` (skill docs)

**Different stack:** `equibles` (.NET), `council` (Swift/iOS), `finance-query` (Rust),
`openmarket` (Rust)

---

## Safety statement — inspiration/ folder can be deleted

- Every repo that was slated for absorption was verified extracted (coverage check
  run before deletion: 159/159 destination trees non-empty; 0 review leftovers).
- Everything skipped is recoverable independently: pip/npm packages by installing
  them; all other repos are public GitHub clones re-obtainable via the URLs in
  [`UPSTREAM_MANIFEST.md`](UPSTREAM_MANIFEST.md).
- The only thing deleting `inspiration/fin-scrape` loses permanently is git history
  of the clones and files deliberately excluded here (docs, tests, examples,
  notebooks of some repos) — all non-essential for wiring.
