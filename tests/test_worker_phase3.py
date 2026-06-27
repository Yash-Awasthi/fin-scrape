"""Phase 3 offline tests: source registry + STALE derivation (no DB, no network).

The live worker cycle (scrape→analyze→ingest→source_health, /api/health freshness)
is the docker verify.
"""

from worker.health import derive_status
from worker.sources import build_sources


def test_build_sources_has_world_rss_and_event_ingestors():
    sources = build_sources(max_articles=5)
    assert "world_rss" in sources
    for name in ("usgs_quakes", "gdelt", "reliefweb", "coingecko"):
        assert name in sources and callable(sources[name])
    assert "opensky" not in sources  # data layer, not an event source


def test_derive_status_stale_after_window():
    assert derive_status("OK", age_s=10, stale_after_min=60) == "OK"
    assert derive_status("OK", age_s=3601, stale_after_min=60) == "STALE"
    # non-OK statuses pass through untouched; None age never goes stale
    assert derive_status("WARN", age_s=999999, stale_after_min=60) == "WARN"
    assert derive_status("EMPTY", age_s=10, stale_after_min=60) == "EMPTY"
    assert derive_status("OK", age_s=None, stale_after_min=60) == "OK"
