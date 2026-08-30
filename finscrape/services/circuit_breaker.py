"""
Circuit Breaker — Extracted from pybreaker patterns.

Circuit breaker pattern with:
- Closed/Open/Half-Open states
- Failure threshold detection
- Recovery timeout
- Decorator support
"""
from __future__ import annotations

import functools
import time
from enum import Enum
from typing import Any, Callable, Optional


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Raised when circuit is open."""
    pass


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exceptions: Optional[tuple] = None,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exceptions = expected_exceptions or (Exception,)
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.monotonic()

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and time.monotonic() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                self._last_state_change = time.monotonic()
        return self._state

    def _handle_success(self) -> None:
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            self._last_state_change = time.monotonic()
        self._failure_count = 0
        self._success_count += 1

    def _handle_failure(self) -> None:
        self._failure_count += 1
        self._success_count = 0
        self._last_failure_time = time.monotonic()

        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._last_state_change = time.monotonic()

    def record_success(self) -> None:
        self._handle_success()

    def record_failure(self) -> None:
        self._handle_failure()

    def can_execute(self) -> bool:
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True
        return False

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not self.can_execute():
                raise CircuitBreakerError(f"Circuit '{self.name}' is open")
            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except self.expected_exceptions as e:
                self.record_failure()
                raise
        return wrapper

    def get_state_info(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time,
        }


class CircuitBreakerRegistry:
    """Registry of circuit breakers."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
            )
        return self._breakers[name]

    def get_all(self) -> list[dict]:
        return [b.get_state_info() for b in self._breakers.values()]

    def reset(self, name: str) -> None:
        if name in self._breakers:
            self._breakers[name]._state = CircuitState.CLOSED
            self._breakers[name]._failure_count = 0
