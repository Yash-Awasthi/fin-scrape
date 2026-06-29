# WorldFin — Demo & Deployment

A scripted ~5-minute walkthrough of the WorldFin global market-intelligence dashboard,
plus one-command bring-up and a cloud-deploy appendix. This is the deal-quality demo:
ingest geopolitics + world news → resolve which tickers/sectors an event moves → judge
the impact → show it on a live globe → and **prove the calls were right** over time.

---

## Prerequisites

- **Docker + Docker Compose** (or Podman with the `docker compose` shim).
- ~4 GB free RAM, ports **8080** (web), **8000** (api), **5432** (postgres) free.
- **No API key required** — the dashboard runs on the seeded dataset out of the box.
  For live ingestion, supply an LLM backend (local Ollama *or* a BYOK OpenRouter key) in
  `.env`; see [`.env.example`](../.env.example).

---

## One-command bring-up (clean machine)

```bash
git clone <repo-url> fin-scrape && cd fin-scrape
cp .env.example .env          # defaults work; no key needed for the seeded demo
make demo                     # builds + starts the stack, then seeds it
```

`make demo` = `make up` (postgres + api + web, waits for health) **+** `make seed` (loads
the curated historical window). When it finishes:

- **Dashboard:** http://localhost:8080
- **API docs:** http://localhost:8000/docs

To reseed at any time (idempotent — same-day re-runs insert nothing new):

```bash
make seed
```

> The seed timestamps are **relative** (resolved to "the last ~6 days" at load time), so
> the globe, feed, calendar, and accuracy curve are full of fresh signal on every launch —
> never an empty-state demo.

---

## The 5-minute walkthrough

**1. The globe (≈30s).** Open http://localhost:8080. Events are plotted by location and
colored by verdict — **green = INVEST, red = PULL_OUT**, amber/neutral for OBSERVE/CAUTIOUS.
Note the cluster over the **Strait of Hormuz** and the **Red Sea** shipping lane: this is a
*world* monitor, not just a ticker feed. The globe auto-rotates when idle.

**2. Breaking correlation (≈45s).** The **BreakingNewsBanner** fires when independent
source-types corroborate one story. The seed includes a **triangulation** signal (wire +
gov + intel agree on the Red Sea disruption) and a **convergence** signal (Hormuz across
3+ source types). Open the **CorrelationPanel** — this is the "before it's news"
differentiator: one event surfacing across independent sources inside a tight time window.

**3. Click an event → the judgment chain (≈90s).** Click the **Hormuz closure** row in the
SignalFeed (or its globe point) to open the **SignalModal**. This is the core thesis on one
screen:
- **Verdict + signal score** (PULL_OUT, −4) with the reasoning.
- **Affected entities, role-tagged:** Oil majors *(primary)*, Shipping lines *(supplier)*,
  Defense contractors *(competitor)*, Marine insurers *(regulator)* — each with a
  directional impact. A geopolitics headline resolved into **who it moves**.
- **Second-order effects:** war-risk premiums, refiner scramble, LNG spillover.
- Click **Analyze** for on-demand AI expansion (uses your LLM backend if configured).

**4. The trust layer — AccuracyPanel (≈60s).** This is what convinces a company. The
**AccuracyPanel** shows the historical **hit-rate** (~87% on the seeded window), a
**by-verdict** breakdown (INVEST vs PULL_OUT), and an **equity curve** sparkline built from
realized price moves. The calls aren't just plausible — they're *scored*.

**5. Variants + panels (≈45s).** Use the **variant switch** (World / Finance / Crypto) to
reflow the panel grid. Tour the supporting panels: **MarketsPanel** (most-mentioned tickers
rolled up from events), **CryptoPanel**, **CalendarPanel** (click a day to load it),
**WorldNewsPanel**, **LiveTVPanel**. Panels drag/resize and persist their layout.

**Close (≈30s).** The pitch in one line: *geopolitics + world news in → which
tickers/sectors it moves → judged first- and second-order impact on a live globe → with the
receipts to prove the calls were right.*

---

## Verifying without the browser

Every panel is backed by an endpoint you can curl:

```bash
curl -s localhost:8000/api/stats        # totals + by-verdict
curl -s localhost:8000/api/dates        # calendar day counts
curl -s localhost:8000/api/accuracy     # hit-rate + equity curve
curl -s localhost:8000/api/correlations # breaking-correlation signals
curl -s localhost:8000/api/markets      # most-mentioned tickers
```

---

## Appendix: cloud deploy ("web later" is a flip, not a rewrite)

The same `docker-compose.yml` runs on any Docker host — the local-first design means cloud
is a config change, not a port:

1. Provision a small VPS / Fly.io / Render box with Docker.
2. Copy the repo + a production `.env` (set `WORLDFIN_CORS_ORIGINS` to your web origin, add
   a real `FINSCRAPE_API_KEY`, and an LLM backend for live ingestion).
3. `make up` (or `docker compose up -d --build`) behind a TLS-terminating reverse proxy.
4. `make seed` once for an instantly-populated dashboard; the **worker** service then keeps
   ingesting live world + finance events on its schedule.
5. Observability: `docker compose -f docker-compose.yml -f docker-compose.obs.yml up -d`
   adds Prometheus + Grafana + Loki (see [`RUNBOOK.md`](RUNBOOK.md)).

Auth, multi-tenant hosting, and managed Postgres are clean seams left for later (see
PLAN.md "Explicitly out of scope").
