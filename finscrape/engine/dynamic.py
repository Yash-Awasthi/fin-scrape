"""
Dynamic Fetcher using Playwright for JS-heavy pages.

Unlike StealthFetcher (which focuses on anti-bot evasion),
DynamicFetcher focuses on full JS rendering — SPAs, infinite
scroll, lazy-loaded content, etc.

Lighter than StealthFetcher: no anti-detection scripts,
but full DOM rendering with network idle detection.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

from finscrape.engine.page import Page

logger = logging.getLogger(__name__)


class DynamicFetcher:
    """
    Playwright-based fetcher for JS-rendered pages.

    Usage:
        fetcher = DynamicFetcher()
        page = fetcher.get("https://example.com/spa-app")
        if page:
            items = page.css(".dynamic-content .item")
    """

    def __init__(
        self,
        headless: bool = True,
        timeout: float = 30.0,
        wait_for_idle: bool = True,
    ):
        self.headless = headless
        self.timeout = timeout
        self.wait_for_idle = wait_for_idle
        self._browser = None
        self._playwright = None

    def _ensure_browser(self):
        if self._browser is None:
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                raise RuntimeError(
                    "Playwright is required for DynamicFetcher.\n"
                    "Install it: pip install playwright && playwright install chromium"
                )

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )
            self._context = self._browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )

    def get(
        self,
        url: str,
        wait_for_selector: str | None = None,
        scroll: bool = False,
    ) -> Optional[Page]:
        """
        Fetch a URL with full JS rendering.

        Args:
            url: Page URL
            wait_for_selector: Optional CSS selector to wait for before extracting
            scroll: If True, scroll down to trigger lazy loading
        """
        try:
            self._ensure_browser()
        except RuntimeError as e:
            logger.error("Cannot launch dynamic browser: %s", e)
            return None

        try:
            page = self._context.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=self.timeout * 1000)

            if self.wait_for_idle:
                try:
                    page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception:
                    pass  # Network idle timeout is non-fatal

            if wait_for_selector:
                try:
                    page.wait_for_selector(wait_for_selector, timeout=10_000)
                except Exception:
                    logger.debug("Selector %r not found within timeout", wait_for_selector)

            if scroll:
                self._auto_scroll(page)

            html = page.content()
            final_url = page.url
            page.close()

            return Page(html=html, url=final_url, status_code=200)

        except Exception as e:
            logger.warning("Dynamic fetch failed for %s: %s", url[:80], e)
            try:
                page.close()
            except Exception:
                pass
            return None

    def _auto_scroll(self, page, max_scrolls: int = 5):
        """Scroll down to trigger lazy loading."""
        for i in range(max_scrolls):
            prev_height = page.evaluate("document.body.scrollHeight")
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == prev_height:
                break

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
