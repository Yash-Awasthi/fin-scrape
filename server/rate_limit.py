"""Per-client sliding-window rate limiter.

In-memory by design: one API replica is the WorldFin demo topology, so a process-local
deque of hit timestamps is the whole limiter — no Redis round-trip on the hot path.

ponytail: in-memory only. Ceiling = a single API replica (each process keeps its own
window). Upgrade path for >1 replica: back `Limiter.hit` with a Redis sorted-set
(ZADD now / ZREMRANGEBYSCORE < now-window / ZCARD) keyed on `settings.redis_url`.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque


class Limiter:
    """Sliding-window counter. `hit(key)` returns (allowed, retry_after_seconds)."""

    def __init__(self, limit_per_min: int, window_s: float = 60.0) -> None:
        self.limit = limit_per_min
        self.window = window_s
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, now: float | None = None) -> tuple[bool, int]:
        if self.limit <= 0:  # disabled
            return True, 0
        now = time.monotonic() if now is None else now
        q = self._hits[key]
        cutoff = now - self.window
        while q and q[0] <= cutoff:
            q.popleft()
        if len(q) >= self.limit:
            # retry once the oldest hit ages out of the window
            retry = max(1, int(q[0] + self.window - now) + 1)
            return False, retry
        q.append(now)
        return True, 0


def client_key(request) -> str:
    """Best-effort client identity: first X-Forwarded-For hop, else peer IP."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
