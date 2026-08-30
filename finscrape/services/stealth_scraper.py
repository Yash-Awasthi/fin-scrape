"""
Stealth web scraping service with anti-detection patterns.

Extracted from abrasio-sdk — TLS fingerprinting, human behavior simulation.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import time
import math
import random
import hashlib
import json


class BrowserProfile(Enum):
    CHROME_120 = "chrome120"
    CHROME_119 = "chrome119"
    SAFARI_15_5 = "safari15_5"
    EDGE_101 = "edge101"


@dataclass
class RequestConfig:
    url: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    cookies: Optional[Dict[str, str]] = None
    timeout: float = 30.0
    retries: int = 3
    delay: float = 0.0


@dataclass
class ScrapeResult:
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    duration: float
    success: bool
    error: Optional[str] = None


# Browser fingerprint templates
BROWSER_FINGERPRINTS = {
    BrowserProfile.CHROME_120: {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_language": "en-US,en;q=0.9",
        "sec_ch_ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec_ch_ua_mobile": "?0",
        "sec_ch_ua_platform": '"Windows"',
        "sec_fetch_dest": "document",
        "sec_fetch_mode": "navigate",
        "sec_fetch_site": "none",
        "sec_fetch_user": "?1",
    },
    BrowserProfile.SAFARI_15_5: {
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_language": "en-US,en;q=0.9",
    },
    BrowserProfile.EDGE_101: {
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Safari/537.36 Edg/101.0.1210.39",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "accept_encoding": "gzip, deflate, br",
        "accept_language": "en-US,en;q=0.9",
    },
}


def generate_headers(profile: BrowserProfile = BrowserProfile.CHROME_120) -> Dict[str, str]:
    """Generate browser-matching headers for a profile."""
    fp = BROWSER_FINGERPRINTS.get(profile, BROWSER_FINGERPRINTS[BrowserProfile.CHROME_120])
    return {
        "User-Agent": fp["user_agent"],
        "Accept": fp["accept"],
        "Accept-Encoding": fp["accept_encoding"],
        "Accept-Language": fp["accept_language"],
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


def bezier_curve(start: float, end: float, control: float, t: float) -> float:
    """Compute a point on a quadratic Bezier curve."""
    return (1 - t) ** 2 * start + 2 * (1 - t) * t * control + t ** 2 * end


def simulate_mouse_path(
    start_x: float, start_y: float,
    end_x: float, end_y: float,
    steps: int = 25,
) -> List[Dict[str, float]]:
    """Generate a natural-looking mouse movement path using Bezier curves."""
    ctrl_x = (start_x + end_x) / 2 + random.uniform(-50, 50)
    ctrl_y = (start_y + end_y) / 2 + random.uniform(-50, 50)

    path = []
    for i in range(steps + 1):
        t = i / steps
        # Add slight jitter
        jitter_x = random.uniform(-1, 1)
        jitter_y = random.uniform(-1, 1)
        path.append({
            "x": bezier_curve(start_x, end_x, ctrl_x, t) + jitter_x,
            "y": bezier_curve(start_y, end_y, ctrl_y, t) + jitter_y,
            "t": t,
        })

    return path


def simulate_typing(
    text: str,
    base_delay: float = 0.05,
    variance: float = 0.03,
) -> List[Dict[str, any]]:
    """Simulate natural typing with variable delays."""
    events = []
    for i, char in enumerate(text):
        delay = base_delay + random.uniform(-variance, variance)
        if char == " ":
            delay *= 1.5
        elif char in ".!?":
            delay *= 2.0
        elif char in ",;:":
            delay *= 1.3

        events.append({
            "char": char,
            "delay": max(0.01, delay),
            "key_down": i,
        })

    return events


def simulate_scroll(
    distance: float,
    duration: float = 1.0,
    steps: int = 20,
) -> List[Dict[str, float]]:
    """Simulate smooth scrolling with easing."""
    events = []
    for i in range(steps):
        t = i / steps
        ease = t * (2 - t)  # Ease-out quadratic
        events.append({
            "offset": distance * ease,
            "timestamp": duration * ease,
        })

    return events


class StealthScraper:
    """Stealth web scraper with anti-detection measures."""

    def __init__(
        self,
        profile: BrowserProfile = BrowserProfile.CHROME_120,
        rate_limit: float = 1.0,
        max_retries: int = 3,
    ):
        self.profile = profile
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.last_request_time = 0.0
        self.request_count = 0

    def prepare_request(self, config: RequestConfig) -> Dict:
        """Prepare a request with stealth headers and fingerprint."""
        headers = generate_headers(self.profile)
        if config.headers:
            headers.update(config.headers)

        # Add realistic referer if missing
        if "Referer" not in headers and config.url:
            from urllib.parse import urlparse
            parsed = urlparse(config.url)
            headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"

        return {
            "url": config.url,
            "method": config.method,
            "headers": headers,
            "cookies": config.cookies or {},
            "timeout": config.timeout,
        }

    def wait_for_rate_limit(self):
        """Wait if needed to respect rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
        self.request_count += 1

    def generate_session_id(self) -> str:
        """Generate a unique session identifier."""
        return hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()

    def should_retry(self, status_code: int, attempt: int) -> bool:
        """Determine if a request should be retried."""
        if attempt >= self.max_retries:
            return False
        if status_code in (429, 503, 504):
            return True
        if status_code >= 500:
            return True
        return False

    def get_retry_delay(self, attempt: int, status_code: int) -> float:
        """Calculate retry delay with exponential backoff."""
        if status_code == 429:
            return min(60, (2 ** attempt) + random.uniform(0, 1))
        return min(30, (2 ** attempt) + random.uniform(0, 1))

    def parse_response(self, content: str, content_type: str = "text/html") -> Dict:
        """Parse response content based on type."""
        result = {"raw": content, "content_type": content_type}

        if "json" in content_type:
            try:
                result["parsed"] = json.loads(content)
                result["format"] = "json"
            except json.JSONDecodeError:
                result["format"] = "raw"
        elif "html" in content_type:
            result["format"] = "html"
            # Extract text content (simplified)
            import re
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            result["text"] = text
        else:
            result["format"] = "raw"

        return result
