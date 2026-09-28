"""Phase 3 offline tests: source registry + STALE derivation (no DB, no network).

The live worker cycle (scrape→analyze→ingest→source_health, /api/health freshness)
is the docker verify.
"""

import pytest

from worker.health import derive_status
from worker.sources import build_sources


def test_build_sources_has_world_rss_and_event_ingestors(monkeypatch):
    monkeypatch.setenv("RELIEFWEB_APPNAME", "test-app")
    sources = build_sources(max_articles=5)
    assert "world_rss" in sources
    for name in ("usgs_quakes", "gdelt", "reliefweb"):
        assert name in sources and callable(sources[name])
    assert "coingecko" not in sources  # crypto removed from the event mix
    assert "opensky" not in sources  # data layer, not an event source


def test_derive_status_stale_after_window():
    assert derive_status("OK", age_s=10, stale_after_min=60) == "OK"
    assert derive_status("OK", age_s=3601, stale_after_min=60) == "STALE"
    # non-OK statuses pass through untouched; None age never goes stale
    assert derive_status("WARN", age_s=999999, stale_after_min=60) == "WARN"
    assert derive_status("EMPTY", age_s=10, stale_after_min=60) == "EMPTY"
    assert derive_status("OK", age_s=None, stale_after_min=60) == "OK"


def test_velocity_history_builds_a_baseline_and_decays():
    """detect_velocity_spike needs baseline > 0, so a worker that never records past
    cycles can never emit the signal at all."""
    from worker.runner import Worker

    w = Worker.__new__(Worker)  # skip __init__: no pipeline or network needed
    w._corr_velocity = {}

    w._record_velocity({"topics": {"energy": 2}})
    w._record_velocity({"topics": {"energy": 4, "conflict": 1}})
    # energy went quiet; it still records a 0 so its baseline decays
    w._record_velocity({"topics": {"conflict": 3}})

    assert w._corr_velocity["energy"] == [2, 4, 0]
    # conflict only appeared in cycle 2 — no back-fill, so a brand-new topic cannot
    # spike against a baseline it never had.
    assert w._corr_velocity["conflict"] == [1, 3]


def test_velocity_history_window_is_bounded():
    from server.correlate import VELOCITY_WINDOW_DAYS
    from server.settings import get_settings
    from worker.runner import Worker

    w = Worker.__new__(Worker)
    w._corr_velocity = {}
    interval = max(1, get_settings().worker_interval_minutes)
    window = max(2, int(VELOCITY_WINDOW_DAYS * 24 * 60 / interval))
    for i in range(window + 10):
        w._record_velocity({"topics": {"energy": i}})
    assert len(w._corr_velocity["energy"]) == window
    assert w._corr_velocity["energy"][-1] == window + 9


def _fake_worker():
    from worker.runner import Worker

    w = Worker.__new__(Worker)
    w.sources = {"world_rss": lambda: [], "gdelt": lambda: []}
    return w


def test_scheduler_covers_every_source_plus_correlate_and_backtest():
    """The interval worker and the one-shot Action must do the same work; a source
    or job missing here silently never runs in the long-lived deployment."""
    pytest.importorskip("apscheduler")
    from server.settings import Settings
    from worker.main import _schedule

    worker = _fake_worker()
    scheduler = _schedule(worker, Settings(_env_file=None))
    ids = {job.id for job in scheduler.get_jobs()}
    assert ids == {"world_rss", "gdelt", "correlations", "backtest", "retention"}


def test_backtest_failure_does_not_take_the_worker_down():
    """Market data is flaky and scoring is resumable — a bad fetch must not kill the
    process or abort the rest of the cycle."""
    import asyncio

    from worker.main import _score_outcomes

    worker = _fake_worker()

    async def boom() -> int:
        raise RuntimeError("yfinance timed out")

    worker.run_backtest = boom
    assert asyncio.run(_score_outcomes(worker)) == 0
