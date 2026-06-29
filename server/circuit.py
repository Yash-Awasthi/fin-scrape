"""Minimal circuit breaker for flaky upstreams (CoinGecko, RSS hosts).

Three states: closed (normal) → open (tripped, fail fast) → half-open (one probe).
Stops a dead upstream from eating threadpool slots and timeout budget on every request.

Usage:
    cb = CircuitBreaker("coingecko")
    try:
        data = cb.call(fetch)          # raises CircuitOpen while tripped
    except CircuitOpen:
        data = fallback

Pure + deterministic: pass `now` in tests; no wall-clock dependency leaks out.
"""

from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class CircuitOpen(RuntimeError):
    """Raised by `call` while the breaker is open (upstream presumed down)."""


class CircuitBreaker:
    def __init__(
        self, name: str, fail_threshold: int = 5, reset_after_s: float = 30.0
    ) -> None:
        self.name = name
        self.fail_threshold = fail_threshold
        self.reset_after = reset_after_s
        self._failures = 0
        self._opened_at: float | None = None

    def _now(self, now: float | None) -> float:
        return time.monotonic() if now is None else now

    def allow(self, now: float | None = None) -> bool:
        """True if a call may proceed (closed, or half-open probe is due)."""
        if self._opened_at is None:
            return True
        if self._now(now) - self._opened_at >= self.reset_after:
            return True  # half-open: let one probe through
        return False

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self, now: float | None = None) -> None:
        self._failures += 1
        if self._failures >= self.fail_threshold:
            self._opened_at = self._now(now)

    def call(self, fn: Callable[[], T], now: float | None = None) -> T:
        if not self.allow(now):
            raise CircuitOpen(f"circuit {self.name!r} open")
        try:
            result = fn()
        except Exception:
            self.record_failure(now)
            raise
        self.record_success()
        return result
