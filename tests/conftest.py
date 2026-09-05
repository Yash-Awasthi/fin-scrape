"""Shared test fixtures for scraper tests — resets circuit breakers."""
import pytest


@pytest.fixture(autouse=True)
def _reset_breakers():
    """Reset circuit breakers between tests so no test inherits a tripped breaker."""
    try:
        from finscrape.scrapers import reset_breakers
        reset_breakers()
    except ImportError:
        pass
    yield
    try:
        from finscrape.scrapers import reset_breakers
        reset_breakers()
    except ImportError:
        pass
