"""Tiny in-process TTL cache with named tiers (fast / medium / slow).

Replaces the ad-hoc dict cache in routes/data.py. One module so every cached read
shares the same eviction + tier semantics. Values are whatever the producer returns
(already-serialized dicts/lists here).

ponytail: process-local, no Redis. Ceiling = single replica; multi-replica wants a
shared store. Upgrade path: swap `_store` get/set for Redis GET/SETEX keyed the same.
"""

from __future__ import annotations

import time
from typing import Callable

# Tier TTLs in seconds — pick by how fast the upstream truth moves.
FAST = 30  # volatile (crypto/markets quotes)
MEDIUM = 120  # semi-static (RSS feeds)
SLOW = 600  # rarely-changing (registries, rollups)

_store: dict[str, tuple[float, object]] = {}


def get_or_set(key: str, ttl: float, produce: Callable[[], object]) -> object:
    """Return cached value for `key`, or call `produce()` and cache it for `ttl`s."""
    now = time.monotonic()
    hit = _store.get(key)
    if hit and hit[0] > now:
        return hit[1]
    value = produce()
    _store[key] = (now + ttl, value)
    return value


def clear() -> None:
    """Drop everything (tests / manual cache-bust)."""
    _store.clear()
