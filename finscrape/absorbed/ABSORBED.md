# Absorbed Features

Feature code extracted from the reference repos (inspiration/fin-scrape,
mirrored in reference/). Code only — no git history, docs, tests or build
config. Each repo lands in its domain; wiring into the real finscrape
modules happens next.

| Repo | Domain | Action | Files | Note |
|---|---|---|---|---|
| abrasio-sdk | scraping | package | 22 |  |
| advocate | security | package | 9 |  |
| ai | - | SKIPPED: npm SDK (vercel/ai); wire via npm | 0 |  |
| ai-auto-trader-ahh | trading | subtrees | 151 |  |
| ai-colosseum-debate | agents | src-layout | 94 |  |
| AI-Geopol-Projects | - | SKIPPED: prompt/project collection — knowledge source only | 0 |  |
| ai-hedge-fund | agents | subtrees | 82 |  |
| ai-investment-advisor | agents | subtrees | 1010 |  |
| ai-investment-goatlens | agents | root | 38 |  |
| ai-kline | trading | package | 5 |  |
| ai-trader | agents | subtrees | 89 |  |
| airbyte | - | SKIPPED: data platform; wire via docker/pip, not in-tree | 0 |  |
| aird | misc | subtrees | 2 |  |
| airflow | - | SKIPPED: orchestration platform; wire via pip, not in-tree | 0 |  |
| alpacatradingagent | trading | root | 217 |  |
| alphalens | quant | package | 24 |  |
| anteroom-oracle | geo | root | 19 |  |
| anti-detect-browser-tools-tech-comparison | - | SKIPPED: comparison write-up only | 0 |  |
| apscheduler | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| argus-intel | geo | root | 486 |  |
| argus-system | geo | subtrees | 9 |  |
| artha-analytics | quant | subtrees | 113 |  |
| asyncpg | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| autogen-financial-analysis | agents | root | 92 |  |
| awesome-ai-in-finance | - | SKIPPED: curated list — knowledge source only | 0 |  |
| awesome-financial-nlp | - | SKIPPED: curated list — knowledge source only | 0 |  |
| awesome-llm-judges | - | SKIPPED: curated list — knowledge source only | 0 |  |
| awesome-trading-agents | - | SKIPPED: curated list — knowledge source only | 0 |  |
| awesome-web-scraping | - | SKIPPED: curated list — knowledge source only | 0 |  |
| backtesting.py | quant | package | 13 |  |
| backtrader | quant | package | 171 |  |
| berkshire-agent-council | agents | package | 21 |  |
| bipia | security | package | 26 |  |
| broadcaster | - | SKIPPED: pip-installable WebSocket broadcast lib | 0 |  |
| browserforge | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| calibration-framework | quant | root | 92 |  |
| cameo-codebook | - | SKIPPED: codebook data — knowledge source only | 0 |  |
| canairy | geo | root | 360 |  |
| circuitbreaker | - | SKIPPED: pip-installable circuit breaker | 0 |  |
| claude-council | agents | subtrees | 2 |  |
| claude-equity-research | agents | subtrees | 4 |  |
| clearmarket | market_data | subtrees | 23 |  |
| client_python | - | SKIPPED: pip-installable Prometheus client (already via server deps) | 0 |  |
| coingecko_py | market_data | package | 21 |  |
| company_name_to_ticker | market_data | subtrees | 3 |  |
| contesttrade | agents | package | 5 |  |
| council | - | SKIPPED: Swift/Xcode iOS app — different stack | 0 |  |
| crawl4ai | scraping | package | 83 |  |
| crisismap | geo | subtrees | 62 |  |
| cryptoagents | agents | package | 6 |  |
| curl-impersonate | - | SKIPPED: native C tool; covered by curl-cffi dependency | 0 |  |
| curl_cffi | - | SKIPPED: already a pip dependency (curl-cffi) in pyproject.toml | 0 |  |
| dbt-core | - | SKIPPED: transform platform; wire via pip, not in-tree | 0 |  |
| debatrix | agents | package | 113 |  |
| dedupe | - | SKIPPED: pip-installable utility; vendor only if wiring needs it | 0 |  |
| deepear | nlp | subtrees | 49 |  |
| deepfund | agents | subtrees | 60 |  |
| dify | - | SKIPPED: LLM app platform; wire via docker, not in-tree | 0 |  |
| edgartools | market_data | subtrees | 551 |  |
| empyrical | quant | package | 16 |  |
| equibles | - | SKIPPED: C#/.NET stack — no Python/JS feature to absorb | 0 |  |
| evals | llm | package | 1243 | large (365 MB) |
| event-extraction-paper | - | SKIPPED: paper index — knowledge source only | 0 |  |
| EventExtractionPapers | - | SKIPPED: paper index — knowledge source only | 0 |  |
| fastapi_websocket_pubsub | - | SKIPPED: pip-installable pub/sub lib | 0 |  |
| fastfeedparser | scraping | src-layout | 2 |  |
| feedparser | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| fenixai_tradingbot | trading | root | 565 |  |
| finance-query | - | SKIPPED: Rust stack — no Python/JS feature to absorb | 0 |  |
| finance-skills | llm | subtrees | 122 |  |
| financemcp | market_data | subtrees | 99 |  |
| financial-analysis--multi-agent-open-source-llm | agents | root | 8 |  |
| fingpt | nlp | subtrees | 254 |  |
| FinNews-Sentiment-Stock-Correlation-Analysis | nlp | subtrees | 2 |  |
| finrobot | nlp | subtrees | 2 |  |
| fintwit-bot | social | subtrees | 119 |  |
| freqtrade | - | SKIPPED: trading bot platform; wire via pip, not in-tree | 0 |  |
| fusion-center | geo | package | 65 |  |
| gdelt-data-pipeline | gdelt | subtrees | 13 |  |
| gdelt-doc-api | gdelt | root | 15 |  |
| gdelt-events-data-eng-project | gdelt | subtrees | 91 |  |
| gdelt-pulse | gdelt | src-layout | 72 |  |
| gdelt_distributed_architecture | gdelt | package | 13 |  |
| gdeltdataacquisition | gdelt | subtrees | 2 |  |
| gdeltpyr | gdelt | subtrees | 26 |  |
| geopol-forecast-council | agents | package | 18 |  |
| geopolitics-ml | geo | subtrees | 131 |  |
| geopolrisk-py | geo | src-layout | 14 |  |
| GeoPulseWebApp | geo | subtrees | 5 |  |
| georisk-ai | geo | root | 127 |  |
| global-affairs-simulation-platform | geo | root | 118 |  |
| global-news-intel-platform | geo | root | 45 |  |
| globe.gl | - | SKIPPED: npm library; web/ already depends on it | 0 |  |
| gpr-equity-observatory | geo | src-layout | 57 |  |
| gpr-zero | geo | subtrees | 18 |  |
| helm-agents | agents | subtrees | 140 |  |
| hermes-geopolitical-market-sim | geo | subtrees | 1 |  |
| hodget | trading | subtrees | 401 |  |
| homerun | misc | subtrees | 899 |  |
| india-geopolitical-risk-monitor | geo | package | 144 |  |
| intelligent-trading-bot | trading | subtrees | 61 |  |
| invest-alert-bot | trading | package | 31 |  |
| layeredmemorytrader | trading | root | 25 |  |
| libcomcat | geo | package | 21 |  |
| live-trade-bench | trading | package | 33 |  |
| llm-deliberate | agents | package | 11 |  |
| llm_trading_sim | trading | subtrees | 185 |  |
| lumibot | trading | package | 222 |  |
| lxml | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| machine-learning-for-trading | quant | root | 1648 | large (269 MB) |
| macropulse | geo | subtrees | 12 |  |
| magi | agents | subtrees | 7 |  |
| mahoraga | geo | subtrees | 89 |  |
| manifold | market_data | root | 2910 |  |
| mats | trading | subtrees | 269 |  |
| maverick-mcp | market_data | subtrees | 237 |  |
| meltano | - | SKIPPED: ELT platform; wire via pip, not in-tree | 0 |  |
| ml-calibration | quant | src-layout | 6 |  |
| moneyfeel-macro-risk-index | geo | root | 8 |  |
| mslive_public | social | root | 7 |  |
| multi-agent-debates-langgraph | agents | root | 7 |  |
| multi-agent-investment | agents | root | 111 |  |
| multi-agent-trading-system | agents | subtrees | 1 |  |
| multi-agents-debate | agents | package | 7 |  |
| multi_agent_llm_debater | agents | subtrees | 6 |  |
| nautilus_trader | - | SKIPPED: trading platform with Rust core; wire via pip | 0 |  |
| neuberg | misc | subtrees | 1656 |  |
| news-globe | geo | subtrees | 1 |  |
| newsglobe | geo | subtrees | 23 |  |
| newspaper | scraping | package | 63 |  |
| NLP_Fnews | nlp | subtrees | 7 |  |
| octobot | - | SKIPPED: trading bot platform; wire via pip, not in-tree | 0 |  |
| ollama | - | SKIPPED: Go LLM server; wire via binary/docker | 0 |  |
| open-prompt-injection | security | package | 46 |  |
| openai-python | - | SKIPPED: pip-installable SDK | 0 |  |
| openinvest | market_data | subtrees | 4 |  |
| openmarket | - | SKIPPED: Rust stack — no Python/JS feature to absorb | 0 |  |
| opennews-mcp | market_data | src-layout | 13 |  |
| OracleX | market_data | subtrees | 405 |  |
| orallexa-ai-trading-agent | trading | root | 455 |  |
| pandas-ta-classic | quant | subtrees | 316 |  |
| pantheon-ssrf-guard | security | root | 2 |  |
| pantheon-trades | trading | subtrees | 944 |  |
| pixiu | trading | subtrees | 3 |  |
| playwright | - | SKIPPED: browser automation monorepo; wire via pip/npm (patchright dep) | 0 |  |
| powertools-lambda-python | - | SKIPPED: AWS pip library — wire via pip if needed | 0 |  |
| praw | - | SKIPPED: pip-installable Reddit client | 0 |  |
| prometheus-eval | llm | subtrees | 42 |  |
| prompt-injection-defenses | - | SKIPPED: README-only repo — knowledge source | 0 |  |
| properscoring | quant | package | 8 |  |
| purgatory | - | SKIPPED: pip-installable rate-limiter utility | 0 |  |
| py-gdelt | gdelt | src-layout | 74 |  |
| pybreaker | - | SKIPPED: pip-installable circuit breaker | 0 |  |
| pycoingecko | market_data | subtrees | 4 |  |
| pyfolio | quant | package | 53 |  |
| pyportfolioopt | quant | subtrees | 18 |  |
| pyscrappy | scraping | src-layout | 53 |  |
| python-financial-technical-indicators-pandas | quant | root | 5 |  |
| python-telegram-bot | - | SKIPPED: pip-installable Telegram client | 0 |  |
| qlib | - | SKIPPED: quant platform (Microsoft); too large, wire via pip if needed | 0 |  |
| QuantDinger | trading | subtrees | 707 |  |
| quantstats | quant | package | 14 |  |
| rapidfuzz | - | SKIPPED: pip-installable utility; vendor only if wiring needs it | 0 |  |
| react-globe.gl | - | SKIPPED: npm library; web/ already depends on it | 0 |  |
| react-router | - | SKIPPED: npm library; wire via npm | 0 |  |
| readability | scraping | subtrees | 3 |  |
| Real-Time-Financial-Analysis-Trading-System | trading | subtrees | 249 |  |
| real-time-geopolitical-instability-prediction | geo | subtrees | 6 |  |
| realpolitik | geo | subtrees | 171 |  |
| rebuff | security | subtrees | 68 |  |
| redditstocksdiscordbot | social | package | 21 |  |
| reliability-diagrams | quant | root | 25 |  |
| reliefweb-python | market_data | root | 7 |  |
| riskfolio-lib | quant | subtrees | 17 |  |
| romancer | agents | subtrees | 40 |  |
| safeurl-python | security | package | 3 |  |
| scenario-lab | geo | subtrees | 11 |  |
| scrapling | - | SKIPPED: already vendored at finscrape/engine/scrapling | 0 |  |
| scrapy | - | SKIPPED: scraping framework; wire via pip, not in-tree | 0 |  |
| sec-edgar-downloader | market_data | subtrees | 9 |  |
| sec-edgar-mcp | market_data | package | 17 |  |
| SeleniumBase | - | SKIPPED: browser testing framework; wire via pip | 0 |  |
| sentiment-analysis-in-event-driven-stock-price-movement-prediction | nlp | package | 8 |  |
| sentinel | geo | root | 21 |  |
| situation-monitor | geo | root | 6 |  |
| snowglobe | llm | subtrees | 36 |  |
| spacy | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| stock-market-news-sentiment-analysis-and-summarization | nlp | subtrees | 3 |  |
| Stock-News-Analysis-with-BERT | nlp | package | 4 |  |
| stocktwits-sentiment | social | root | 5 |  |
| supplychain | geo | subtrees | 53 |  |
| ta | quant | package | 8 |  |
| ta-lib-python | quant | subtrees | 15 |  |
| taiwan-situation | geo | root | 7 |  |
| talipp | quant | package | 68 |  |
| tensionr | geo | src-layout | 33 |  |
| terra-watch | geo | subtrees | 392 |  |
| three-globe | - | SKIPPED: npm library; web/ already depends on it | 0 |  |
| three-js | - | SKIPPED: npm library; wire via npm | 0 |  |
| tickertick-api | - | SKIPPED: skill/docs-only repo — knowledge source | 0 |  |
| trading-agents | agents | subtrees | 71 |  |
| tradingagents-ashare | agents | root | 202 |  |
| tradingagents-astock | agents | root | 143 |  |
| tradingagents-mcpmode | agents | package | 114 |  |
| trafilatura | scraping | package | 23 |  |
| trendradar | geo | package | 54 |  |
| unified-marco-markets | market_data | subtrees | 201 |  |
| valuecell | agents | subtrees | 580 |  |
| verdict | llm | package | 29 |  |
| war-probability-osint | geo | root | 20 |  |
| watchboard | geo | subtrees | 8560 |  |
| world-intel-mcp | geo | src-layout | 106 |  |
| world-monitor | geo | subtrees | 21 |  |
| worldmonitor | geo | subtrees | 28 |  |
| worldview-intelligence | geo | root | 46 |  |
| yfinance | - | SKIPPED: already a pip dependency in pyproject.toml | 0 |  |
| yt-dlp | - | SKIPPED: media downloader; wire via pip | 0 |  |
| zipline | - | SKIPPED: legacy quant platform; wire via pip if needed | 0 |  |
