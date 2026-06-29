"""Phase 8 hardening: unit tests + middleware integration (no DB needed).

The middleware tests mount a throwaway FastAPI app and run `configure_hardening` on it
with a couple of trivial routes, so the security/rate-limit/etag/error-envelope
behaviour is exercised end-to-end without a Postgres pool or the real routers.
"""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("pydantic_settings")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from server import cache  # noqa: E402
from server.circuit import CircuitBreaker, CircuitOpen  # noqa: E402
from server.rate_limit import Limiter  # noqa: E402
from server.settings import get_settings  # noqa: E402
from server.ssrf import SSRFError, assert_public_host, assert_public_url, is_public_ip  # noqa: E402

# --- SSRF guard -------------------------------------------------------------


def test_is_public_ip_rejects_private_and_loopback():
    for bad in (
        "127.0.0.1",
        "10.0.0.1",
        "192.168.1.1",
        "169.254.0.1",
        "::1",
        "0.0.0.0",
    ):
        assert is_public_ip(bad) is False, bad
    for good in ("8.8.8.8", "1.1.1.1", "93.184.216.34"):
        assert is_public_ip(good) is True, good


def test_assert_public_host_blocks_loopback_literal():
    with pytest.raises(SSRFError):
        assert_public_host("127.0.0.1")
    # a public literal resolves to itself and passes
    assert_public_host("8.8.8.8")


def test_assert_public_url_rejects_bad_scheme_and_private():
    with pytest.raises(SSRFError):
        assert_public_url("file:///etc/passwd")
    with pytest.raises(SSRFError):
        assert_public_url("http://169.254.169.254/latest/meta-data/")  # cloud metadata


# --- rate limiter -----------------------------------------------------------


def test_limiter_blocks_past_threshold_and_returns_retry():
    lim = Limiter(limit_per_min=3, window_s=60.0)
    assert all(lim.hit("ip", now=0.0)[0] for _ in range(3))
    allowed, retry = lim.hit("ip", now=0.0)
    assert allowed is False
    assert retry >= 1


def test_limiter_window_slides():
    lim = Limiter(limit_per_min=2, window_s=10.0)
    assert lim.hit("ip", now=0.0)[0]
    assert lim.hit("ip", now=1.0)[0]
    assert lim.hit("ip", now=2.0)[0] is False
    # first hit ages out after the 10s window → room again
    assert lim.hit("ip", now=11.0)[0] is True


def test_limiter_zero_disables():
    lim = Limiter(limit_per_min=0)
    assert all(lim.hit("ip")[0] for _ in range(100))


# --- circuit breaker --------------------------------------------------------


def test_circuit_opens_then_half_opens_then_recovers():
    cb = CircuitBreaker("x", fail_threshold=2, reset_after_s=5.0)

    def boom():
        raise RuntimeError("down")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            cb.call(boom, now=0.0)
    # tripped → fail fast without calling fn
    with pytest.raises(CircuitOpen):
        cb.call(boom, now=1.0)
    # after reset window → half-open probe allowed; a success closes it
    assert cb.call(lambda: "ok", now=10.0) == "ok"
    assert cb.allow(now=11.0) is True


# --- cache ------------------------------------------------------------------


def test_cache_memoizes_until_ttl_via_call_count():
    cache.clear()
    calls = {"n": 0}

    def produce():
        calls["n"] += 1
        return calls["n"]

    a = cache.get_or_set("k", cache.SLOW, produce)
    b = cache.get_or_set("k", cache.SLOW, produce)
    assert a == b == 1
    assert calls["n"] == 1  # second call served from cache


# --- middleware integration -------------------------------------------------


def _app(monkeypatch, **env) -> FastAPI:
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    get_settings.cache_clear()
    from server.middleware import configure_hardening

    app = FastAPI()
    configure_hardening(app)

    @app.get("/ping")
    async def ping() -> dict:
        return {"pong": True}

    @app.get("/boom")
    async def boom() -> dict:
        raise HTTPException(status_code=418, detail="teapot")

    return app


def test_security_headers_present(monkeypatch):
    client = TestClient(_app(monkeypatch, WORLDFIN_RATE_LIMIT_PER_MIN="0"))
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "content-security-policy" in r.headers


def test_etag_then_304(monkeypatch):
    client = TestClient(_app(monkeypatch, WORLDFIN_RATE_LIMIT_PER_MIN="0"))
    r1 = client.get("/ping")
    etag = r1.headers.get("etag")
    assert etag and etag.startswith('W/"')
    r2 = client.get("/ping", headers={"If-None-Match": etag})
    assert r2.status_code == 304
    # security headers still ride along on the 304
    assert r2.headers["x-content-type-options"] == "nosniff"


def test_rate_limit_returns_429_with_retry_after(monkeypatch):
    client = TestClient(_app(monkeypatch, WORLDFIN_RATE_LIMIT_PER_MIN="3"))
    codes = [client.get("/ping").status_code for _ in range(5)]
    assert codes.count(200) == 3
    assert codes.count(429) == 2
    blocked = client.get("/ping")
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) >= 1
    assert blocked.json()["error"]["status"] == 429


def test_error_envelope_shape(monkeypatch):
    client = TestClient(_app(monkeypatch, WORLDFIN_RATE_LIMIT_PER_MIN="0"))
    r = client.get("/boom")
    assert r.status_code == 418
    assert r.json() == {"error": {"status": 418, "message": "teapot"}}


def teardown_module(module):  # restore the cached settings singleton for other tests
    get_settings.cache_clear()
