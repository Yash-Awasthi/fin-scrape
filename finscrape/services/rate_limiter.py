"""
Rate Limiter — Extracted from Verdict patterns.

Rate limiting with:
- Concurrent rate limiting
- Time window rate limiting
- Token bucket algorithm
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional


class ConcurrentRateLimiter:
    """Limit concurrent operations."""

    def __init__(self, max_concurrent: int = 5) -> None:
        self.max_concurrent = max_concurrent
        self.current = 0
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._event.set()

    def acquire(self, timeout: Optional[float] = None) -> bool:
        with self._lock:
            if self.current < self.max_concurrent:
                self.current += 1
                self._event.clear()
                return True
        return self._event.wait(timeout)

    def release(self) -> None:
        with self._lock:
            self.current = max(0, self.current - 1)
            if self.current < self.max_concurrent:
                self._event.set()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


class TimeWindowRateLimiter:
    """Rate limit within a time window."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: deque = deque()
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        now = time.time()
        with self._lock:
            while self._timestamps and self._timestamps[0] < now - self.window_seconds:
                self._timestamps.popleft()
            if len(self._timestamps) < self.max_requests:
                self._timestamps.append(now)
                return True
        return False

    def wait(self) -> float:
        now = time.time()
        with self._lock:
            if self._timestamps:
                oldest = self._timestamps[0]
                wait_time = self.window_seconds - (now - oldest)
                if wait_time > 0:
                    return wait_time
        return 0.0


class TokenBucketRateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
        return False

    def wait_for_tokens(self, tokens: int = 1) -> float:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0
            needed = tokens - self.tokens
            return needed / self.rate
