# WorldFin — Master Execution Plan (2026-09-07)

*Written end-of-day 09-06. Everything below is pre-scoped with file paths,
acceptance checks, and ordering. Work top-down; commit per item; keep
`main.py serve` green on :8080 between items. Background jobs keep running:
news monitor (15-min), server.*

---

## 0. Session bootstrap (2 min)

- [ ] `git pull origin fresh` (concurrent session may have pushed)
- [ ] `.venv/Scripts/python.exe main.py serve` (background) → verify `:8080/api/health`
- [ ] Check `docs/WORKLOG.md` for cross-session notes; do NOT pop their stash
- [ ] Run: `.venv/Scripts/python.exe -m pytest tests/ -q` (expect ~1164 pass) — baseline

---

## PHASE A — Data & intelligence depth (the moat)

### A1. Sector heat panel (backend + frontend) — ~1h
**Why:** sector_impact data exists in events; no visualization. Bloomberg-style
sector view is table stakes and we have the data already.
- [ ] `finscrape/serve.py`: add `GET /api/sectors` — group events by
  `sector_impact` (fallback: NLP `sector` from subject text via
  `finscrape.analysis.nlp.FinancialNLP._detect_sector`), return per-sector:
  `{sector, event_count, avg_score, bull_bear_ratio, top_tickers[], last_event}`
- [ ] Same route in `server/routes/data.py` (Postgres GROUP BY, for production parity)
- [ ] `web/src/panels/panels.ts`: `SectorPanel` — grid of sector chips, sized by
  event_count, colored green→red by avg_score, click → filter signal feed
  (dispatch `worldfin:select-sector` event; SignalFeedPanel subscribes)
- [ ] Add to `PAGE_LAYOUT` band 3 (`w:4 h:4`), register in main.ts, styles
- [ ] Test: `tests/test_serve.py` — `/api/sectors` shape + non-empty with current DB

### A2. Signal feed momentum inline — ~30m
- [ ] `SignalFeedPanel.update()`: for each event, compute ticker-set ∩ top-10
  suggestion tickers; render 🔥 badge on rows mentioning surging tickers
- [ ] Needs suggestions fetched into a module-level cache: fetch once in
  `loadAll()` → `window.__wfSuggestions`, panels read from it
- [ ] Acceptance: feed rows for XOM/CVX-class surging tickers show the badge

### A3. Outcome accrual → CEIP recalibration — ~45m
**Why:** prediction quality improves only as outcomes accrue; make it automatic.
- [ ] `finscrape/accuracy.py`: verify `check_outcomes` marks `correct` using
  yfinance 5-day move; if the window is shorter, parameterize `WINDOW_DAYS=5`
- [ ] `main.py monitor`: after each cycle, run accuracy check (thread) so
  outcomes score themselves continuously overnight
- [ ] `scripts/backfill_reasoning.py` pattern → `scripts/score_outcomes.py`:
  standalone backfill for old signals (idempotent: skip already-scored)
- [ ] Frontend: PredictionPanel auto-refresh every 60s
- [ ] Acceptance: `SELECT COUNT(*), SUM(outcome IS NOT NULL) FROM signal_outcomes`
  grows; `/api/reliability` sample_size increases day over day

### A4. Second-order effects view — ~1.5h
**Why:** README promises second-order chains; events already store
`second_order_effects[]` from the LLM but nothing renders them.
- [ ] `/api/events` already returns them — check local `_event_row` JSON-decodes
  the column (add to the decode list if missing)
- [ ] Modal: render second-order effects as a chain list (⚡ icon per hop)
- [ ] Feed rows: show `→n` badge when n>0 effects exist
- [ ] Prompt-side: verify `finscrape/analysis/prompts.py` asks for them
  (production prompt does; heuristic path doesn't — fine)

### A5. Event clustering (embeddings, local Ollama) — ~2h
**Why:** same story ×5 sources = 5 feed rows. Cluster into one storyline.
- [ ] `finscrape/analysis/embeddings.py` already exposes `embed`/`cosine`
- [ ] New `finscrape/analysis/clusters.py`: greedy clustering — embed subjects,
  group by cosine ≥ 0.75 within 48h window; cluster meta = {members, tickers ∪,
  sources ∪, avg_score, first_seen}
- [ ] `/api/storylines`: top clusters by member count × recency
- [ ] Feed: collapse cluster members under the top row (`+4 sources` expander)
- [ ] Tests: pure clustering fn with fake embeddings (no network)
- [ ] Degradation: Ollama down → clusters = singletons (feed unchanged)

---

## PHASE B — Frontend: density + interaction (the Bloomberg feel)

### B1. Right-rail inspector — ~1.5h
**Why:** clicking a signal opens a modal (jarring). Terminals use an inspector rail.
- [ ] Replace `SignalModal` with a persistent right rail (`#inspector`, 320px,
  grid-template-columns: 1fr 320px on `.app-main`)
- [ ] Selected event renders in the rail: verdict badge, score, reasoning full,
  prediction (P bar), affected entities, second-order chain, article link,
  `↻ Re-run AI analysis` (reuse modal logic, relocated)
- [ ] Mobile/narrow: rail overlays (fixed right, shadow)
- [ ] Keep modal code deleted or behind flag — no dead exports (tsc noEmit gate)

### B2. Keyboard navigation — ~1h
- [ ] `j/k` → next/prev signal in feed; `Enter` → select into inspector;
  `Esc` → clear; `1-9` → switch panel scroll targets
- [ ] Wire in `main.ts` via one keydown listener; respects input focus
  (`if ((e.target as HTMLElement).matches('input,select,textarea')) return`)
- [ ] Show hints in footer strip (`j/k navigate · ⌘K commands`)

### B3. Feed virtualization — ~45m
**Why:** 60 DOM rows × re-render on every WS push = jank as events grow.
- [ ] Simple windowing: render rows in view + 10 overscan via IntersectionObserver
  on sentinel divs; keep full array in memory
- [ ] No library — ~40 lines in SignalFeedPanel

### B4. Tape click → symbol select — ~15m
- [ ] `TickerTape.render()`: wrap items in `.tape-item[data-sym]`, click →
  dispatch `worldfin:select-symbol` (already handled by chart/sentiment/agents)

### B5. Dark/light + density toggle — ~1h
- [ ] CSS custom properties already themed; add `:root[data-density=compact]`
  (row padding 6px→3px, font 13→12px) and a `[data-theme=light]` override set
- [ ] Toggle in header, persisted localStorage `worldfin.density/theme`

---

## PHASE C — Coverage & ingestion (more signal, less noise)

### C1. RSSHub container + provider test — ~1h
- [ ] `docker-compose.yml`: add `rsshub` service (diygod/rsshub:latest, :1200)
- [ ] `main.py devtools set news_fetch rsshub --field base_url=http://localhost:1200`
- [ ] Extend `RSSHubScraper` default feeds: reuters/world, bloomberg, ft,
  economist, scmp, ndtv, timesofindia (verify routes at rsshub.app/docs)
- [ ] Add `rsshub` to monitor loop sources; acceptance: events with
  `sources LIKE 'rsshub/%'` appear within one cycle
- [ ] No docker on this machine → document; test at deploy time (render/yolo)

### C2. Earnings calendar ingestion — ~1.5h
**Why:** catalysts are the highest-actionability events; we have none.
- [ ] `finscrape/scrapers/calendar.py`: scrape Nasdaq/API earnings calendar
  (keyless endpoint `api.nasdaq.com/api/calendar/earnings` w/ browser headers
  via fastfetch; fallback: `finnhub`/`alphavantage` through dev-mode keys)
- [ ] Emit `ScrapedArticle`-shaped rows with `event_type=earnings_calendar`,
  tickers attached; pipeline gate passes them (already market-relevant)
- [ ] Frontend: CalendarPanel upgrade — dates with earnings show ticker chips
- [ ] CLI: `main.py scrape --sources calendar`

### C3. Source health panel — ~45m
**Why:** worker already tracks per-source freshness; surface it.
- [ ] `/api/sources`: from `visited_urls` GROUP BY source + last event per source
  (SQLite); production reads `source_health` table (exists in migration 0001)
- [ ] `SourceHealthPanel`: rows with status dot (fresh <2h / stale <24h / dead),
  last-seen, event count; click → filter feed by source

### C4. Geo-ingestor wiring into local loop — ~1h
**Why:** GDELT/ReliefWeb ingestors exist (`finscrape/ingestors/`) with real
lat/lon but only run in the production worker.
- [ ] `main.py scrape --sources world` → runs ingestor producers (reuse
  `worker/sources.py build_sources`), analyze via heuristic path (fast
, free),
  store with true coordinates (globe gets real points, not just HQ fallback)
- [ ] Market-relevance gate applies (quake briefs without market angle stay
  filtered); GDELT economy/quarrel events pass
- [ ] Acceptance: stored events with real lat/lon whose subjects lack country
  keywords (i.e. came from ingestors, not _derive_geo)

---

## PHASE D — Prediction & analytics upgrades

### D1. Per-ticker prediction history + calibration curve — ~1.5h
- [ ] `predictions` table (event_id, p_verdict_correct, tier, created_at) via
  the lazy-migration pattern in storage.py (`_migrate_event_columns`)
- [ ] `/api/predict/{id}` write-through on generation
- [ ] Chart overlay: diamond markers at event dates on candles (green p>.5)
- [ ] Calibration-curve panel: predicted-p buckets vs realized hit rate
  (~30 lines; absorbed reliability-diagrams has the reference math)
- [ ] PredictionPanel gains the curve; tests for the pure bucketing fn

### D2. Sentiment ensemble (lexicon + spaCy) — ~1h
- [ ] Second scorer in services/sentiment_analyzer.py: adjective/adv polarity
  near ticker mentions via spaCy; blend 60/40; API unchanged (all tests pass)
- [ ] Agreement field: both engines same sign = high conf, split = low

### D3. Alert rules UI — ~1.5h
- [ ] `/api/rules` GET/POST/DELETE on `alert_rules` (exists in SQLite+PG)
- [ ] RulesPanel: list, create (ticker, condition, channel), delete
- [ ] Pipeline-fired rules surface in the existing Alerts panel

---

## PHASE E — Production & ops

### E1. Deploy rehearsal — ~1h
- [ ] docker compose up (api, worker, postgres, rsshub) if Docker available;
  else document exact steps and defer to Render
- [ ] Run worker once against Postgres; verify /api/predict on production
  reads accuracy_outcomes correctly (E2E of insight routes)
- [ ] Fix drift found (expect env defaults, migration gaps) — small commits

### E2. Performance baseline — ~45m
- [ ] Index events(timestamp), events(verdict) in migration; EXPLAIN on
  /api/events at 10k rows
- [ ] /api/suggestions 60s TTL cache via server.cache.get_or_set
- [ ] Vite bundle audit: main <50KB gzip, globe chunk lazy (already ~2MB ok)

### E3. Security pass — ~45m
- [ ] Rate-limit /api/agents/analyze (expensive LLM endpoint): token bucket,
  10/hour/IP default, env override
- [ ] bandit -r finscrape server; triage; fix cheap items
- [ ] Confirm secrets/ stays gitignored; dev_tools.json template sanitized

---

## PHASE F — Innovations (be-first; only after A–E)

### F1. "Why this moved" — ~2h
Inspector button: fetch candles ±3d around event → LLM gets price path +
event context → 3-bullet causal narrative. `/api/explain/{id}`, cached
(ai_analysis_cache pattern). Nobody free does this end-to-end.

### F2. Scenario lab — ~3h
`what if <text>` (palette command) → embedding retrieval over historical
analog events → LLM narrates likely price paths per ticker, probabilities from
CEIP. Draws on absorbed scenario-lab + romancer (case-based reasoning).
`/api/scenario`.

### F3. Cross-market regime detection — ~2h
Comovement regimes from event clusters (A5) + quote moves: gold+oil+defense
together = war-risk regime → `regime` alerts. Generalizes the 3-source
corroboration engine to asset classes.

### F4. Telegram digest — ~1h
Daily 09:00: top-5 momentum suggestions + best-calibrated predictions via
configured bot (dev-mode alerts class). `main.py digest --telegram`.

---

## Definition of done (every item)
- pytest + vitest green; ruff clean on touched files
- serve restarted, endpoint smoke-checked on :8080
- one commit per feature, pushed to origin/fresh
- WORKLOG.md one-line update

## Short on time? Do only:
**A1 sector heat → B1 inspector rail → A5 clustering → D1 prediction
history + calibration curve.** Highest visible value per hour.
