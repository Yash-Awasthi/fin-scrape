# Notes

Handover log. Open work lives in `task.md`; this file records what is known and
what has closed.

## Where things stand

As of 28 Sep 2026 the stack runs locally end to end: live feeds, the Postgres
worker, Ollama analysis, Laya sector labels and the API on `:8010`. One full
worker cycle ingested 7 new events and merged one cross-source report. All gates
are green: ruff, pyright, selfcheck, 1278 pytest (none skipped), web
typecheck/vitest/build, and 5 Playwright specs.

## Measured, worth not re-deriving

- Cold `/api/scenarios?window=200` is ~73s, almost entirely Ollama embedding
  (~360 ms/subject at `_PREFETCH_WORKERS = 6`). Cosine clustering is ~2.5s.
- That cost is once per process, not once per cache TTL — `embeddings.embed` is
  LRU-cached, so a TTL miss with a warm process rebuilds in ~0.04s. Startup
  warm-up now pays it, and the first caller sees single-digit milliseconds.
- Every scenario is a singleton and that is correct: `_find_duplicate` merges
  same-story coverage at ingest, so corroboration lives in one event's
  `articles`/`sources`, never in cluster size.
- Sector labels on 74 events after the Laya chain: 0 blank (was 31%),
  `technology` 11 (was 27% of labelled events), `other` 17, mostly political.
- The LLM's reasoning text itself invents technology angles ("affecting
  semiconductor firms"), so Laya is given article text, never the reasoning.
- Laya's checkpoint has no valid calibration for 11+ options, so the sector
  question offers ten and treats low confidence as `other`.

## Closed

- Worker re-sent every article to the LLM each cycle; now skips seen URLs (c9158d9e).
- RSS cap starved all but the fastest feeds; feeds interleave before the cap (c9158d9e).
- Same-story merges reached SQLite only; now copied to Postgres (c9158d9e).
- Correlation rows duplicated every cycle; now one row per signal (c9158d9e).
- Junk tickers (NATO, CIA, indices) filtered (c9158d9e).
- Scenario cards read 51–52% and said "reduce other"; fixed (c9158d9e).
- Local `.env` leaked into tests (1aef71dd); smoke tests used stale settings (43e501ba).
- Playwright reused another stack's server on 4173; e2e now uses 4183.

## Local hazards

- `tests/server/` truncates its database, so it reads
  `WORLDFIN_TEST_DATABASE_URL` and refuses any database not named `*_test`.
  Locally that is `worldfin_test` on port 5434 (set as a Windows user variable).
- The nexus Docker stack holds 8000, 5432, 6379, 3000 and 4173. WorldFin's API
  runs on 8010; compose publishes Postgres on 5433, Redis on 6380, Grafana on
  3002; Playwright previews on 4183. The native Postgres 17 service runs on 5434
  and `.env` points `WORLDFIN_DATABASE_URL` there.
- The worker skips URLs in the Postgres `visited_urls` table; the SQLite
  `data/finscrape.db` still holds the pipeline's in-process dedup events, and
  merges found there are copied onto the Postgres row with the same subject.
- Laya (`pip install laya`, CPU torch) loads ~800MB on first use and takes ~2s
  per article on CPU. `FINSCRAPE_LAYA=0` turns it off.
- Local run needs Ollama serving `nomic-embed-text`; `qwen2.5:7b` via
  `OPENAI_BASE_URL` works for the analysis LLM at roughly 20s per article.
- A nightly Windows task "WorldFin DB backup" dumps `worldfin` into `backups/`
  (newest 14 kept); `make restore FILE=...` restores one.
