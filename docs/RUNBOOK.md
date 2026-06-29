# WorldFin — Operations Runbook

How to operate, observe, restore, and rotate secrets for the WorldFin stack. Pairs with
[`SECURITY.md`](SECURITY.md) (threat model) and [`DATA_SOURCES.md`](DATA_SOURCES.md) (feeds).

Stack = **postgres** + **api** (FastAPI :8000) + **worker** (APScheduler) + **web** (nginx :8080).
Optional observability overlay = **prometheus** + **grafana** + **loki** + **promtail**.

---

## 1. Operate

### Bring up / tear down
```bash
cp .env.example .env            # set OPENROUTER_API_KEY or OPENAI_BASE_URL (Ollama); else LLM falls back
docker compose up -d            # core stack
docker compose ps               # health
docker compose logs -f api      # tail one service
docker compose down             # stop (keeps the pgdata volume)
```

With observability:
```bash
docker compose -f docker-compose.yml -f docker-compose.obs.yml up -d
# Grafana http://localhost:3000 (admin/admin) → "WorldFin — Observability" dashboard
# Prometheus :9090 · Loki :3100
```

### Health probes
- `GET /health` — liveness, always 200 (`degraded` if DB unreachable).
- `GET /ready` — readiness, 503 until the DB pool answers (orchestrator gate).
- `GET /api/health` — per-source freshness (OK/STALE/WARN/EMPTY).
- `GET /metrics` — Prometheus exposition (API). Worker metrics on `worker:9100/metrics`.

### Scaling notes
- Rate limiting + tiered cache are **in-process** (single API replica by design). Going
  multi-replica needs Redis — `WORLDFIN_REDIS_URL` is the documented seam (`server/cache.py`,
  `server/rate_limit.py`, `server/ws.py`).
- WS fan-out is in-process too; same Redis seam.

---

## 2. Observe

| Signal | Where | Metric / query |
|---|---|---|
| Ingest rate | Grafana / Prom | `rate(worldfin_events_ingested_total[5m])` |
| Duplicates | Prom | `rate(worldfin_events_duplicate_total[5m])` |
| LLM latency p95 | Grafana / Prom | `histogram_quantile(0.95, rate(worldfin_llm_request_seconds_bucket[5m]))` |
| Source freshness | Grafana / Prom | `worldfin_source_age_seconds`, `worldfin_source_up` |
| WS clients | Prom | `worldfin_ws_clients` |
| HTTP rate/latency | Prom | `worldfin_http_requests_total`, `worldfin_http_request_seconds` |
| Logs | Loki/Grafana | `{container=~".*api.*|.*worker.*"}` |

Logs are one-line JSON when `WORLDFIN_LOG_JSON=true` (default in compose) with a
`correlation_id` per HTTP request (also returned in the `X-Request-ID` response header) and
per worker source-cycle — grep one id to trace a unit of work end to end.

---

## 3. Common incidents

| Symptom | Likely cause | Action |
|---|---|---|
| `/api/health` shows a source **STALE** | feed down / network | check `docker compose logs worker`; transient feeds self-heal next cycle. Persistent → verify the URL in `DATA_SOURCES.md`. |
| A source **WARN** | producer threw | the worker degrades that source and keeps going; last error is in `source_health.last_error`. |
| `/ready` returns 503 | DB pool can't answer | check `postgres` health; `docker compose restart api` after DB is back. |
| 429s | per-IP rate limit | raise `WORLDFIN_RATE_LIMIT_PER_MIN` or front with a CDN; 0 disables. |
| LLM analysis is generic | no LLM configured or call failed | expected graceful fallback (`server/ai.py`); set `OPENROUTER_API_KEY`/Ollama. `worldfin_llm_request_seconds{outcome="error"}` rising = backend issue. |

---

## 4. Backup & restore (Postgres)

Data lives in the `pgdata` volume. Logical backup:
```bash
docker compose exec -T postgres pg_dump -U worldfin worldfin | gzip > backup-$(date +%F).sql.gz
```
Restore into a fresh DB:
```bash
gunzip -c backup-YYYY-MM-DD.sql.gz | docker compose exec -T postgres psql -U worldfin worldfin
```
Migrations are idempotent and run on startup (`WORLDFIN_RUN_MIGRATIONS=true`); a restored dump
already has the schema, so this is a no-op safety net. Events are content-deduped on ingest, so
re-running the worker after a restore won't double-insert.

---

## 5. Secret rotation

All secrets come from `.env` / the environment — no secrets in the image or git.

| Secret | Var | Rotate |
|---|---|---|
| Ingest API key | `FINSCRAPE_API_KEY` | set new value, `docker compose up -d api worker`; update any caller. |
| LLM key | `OPENROUTER_API_KEY` | revoke old at OpenRouter, set new, recreate `api`+`worker`. |
| DB password | `POSTGRES_PASSWORD` + DSN in `WORLDFIN_DATABASE_URL` | `ALTER USER worldfin PASSWORD '…';` then update both vars and recreate `api`+`worker`. |
| Grafana admin | `GRAFANA_PASSWORD` | set and recreate `grafana`. |

After rotation, confirm green: `/health`, `/ready`, and one authenticated mutating route.

---

## 6. Log retention

Container stdout/stderr → Docker json-file driver (cap with `--log-opt max-size`/`max-file` or a
daemon-level default). Loki retention is set in `obs/loki-config.yml`; Prometheus TSDB retention
is `--storage.tsdb.retention.time` in `docker-compose.obs.yml` (15d default). Tune both to disk.
