# Tasks

The working list for WorldFin. `notes.md` is the handover log that goes with it.

## How to work this list

- Take open items top to bottom. For each one: investigate, write a failing test,
  fix, check it live against the running stack, then make one commit.
- When an item closes, delete it here and add one line to `notes.md` under
  "Closed" (what changed, the commit, the live check).
- A **gated** item needs something only the owner can supply. Skip it and add a
  line under its entry saying what was checked and why it is still blocked.
- Push at the end of the session.

Local stack: API `:8010`, Postgres 17 `:5434` (database `worldfin`; tests use
`worldfin_test` through `WORLDFIN_TEST_DATABASE_URL`), Ollama `:11434`. The Docker
stack called nexus owns 8000, 5432, 6379, 3000 and 4173; never use those ports.

Gates to keep green: `pytest -q`, `ruff check` and `ruff format --check` on the
`NEW_DIRS` in the Makefile, `pyright`, `python -m tests.server.selfcheck`, and in
`web/`: `npm run typecheck`, `npm run test`, `npm run build`, `npx playwright test`.

## Open

### 1. Company headlines lose their sector
"amd joins 1 trillion club" and "amazon amzn to join 4 trillion club" are
labelled `other`. `laya.choose_sector` rejects the LLM's "technology" without
a keyword, and the keyword list cannot name every company.
- Fix direction: a sector for the tickers in `finscrape/analysis/ticker_map.py`,
  passed into `choose_sector` as supporting evidence alongside keywords.
- Test: `choose_sector("technology", view_other, "", tickers=["AMD"])` returns
  `technology`, and a political story with no tickers still returns `other`.
- Live check: re-label the corpus and confirm neither headline reads `other`
  and that no Gaza or Pakistan story turns into `technology`.

### 2. A measured sector accuracy number
The sector chain was tuned by eye on 74 events. There is no fixed evaluation.
- Build `tests/fixtures/sector_gold.json` (about 50 real subjects with the
  expected sector and a one-line reason) and an eval test that runs the chain
  without Laya and reports accuracy. Record the number in `notes.md`.
- Mark the gold labels as provisional so the owner can review them.
- Live check: run the eval with Laya installed and record that number too.

### 3. Feed-level health for world RSS
`source_health` has one `world_rss` row. A single dead feed out of 32 is
invisible; it only shows as a WARN line in the log.
- Record one row per feed (`world/<key>`) with its entry count and status.
- Test: a feed whose fetch fails produces a WARN row; the others stay OK.
- Live check: `/api/health` lists every feed after one worker cycle.

### 4. GDELT runs on its own slower interval
GDELT answers 429 on most first attempts. It shares the 15-minute interval.
- Add `WORLDFIN_GDELT_INTERVAL_MIN` (default 30) and use it for that job only.
- Test: the scheduler gives the `gdelt` job the configured interval.
- Live check: one cycle logs fewer 429 retries.

### 5. ETag accepts lists and `*`
The ETag middleware compares `If-None-Match` as one exact string, so a client
sending `W/"a", W/"b"` or `*` gets 200 instead of 304.
- Test: both forms return 304 for an unchanged response.
- Live check: `curl -H 'If-None-Match: *' localhost:8010/api/stats` returns 304.

### 6. Scenario direction once outcomes exist
Direction leads with each event's `signal_score` until `predict()` reaches the
`empirical` tier. The backtest has now scored 37 outcomes.
- Investigate what tier current scenarios report and whether the blend in
  `finscrape/scenarios._member_p` still makes sense with real outcomes.
- Test and change only if the numbers show a problem; otherwise record the
  finding in `notes.md` and close.

### 7. Quiet the test warnings
pytest prints 21 warnings, including Starlette's notice that `httpx` with its
TestClient is deprecated.
- Fix each at its source; do not filter warnings away.
- Check: `pytest -q -W error::DeprecationWarning` passes for our own code.

### 8. Full-stack end-to-end test
The Playwright suite mocks REST and WebSocket by design.
`tests/server/test_routes_smoke.py` is the only test that touches a live database.
- Add one Playwright spec that runs against the real API and `worldfin_test`,
  seeded with `server.seed`, and walks feed, inspector and scenarios.
- Keep it out of the default CI run if CI has no Postgres; document how to run it.

### 9. One store for local state
`data/finscrape.db` (SQLite) still holds the pipeline's dedup events, alert
rules, portfolio and signal outcomes. The worker copies merges to Postgres by
subject, which works only while both stores agree.
- Move the dedup lookup (`FinScrapePipeline._find_duplicate`) to read recent
  events from Postgres, then retire the SQLite events table.
- Test: a paraphrased second report merges into the Postgres row with no
  SQLite involved.
- Large item: split it into more than one commit if the steps stand alone.

### 10. Upgrade ruff to 0.16
Ruff and pyright are pinned (`pyproject.toml`, dev group) because `uv.lock` is not
committed and CI once picked up ruff 0.16.9, whose new default rules reported 92
findings (RUF100, UP017, BLE001, I001 and others) in code that had not changed.
- Bump the pin, run `ruff check` on the `NEW_DIRS`, and fix the findings in the
  same commit. Blind `except Exception` handlers that guard a worker cycle need a
  reason comment or a narrower type, not a blanket ignore.
- Check: CI's backend job goes green on the new version.

## Gated

### G1. ReliefWeb source
v1 is retired (410) and v2 rejects unapproved app names (403). Needs the owner to
request an app name at https://apidoc.reliefweb.int/parameters#appname and set
`RELIEFWEB_APPNAME` in `.env`; the source turns itself on after that.

### G2. Fine-tune Laya
Needs a labelled set of WorldFin decisions and a GPU run of the upstream
notebook. Revisit after item 2 gives an accuracy number worth improving.

### G3. Refuse the default API key in production
Startup warns when `FINSCRAPE_API_KEY` is the published default. Refusing needs a
signal that separates a deployment from a local demo (for example
`WORLDFIN_ENV=production`). That is a product decision for the owner.

### G4. CORS origins
CORS is `*` by default, and the API accepts no credentials. Tighten it only when a
deployment names its browser origins in `WORLDFIN_CORS_ORIGINS`.
