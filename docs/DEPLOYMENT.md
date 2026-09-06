# WorldFin — Deployment & API

The same codebase runs three ways. All expose the identical REST contract
(`/api/*`), so the SPA never changes between them.

## 1. Local (this machine) — SQLite + Ollama

```bash
npm --prefix web run build
.venv/Scripts/python.exe main.py serve --port 8080
```

AI runs on local Ollama (`qwen2.5:7b` analysis, `nomic-embed-text` dedup):
`ollama serve`, then dev mode on (`main.py devtools on`). $0/month.

## 2. Cloud AI, same local server

Any OpenAI-compatible provider. Two ways:

- **Dev mode**: `main.py devtools set ai openrouter --field api_key=sk-or-...`
  (or provider `openai`, base_url `https://api.openai.com/v1`, model `gpt-4o-mini`)
- **Env**: `OPENAI_BASE_URL` + `OPENAI_API_KEY` + `FINSCRAPE_MODEL`

## 3. Deployed API (Render / Railway / any container host)

`Dockerfile.serve` builds the API + prebuilt SPA in one image:

```bash
docker build -f Dockerfile.serve -t worldfin .
docker run -p 8080:8080 \
  -e OPENROUTER_API_KEY=sk-or-... \
  -e FINSCRAPE_MODEL=deepseek/deepseek-chat \
  -v worldfin-data:/app/data \
  worldfin
```

- SQLite persists in the mounted volume (`/app/data`).
- The AI provider is whatever the env says — cloud keys, never in the image.
- For multi-user/production scale, the Postgres-backed `server/` (docker-compose)
  remains the reference deployment.

## API surface (view-only — the platform renders intelligence, it never trades)

**Feature parity between local (`main.py serve`) and production (`server/`) —
the SPA is one build for both.**

| Endpoint | Purpose | Local | Production |
|---|---|---|---|
| `GET /api/quotes?symbols=` | live quotes, all markets | ✅ | ✅ `routes/market.py` |
| `GET /api/candles?symbol=&period=&interval=` | OHLCV chart data | ✅ | ✅ `routes/market.py` |
| `GET /api/events` · `/api/stats` · `/api/dates` | stored intelligence | ✅ | ✅ |
| `GET /api/suggestions` | momentum-ranked tickers | ✅ | ✅ (surge multiplier in SQL) |
| `GET /api/predict/{id}` · `/api/reliability` | calibrated probabilities + evidence | ✅ | ✅ `routes/insight.py` |
| `GET /api/agents/analyze?ticker=` | multi-agent research commentary | ✅ | ✅ `routes/agents.py` |
| `GET /api/ai/analyze?id=` | per-event LLM reasoning | ✅ | ✅ |
| `GET /api/feeds` · `/api/rss-proxy` | world news feeds | ✅ | ✅ |
| `GET /api/accuracy` · `/api/sentiment` · `/api/portfolio` | tracking panels | ✅ | ✅ |
| `GET /api/correlations` | cross-source signals | ✅ (local heuristic) | ✅ (pipeline tables) |
| `GET /api/alerts` | fired pipeline alerts | ✅ | via worker tables |
| `WS /ws` | realtime event push | ✅ | ✅ |

Production deploy = Render (API from `server/`) + Cloudflare Pages (`web/dist`)
+ Neon Postgres + GitHub Actions worker — see README. The new routes ship
automatically with the `server/` deploy; no SPA rebuild needed beyond `npm run build`.
