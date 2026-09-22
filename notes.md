# Notes

Handover for the next session. Current branch: `fresh`.

## Where things stand

`/api/scenarios` has been run against live feeds, a real Postgres and a real
Ollama — not mocks. That pass fixed a `/api/suggestions` SQL bug that made the
route a 500 on every call, changed scenarios to count reports instead of cluster
members, consolidated the sector taxonomy, and added cache single-flight plus a
startup warm-up. All gates green: ruff, pyright, selfcheck, 1278 pytest, web
typecheck/vitest/build.

## Measured, worth not re-deriving

- Cold `/api/scenarios?window=200` is ~73s, almost entirely Ollama embedding
  (~360 ms/subject at `_PREFETCH_WORKERS = 6`). Cosine clustering is ~2.5s.
- That cost is once per process, not once per cache TTL — `embeddings.embed` is
  LRU-cached, so a TTL miss with a warm process rebuilds in ~0.04s. Startup
  warm-up now pays it, and the first caller sees single-digit milliseconds.
- Every scenario is a singleton and that is correct: `_find_duplicate` merges
  same-story coverage at ingest, so corroboration lives in one event's
  `articles`/`sources`, never in cluster size.
- `sector_impact` strings are short, clean tokens — they read as sectors. The
  problem is content, not format: 31% blank, 27% labelled `technology`
  regardless of subject.

## Next, in order

1. **Sector labelling.** Two-thirds of cards render no sector bar at all. The
   prompt enum was disambiguated but the fix is unvalidated — it needs a
   re-ingest against a small hand-labelled set to know if it helped.
2. **Junk tickers.** `NATO`, `CIA`, `IOM`, and indices `^DJI`/`^GSPC`/`^IXIC`
   render as tradeable chips. Needs a denylist and an index filter in
   `resolve_tickers`.
3. **Dead feeds.** `eu_commission` fails the fetch outright; `reliefweb` returns
   410, its API having been retired. Both degrade silently to WARN.
4. **Full-stack e2e.** The Playwright suite is entirely mocked by design;
   `tests/server/test_routes_smoke.py` is the only live-DB coverage.

Three known behaviours were left alone as product calls, not defects: scenario
`probability` is ≥50% by construction so every card reads 51–52%; direction
comes from lexicon sentiment over the analysis prose rather than `signal_score`,
which lets related events advise opposite ways; and a single sector leg always
draws a full-width bar because it is its own peak.

## Local hazards

- `tests/server/` TRUNCATEs whatever `WORLDFIN_DATABASE_URL` points at. Point it
  at a database whose contents you want and the suite deletes them.
- Re-running the worker inserts almost nothing: `visited_urls` in
  `data/finscrape.db` suppresses seen URLs, and `_find_duplicate` then merges
  the rest into existing rows. Clearing both is what rebuilds a corpus.
- Local run needs a `worldfin` role and database in Postgres, plus Ollama
  serving `nomic-embed-text`; `qwen2.5:7b` via `OPENAI_BASE_URL` works for the
  analysis LLM at roughly 20s per article.
