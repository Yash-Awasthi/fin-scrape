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

## Analysis pipeline (the finscrape brain)

`finscrape/pipeline.py:FinScrapePipeline._analyze_article` is the fusion entry point (see the Reuse
map above). Per article: scrape → freshness gate → `call_ai` (or council) → relevance gate → NLP
enrich → ticker fusion → market data → heuristic score → divergence check → confidence fuse. The
subsections below describe the pieces that changed in the 2026-08-16 analysis-layer hardening pass;
see [`../PLAN.md`](../PLAN.md) for that pass's full change list.

**Ticker resolution.** `finscrape/analysis/ticker_map.py` is the single company-name-to-ticker map;
`finscrape/entity_map.py` is the separate sector/region-to-ticker map used for geopolitics headlines
that name no company. Both share the word-boundary matcher in `entity_map._matches`, so a bare name
like "arm" or "target" cannot fire on a substring inside "pharma" or "price target". The resolved
ticker list is filtered through `finscrape/analysis/validator.py:clean_tickers(tickers, text=...)`,
which only lets a stopword-listed word (`NOW`, `ALL`, `IT`, `AI`, `KEY`, `GO`, `ONE`, …) through when
the source text carries it as an explicit `$TICK` or `(TICK)` marker; both `finscrape/pipeline.py`
and `push_to_dashboard.py` pass the article text into this call.

**Market boost.** `finscrape/market_data.py:calculate_market_boost` picks the single biggest mover
(by absolute percent change) across the resolved tickers and returns a boost signed to match that
mover's direction: `±1` at `≥5%`, `±2` at `≥10%`, `0` below that. `finscrape/pipeline.py` adds this
to the AI's `signal_score` and clamps the result to `[-5, 5]`.

**Confidence fusion.** `finscrape/analysis/validator.py:fuse_confidence` is the single place all
confidence adjustments combine, called from `finscrape/pipeline.py`. The two multiplicative steps
(`apply_source_credibility`, then `apply_recency_decay`) run before the two additive steps (a `-0.15`
divergence penalty, a `+0.10` breaking-news bonus); the result then clamps to `[0, 1]`. Running the
multipliers first means the divergence penalty always costs exactly `0.15`, regardless of how much
the multipliers already discounted the base confidence.

**Heuristic impact score.** `finscrape/analysis/validator.py:calculate_heuristic_score` converts the
event type's base impact to log-odds (`logit_base = log(base / (1 - base))`), adds magnitude-word and
extracted-figure boosts, and runs the sum through a sigmoid. A zero boost returns the base impact
unchanged — there is no double-counting.

**Council crash handling.** `finscrape/agents/base.py:AgentVerdict` carries an `error` flag, set
whenever an agent raises or its response fails to parse. `finscrape/agents/council.py`'s
`_build_consensus` computes every consensus number — score, agreement, confidence, dissent,
risks/opportunities — only from verdicts with `error=False`; a council where every agent crashed
reports `consensus_confidence=0.0` and a `failed_agents` count instead of folding a crashed agent's
implicit verdict into the average.

**Prompt template safety.** `finscrape/analysis/prompts.py:render_prompt` fences the article body
between literal markers, strips any `{{`/`}}` from it, and substitutes it before the title, so
neither the body nor the title can forge a placeholder that hijacks the other slot.
`EVENT_TYPES_PIPE` is built once from `constants.VALID_EVENT_TYPES` at import time, so the prompt's
allowed event types and the validator's accepted set cannot drift apart. Both prompt-registry
variants (`finscrape/analysis/prompt_registry.py`, v1/v2 for the accuracy A/B split) reuse this same
prompt and render path.

**Not present:** `finscrape/analysis/multi_model.py` (cross-provider agreement scoring) was removed;
nothing in the pipeline called it. Relationship extraction and coreference resolution are not
implemented in `finscrape/analysis/nlp.py` despite earlier documentation claiming otherwise —
`nlp.py` does NER, entity disambiguation, ticker resolution, and financial metric extraction only.
`temporal.py` shares a single spaCy parse with `nlp.py` rather than re-parsing the article.

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
