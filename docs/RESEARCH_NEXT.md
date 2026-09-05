# Research → Next: where WorldFin goes from here

*Synthesized from open-source landscape research, trader pain-point threads, and
patterns mined from our own absorbed reference repos (September 2026).*

---

## What the research says

### Scraping speed & anti-bot (what actually works in 2025/26)

| Layer | Best open source | Our status |
|---|---|---|
| HTTP-level (fastest) | **curl_cffi** TLS/JA3 impersonation — consensus "fastest free bypass" | ✅ vendored + our `fastfetch` (profile rotation on 403/429, ETag caching) |
| Anti-detect browser (heavy JS/Cloudflare) | **Camoufox** (custom Firefox build) > patched Playwright | ⚠️ we have patchright (patched Playwright); Camoufox is the upgrade path |
| Full framework | **Scrapling** — "fastest undetectable" scraping lib | ✅ vendored at `finscrape/engine/scrapling` |
| Fallback | FlareSolverr (maintenance shaky), nodriver | optional dev-mode tool later |
| Managed (paid) | ZenRows, ScrapingBee, TinyFish | dev-mode `news_fetch` class accepts any of them |

Sources: [Scrapfly anti-bot survey](https://scrapfly.io/blog/posts/best-anti-bot-bypass-tools),
[tools comparison](https://dev.to/vhub_systems_ed5641f65d59/web-scraping-tools-comparison-2026-requests-vs-curlcffi-vs-playwright-vs-scrapy-2fad),
[Datahut tests](https://www.blog.datahut.co/post/web-scraping-tools/).

### News infrastructure (what people actually use/want)

- **RSSHub** ("Everything is RSSible") — 5,000+ instances turning *anything* into RSS.
  → Our single biggest cheap win: add an RSSHub instance as a dev-mode source and we
  inherit thousands of feeds (Weibo, gov sites, regulators) with zero new scrapers.
- **GDELT 2.0 / GDELT Cloud** — already our ingestor; GDELT Cloud adds CAMEO/ACLED-aligned
  structured events → better second-order mapping later.
- **EventRegistry/NewsAPI.ai, Marketaux, Finnhub** — what paid competitors ship:
  entity/ticker-tagged news + sentiment + WebSocket delivery. Our dev-mode classes
  accept them all; the differentiator must be our *free* pipeline.
- Developer wish-list (from API comparisons + Reddit): free tiers that survive past
  prototyping, entity/ticker metadata, **self-hosting**, WebSocket delivery, clean docs.

### Global market data (how the trading bots do it)

- **China**: AKShare / Tushare (libs) — but the raw endpoints they wrap are keyless:
  Eastmoney `push2.eastmoney.com/api/qt/...` and Sina `hq.sinajs.cn` (Referer trick).
  Our absorbed `tradingagents-ashare`, `qlib`, `deepear` all use exactly these.
  → **Implemented now**: `finscrape/exchanges.py` ships both adapters.
- **India**: yfinance `.NS`/`.BO` covers NSE/BSE; official NSE real-time is a paid
  product; OpenBB still has open issues for NSE/BSE → an opening for us.
- **Everything else**: Yahoo suffix convention (`.L`, `.DE`, `.PA`, `.T`, `.HK`, `.KS`,
  `.SA`, `.SR`, …) covers ~30 exchanges from one dependency we already vendor.
- **Execution frameworks** (later, roadmap): vnpy (CN gateways), NautilusTrader (Rust core),
  Freqtrade. We stay intelligence-first; these are Phase-16 candidates.

### What traders say they want (Reddit pain-point threads)

1. **One screen**: news + sentiment + technicals + alerts consolidated (fragmentation is
   the #1 complaint — every builder thread is a response to it).
2. **Low-noise, actionable alerts** — not more feeds; better filtering.
3. **Early (pre-crowd) signals**: Reddit hype, alt-data, "what others ignore".
4. **Skepticism of paid tools** — "is anything worth paying for?" is a recurring theme.

Sources: [r/Daytrading: worth paying for?](https://www.reddit.com/r/Daytrading/comments/1p9vib8/what_trading_tool_is_worth_paying_for/),
[r/Trading: what's missing](https://www.reddit.com/r/Trading/comments/1rrkxq3/what_do_you_think_is_truly_missing_in_todays/),
[Reddit-hype detector](https://www.reddit.com/r/Daytrading/comments/1pgoolk/built_a_tool_that_spots_reddit_hype_before_the/),
[overlooked data edge](https://www.reddit.com/r/Daytrading/comments/1q6fux3/i_tracked_stuff_most_traders_ignore_heres_how/).

---

## Our gap list (ranked)

0. **Skip-list audit (post-hoc, verified)** — every "skip" from the absorption was
   re-checked against reality:
   - All 9 "already a pip dependency" claims verified TRUE in `pyproject.toml`.
   - Every "pip-installable utility" skip has an in-house replacement already in the
     tree: `server/circuit.py` (circuit breakers), `server/rate_limit.py` (rate
     limiting), `server/ws.py` (pub/sub), `finscrape/alerts.py` (Telegram via HTTP),
     `finscrape/analysis/ai_client.py` (OpenAI-compatible client, no SDK needed).
   - `praw` / `rapidfuzz` are used only inside absorbed reference code — they become
     real dependencies when the social-panel upgrade (praw) and fuzzy dedup speedup
     (rapidfuzz, which absorbed `py-gdelt` already imports) are wired. Not installed
     yet by design (lean deps).
   - **three-globe surprise**: the installed 2.45.2 (= latest npm) upstream source in
     `reference/three-globe` no longer contains a Bars layer at all (layers/: arcs,
     hexbin, polygons, points, tiles, … — no bars.js). The globe "bars" are therefore
     correctly built as extruded polygons in `web/src/globe/globe.ts` + `toBars()` —
     this is the supported path, not a workaround. Watch upstream for a bars
     re-addition before ever switching back.
1. **Global exchange coverage was US-only** → ✅ `finscrape/exchanges.py` (28 exchanges,
   keyless CN adapters) — needs wiring into the pipeline's market-facts + panels.
2. **Site scrapers drift** (marketwatch/seekingalpha/investingcom return 0) → keep RSS
   as spine, add RSSHub as a dev-mode source, fix scrapers opportunistically.
3. **Alert quality** — correlation engine fires 194 alerts for a handful of events.
   Needs scoring/ranking + dedup so alerts are low-noise (traders' #1 ask).
4. **Suggestions are naive** — volume × trust only; add momentum (mention velocity),
   novelty, and per-verdict weighting; expose per-exchange suggestions once the
   registry feeds the pipeline.
5. **No WebSocket push for news** (server has WS hub; ingest path doesn't emit).
6. **Latency** — LLM analysis is CPU-bound locally; embeddings dedup helps, but
   async/batched analysis + "headline-first, body-later" two-phase ingestion is the fix.
7. **Event ticker display duplicates** — cosmetic, known.

## Where we can be genuinely first

**"The free, local-first, global geopolitical market terminal."** Nobody combines:
- all-exchange coverage with keyless native adapters (paid terminals gate this),
- a local LLM + local embeddings pipeline ($0 running cost — every competitor is a
  cloud API),
- verified-accuracy signals (we track hit-rates per verdict and per *source* and feed
  that trust back into suggestions — nobody open-source does the trust loop),
- self-hosted privacy (traders increasingly don't want their watchlists in someone's cloud).

The trust loop is the moat: every alert we fire is scored against reality, and that
score changes future ranking. Ship that well and "first" follows.

## Immediate roadmap (next sessions)

1. Wire `exchanges.get_global_quotes` into `get_indicators`/market-facts so the council
   reasons over any market's live data, not just yfinance-US.
2. Alert ranking layer (score, cap, group) before push.
3. RSSHub dev-mode source (`news_fetch` class) — thousands of feeds for free.
4. Momentum into suggestions (mentions/hour velocity, breaking-news multiplier).
5. Two-phase ingestion: headline+summary analyzed instantly, full body enriches after.
6. Camoufox behind the dev-mode `scraping` class for the hardest anti-bot sites.
