# WorldFin — Worklog (agent continuity)

*Concurrent sessions work this repo. Commit small, commit often, never reset.
A stash (`multi_model` removal WIP) belongs to another session — leave it.*

## State (2026-09-06, night run)

- Branch `fresh`, everything pushed through `7d0ad042`.
- Local server: `main.py serve` → http://127.0.0.1:8080 (SQLite backend, Ollama AI).
- **Known concurrent session**: left a stash (multi_model removal WIP) + PLAN.md
  housekeeping commit (604ec19, dangling). Do not pop the stash; do not reset.

## Done this run

- 159-repo absorption committed; FEATURES/ABSORBED/UPSTREAM manifests in-tree.
- Global exchanges (28) + keyless China adapters; quotes CLI + API.
- Local server `serve.py` (SQLite): events/stats/dates/correlations/accuracy/
  sentiment/portfolio/quotes/candles/agents-analyze + static SPA + WS.
- Dev-mode tool registry (27 verified channels, any-tool classes).
- NLP: SEC 10k resolution, blended sentiment, relevance gate; storage schema
  migration (reasoning/lat/lon/...); trafilatura enrichment; fastfetch anti-bot.
- Frontend: single-page deterministic layout, ticker tape, Markets Live,
  watchlist, News Lobby, candles chart, agent-analysis panel, auto-AI modal,
  27-channel Live TV with country filter.
- Reasoning backfill: 28/28 events carry LLM reasoning.
- All work pushed to origin/fresh.

## In progress / next (pick up here)

1. **Calibrated Event-Impact Probability (CEIP)** — `finscrape/prediction.py`:
   reliability tables from signal_outcomes (per verdict/source/event_type,
   confidence buckets, recency decay) → calibrated P(move) per event.
   Endpoints /api/predict/{id} + /api/reliability; frontend gauge + diagram.
   NOTE: current 96 outcomes are heuristic-era with 0% hit-rate — encode
   source/verdict reliability honestly (low weight for heuristic verdicts).
2. Outcome backfill: score pending signal_outcomes vs yfinance prices
   (`main.py accuracy check`) — run in background, expands calibration data.
3. Frontend: feed filters (verdict/ticker), volume bars + SMA20 in chart,
   wire ⌘K palette (search events, "chart X", "analyze X").
4. Continuous ingestion: `FINSCRAPE_HEURISTIC_FALLBACK=1 main.py monitor
   --sources rss google_news --interval 600` in background.
5. RSSHub as a dev-mode news_fetch provider (thousands of feeds free).
