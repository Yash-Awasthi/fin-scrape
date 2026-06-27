# WorldFin — Risk register, dependency graph & effort sizing

Resolves PLAN.md open-investigation #3. Living doc — revisit each checkpoint.

## Dependency graph (phase order is load-bearing)

```
Phase 0 (foundations: db schema, settings, contract)
   │
   ├─▶ Phase 1 (backend API: ingest/dedup/feed/stats/WS) ──┐
   │        │                                               │
   │        ▼                                               ▼
   ├─▶ Phase 2 (world data: feeds, ingestors, geocode, widened prompt)
   │        │
   │        ▼
   └─▶ Phase 3 (worker: scheduling, source_health) ──▶ Phase 4 (correlation)
            │                                               │
            ▼                                               ▼
        Phase 5 (frontend shell + globe) ──▶ Phase 6 (panels) ──▶ Phase 7 (trust layer)
                                                                        │
                            Phase 8 (hardening) ◀───────────────────────┤
                            Phase 9 (observability) ◀───────────────────┤
                            Phase 10 (CI/CD) ─────────▶ Phase 11 (demo polish)
```

Critical path: **0 → 1 → 2 → 3 → 4 → 6 → 7** (the demo thesis: geopolitics event →
tickers → judged impact → accuracy proof). 5 can proceed in parallel with 2–4 once 1 is up.
8/9/10 are cross-cutting; 11 is last.

## Effort sizing (rough, S/M/L/XL = ~0.5 / 1–2 / 3–5 / 6+ focused days)

| Phase | Size | Driver of cost |
|---|---|---|
| 0 Foundations | **M** | schema correctness; compose healthchecks; idempotent migrations |
| 1 Backend API | **L** | porting `signals-do.ts`+`app.ts`; fixing 3 root bugs; WS; contract tests |
| 2 World data | **L** | 583-feed registry; 5 keyless ingestors; prompt widening; geocode bboxes |
| 3 Worker | **M** | APScheduler loop; blocking calls off-loop; source_health; resilience |
| 4 Correlation | **L** | faithful Python port of 752-line `analysis-core.ts` + per-detector tests |
| 5 Frontend shell | **L** | vanilla-TS panel system + globe.gl wrapper + WS client (no React crutch) |
| 6 Panels | **XL** | ~10 panels, each API-fed; variant presets; expand UX |
| 7 Trust layer | **M** | reuse accuracy.py + council; mostly wiring + viz |
| 8 Hardening | **M** | auth, rate limit, SSRF guard, cache tiers, circuit breakers |
| 9 Observability | **S/M** | logging extend; Prometheus /metrics; optional Grafana profile |
| 10 CI/CD | **M** | server tests + web E2E (Playwright) + image build + security scan |
| 11 Demo polish | **M** | seed script; DEMO.md; one-command bring-up |

## Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Blocking finscrape calls (scrapers, `yf.download`, LLM) stall the async event loop** | High | High | Run all blocking work in a threadpool (`run_in_executor`) from the worker, never in API request handlers. Cache/stub `get_market_data` in the worker hot path (Appendix C caveat). |
| R2 | **Correlation port drifts from WM semantics** (rounding, greedy-cluster non-transitivity, first-signal-per-type) | Med | High | Port against the exact formulas in Appendix A; unit-test each detector; use `floor(x*10+0.5)/10` for JS half-up rounding. |
| R3 | **Dedup still lets dupes through** (the live ~4× bug) | Med | High | Deterministic `content_hash` UNIQUE + `ON CONFLICT DO NOTHING` (atomic) — fixes at the DB layer, not per-caller. Verify: ingest twice → 1 row. |
| R4 | **Timezone/count mismatch returns** | Med | Med | TIMESTAMPTZ UTC-normalized at ingest; ONE half-open `[day, day+1)` query reused by feed/dates/stats; `last_update = MAX(created_at)`. |
| R5 | **LLM unavailable / slow** (no key and no Ollama, or Ollama on CPU) | Med | Med | Heuristic-only path already exists (`validator.py`); BYOK→Ollama→heuristic fallback. Don't block ingest on AI (background batches). |
| R6 | **Widened world prompt degrades finance extraction** | Med | Med | Keep schema unchanged; A/B the prompt; gate behind accuracy.py before/after; revert is one prompt swap. |
| R7 | **RSS-proxy SSRF** (user-driven fetch of arbitrary URLs) | Med | High | Domain allowlist from the feed registry; block private IPs + redirects (Phase 8). Security boundary — do not defer past Phase 8. |
| R8 | **AGPL contamination from worldmonitor** | Low | High | Never copy WM source; only facts (feed URLs, JSON) + independent reimplementation. Record provenance in `docs/DATA_SOURCES.md`. |
| R9 | **Keyless free APIs rate-limit or vanish** (GDELT/USGS/etc.) | Med | Low | Per-source backoff + `source_health` STALE marking; a dead source degrades, never crashes the run. |
| R10 | **Env Python drift** (spacy has no cp314 wheel) | Hit | Low | Pin runtime to 3.13 (Makefile/Docker); documented. |
| R11 | **Scope creep into out-of-scope v1 items** (auth, multi-tenant, 56 map layers) | Med | Med | PLAN.md "Explicitly out of scope" is the fence; each has a clean seam for later. |

## Confirmed stack micro-choices (resolves open-investigation #2)

- **DB driver:** asyncpg (raw, fast) — not SQLAlchemy-async (no ORM needed for this shape).
- **Migrations:** raw versioned `.sql` + a tiny runner (`server/db.py`) — no alembic/yoyo dependency.
- **Scheduler:** APScheduler in the worker process.
- **Blocking work:** threadpool via `run_in_executor`; worker process separate from API.
- **Redis:** optional — only when >1 API replica needs WS fan-out / shared rate-limit (compose profile).
