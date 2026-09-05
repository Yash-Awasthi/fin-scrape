"""Shared fake engine + Fetcher mock for scraper tests.

Both test_scraper_retry.py and test_scraper_circuit_breaker.py stub
finscrape.engine with a _FakeFetcher. If each file creates its own class,
they end up with different MagicMock instances — setting side_effect on
one doesn't affect the other. This shared module ensures both test files
use the SAME _FakeFetcher so mock state is visible across test files.
"""
import sys
import types
from unittest.mock import MagicMock


def install_fake_engine():
    """Install the fake finscrape.engine module if not already installed.

    Returns the shared _FakeFetcher class so test files can set side_effect
    and return_value on the same MagicMock instance.
    """
    if "finscrape.engine" not in sys.modules or not hasattr(sys.modules["finscrape.engine"], "_shared"):
        _fake_engine = types.ModuleType("finscrape.engine")
        _fake_response = MagicMock()

        class _FakeFetcher:
            get = MagicMock(return_value=_fake_response)

        class _FakeStealthyFetcher:
            fetch = MagicMock(return_value=_fake_response)

        class _FakeDynamicFetcher:
            fetch = MagicMock(return_value=_fake_response)

        _fake_engine.Fetcher = _FakeFetcher
        _fake_engine.StealthyFetcher = _FakeStealthyFetcher
        _fake_engine.DynamicFetcher = _FakeDynamicFetcher
        _fake_engine.Response = MagicMock
        _fake_engine._shared = True  # marker so we don't re-install
        _fake_engine._fake_response = _fake_response
        sys.modules["finscrape.engine"] = _fake_engine

    return sys.modules["finscrape.engine"]


def get_fake_fetcher():
    """Get the shared _FakeFetcher class."""
    return install_fake_engine().Fetcher


def get_fake_response():
    """Get the shared fake response mock."""
    return install_fake_engine()._fake_response


def reset_fetcher():
    """Reset the shared Fetcher.get mock — call between tests."""
    fg = get_fake_fetcher()
    fg.get.reset_mock(side_effect=True)
    fg.get.return_value = get_fake_response()
