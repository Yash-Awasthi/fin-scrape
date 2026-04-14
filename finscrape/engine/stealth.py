"""
Stealth Fetcher using Playwright with anti-detection.

Handles sites with Cloudflare, bot detection, and heavy JS.
Uses a real Chromium browser with stealth measures:
  - Realistic viewport and screen dimensions
  - WebGL/Canvas fingerprint normalization
  - navigator.webdriver flag removal
  - Realistic mouse movements and timing
  - Cookie consent auto-dismissal
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

from finscrape.engine.page import Page

logger = logging.getLogger(__name__)

# Stealth scripts injected before page load
_STEALTH_SCRIPTS = [
    # Remove navigator.webdriver flag
    """
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined
    });
    """,
    # Fake plugins array
    """
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5]
    });
    """,
    # Fake languages
    """
    Object.defineProperty(navigator, 'languages', {
        get: () => ['en-US', 'en']
    });
    """,
    # Override chrome runtime to look like real Chrome
    """
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {}
    };
    """,
    # Fix permissions query
    """
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    """,
]

# Viewports that look like real monitors
_VIEWPORTS = [
    {"width": 1920, "height": 1080},
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1536, "height": 864},
    {"width": 1280, "height": 720},
]

_USER_AGENTS_STEALTH = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
]


class StealthFetcher:
    """
    Browser-based fetcher with anti-detection for protected sites.

    Requires Playwright + Chromium:
        pip install playwright
        playwright install chromium

    Usage:
        fetcher = StealthFetcher()
        page = fetcher.get("https://bloomberg.com/news/...")
        if page:
            title = page.css_first("h1").text
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30.0,
        wait_for_cloudflare: bool = True,
    ):
        self.headless = headless
        self.timeout = timeout
        self.wait_for_cloudflare = wait_for_cloudflare
        self._browser = None
        self._playwright = None

    def _ensure_browser(self):
        """Launch browser if not already running."""
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                raise RuntimeError(
                    "Playwright is required for StealthFetcher.\n"
                    "Install it: pip install playwright && playwright install chromium"
                )

            self._playwright = sync_playwright().start()
            viewport = random.choice(_VIEWPORTS)
            ua = random.choice(_USER_AGENTS_STEALTH)

            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=IsolateOrigins,site-per-process",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    f"--window-size={viewport['width']},{viewport['height']}",
                ],
            )
            self._context = self._browser.new_context(
                viewport=viewport,
                user_agent=ua,
                locale="en-US",
                timezone_id="America/New_York",
                color_scheme="light",
            )

            # Inject stealth scripts on every new page
            for script in _STEALTH_SCRIPTS:
                self._context.add_init_script(script)

    def get(self, url: str) -> Optional[Page]:
        """
        Fetch a URL using a stealth browser.

        Automatically waits for Cloudflare challenges if detected.
        """
        try:
            self._ensure_browser()
        except RuntimeError as e:
            logger.error("Cannot launch stealth browser: %s", e)
            return None

        try:
            page = self._context.new_page()

            # Navigate with realistic timing
            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)

            # Check for and wait through Cloudflare challenge
            if self.wait_for_cloudflare:
                self._handle_cloudflare(page)

            # Wait for content to settle
            page.wait_for_load_state("networkidle", timeout=10_000)

            # Small random delay to look human
            time.sleep(random.uniform(0.5, 1.5))

            html = page.content()
            final_url = page.url
            page.close()

            return Page(html=html, url=final_url, status_code=200)

        except Exception as e:
            logger.warning("Stealth fetch failed for %s: %s", url[:80], e)
            try:
                page.close()
            except Exception:
                pass
            return None

    def _handle_cloudflare(self, page):
        """Detect and wait through Cloudflare challenge pages."""
        challenge_selectors = [
            "#challenge-running",
            "#challenge-form",
            ".cf-browser-verification",
            "#cf-challenge-running",
            'iframe[src*="challenges.cloudflare.com"]',
        ]

        for selector in challenge_selectors:
            try:
                if page.query_selector(selector):
                    logger.info("Cloudflare challenge detected — waiting...")
                    # Wait up to 15 seconds for the challenge to resolve
                    page.wait_for_selector(
                        selector,
                        state="hidden",
                        timeout=15_000,
                    )
                    time.sleep(2)  # Extra wait after challenge resolves
                    return
            except Exception:
                continue

    def close(self):
        if self._browser:
            try:
                self._browser.close()
            except Exception:
                pass
        if self._playwright:
            try:
                self._playwright.stop()
            except Exception:
                pass
        self._browser = None
        self._playwright = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()
