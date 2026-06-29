# FinScrape / WorldFin — Master Plan & Living Spec

> **This is the single source of truth.** It merges the long-horizon strategic
> [roadmap](#part-iii--long-horizon-roadmap-the-2-year-arc) (formerly `ROADMAP.md`) with the
> concrete near-term [build plan](#part-ii--active-build-track-worldfin-dashboard) for the
> WorldFin global market-intelligence dashboard (formerly `WORLDFIN_PLAN.md`). It is a *living*
> document: phases carry checkboxes, and every work session leaves a checkpoint in
> [`progress/`](progress/) so work survives context limits, top-ups, and restarts.

---

## ⚡ READ THIS FIRST — Every new session

Do these **before** writing any new code or plan. They cost a minute and save a restart.

1. **Resume from the latest checkpoint.** Open the highest-numbered file in
   [`progress/`](progress/) (e.g. `progress/progress-007.md`). It tells you exactly what is
   done, what is mid-flight, what is next, and which commands/files to pick up. Then skim this
   `PLAN.md` for the phase you are on. **Never re-derive state from scratch** — that is the whole
   reason this system exists.
2. **Tidy git history (squash WIP → meaningful commits).** Before new work, look at the recent
   commits and the working tree:
   ```bash
   git log --oneline -15
   git status --short
   ```
   Squash throwaway/`fixup`/`wip`/`tmp` commits into the coherent commit they belong to, so the
   history reads as a sequence of *useful* changes (one logical change per commit, imperative
   subject, conventional `feat:`/`fix:`/`docs:` prefix). Use an interactive rebase **only on
   un-pushed local commits** — never rewrite commits already pushed/merged to `master` or shared
   branches. If everything is already pushed, leave it and just commit cleanly going forward.
   *(Interactive `-i` rebases are not available inside the agent harness — when squashing is
   needed, either do it with explicit non-interactive `git rebase --onto` / `git reset --soft`
   sequences, or tell the user the exact `git rebase -i` command to run themselves via `! ...`.)*
3. **Confirm the green baseline.** `make test` / `pytest` (112 tests) must pass before you build
   on top. A red baseline means fix that first — do not stack new work on broken ground.
4. **At the end of the session (or when a top-up / context limit looms): write a new
   checkpoint.** See [Checkpoint protocol](#-checkpoint-protocol). This is mandatory, not
   optional — an un-checkpointed session is a session you will have to reconstruct.

---

## How to use this document

- **Status legend** (used on every phase header and milestone):
  - `(done)` / `[x]` — shipped, verified, tests green.
  - `(in progress)` / `[~]` — started, not yet verified-green.
  - `[ ]` — not started.
  - `(blocked: …)` — cannot proceed; reason noted inline.
- **Mark items as you go.** Tick the checkbox *and* update the phase header suffix. A phase is
  only `(done)` when its **Verify** step passes.
- **Two tracks run in parallel conceptually but are sequenced in practice:**
  - **Part II — Active build track (WorldFin):** the immediate, deal-quality product. Phases 0→11,
    each ending *green* (typechecks + tests + a runnable verification). This is what you work on now.
  - **Part III — Long-horizon roadmap:** the 2-year arc (intelligence layer → multi-agent council
    → alt-data → autonomous signals → platform). Much of Phase 1 here is *already done* (it is the
    existing `finscrape/` brain); the rest is post-WorldFin.
- The two tracks share one brain: `finscrape/`'s LLM contract + data model already implement
  event→entity→judge→second-order→signal. WorldFin builds the *body*; the roadmap deepens the *mind*.

---

## 📌 Checkpoint protocol

The point: any session can be interrupted (top-up, context limit, crash) and the next one resumes
in under five minutes with zero lost reasoning.

**Where:** the [`progress/`](progress/) directory. See [`progress/README.md`](progress/README.md)
for the full spec; the short version:

- Files are named **`progress-NNN.md`** (zero-padded, monotonically increasing: `progress-000.md`,
  `progress-001.md`, …). **Highest number = latest = read this one first.**
- `progress/TEMPLATE.md` is the canonical shape. Copy it for each new checkpoint.
- **When to write one:**
  - End of a work session.
  - When you sense a top-up / context truncation coming (don't wait — write it early).
  - After completing a phase or a meaningful sub-milestone.
- **What goes in one** (full schema in the template): date; phase pointer; what got done this
  session (with file paths + commit SHAs); what is mid-flight and exactly where you stopped; the
  *next 1–3 concrete actions*; open questions/decisions pending; resume commands (the literal
  shell/workflow lines to run); and links to any scratch output files.
- **Never edit old checkpoints** — they are an append-only ledger. Correct course in the *next*
  checkpoint, not by rewriting history.
- **Keep PLAN.md checkboxes and the latest checkpoint consistent** — the checkpoint is the
  narrative; PLAN.md is the state. They must agree.

---

# Part I — Vision & context

## Vision

FinScrape starts as a news scraper but ends as an **autonomous market-intelligence system** — one
that doesn't just report what happened, but resolves *which* tickers/companies/sectors an event
moves, judges the first- and second-order market impact, simulates how different investor archetypes
would react, and eventually surfaces consensus-weighted, accuracy-proven signals. The end state is a
platform where AI agents with distinct investment philosophies debate market events and produce
trustworthy, explainable calls — over geopolitics *and* finance, on a live globe, with the receipts
to prove the calls were right.

**WorldFin** is the near-term embodiment of that vision: a fresh, **worldmonitor.app-style** global
intelligence dashboard, built to demo to a company as a deal-quality product (not an MVP). Its thesis:

> ingest **geopolitics + world news** → resolve **which tickers/companies/sectors** the event moves
> → **judge** the market impact (first- and second-order) → show it on a live globe + panels → and
> **prove the calls were right** over time.

## Where we are today (the asset we're building on)

`fin-scrape` today is **two things**:

1. **A mature Python intelligence pipeline (~3k LOC, 112 passing tests, CI):** 11 stealth news
   scrapers on a vendored Scrapling engine, LLM event extraction, a heuristic validator, a
   multi-agent council, market personas, SEC EDGAR, Reddit/StockTwits sentiment, accuracy
   backtesting, Telegram alerts, portfolio tracking.
2. **A Cloudflare Workers + React dashboard** (the existing `dashboard/`). Its live deploy has
   visible defects — rows duplicated ~4×, stat/feed count mismatch, timezone drift — all
   symptomatic of the Workers/D1 split-storage design and ingest-only dedup. WorldFin replaces this
   with a Postgres-backed FastAPI service that fixes those bugs **at the root** (see
   [Appendix B](#appendix-b--api-contract--root-cause-bug-fixes)).

**The single most important scoping fact:** the LLM contract
(`finscrape/analysis/prompts.py`) and data model (`finscrape/models/events.py`) **already implement
the exact flow** WorldFin needs — event extraction → `affected_entities` (role-tagged:
primary/competitor/supplier/regulator/analyst/customer + per-entity impact) → `second_order_effects`
→ `signal_score` (-5..+5) → `verdict`, with a `geopolitical_event` type already defined. **The brain
exists.** WorldFin builds the **body** (portable backend, world data, a real frontend) and the
**trust layer** (accuracy proof, health, observability) around it.

## Locked decisions (WorldFin)

- **Frontend:** vanilla TypeScript + Vite SPA, panel-grid model like worldmonitor (no React).
- **Backend:** Python **FastAPI + Postgres** (asyncpg), dockerized. Reuses `finscrape/` directly.
- **LLM:** **BYOK** — use a supplied OpenRouter/OpenAI key if present, else default to local
  **Ollama** (Qwen2.5). `finscrape/analysis/ai_client.py` already supports both via env.
- **Deploy:** Docker Compose, local first (cloud later). Built so cloud is a config change, not a rewrite.
- **Auth:** none in v1 (architecture leaves a clean seam for it).
- **License:** worldmonitor is **AGPL-3.0** → we **never fork or vendor its source**. We copy only
  *non-copyrightable facts* (feed URLs, country/crypto JSON) and *reimplement* algorithms
  (correlation, clustering) in our own code. fin-scrape stays MIT.

## ✅ Open investigations — ALL RESOLVED during the build

These were owed by an early deep-dive workflow. Every one landed:

1. **[x] Postgres DDL** — `server/migrations/0001_init.sql` (events + 5 aux tables, JSONB cols,
   `content_hash UNIQUE`, lat/lon, GIN+btree indexes; TIMESTAMPTZ; one half-open `[day,day+1)`). Phase 0.
2. **[x] Backend stack micro-choices** — confirmed: asyncpg + raw-SQL versioned migrations + APScheduler
   + `asyncio.to_thread` for blocking finscrape work + Redis only as the cross-process WS seam (Phase 12).
3. **[x] Risk register + dependency graph + effort sizing** — `docs/RISKS.md` (Phase 0).
4. **[x] feeds / geocode / live-TV detail** — `finscrape/scrapers/world/feeds.py` (14-feed registry),
   `server/geocode.py` (country-centroid table), `web/src/data/channels.ts` (live-TV iframes).
5. **(closed: won't-do) glint.trade** — Google-auth gated, no public docs; worldmonitor remained the
   working reference. Not needed; not revisited.

---

# Part II — Active build track: WorldFin dashboard

> Each phase ends **green**: typechecks, tests, and a runnable verification pass. **No phase leaves
> a stub for "later".** Order is chosen so there is a demoable slice early, then depth. Tick boxes as
> you complete items; a phase is `(done)` only when its **Verify** passes and tests are green.

## Target architecture

```
                                  docker compose
┌────────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐    APScheduler     ┌────────────────────────────────────┐ │
│  │  worker      │  (continuous loop)  │            Postgres                 │ │
│  │ finscrape    │ ──────────────────▶ │  events · correlations · runs ·     │ │
│  │ + world RSS  │   scrape→analyze    │  source_health · accuracy · ai_cache│ │
│  │ + free APIs  │   →judge→correlate  └──────────────┬─────────────────────┘ │
│  └──────┬───────┘        ▲ LLM (Ollama|BYOK)         │ asyncpg pool          │
│         │ writes         │                            │                       │
│         └────────────────┘              ┌─────────────▼──────────────┐        │
│                                         │  api (FastAPI, Uvicorn)     │        │
│   ┌───────────┐  optional               │  REST + WS + SSE            │        │
│   │  ollama   │◀── LLM if no key         │  /api/events /stats /dates  │        │
│   └───────────┘                          │  /correlations /accuracy    │        │
│   ┌───────────┐                          │  /rss-proxy  /health        │        │
│   │  redis    │◀── cache + rate-limit    │  WS /ws                     │        │
│   │ (optional)│    + WS fan-out          └─────────────┬───────────────┘        │
│   └───────────┘                                        │ fetch / WS             │
│                                          ┌─────────────▼──────────────┐        │
│                                          │  web (Vite SPA → nginx)     │        │
│                                          │  globe.gl + panel grid      │        │
│                                          └─────────────────────────────┘        │
└────────────────────────────────────────────────────────────────────────────┘
   Observability: structured JSON logs (reuse finscrape/logging_config.py) →
   /metrics (Prometheus) ; optional Grafana + Loki compose profile.
```

Services: `postgres`, `redis`(optional), `api`, `worker`, `web`, `ollama`(profile). Optional
`grafana`+`prometheus` profile for the observability demo.

## Repo layout (target)

```
fin-scrape/
├── finscrape/                 # EXISTING — reused, lightly extended
│   ├── scrapers/world/        # NEW thin RSS-backed world/geopolitics scrapers
│   ├── ingestors/             # NEW keyless API pullers (usgs, gdelt, reliefweb, coingecko, opensky)
│   └── analysis/prompts.py    # widen system-prompt scope finance→world
├── server/                    # NEW FastAPI service
│   ├── main.py  app.py        # ASGI app, lifespan, route mounting
│   ├── db.py  migrations/     # asyncpg pool; SQL migrations (yoyo or raw, versioned)
│   ├── routes/                # events, stats, correlations, accuracy, rss_proxy, ai, health
│   ├── ingest.py              # FinEvent→PG, dedup (content-hash), upsert
│   ├── correlate.py           # clustering + cross-source correlation (Python port)
│   ├── geocode.py             # event→lat/long via country/entity → bbox
│   ├── ws.py                  # WS hub (+ Redis pub/sub fan-out if enabled)
│   ├── cache.py rate_limit.py security.py settings.py(pydantic-settings)
│   └── metrics.py             # Prometheus exporters
├── web/                       # NEW Vite vanilla-TS SPA
│   ├── src/{main.ts, app/, panels/, globe/, components/, data/, api.ts, ws.ts, state.ts, i18n/}
│   ├── public/  index.html  vite.config.ts  tsconfig.json
│   └── Dockerfile (multi-stage → nginx)
├── docker-compose.yml  docker-compose.obs.yml
├── Dockerfile.api  Dockerfile.worker
├── .env.example  Makefile  README (deploy + demo script)
├── PLAN.md  progress/         # this plan + checkpoint ledger
└── docs/ (ARCHITECTURE.md, RUNBOOK.md, DEMO.md, SECURITY.md, DATA_SOURCES.md)
```

---

## Phases 0–11 — WorldFin v1 build track  `[x]` (done, shipped on `master`)

> Collapsed for readability — each phase shipped *green* (typechecks + tests + a runnable verify) and
> is one logical commit in git history; the narrative lives in `progress/`. Full original specs are in
> git history of this file. Phase **12** below is the active phase.

- **Phase 0 — Foundations & contracts** `[x]` — dockerized skeleton; pydantic-settings; asyncpg pool +
  versioned SQL migrations; schema (`events` + `correlations`/`scrape_runs`/`source_health`/
  `accuracy_outcomes`/`ai_analysis_cache`); Pydantic API contract; `docs/RISKS.md`.
- **Phase 1 — Backend API** `[x]` — `POST/GET /api/events` with deterministic `content_hash` dedup;
  `stats`/`dates`/feed share **one** UTC day-bounds; `/api/ai/analyze`; WS hub. Killed the live ~4× dup +
  count-mismatch + tz drift at the root (Appendix B).
- **Phase 2 — World data ingestion** `[x]` — `finscrape/scrapers/world/` feed registry + keyless
  ingestors (USGS/GDELT/ReliefWeb/CoinGecko/OpenSky); world-widened LLM prompt; `server/geocode.py`.
- **Phase 3 — Worker orchestration** `[x]` — APScheduler worker; `source_health` + `scrape_runs`;
  `/api/health` with read-time STALE derivation; a flaky source degrades to WARN, never crashes.
- **Phase 4 — Correlation engine** `[x]` — Python port of WM `analysis-core.ts`: Jaccard clustering +
  convergence/triangulation/divergence detectors; `/api/correlations`; worker post-scrape pass.
  *(`find_news_for_market_symbol` stubbed → Phase 12.)*
- **Phase 5 — Frontend foundation** `[x]` — vanilla-TS SPA shell; `globe.gl` wrapper; panel base +
  layout manager (persist/drag); typed `api`/`ws`/`state`; SignalFeed + Modal.
- **Phase 6 — Panels** `[x]` — Globe, Correlation, BreakingNews, Crypto, Calendar, WorldNews, LiveTV,
  Markets panels; `server/routes/data.py` (SSRF-guarded rss-proxy); World/Finance/Crypto variants.
  *(SentimentPanel + live price quotes deferred.)*
- **Phase 7 — Trust layer** `[x]` — `/api/accuracy` + AccuracyPanel (hit-rate, by-verdict, equity
  curve); injectable backtest; `/api/ai/council` explainability (flag-gated).
- **Phase 8 — Hardening** `[x]` — per-IP rate limit; CORS allowlist; SSRF guard; CSP/security headers;
  tiered cache + ETag/304; circuit breaker; `/health`+`/ready`; `docs/SECURITY.md`.
- **Phase 9 — Observability** `[x]` — JSON logs + correlation/request IDs; Prometheus `/metrics` (9
  `worldfin_*` families); `docker-compose.obs.yml` (Prometheus+Grafana+Loki); RUNBOOK + DATA_SOURCES.
- **Phase 10 — Quality gates, CI/CD** `[x]` — 5-job CI (python/web/e2e/images/security); multi-stage
  non-root images; **scoped pyright** gate (`server/`+`worker/`).
- **Phase 11 — Demo polish** `[x]` — `make seed` (curated dataset) + `make demo` + `docs/DEMO.md`; the
  dashboard is full of signal on first launch, no API key needed to tour.

## Phase 12 — Live intelligence: entity→ticker resolution + continuous worker operation  `[x]`

*Goal: turn the **seeded** demo into a **self-populating live** product. Fixed the one gap that broke
the core thesis on live geopolitics headlines — **entity→ticker resolution** — and de-risked the worker's
yfinance hot-path. Before this phase a geopolitics headline resolved role-tagged `affected_entities` with
**empty ticker fields**, so `_analyze_article` dropped it at "No valid tickers found"; the same gap stubbed
`explained_market_move`. Fixed live with qwen2.5:7b.*

### A. Entity→ticker resolution (the core fix)
- [x] **`finscrape/entity_map.py` + `finscrape/data/entity_index.json`** — a standalone, data-driven
      sector/region→ticker map (oil/shipping/defense/semis/cyber/pharma/crypto/… + geopolitics triggers
      Hormuz/Taiwan/Red Sea/Iran/Russia/…). `resolve_tickers(text)` (word-boundary/phrase match) is added
      to the pipeline ticker fusion (`finscrape/pipeline.py`), so a world headline that names a sector/region
      but no company still resolves tickers and **survives the gate**. *(Chosen over seeding the SQLite
      `StateManager` index, whose `resolve_entity_tickers` also requires the company name in-text — too
      strict for geopolitics. This also makes the NLP-fallback item moot: sector tickers enter via fusion.)*
- [x] **Prompt few-shots** (`finscrape/analysis/prompts.py`): a filled geopolitics→symbols worked example
      (Hormuz → XOM/CVX/RTX/ZIM) + imitation list (Taiwan→TSM/NVDA, Red Sea→FDX/UPS/ZIM, OPEC→XOM/OXY).
      **Schema unchanged.** Best-effort nudge; the entity_map is the robust path.
- [x] **Port `find_news_for_market_symbol`** (`server/correlate.py`) → entity-aware via
      `entity_map.keywords_for_ticker` (reverse map) → unblocks **`explained_market_move`**. Worker's
      `run_correlations` now also feeds **market moves** (top recent tickers → `get_market_data`) so
      `detect_market` actually runs (was never passed markets before).
- [x] **Verify (A) — live (qwen2.5:7b):** the Hormuz extraction now **survives the gate** with **14 tickers**
      (XOM/CVX/SHEL/COP/OXY/SLB + RTX/LMT/NOC/GD + FDX/UPS/ZIM/MATX), verdict PULL_OUT; the orchestrator
      emits `explained_market_move` on a news-backed move. Unit tests in `tests/server/test_phase12.py`.

### B. Worker live operation
- [x] **Market-data TTL cache** (`finscrape/market_data.py`): per-process cache (`FINSCRAPE_MARKET_TTL`,
      default 600s) + single batched `yf.download`; only missing/stale tickers refetched; degrades to `{}`
      on error so a slow/dead yfinance never crashes the cycle. Kills the per-article hot-path (RISKS R1).
- [x] **Live worker cycle end-to-end** (verified bounded run vs podman PG): USGS scrape → `_analyze_article`
      (LLM) → entity_map tickers → geocode → ingest (**26 geo events landed**) → correlate (snapshot seeded)
      → `source_health` OK + `scrape_runs` recorded. The APScheduler continuous loop (Phase 3) drives this.
- [x] **Cross-process new-event push:** Redis pub/sub seam wired (`server/pubsub.py`, lazy-imported + gated
      on `settings.redis_enabled`): worker `run_source` publishes `new_events`; API lifespan subscribes and
      forwards to the WS hub. No-op (worker silent to clients) when Redis is off → single-process needs no Redis.

- [x] **Phase Verify:** live Hormuz headline → tickered, geolocated, survives gate (was `event=None` in
      017); `explained_market_move` fires; live worker cycle ingests geo events; **684 pass**; ruff + fmt
      + pyright 0; full `make ci` green (python + web + e2e).

> **Env-deferred (not code):** live **yfinance** market fetch (Yahoo unreachable in this sandbox) → so
> `explained_market_move` over *real* market moves + the accuracy backtest from live prices await a
> network-enabled host; verified instead with injected moves. Live **cross-process WS** render needs the
> Redis profile up (seam + no-op path unit-tested). Stronger model (OpenRouter `deepseek-chat`/qwen2.5:14b+)
> emits symbols more reliably than 7B. **Breadth parked for later:** SentimentPanel, live `/api/markets`
> price quotes, portfolio/telegram routes, prompt A/B (see checkpoint 020 backlog).

## Phase 13 — Breadth: sentiment, portfolio, alerts, prompt A/B + freshness audit  `[x]`

*Goal: widen the product surface by surfacing finscrape capabilities that already exist but
weren't wired into WorldFin, and audit that live news is actually fresh. Each reuses a finscrape
module behind a thin route + (where useful) a panel.*

- [x] **SentimentPanel + `GET /api/sentiment?ticker=`** (`server/routes/sentiment.py`): reuses
      `finscrape.sentiment.SentimentAggregator` (Reddit + StockTwits). Blocking scrape runs in a
      threadpool, behind a **circuit breaker** + MEDIUM TTL cache; any upstream failure (timeout,
      rate-limit, open breaker) **degrades to an empty result** — never an error. `SentimentPanel`
      (ticker input → score + bull/bear + top posts) in `web/src/panels/panels.ts`.
- [x] **Portfolio/watchlist routes + PortfolioPanel** (`server/routes/portfolio.py`): `GET /api/portfolio`,
      `POST/DELETE /api/portfolio/position`, `POST/DELETE /api/portfolio/watchlist` (mutations auth'd)
      reusing `finscrape.portfolio.PortfolioManager` (SQLite at `<WORLDFIN_DATA_DIR>/portfolio.db`,
      module singleton). `PortfolioPanel` lists positions + watchlists + summary.
- [x] **Telegram webhook** (`server/routes/telegram.py`): `POST /api/telegram/webhook` **always 200**,
      command handling (`/subscribe /unsubscribe /status /latest /help`) off the request path
      (BackgroundTasks); subscribers persist to `<data_dir>/telegram_subs.json`. Outbound INVEST/PULL_OUT
      alerts (`notify_new_events`, finscrape alert message format) wired into the ingest path on
      `insertedIds`. **No-ops gracefully without `TELEGRAM_BOT_TOKEN`.**
- [x] **Prompt versioning + A/B** (`finscrape/analysis/prompt_registry.py`): v1 (current) + v2
      (conservative-calibration) variants; **opt-in** via `WORLDFIN_PROMPT_AB` (off → always v1, zero
      behaviour change). Deterministic per-article assignment (title hash); variant stamped into
      `key_metrics["prompt_variant"]` (no migration); the AI cache keys on prompt text so v1/v2 never
      collide. `GET /api/accuracy/by-variant` compares realized hit-rate per variant.
- [x] **Verify (live vs podman PG):** portfolio CRUD ✓; telegram webhook → `{"ok":true}` ✓; sentiment →
      200 + graceful empty (Reddit/StockTwits blocked in sandbox) ✓; **`/api/accuracy/by-variant` →
      `v1: 0.9 (10) · v2: 1.0 (1)`** ✓. 8 new unit tests; **692 pass**; ruff + fmt + pyright 0; full
      `make ci` green (python + web tsc/Vitest 10 + e2e 3).
- [x] **Freshness audit (item 6):** **13/14 world feeds reachable + carrying fresh items**; wire feeds
      (Reuters/AP) 15/15 & 9/9 ≤24h; `WorldRSSScraper` yielded **40 articles, all ≤24h — the 24h
      freshness gate holds** (no stale leaked). USGS 108 events. *(CSIS feed empty → replace later;
      finance scrapers use the 2h `FINSCRAPE_MAX_AGE_HOURS` window, world uses 24h by design.)*

> **Env-deferred (not code):** live social-sentiment data (Reddit/StockTwits rate-limited/blocked in
> this sandbox — endpoint + degrade verified); live Telegram send (needs a bot token — format + no-op
> path tested); panel on-screen render (Playwright covers the mocked path; new panels show in the
> Finance/Crypto variants).

---

## WorldFin master verification (acceptance for the company demo)

Verified across Phases 7/11/12/13 + the checkpoint-019 live sweep (against postgres:16 via podman +
local Ollama qwen2.5:7b). Items marked **(env)** are verified to the limit of this sandbox; the residue
is environmental (no docker daemon / Yahoo + Reddit + GDELT network-blocked / no browser display), not a
code gap.

1. [x] **(env)** `make seed` → fully-populated dashboard; endpoints all serve signal. *(Clean-clone
   `make demo` via `docker compose` is CI-validated; live bring-up here used podman `--network host`.)*
2. [x] Worker ingests world + finance end-to-end (bounded live cycle: 26 geo events); `/api/health`
   aggregates source freshness; APScheduler drives the continuous loop. *(Multi-cycle 24×7 run = ops.)*
3. [x] **(env)** globe plots geolocated events by verdict; breaking-correlation banner + WS live-update —
   rendered headless in Playwright (3 E2E specs green). *(On-screen browser visual = a `make up` pass.)*
4. [x] Click a **geopolitical** event → resolved affected tickers/sectors (Hormuz → 14 tickers, survives
   the gate) → judged impact + second-order + **council via `/api/ai/council` (live LLM)**.
5. [x] AccuracyPanel proves hit-rate + equity curve (`/api/accuracy` → 0.9, 10/12 + curve).
6. [x] Crypto/Markets/News/Live-TV/**Sentiment** panels wired; variant switch (World/Finance/Crypto)
   works. *(Sentiment/crypto live data depends on reachable upstreams; endpoints degrade gracefully.)*
7. [x] **(env)** `make ci` green: ruff + **pyright** + pytest (**692**) + web typecheck + Vitest(10) +
   Playwright(3) + image build + security scan. *(Grafana/Loki obs dashboard live-check = obs overlay up.)*

**Bottom line:** every acceptance item is met in code + verified to the limit of this environment. The
only residue is environment-bound (live cloud/browser/3rd-party-network), not unfinished work.

## Reuse map (build on these, don't reinvent)

| Capability | Action | Source |
|---|---|---|
| event→entity→judge LLM contract | reuse; widen prompt scope | `finscrape/analysis/prompts.py`, `ai_client.py` |
| BYOK / Ollama dual backend | reuse as-is | `finscrape/analysis/ai_client.py` |
| Data model (`affected_entities`, `second_order_effects`) | reuse as-is | `finscrape/models/events.py` |
| Heuristic score + dedup helpers | reuse | `finscrape/analysis/validator.py` |
| Multi-agent council + market personas | reuse (explainability/dissent) | `finscrape/agents/*` |
| Multi-model agreement | reuse | `finscrape/analysis/multi_model.py` |
| Continuous monitor loop | port intent → APScheduler worker | `finscrape/monitor.py` |
| Accuracy backtesting | reuse → AccuracyPanel | `finscrape/accuracy.py` |
| Reddit/StockTwits sentiment | reuse → SentimentPanel | `finscrape/sentiment/*` |
| Market quotes | reuse | `finscrape/market_data.py` |
| Alerts / digest | reuse (optional) | `finscrape/alerts.py`, `digest.py` |
| Structured logging | extend | `finscrape/logging_config.py` |
| Ingest/dedup/stats/WS logic | port TS→Python, fix bugs at root | `dashboard/workers/signals-do.ts`, `app.ts`, `app/lib/use-realtime.ts` |
| Feed URL list + tiers + risk | copy facts | WM `src/config/feeds.ts`, `shared/source-tiers.json` |
| Country bboxes, crypto ids | copy facts | WM `shared/country-bboxes.json`, `crypto.json` |
| Correlation/clustering algorithm | reimplement in Python | WM `src/services/analysis-core.ts` |
| Globe | use library directly | `globe.gl` npm |
| Live-TV/YouTube embed pattern | reference only | WM `LiveNewsPanel.ts` |

## Explicitly out of scope (WorldFin v1)

Login/auth, public multi-tenant web hosting, Tauri desktop, protobuf/sebuf API, Pro paywall, MCP
server, the full 56 WM map layers, i18n beyond a stub. Each has a clean seam to add later. The
existing Cloudflare `dashboard/` is left intact as reference and is **not** deployed.

## License & compliance

worldmonitor source (AGPL-3.0) is never copied into this repo — only factual data (URLs, JSON) and
independently-reimplemented algorithms. `docs/DATA_SOURCES.md` records each upstream source's terms
and key requirement. fin-scrape stays MIT.

---

# Part III — Long-horizon roadmap (the 2-year arc)

> The strategic plan beyond WorldFin v1. Phase 1 here is **largely already built** — it *is* the
> existing `finscrape/` brain — and is kept for the record. Phases 2–6 deepen the mind once the body
> (WorldFin) is shipped. Items already done are ticked; the rest are extrapolated targets, to be
> re-scoped as WorldFin lands.

## R-Phase 1: Foundation Overhaul — `(done)`

*Goal: replace the prototype with production-grade architecture and multi-source scraping. This is
the asset WorldFin builds on.*

### Architecture rebuild
- [x] Consolidate `src/`, `backend/`, `aiwebscrape/` into one unified `finscrape/` package
- [x] Proper data models (dataclasses) for events, signals, verdicts
- [x] Plugin-based scraper system — add sources without touching the core pipeline
- [x] Internal scraping engine (`finscrape/engine/`) — zero external framework deps
- [x] Vendor Scrapling v0.4.6 (lxml, curl_cffi, patchright, browserforge, orjson)
- [x] SQLite storage (querying, indexing, historical analysis) — *WorldFin migrates this to Postgres*
- [x] Structured logging with context (source, ticker, stage)
- [x] Centralized config — all tunables via env
- [x] Test suite (112 tests) + CI (ruff, pytest, type-check)

### Internal scraping engine
- [x] `Fetcher` — curl_cffi TLS impersonation + browserforge headers
- [x] `StealthyFetcher` — patchright + Cloudflare Turnstile solver + fingerprint normalization
- [x] `DynamicFetcher` — patchright for JS-heavy pages, network-idle detection
- [x] Unified `Response`/`Selector` API (CSS/XPath) across fetchers
- [x] Session management (cookies/auth); adaptive selector tracking (survive redesigns)

### Multi-source scraping (11 sources)
- [x] Yahoo Finance (HTTP+RSS), Bloomberg, Reuters, CNBC, generic RSS engine, Seeking Alpha,
      MarketWatch, Benzinga, Investing.com, Financial Times, SEC EDGAR (8-K)

### Investment verdict system
- [x] Verdict categories INVEST / PULL_OUT / OBSERVE / CAUTIOUS; score normalization
- [x] Divergence penalty (AI vs heuristics); dual AI backend (OpenAI-proxy + OpenRouter)
- [x] Confidence-weighted aggregation across articles for the same event

## R-Phase 2: Intelligence layer — `(in progress)`

*Goal: go beyond extraction — understand context, track entities, monitor in real time. WorldFin
Phases 2–4 advance much of this.*

### Advanced NLP
- [x] spaCy NER (company/person/org); entity disambiguation; relationship extraction; temporal extraction
- [ ] Coreference resolution — link pronouns/references to entities
- [ ] Custom financial NER fine-tuned on SEC filings + earnings transcripts
  - *Extrapolated:* start from the spaCy pipeline; weak-label from existing extractions to bootstrap a training set before any manual annotation.

### Real-time monitoring
- [x] Continuous scraping loop (configurable intervals); WS event stream; per-domain rate limit/backoff
- [x] Dedup across sources (URL + subject); breaking-news detection (3+ sources in minutes)
- [x] 30-min auto-refresh w/ countdown; Google News Business topic scraping
  - *Note:* WorldFin Phase 3 supersedes the loop with an APScheduler worker + `source_health`.

### Portfolio tracking
- [x] Watchlist management; position-aware weighting; sector grouping; historical accuracy tracking

### Alerts
- [x] Telegram notifications (`/subscribe /status /latest /portfolio /watchlists`)
- [x] Email digests (daily/weekly via Resend proxy); custom alert rules (AlertEngine presets)
- [ ] Discord bot; [ ] Slack integration
  - *Extrapolated:* both reuse the existing `AlertEngine` rule layer; only the delivery sink differs.

## R-Phase 3: Multi-Agent AI Council — `(mostly done)`

*Goal: replace single-model analysis with multi-agent deliberation. WorldFin Phase 7 surfaces this
as the explainability/dissent layer.*

### Agent architecture
- [x] Analyst (1.5), Contrarian (1.0), Risk (1.2), Momentum (0.8), Fundamentals (1.0), Scout (0.7),
      Reviewer (1.4) agents
- [x] Parallel deliberation (ThreadPoolExecutor) → structured `AgentVerdict`; weighted consensus → `CouncilVerdict`

### Market persona simulation
- [x] Institutional Whale (1.3), Retail Day Trader (0.6), Contrarian (0.9), Quant (1.1), ESG (0.7)
- [x] Independent persona verdicts → "market consensus"; persona divergence = uncertainty signal

### LLM infrastructure
- [x] Multi-model support (DeepSeek/Claude/GPT/Llama via `MultiModelClient`); model-agreement scoring;
      LRU+TTL response cache (SHA256 key)
- [x] Local model via Ollama (BYOK/Ollama dual backend) — *landed; powers WorldFin's keyless default*
- [ ] Prompt versioning + A/B testing framework
  - *Extrapolated:* version prompts in `analysis/prompts.py` with a registry + hash; A/B by routing a
    fraction of events through variant prompts and comparing accuracy via `accuracy.py`.

## R-Phase 4: Alternative data & social sentiment — `(in progress)` (H1 2027)

*Goal: beyond news — social media, insider data, options flow, macro indicators.*

### Social sentiment
- [x] Reddit (`RedditSentimentScraper`, bot detection); StockTwits (`StockTwitsScraper`, native labels);
      aggregation w/ bot/spam filtering (`SentimentAggregator`, platform weights)
- [ ] Twitter/X (FinTwit) live; [ ] influencer tracking (weight by historical accuracy);
      [ ] viral detection (spreading narratives before they move markets)

### Alternative data
- [x] SEC EDGAR deep (10-K/10-Q/8-K/DEF 14A/13-F: `FilingFetcher`+`FilingParser`); insider tracker (Form 4)
- [ ] Options flow (unusual activity); earnings-call transcript tone/hedge-word analysis; patents;
      job postings; satellite proxies (foot traffic/shipping); app-store rankings

### Macroeconomic layer
- [ ] Fed funds tracking + impact modeling; CPI/PPI/employment; yield curve; FX correlation;
      commodity feeds; geopolitical risk scoring
  - *Note:* WorldFin Phase 2's keyless ingestors (GDELT, USGS, ReliefWeb) seed the geopolitical-risk input.

### Cross-asset correlation
- [ ] News-about-A historically moves B; sector rotation; supply-chain mapping; competitor-impact
  - *Note:* WorldFin Phase 4's correlation engine is the foundation; this extends it to price-history-driven links.

## R-Phase 5: Autonomous trading signals — `[ ]` (H2 2027)

*Goal: from "what happened" to "what to do" — validated by paper trading first. Human-in-the-loop is
mandatory for real money.*

- [ ] **Signal generation:** composite scoring (news + social + alt-data + technicals); entry/exit
      with confidence intervals; position sizing; multi-timeframe; sector allocation; risk-adjusted projections
- [ ] **Paper trading & backtesting:** paper engine; backtest vs historical data; Sharpe/max-drawdown/
      win-rate; signal-decay analysis; Monte Carlo stress; SPY benchmark
- [ ] **Platform integration:** Alpaca (paper+live); Interactive Brokers; mandatory human-in-the-loop
      above a threshold; order-book-aware execution; rebalancing
- [ ] **Risk management:** per-ticker/sector size limits; drawdown circuit breaker; correlation-aware
      sizing; VIX-scaled sizing; black-swan/model-unreliability detection

## R-Phase 6: Platform & API — `(partly done)` (2028)

*Goal: open FinScrape as a platform others build on. WorldFin's FastAPI service is the seed of the
public API; its dashboard is the seed of the web product.*

### REST/streaming API
- [ ] Public API (free + paid tiers); WS streaming; webhooks; API-key mgmt + rate limiting; OpenAPI docs
  - *Note:* WorldFin Phases 0/1/8 already deliver the contract, auth seam, and rate limiting internally.

### Web dashboard
- [x] Real-time feed w/ filter+search; date pagination+calendar; sortable columns; AI event expansion;
      on-demand Workers-AI analysis w/ SQLite cache; dynamic ticker detection; background AI on ingest;
      portfolio tracker + watchlists; URL+subject dedup; heuristic-only zero-cost mode; responsive
      design; 3D card effects/sticky header; 30-min auto-refresh; WS live updates w/ auto-reconnect
  - *Note:* the above is the **Cloudflare** dashboard (kept as reference). WorldFin Phases 5–7 are the
    **new** vanilla-TS dashboard that replaces it.
- [ ] Signal-accuracy leaderboard (WorldFin Phase 7 delivers the first cut); custom watchlist alert
      thresholds; historical signal explorer with backtest charts

### Plugin ecosystem
- [ ] Scraper / analysis / alert / trading plugins; marketplace + versioning
  - *Note:* the existing plugin-based scraper system (R-Phase 1) is the foundation.

### Global market coverage
- [ ] Europe (LSE/Euronext/XETRA); Asia (TSE/HKEX/SSE/BSE/NSE); crypto (top 50); forex majors;
      commodity-specific news; multi-language (Chinese/Japanese/Hindi/German)
  - *Note:* WorldFin's 583-feed world registry + globe already push toward global coverage.

### Institutional features
- [ ] Multi-user RBAC; audit trail; compliance reporting (MiFID II / SEC); custom model training;
      on-prem deployment; SLA-backed uptime

## Milestone summary (merged)

| When | Milestone | Metric | Status |
|:--|:--|:--|:--:|
| Q2 2026 | Multi-source scraping (internal engine) | 11 sources active | `(done)` |
| Q2 2026 | Cloudflare live dashboard | WS + 30-min refresh | `(done)` |
| Q2 2026 | Telegram bot alerts | /subscribe /status /latest /portfolio | `(done)` |
| Q2 2026 | AI dashboard w/ on-demand analysis | Workers AI + SQLite cache | `(done)` |
| **Now** | **WorldFin v1 — global intel dashboard** | **Phases 0–11 green; demo acceptance met** | **`(in progress)`** |
| Q3 2026 | Real-time monitoring + NLP pipeline | <5 min publish→signal | `(in progress)` |
| Q4 2026 | Multi-agent AI council | 7 agents + 5 personas | `(mostly done)` |
| Q1 2027 | Social sentiment integration | Twitter + Reddit + StockTwits live | `(in progress)` |
| Q2 2027 | Alternative data (SEC, options, insider) | 10+ alt-data sources | `(in progress)` |
| Q3 2027 | Paper trading validation | 6-mo backtest, positive Sharpe | `[ ]` |
| Q4 2027 | Live trading integration | Alpaca + IB w/ safety rails | `[ ]` |
| Q1 2028 | Public API launch | Beta users on free tier | `[ ]` |
| Q2 2028 | Full web dashboard | Portfolio viz + accuracy tracking | `(partly done)` |
| H2 2028 | Global markets + institutional | Multi-market, multi-language | `[ ]` |

## Principles

1. **Accuracy over speed** — a wrong signal is worse than a late one. Always validate.
2. **Hybrid intelligence** — AI + heuristics + human review. No single point of failure.
3. **Transparency** — every verdict must be explainable. Show the reasoning chain.
4. **Safety first** — human-in-the-loop for any real-money decision. Paper trade first.
5. **Open core** — the core engine stays open source. Premium features fund development.
6. **Resumability** — every session ends with a checkpoint. Never reconstruct lost state.

---

# Appendices

## Appendix A — Correlation engine spec
*(Phase 4 — Python port of WM `analysis-core.ts`)*

Constants: `SIMILARITY_THRESHOLD=0.5`, `MARKET_MOVE_THRESHOLD=2`, `PREDICTION_SHIFT=5`,
`NEWS_VELOCITY=3`, `FLOW_PRICE=1.5`, energy syms `{CL=F, NG=F}`, cluster input cap `1000`, velocity
baseline window `7d`, spike multiplier `3`, convergence window `1h`, **final confidence floor `0.6`**
(only signals ≥0.6 emitted). JS `Math.round(x*10)/10` rounds half-up — use `floor(x*10+0.5)/10` in
Python.

**Primitives:** `tokenize` = lowercase → non-`[a-z0-9 ]`→space → split → keep `len>2` and
`∉STOP_WORDS` → set. `jaccard(a,b)=|a∩b|/|a∪b|` (0 if both empty). `containsTopicKeyword` =
word-boundary regex; `includesKeyword` = substring. `dedupeKey`: market types
(`silent_divergence`/`flow_price_divergence`/`explained_market_move`) = `type:id`; else
`type:id:round1(value)`.

**`clusterNewsCore(items, getSourceTier)`:** bound to 1000 (sort newest-first then
source/title/link asc) → attach tier → tokenize titles → inverted index token→[idx asc] → **greedy
single-pass:** for each unassigned seed `i`, candidates = `{idx>i sharing ≥1 token}`, for `j` in
sorted(candidates) if `jaccard(tokensI,tokensJ)≥0.5` add to cluster (seed-vs-candidate only, never
transitive, clusters never merge) → build `ClusteredEventCore` (primary = lowest tier then newest;
`firstSeen/lastUpdated` = raw min/max getTime; geo = most-frequent (lat,lon) among members;
`threat`=tier-weighted aggregate) → sort output by `lastUpdated` desc.

**`analyzeCorrelationsCore(events, predictions, markets, prevSnapshot, getSourceType, isDup,
markSeen)`:** **first call (no prevSnapshot) → emits nothing**, returns snapshot. Else: extractTopics
(TOPIC_KEYWORDS word-boundary, skip SUPPRESSED, score=`velocity+sourceCount`) → update 7d velocity
history → run detectors in order, each gated by `isDup(dedupeKey)`:
- `prediction_leads_news`: |Δprice|≥5 AND related-topic news activity <3 → conf `min(.9,.5+shift/20)`
- `velocity_spike`: velocity >6 AND >3×baseline → conf `min(.9,.45+mult/8)`
- market loop (per market |change|≥2): entity-news found → `explained_market_move`
  `min(.9,.5+.1·n+chg/20)`; else `silent_divergence` (topic mentions <2) `min(.8,.4+chg/10)`
- `flow_price_divergence` (CL=F/NG=F signed ≥1.5, mentions<2, 0 pipeline signals) `min(.85,.4+chg/8)`
- `detectConvergence`: cluster recent(<1h)≥3 items AND ≥3 distinct source-types (excl `other`)
  `min(.95,.6+.1·types)`
- `detectTriangulation`: cluster has all of `{wire,gov,intel}` → fixed `0.9`
- `flow_drop`: pipeline+flow keywords in cluster → `min(.9,.4+sourceCount/10)`

**Final:** keep only the FIRST signal per `type` (insertion order), then drop `<0.6`. SourceType from
`source-tiers.json` (`wire|gov|intel|mainstream|market|tech|other`). Entity-aware
`findNewsForMarketSymbol` needs WM `entity-index.ts` — **stub to `[]` in v1** (forces all moves down
`silent_divergence`); port the entity index later for `explained_market_move`. **Verify:** unit-test
each detector against the formulas above.

## Appendix B — API contract + root-cause bug fixes
*(Phase 1 — port of `signals-do.ts`/`app.ts`)*

Endpoints (auth = `X-API-Key` or `Bearer`, only on the 4 mutating routes):
`POST /api/events`→`{ok,inserted,duplicates,insertedIds}`; `GET /api/events`
(limit/offset/verdict/ticker/source/event_type/date/sort/dir); `GET /api/stats`→DashboardStats;
`GET /api/dates`→`{dates:[{day,count}]}`; `GET /api/ai/analyze?id=`→`{summary,ticker_impacts[],
verdict_reason}` (cache→LLM→merge ≤6-char tickers back into event); `GET /api/portfolio`,
`POST/DELETE /api/portfolio/position`, `POST /api/portfolio/watchlist`; `POST /api/telegram/webhook`
(always 200); `WS /api/ws` msgs `init`(latest 20)/`new_events`/`ai_updated`/`pong`. Ingest
side-effects (bg AI batches of 3 + Telegram for INVEST/PULL_OUT) must not block the response;
**alert on `insertedIds`, not raw input** (existing bug re-alerts dupes).

**3 root bugs to fix in the port (cause the live ~4× dup + count mismatch):**
1. **Timezone drift (the count mismatch):** `timestamp` is client-supplied TEXT; `getEvents?date`
   uses half-open `[T00:00Z, nextT00:00Z)`, but `getAvailableDates` uses `DATE(timestamp)` and stats
   `last_update` uses `ORDER BY id DESC` — three conventions disagree for non-`Z`/offset timestamps.
   **Fix:** store `TIMESTAMPTZ` normalized to UTC at ingest; derive the day with one
   `(ts AT TIME ZONE 'UTC')::date`; use the SAME half-open `[day,day+1)` in dedup, feed, dates, stats.
   `last_update = MAX(created_at)`.
2. **Dedup substring `instr(articles, url)`** → false pos/neg (prefix collisions, only checks
   `articles[0]`). **Fix:** canonicalize URLs, store `content_hash` UNIQUE, `INSERT … ON CONFLICT DO
   NOTHING`, count affected rows.
3. **Read-then-write dedup race** (concurrent ingest double-inserts). **Fix:** the same UNIQUE
   constraint + ON CONFLICT (atomic). **Verify:** ingest `test_event.json` twice → exactly 1 row;
   stats count == feed count for that day.

## Appendix C — Scoring fusion
*(reuse `finscrape` verbatim; Phase 1/3 worker)*

Reuse `FinScrapePipeline._analyze_article` as the fusion unit (construct with
`enable_alerts/accuracy/portfolio=False`). Per-article order: scrape→freshness gate→`call_ai` (or
council)→relevance gate→NLP enrich→ticker fusion→market data→heuristic→divergence→fuse. **Score:**
`final = clamp(-5,5, ai_score + market_boost)` where `market_boost`∈{0,1,2} from `abs(change%)≥5→1,
≥10→2` (only ever raises). **Confidence, order is load-bearing:** `conf` → if divergence `−0.15` →
`apply_source_credibility` (`conf*0.7+conf*cred*0.3`; bloomberg/reuters 1.0…rss/default 0.5) →
`apply_recency_decay` (`*exp(-0.05*age_h)`, age None→`*0.85`, clamp 48h) → if breaking `+0.10`.
`Verdict.from_score`: ≥3 INVEST, ≥1 OBSERVE, ≥−1 CAUTIOUS, else PULL_OUT. `calculate_heuristic_score`
logistic intentionally double-counts base_impact — match exactly. **`call_ai(prompt, system_prompt,
model=None)`** picks backend: `OPENAI_BASE_URL` (Ollama) → else `OPENROUTER_API_KEY` (BYOK) → else
None; strips `<think>`, regex `{...}`, validates + clamps; sha256 model-aware LRU+TTL cache. **Worker
caveat:** `get_market_data` calls `yf.download` per article in the hot path — cache/stub it so the
worker doesn't block on Yahoo. Council (`use_council=True`) gives `CouncilVerdict{consensus_score,
agreement_level, dissenting_agents, key_risks/opportunities}` for the Phase-7 explainability panel.

---

> **Living document.** Update the checkboxes as you ship; record the narrative in `progress/`.
> Priorities shift as the market and technology evolve — and as each checkpoint teaches us something.
