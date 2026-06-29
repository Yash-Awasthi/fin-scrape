# WorldFin — free-tier production deploy

The live stack runs **$0/month, no credit card** across four free services + a free LLM.

## Live URLs
- **Landing:** https://winfin.pages.dev
- **Dashboard:** https://winfin.pages.dev/app/
- **API:** https://winfin-api.onrender.com (`/docs`, `/health`)

## Architecture
| Layer | Service | Notes |
|---|---|---|
| Web (landing + SPA) | **Cloudflare Pages** (`winfin`) | static, no sleep; landing `/`, app `/app/` |
| API | **Render** free web service (`winfin-api`, Singapore) | Docker `Dockerfile.api` → Neon; sleeps after 15 min idle |
| Database | **Neon** Postgres (Singapore) | serverless, scales to zero; permanent free tier |
| Worker | **GitHub Actions** cron (`.github/workflows/ingest.yml`, :13/:43) | `python -m worker.main --once`; unlimited on public repo |
| LLM | **freemodel.dev** GPT-5.x (Responses API) | free; `FINSCRAPE_WIRE_API=responses`. ⚠️ **key expires 2026-07-28** — see below. Heuristic fallback covers outages |

## Environment

**Render API** (`srv-...` env vars) and **GitHub Actions secrets** share:
- `WORLDFIN_DATABASE_URL` — Neon connection string (direct, `?sslmode=require`, no `channel_binding`)
- `OPENAI_BASE_URL=https://api.freemodel.dev`, `OPENAI_API_KEY=<freemodel>`, `FINSCRAPE_WIRE_API=responses`, `FINSCRAPE_MODEL=gpt-5.4-mini`
- `FINSCRAPE_HEURISTIC_FALLBACK=true` (worker — ingest never stalls if the LLM is down)

API-only: `WORLDFIN_CORS_ORIGINS`, `FINSCRAPE_API_KEY`, `WORLDFIN_RUN_MIGRATIONS=true`, `WORLDFIN_ENABLE_COUNCIL=true`.
The API reads `$PORT` (Render injects it; `settings.port` aliases `WORLDFIN_PORT`/`PORT`).

## Redeploy
- **Web:** `cd web && VITE_API_BASE=https://winfin-api.onrender.com npm run build && npx wrangler pages deploy dist --project-name=winfin --branch=main`
- **API:** push to `master` → Render auto-deploys (`autoDeploy: yes`). Or POST a deploy via the Render API.
- **Worker:** runs every 30 min automatically; `gh workflow run ingest.yml` to fire now.

## Known free-tier limits
- Render free **sleeps after 15 min idle** → first hit after idle ~30–50 s (cold start). A keep-warm GH cron ping fixes it (uses free Actions minutes).
- Worker updates the dashboard on **refresh**, not live WS push (cross-process WS needs Redis — deferred).
- GitHub cron can be delayed/skipped under load (~"every 30 min", not exact).
- Neon: 0.5 GB + 100 compute-hrs/mo; freemodel/OpenRouter free have daily caps — the heuristic fallback absorbs LLM exhaustion.

## Keys / secrets
These are **temporary throwaway account keys** — kept in **GitHub → Settings → Secrets** and
**Render → Environment** only (never in the repo, never in Neon).

⚠️ **The freemodel.dev AI key (`OPENAI_API_KEY`) stops working after 2026-07-28.** After that date:
- The **worker keeps ingesting** — `FINSCRAPE_HEURISTIC_FALLBACK=true` falls back to heuristic
  scoring + entity-map tickers, so events still land (no LLM affected_entities / reasoning).
- On-demand `/api/ai/analyze` and the council go best-effort/empty until a new LLM is wired.
- **To restore full LLM:** get a new free key (freemodel.dev again, or OpenRouter `:free`, or a paid
  key) and update `OPENAI_API_KEY` (+ `OPENAI_BASE_URL`/`FINSCRAPE_MODEL`/`FINSCRAPE_WIRE_API`) in the
  GitHub secret + Render env. No code change needed.
