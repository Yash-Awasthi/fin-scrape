# WorldFin

**See what moves markets — before it's news.**

WorldFin ingests geopolitics + world news, resolves **which tickers and sectors** each event
moves, judges the **first- and second-order** market impact on a **live globe**, and **proves the
calls were right** over time. It's built on `finscrape` — a mature Python intelligence engine
(11 stealth scrapers, LLM event extraction, a 7-agent council, accuracy backtesting).

### ▶︎ Live (free-tier, $0)
- **Landing:** https://winfin.pages.dev
- **Dashboard:** https://winfin.pages.dev/app/
- **API:** https://winfin-api.onrender.com/docs

> Open a geopolitics event on the globe → see the resolved affected tickers, role-tagged entities,
> first/second-order impact, a calibrated −5…+5 score, the council's consensus + dissent, and the
> historical hit-rate with an equity curve.

---

## What it does

```
 INGEST  →  RESOLVE        →  JUDGE                 →  PROVE
news +     which tickers/    first/second-order +     score every call vs the
geopolitics sectors it moves  verdict (−5…+5)          realized move (hit-rate + curve)
```

A Strait-of-Hormuz headline becomes **XOM, CVX, RTX, ZIM** — oil majors *(primary)*, defense
*(competitor)*, shippers *(supplier)*, insurers *(regulator)* — each with a directional impact and a
chain of second-order effects (war-risk premiums, rerouting, LNG spillover).

### Features
- **Live globe** — every event geolocated, colored by verdict (INVEST / PULL_OUT / OBSERVE / CAUTIOUS).
- **Event → ticker resolution** — entity-map + LLM resolve world events to real symbols.
- **Multi-agent AI council** — 7 analyst personas deliberate; surfaces consensus *and* dissent.
- **Accuracy proof** — backtested hit-rate, by-verdict breakdown, equity-curve sparkline.
- **Correlation engine** — fires when 3+ independent source-types corroborate a story; flags
  news↔market divergence ("before it's news").
- **Breaking-news triangulation**, **social sentiment** (Reddit + StockTwits), **portfolio + watchlists**,
  **Telegram alerts**, **crypto + markets panels**, **prompt A/B** with accuracy-by-variant.
- **Freshness guaranteed** — only news ≤24h, with per-source health monitoring.

---

## Architecture

```
            GitHub Actions cron (worker)                  Cloudflare Pages
        scrape → LLM → resolve → ingest                  ┌──────────────────┐
        → correlate → backtest  ─────────────┐           │  landing  (  /  ) │
                                             ▼           │  SPA      ( /app )│
   freemodel.dev / OpenRouter ──▶  ┌──────────────┐      └────────┬─────────┘
        (free GPT-5.x LLM)         │   Neon PG     │               │ fetch / WS
                                   │  (asyncpg)    │      ┌────────▼─────────┐
   heuristic fallback ────────────▶│ content-hash  │◀────▶│  FastAPI (Render)│
        (never stalls)             │  dedup, JSONB │      │ REST · WS · /docs│
                                   └──────────────┘      └──────────────────┘
```

- **Backend:** FastAPI + Postgres (asyncpg), reuses the `finscrape/` brain. Root-cause fixes for the
  old dashboard's dup/count/timezone bugs (deterministic `content_hash` dedup, one UTC day-bounds).
- **Worker:** one ingest cycle per run (`worker.main --once`), driven by a scheduled GitHub Action.
- **Frontend:** vanilla-TS Vite SPA (globe.gl, panel grid) + a hand-coded landing page.
- **Quality:** 692 tests, ruff + pyright + Vitest + Playwright, multi-stage non-root Docker images, CI.

Full design + the 2-year roadmap live in **[PLAN.md](PLAN.md)**.

---

## Quickstart (local)

```bash
git clone https://github.com/Yash-Awasthi/fin-scrape.git && cd fin-scrape
cp .env.example .env          # defaults work; no key needed for the seeded demo
make demo                     # docker compose up + seed → a populated dashboard
#   web → http://localhost:8080   ·   api → http://localhost:8000/docs
```

No Docker? Run the pieces directly (Postgres + `python -m server.main` + `python -m worker.main`);
see **[docs/DEMO.md](docs/DEMO.md)** for the scripted 5-minute walkthrough.

## Deploy it free

The live stack runs **$0/month, no credit card**: Cloudflare Pages (web) + Render (API) + Neon
(Postgres) + GitHub Actions (worker) + a free GPT-5.x LLM. Full recipe in **[docs/DEPLOY.md](docs/DEPLOY.md)**.

---

## Configuration

All via env (`.env.example`). Key ones:

| Var | Purpose |
|---|---|
| `WORLDFIN_DATABASE_URL` | Postgres DSN |
| `OPENAI_BASE_URL` + `OPENAI_API_KEY` + `FINSCRAPE_WIRE_API` | LLM backend (Ollama / freemodel responses) |
| `OPENROUTER_API_KEY` + `FINSCRAPE_MODEL` | BYOK LLM alternative |
| `FINSCRAPE_HEURISTIC_FALLBACK` | ingest with heuristics when the LLM is unavailable |
| `WORLDFIN_ENABLE_COUNCIL` | multi-agent explainability |
| `TELEGRAM_BOT_TOKEN` | outbound alerts + `/api/telegram/webhook` |

## Tech stack
Python 3.13 · FastAPI · asyncpg · Postgres · APScheduler · pydantic-settings · Prometheus ·
vanilla TypeScript · Vite · globe.gl · Docker · GitHub Actions. LLM via Ollama / OpenRouter /
freemodel (OpenAI Responses API). Heuristics + spaCy NLP.

## Repo layout
```
finscrape/   # the intelligence engine: scrapers, LLM extraction, council, entity-map, accuracy
server/      # FastAPI service: routes, ingest/dedup, correlation, accuracy, sentiment, portfolio
worker/      # APScheduler ingest worker (+ --once for cron)
web/         # Vite SPA (dashboard at /app) + hand-coded landing (/)
docs/        # PLAN, DEPLOY, DEMO, RUNBOOK, ARCHITECTURE, SECURITY, RISKS, DATA_SOURCES
dashboard/   # legacy Cloudflare Workers dashboard (reference; not deployed)
```

## Docs
[PLAN.md](PLAN.md) · [DEPLOY](docs/DEPLOY.md) · [DEMO](docs/DEMO.md) · [RUNBOOK](docs/RUNBOOK.md) ·
[ARCHITECTURE](docs/ARCHITECTURE.md) · [SECURITY](docs/SECURITY.md) · [RISKS](docs/RISKS.md) ·
[DATA_SOURCES](docs/DATA_SOURCES.md)

## License
MIT — see [LICENSE](LICENSE). WorldFin is market intelligence, **not financial advice**.
