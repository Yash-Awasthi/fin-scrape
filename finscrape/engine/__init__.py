"""
FinScrape Engine — internal scraping layer.

Replaces the external Scrapling dependency with our own implementation
built on httpx, BeautifulSoup, and Playwright. Three fetch modes:

  - Fetcher:         Fast HTTP with stealth headers + TLS fingerprinting
  - StealthFetcher:  Playwright with anti-detection (Cloudflare bypass, etc.)
  - DynamicFetcher:  Playwright for JS-heavy pages that need rendering

All return a unified `Page` object with CSS/XPath selectors and
element access so the rest of the codebase doesn't care which
fetcher was used.
"""

from finscrape.engine.page import Page, Element
from finscrape.engine.fetcher import Fetcher
from finscrape.engine.stealth import StealthFetcher
from finscrape.engine.dynamic import DynamicFetcher

__all__ = ["Page", "Element", "Fetcher", "StealthFetcher", "DynamicFetcher"]
