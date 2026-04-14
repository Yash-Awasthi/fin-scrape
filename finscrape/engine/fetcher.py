"""
HTTP Fetcher with stealth headers and retry logic.

Mimics a real browser via:
  - Rotating realistic User-Agent strings
  - Full browser-like header sets (Accept, Accept-Language, etc.)
  - Connection pooling and retry with exponential backoff
  - Configurable timeouts
"""

from __future__ import annotations

import logging
import random
import time
from typing import Optional

import httpx

from finscrape.engine.page import Page

logger = logging.getLogger(__name__)

# Realistic User-Agent strings (Chrome on different OS)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Accept-Language values
ACCEPT_LANGUAGES = [
    "en-US,en;q=0.9",
    "en-US,en;q=0.9,es;q=0.8",
    "en-GB,en;q=0.9,en-US;q=0.8",
    "en-US,en;q=0.8",
]


def _build_stealth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    """Build a realistic browser-like header set."""
    ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": random.choice(ACCEPT_LANGUAGES),
        "Accept-Encoding": "gzip, deflate, br",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"' if "Windows" in ua else '"macOS"' if "Mac" in ua else '"Linux"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
    }
    if extra:
        headers.update(extra)
    return headers


class Fetcher:
    """
    Fast HTTP fetcher with stealth headers and retry logic.

    Usage:
        fetcher = Fetcher()
        page = fetcher.get("https://example.com")
        if page:
            for link in page.css("a[href]"):
                print(link.attrib.get("href"))
    """

    def __init__(
        self,
        timeout: float = 15.0,
        retries: int = 3,
        backoff_factor: float = 1.0,
    ):
        self.timeout = timeout
        self.retries = retries
        self.backoff_factor = backoff_factor
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        if self._client is None or self._client.is_closed:
            self._client = httpx.Client(
                timeout=httpx.Timeout(self.timeout),
                follow_redirects=True,
                http2=True,
            )
        return self._client

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        stealth: bool = True,
    ) -> Optional[Page]:
        """
        Fetch a URL and return a parsed Page.

        Returns None on failure after all retries.
        """
        request_headers = _build_stealth_headers() if stealth else {}
        if headers:
            request_headers.update(headers)

        client = self._get_client()
        last_error = None

        for attempt in range(self.retries):
            try:
                response = client.get(url, headers=request_headers)

                if response.status_code in (429, 500, 502, 503, 504):
                    delay = self.backoff_factor * (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        "HTTP %d from %s — retry %d/%d in %.1fs",
                        response.status_code, url[:80], attempt + 1, self.retries, delay,
                    )
                    time.sleep(delay)
                    continue

                return Page(
                    html=response.text,
                    url=str(response.url),
                    status_code=response.status_code,
                )

            except httpx.RequestError as e:
                last_error = e
                delay = self.backoff_factor * (2 ** attempt)
                logger.warning(
                    "Request error for %s — retry %d/%d: %s",
                    url[:80], attempt + 1, self.retries, e,
                )
                time.sleep(delay)

        logger.error("All %d retries exhausted for %s: %s", self.retries, url[:80], last_error)
        return None

    def close(self):
        if self._client and not self._client.is_closed:
            self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()
