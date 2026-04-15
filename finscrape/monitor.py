"""
Real-time monitoring engine — continuous scraping loop.

Runs the pipeline on configurable intervals per source,
with rate limiting, backoff on errors, and breaking news detection.
"""

from __future__ import annotations

import logging
import signal
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

from finscrape.pipeline import FinScrapePipeline
from finscrape.dashboard import DashboardClient
from finscrape.models import FinEvent

logger = logging.getLogger(__name__)

# Default intervals in seconds per source.
DEFAULT_INTERVALS: dict[str, int] = {
    "yahoo": 300,
    "rss": 300,
    "cnbc": 300,
    "benzinga": 300,
    "bloomberg": 900,
    "reuters": 900,
    "seekingalpha": 900,
    "ft": 900,
    "marketwatch": 600,
    "investingcom": 600,
    "edgar": 1800,
}

# Maximum backoff interval (1 hour).
MAX_BACKOFF_SECONDS = 3600

# Breaking-news detection window (10 minutes).
BREAKING_NEWS_WINDOW = 600

# Minimum sources with overlapping tickers to flag breaking news.
BREAKING_NEWS_MIN_SOURCES = 3

# Minimum delay between requests to the same domain (seconds).
MIN_DOMAIN_DELAY = 2.0


class _SourceState:
    """Tracks runtime state for a single source."""

    __slots__ = (
        "name",
        "base_interval",
        "current_interval",
        "consecutive_failures",
        "last_run",
        "next_run",
    )

    def __init__(self, name: str, interval: int):
        self.name = name
        self.base_interval = interval
        self.current_interval = interval
        self.consecutive_failures = 0
        self.last_run: float = 0.0
        self.next_run: float = 0.0  # eligible immediately on first cycle

    def record_success(self) -> None:
        self.consecutive_failures = 0
        self.current_interval = self.base_interval
        self.last_run = time.monotonic()
        self.next_run = self.last_run + self.current_interval

    def record_failure(self) -> None:
        self.consecutive_failures += 1
        self.current_interval = min(
            self.base_interval * (2 ** self.consecutive_failures),
            MAX_BACKOFF_SECONDS,
        )
        self.last_run = time.monotonic()
        self.next_run = self.last_run + self.current_interval

    @property
    def is_due(self) -> bool:
        return time.monotonic() >= self.next_run


class Monitor:
    """
    Continuous scraping monitor.

    Runs each configured source on its own schedule using a threaded model.
    Provides rate limiting, exponential backoff on errors, and breaking-news
    detection when multiple sources report overlapping tickers in a short window.
    """

    def __init__(
        self,
        sources: list[str],
        intervals: Optional[dict[str, int]] = None,
        default_interval: Optional[int] = None,
        max_articles_per_source: int = 10,
        data_dir: Optional[str] = None,
        min_domain_delay: float = MIN_DOMAIN_DELAY,
        use_council: bool = False,
    ):
        self._sources = sources
        self._max_articles = max_articles_per_source
        self._data_dir = data_dir
        self._min_domain_delay = min_domain_delay
        self._use_council = use_council

        # Merge caller overrides with defaults.
        merged_intervals = dict(DEFAULT_INTERVALS)
        if default_interval is not None:
            for src in sources:
                merged_intervals[src] = default_interval
        if intervals:
            merged_intervals.update(intervals)

        # Per-source state.
        self._states: dict[str, _SourceState] = {}
        for src in sources:
            interval = merged_intervals.get(src, default_interval or 300)
            self._states[src] = _SourceState(src, interval)

        # Dashboard client (shared across cycles).
        self._dashboard = DashboardClient()

        # Rate-limiting: last request time per domain.
        self._domain_last_request: dict[str, float] = {}
        self._domain_lock = threading.Lock()

        # Recent events for breaking-news detection.
        # List of (timestamp_monotonic, source_name, set_of_tickers).
        self._recent_events: list[tuple[float, str, set[str]]] = []
        self._events_lock = threading.Lock()

        # Shutdown coordination.
        self._shutdown_event = threading.Event()
        self._threads: list[threading.Thread] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start the monitoring loop.  Blocks until shutdown signal."""
        self._install_signal_handlers()

        logger.info(
            "Monitor starting — %d sources: %s",
            len(self._sources),
            ", ".join(self._sources),
        )
        print(f"\n{'='*60}")
        print(f"  FinScrape Monitor — started {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Sources: {', '.join(self._sources)}")
        print(f"  Intervals: {', '.join(f'{s}={self._states[s].base_interval}s' for s in self._sources)}")
        print(f"{'='*60}\n")

        # Launch one thread per source.
        for src in self._sources:
            t = threading.Thread(
                target=self._source_loop,
                args=(src,),
                name=f"monitor-{src}",
                daemon=True,
            )
            self._threads.append(t)
            t.start()

        # Main thread waits for shutdown.
        try:
            while not self._shutdown_event.is_set():
                self._shutdown_event.wait(timeout=1.0)
        except KeyboardInterrupt:
            pass

        self._shutdown()

    def stop(self) -> None:
        """Request a graceful shutdown from any thread."""
        self._shutdown_event.set()

    # ------------------------------------------------------------------
    # Signal handling
    # ------------------------------------------------------------------

    def _install_signal_handlers(self) -> None:
        """Register SIGINT/SIGTERM for graceful shutdown."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_signal)

    def _handle_signal(self, signum: int, frame) -> None:
        signame = signal.Signals(signum).name
        logger.info("Received %s — shutting down gracefully", signame)
        print(f"\n[MONITOR] Received {signame} — shutting down...")
        self._shutdown_event.set()

    def _shutdown(self) -> None:
        logger.info("Monitor shutting down — waiting for threads")
        print("[MONITOR] Waiting for source threads to finish...")
        for t in self._threads:
            t.join(timeout=10.0)
        print("[MONITOR] Shutdown complete.")
        logger.info("Monitor stopped")

    # ------------------------------------------------------------------
    # Per-source loop (runs in its own thread)
    # ------------------------------------------------------------------

    def _source_loop(self, source_name: str) -> None:
        """Continuous loop for a single source."""
        state = self._states[source_name]

        while not self._shutdown_event.is_set():
            if not state.is_due:
                # Sleep in small increments so we can respond to shutdown quickly.
                self._shutdown_event.wait(timeout=1.0)
                continue

            self._run_source(source_name, state)

    def _run_source(self, source_name: str, state: _SourceState) -> None:
        """Execute one scrape cycle for a source."""
        # Rate-limit by domain.
        self._enforce_domain_delay(source_name)

        cycle_start = time.monotonic()
        ts = datetime.now().strftime("%H:%M:%S")
        logger.info("[%s] Cycle start", source_name)
        print(f"[{ts}] [{source_name.upper()}] Starting scrape cycle...")

        try:
            pipeline = FinScrapePipeline(
                sources=[source_name],
                max_articles_per_source=self._max_articles,
                data_dir=self._data_dir,
                use_council=self._use_council,
            )
            events = pipeline.run()
            elapsed = time.monotonic() - cycle_start

            state.record_success()

            logger.info(
                "[%s] Cycle complete — %d events in %.1fs (next in %ds)",
                source_name,
                len(events),
                elapsed,
                state.current_interval,
            )
            print(
                f"[{ts}] [{source_name.upper()}] Done — {len(events)} events "
                f"in {elapsed:.1f}s (next in {state.current_interval}s)"
            )

            # Push to dashboard.
            if events and self._dashboard.is_configured:
                result = self._dashboard.push_events([e.to_dict() for e in events])
                logger.info("[%s] Dashboard push: %s", source_name, result)

            # Feed into breaking-news detector.
            if events:
                self._record_events_for_breaking_news(source_name, events)

        except Exception as exc:
            elapsed = time.monotonic() - cycle_start
            state.record_failure()

            logger.error(
                "[%s] Cycle failed (attempt %d) — %s (backoff %ds)",
                source_name,
                state.consecutive_failures,
                exc,
                state.current_interval,
            )
            print(
                f"[{ts}] [{source_name.upper()}] ERROR: {exc} "
                f"(backoff {state.current_interval}s, failures={state.consecutive_failures})"
            )

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------

    def _enforce_domain_delay(self, source_name: str) -> None:
        """Ensure minimum delay between requests to the same logical domain."""
        domain = self._source_to_domain(source_name)
        with self._domain_lock:
            last = self._domain_last_request.get(domain, 0.0)
            elapsed = time.monotonic() - last
            if elapsed < self._min_domain_delay:
                wait = self._min_domain_delay - elapsed
                logger.debug("[%s] Rate limit — sleeping %.2fs for domain %s", source_name, wait, domain)
                time.sleep(wait)
            self._domain_last_request[domain] = time.monotonic()

    @staticmethod
    def _source_to_domain(source_name: str) -> str:
        """Map source names to their primary domains for rate-limiting purposes."""
        domain_map = {
            "yahoo": "finance.yahoo.com",
            "bloomberg": "bloomberg.com",
            "reuters": "reuters.com",
            "cnbc": "cnbc.com",
            "rss": "rss",
            "marketwatch": "marketwatch.com",
            "seekingalpha": "seekingalpha.com",
            "benzinga": "benzinga.com",
            "investingcom": "investing.com",
            "ft": "ft.com",
            "edgar": "sec.gov",
        }
        return domain_map.get(source_name, source_name)

    # ------------------------------------------------------------------
    # Breaking-news detection
    # ------------------------------------------------------------------

    def _record_events_for_breaking_news(
        self, source_name: str, events: list[FinEvent]
    ) -> None:
        """Record events and check for breaking-news conditions."""
        now = time.monotonic()
        tickers_this_batch: set[str] = set()
        for ev in events:
            tickers_this_batch.update(ev.tickers)

        if not tickers_this_batch:
            return

        with self._events_lock:
            self._recent_events.append((now, source_name, tickers_this_batch))

            # Prune events older than the detection window.
            cutoff = now - BREAKING_NEWS_WINDOW
            self._recent_events = [
                (t, s, tk) for t, s, tk in self._recent_events if t >= cutoff
            ]

            # Check: do 3+ distinct sources share any ticker within the window?
            self._check_breaking_news()

    def _check_breaking_news(self) -> None:
        """
        Detect breaking news: if 3+ distinct sources produced events with
        overlapping tickers within the detection window, fire an alert.

        Must be called while holding ``_events_lock``.
        """
        # Build ticker -> set-of-sources mapping.
        ticker_sources: dict[str, set[str]] = defaultdict(set)
        for _ts, source, tickers in self._recent_events:
            for tk in tickers:
                ticker_sources[tk].add(source)

        for ticker, sources in ticker_sources.items():
            if len(sources) >= BREAKING_NEWS_MIN_SOURCES:
                self._fire_breaking_news_alert(ticker, sources)

    def _fire_breaking_news_alert(self, ticker: str, sources: set[str]) -> None:
        """Push a breaking-news alert to dashboard and logs."""
        ts = datetime.now().strftime("%H:%M:%S")
        msg = (
            f"BREAKING NEWS detected for {ticker} — "
            f"reported by {len(sources)} sources: {', '.join(sorted(sources))}"
        )
        logger.warning(msg)
        print(f"\n[{ts}] *** {msg} ***\n")

        if self._dashboard.is_configured:
            alert_event = {
                "subject": f"Breaking news alert: {ticker}",
                "event_type": "breaking_news",
                "tickers": [ticker],
                "impact_direction": "unknown",
                "signal_score": 0,
                "confidence": 0.0,
                "verdict": "OBSERVE",
                "sources": sorted(sources),
                "articles": [],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "breaking_news": True,
            }
            self._dashboard.push_events([alert_event])
