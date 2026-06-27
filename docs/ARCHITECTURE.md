# WorldFin — Architecture (as built, Phases 0–4)

How the system is wired today. Frontend (globe/panels) is Phase 5+; this reflects the
backend + worker + correlation foundation. See [../PLAN.md](../PLAN.md) for the roadmap.

## Services (docker-compose)

```
            ┌──────────────┐         ┌────────────────────────────────────┐
            │   worker     │  writes │             Postgres 16             │
            │ (APScheduler)│ ───────▶│ events · correlations · scrape_runs │
            │ scrape→judge │         │ source_health · accuracy · ai_cache │
            │ →geocode→corr│         └───────────────┬────────────────────┘
            └──────┬───────┘                         │ asyncpg pool (+jsonb codec)
                   │ reuses finscrape brain          │
                   ▼                    ┌────────────▼─────────────┐
            FinScrapePipeline           │   api (FastAPI/uvicorn)  │
            ._analyze_article           │  REST + WS               │
                                        │  /api/events /stats      │
                                        │  /dates /ai/analyze      │
                                        │  /correlations /health   │
                                        │  WS /api/ws              │
                                        └──────────────────────────┘
```

- **postgres** — datastore. Schema in `server/migrations/0001_init.sql`, applied idempotently
  on api/worker startup by `server/db.py:run_migrations` (tracked in `schema_migrations`).
- **api** (`server/`) — FastAPI app (`server/app.py:create_app`). Lifespan opens the asyncpg
  pool + runs migrations. Routers under `server/routes/`.
- **worker** (`worker/`) — separate long-running process (`worker/main.py`), `AsyncIOScheduler`,
  one interval job per source + a post-scrape correlation pass.
- **redis** — optional (compose profile); the seam for multi-replica WS fan-out + rate-limit
  (Phase 8). Not required in v1.

LLM is **BYOK or local Ollama**, shared with finscrape via env (`OPENAI_BASE_URL` /
`OPENROUTER_API_KEY` / `FINSCRAPE_MODEL`). Typed settings: `server/settings.py`.

## Data flow

1. **Worker cycle** (`worker/runner.py:Worker.run_source`): a source producer
   (`worker/sources.py`) fetches articles (world RSS) or `RawGeoEvent`s (keyless ingestors) →
   blocking scrape/LLM/market work runs in `asyncio.to_thread` → `FinScrapePipeline._analyze_article`
   produces a `FinEvent` → `server/geocode.py:geocode_event` attaches lat/lon (explicit ingestor
   coords win, else country centroid) → `server/ingest.py:ingest_events` upserts.
2. **Dedup** is atomic: a deterministic `content_hash` (normalized subject + canonical first-article
   URL + UTC day) with a UNIQUE constraint + `ON CONFLICT DO NOTHING`.
3. **Correlation** (`worker/runner.py:run_correlations` → `server/correlate.py`): recent events are
   clustered (Jaccard) and run through the detectors; emitted signals persist to `correlations`.
4. **API reads** (`server/queries.py`): the feed, stats, and dates all use the **same** half-open
   `[day, day+1)` UTC bounds (`server/ingest.py:day_bounds`).
5. **Live updates**: `server/ws.py` broadcasts `init`/`new_events`/`ai_updated`/`pong`. API-side
   ingest broadcasts directly; worker→client broadcast waits on the Redis seam (Phase 8).

## The three root-cause bug fixes (vs the old Workers/D1 dashboard)

1. **~4× duplication** → deterministic `content_hash` UNIQUE + `ON CONFLICT DO NOTHING` (atomic;
   no read-then-write race, no fragile `instr(articles,url)` substring match).
2. **Stat/feed count mismatch** → one `day_bounds` convention reused by feed/dates/stats.
3. **Timezone drift** → `parse_timestamp` normalizes everything to UTC `TIMESTAMPTZ` at ingest;
   day derived as `(timestamp AT TIME ZONE 'UTC')::date`; `last_update = MAX(created_at)`.

## Reuse map (the finscrape "brain")

| Capability | Module |
|---|---|
| event→entity→judge fusion | `finscrape/pipeline.py:FinScrapePipeline._analyze_article` |
| data model | `finscrape/models` (`FinEvent`, `ScrapedArticle`, `Verdict`) |
| LLM backends (BYOK/Ollama) | `finscrape/analysis/ai_client.py` (extraction); `server/ai.py` (analyze shape) |
| world-widened prompt | `finscrape/analysis/prompts.py` |
| world feeds + tiers | `finscrape/scrapers/world/feeds.py` |
| keyless ingestors | `finscrape/ingestors/` |
| correlation algorithm | `server/correlate.py` (independent port; spec = PLAN Appendix A) |

## Testing

- Pure logic is unit-tested offline (dedup/timezone, geocode, ingestor parsers, correlation
  detectors, STALE derivation): `tests/server/`, `tests/test_world_phase2.py`,
  `tests/test_worker_phase3.py`, `tests/test_correlate_phase4.py`.
- DB-dependent paths are **skip-ready** integration tests (`tests/server/test_*integration.py`)
  that auto-skip without Postgres and run under `make up` / CI (postgres service).
- `make lint` / `make fmt-check` / `make selfcheck` / `make test`.

## Known gaps / deferred

- Live `make up` verify (DB+LLM) pending docker; integration tests are ready.
- Worker `get_market_data` (`yf.download`) per-article cost → Phase 8 cache/stub.
- `find_news_for_market_symbol` stubbed → `[]` (port WM entity index for `explained_market_move`).
- Worker→client WS fan-out needs Redis (Phase 8). Portfolio + telegram routes: Phase 1 tail.
