# WorldFin — Data Sources

Every external source WorldFin pulls, its access terms, and key status. All sources are
**keyless** (no API key required) in v1. Source of truth in code:
`finscrape/scrapers/world/feeds.py` and `finscrape/ingestors/`.

## License & compliance

worldmonitor.app (AGPL-3.0) is **never** copied into this repo — we use only
non-copyrightable **facts** (public feed URLs, country/crypto JSON) and **independently
reimplement** algorithms (clustering, correlation: `server/correlate.py`). fin-scrape stays MIT.

## World / geopolitics RSS feeds

Seed registry (`finscrape/scrapers/world/feeds.py`). `tier` ∈ wire/gov/intel/mainstream/market;
`risk` = propaganda risk used for trust weighting. Public RSS endpoints; classification is ours.
This is a representative subset — extendable; nothing is count-load-bearing.

| key | source | tier | risk | endpoint |
|---|---|---|---|---|
| un_news | UN News | gov | low | news.un.org/feed/subscribe/en/news/all/rss.xml |
| eu_commission | European Commission | gov | low | ec.europa.eu/commission/presscorner/api/rss |
| defense_one | Defense One | intel | low | defenseone.com/rss/all/ |
| war_on_the_rocks | War on the Rocks | intel | low | warontherocks.com/feed/ |
| csis | CSIS | intel | low | csis.org/analysis/feed |
| bbc_world | BBC World | mainstream | low | feeds.bbci.co.uk/news/world/rss.xml |
| guardian_world | The Guardian World | mainstream | low | theguardian.com/world/rss |
| aljazeera | Al Jazeera | mainstream | medium | aljazeera.com/xml/rss/all.xml |
| npr_world | NPR World | mainstream | low | feeds.npr.org/1004/rss.xml |
| dw_world | Deutsche Welle | mainstream | low | rss.dw.com/rdf/rss-en-world |
| france24 | France 24 | mainstream | low | france24.com/en/rss |
| reuters_world_gnews | Reuters (via Google News) | wire | low | news.google.com/rss/search (source:reuters) |
| ap_gnews | Associated Press (via Google News) | wire | low | news.google.com/rss/search (Associated Press) |
| cnbc_world | CNBC World | market | low | cnbc.com/id/100727362/device/rss/rss.html |

> Reuters/AP are pulled via Google News RSS search because their direct RSS is gated — the
> aggregator URL is a public fact. Respect each outlet's terms for downstream redistribution.

## Keyless free-API ingestors

`finscrape/ingestors/`. Network `fetch` is separate from pure `parse` (parsers unit-tested
against fixtures). All no-auth.

| ingestor | role | endpoint | notes |
|---|---|---|---|
| `usgs_quakes` | earthquakes (event) | earthquake.usgs.gov/.../summary/4.5_week.geojson | carries exact lat/lon; M4.5+ filter |
| `gdelt` | global news (event) | api.gdeltproject.org/api/v2/doc/doc | ArtList JSON; default conflict/crisis query |
| `reliefweb` | disasters (event) | api.reliefweb.int/v1/disasters | **requires `appname`** (`finscrape-worldfin`) |
| `coingecko` | crypto movers (event) | api.coingecko.com/api/v3/coins/markets | emits only \|24h%\| ≥ 8 movers |
| `opensky` | live flights (data layer) | opensky-network.org/api/states/all | NOT an event source; `parse_states` only |

### Terms notes
- **USGS** — US Government public domain.
- **GDELT** — free/open; be polite with request volume (worker intervals + jitter).
- **ReliefWeb** — free; `appname` query param is mandatory per their API terms.
- **CoinGecko** — public/demo tier; rate-limited. Keep `per_page` modest; cache later (Phase 8).
- **OpenSky** — anonymous access is rate-limited and time-resolution-limited; a flights layer,
  not a market signal.

## Key status

All sources above are **keyless**. The only optional keys in the system are the **LLM** backend
(`OPENROUTER_API_KEY`, or local Ollama via `OPENAI_BASE_URL`) and the ingest `FINSCRAPE_API_KEY`
(auth for mutating `/api` routes) — see `.env.example`.
