"""
Stealth Scraper V2 — Extracted from Scrapling patterns.

Advanced web scraping with:
- Browser fingerprint rotation
- Anti-bot detection bypass
- CSS selector engine with custom attributes
- Text content cleaning and normalization
- HTML entity handling
"""
from __future__ import annotations

import hashlib
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class ScrapedElement:
    tag: str
    attributes: Dict[str, str]
    text: str
    html: str
    children: List['ScrapedElement'] = field(default_factory=list)
    parent: Optional['ScrapedElement'] = None

    @property
    def inner_text(self) -> str:
        """Clean text content with normalized whitespace."""
        return self.text.strip()

    @property
    def full_text(self) -> str:
        """Text from all descendant elements."""
        texts = [self.inner_text]
        for child in self.children:
            child_text = child.full_text
            if child_text:
                texts.append(child_text)
        return ' '.join(t for t in texts if t)

    def get_attribute(self, name: str, default: str = '') -> str:
        return self.attributes.get(name, default)

    def query_selector(self, css_selector: str) -> Optional['ScrapedElement']:
        """Simple CSS selector matching."""
        if not self.children:
            return None
        tag, attrs = self._parse_selector(css_selector)
        for child in self.children:
            if self._matches(child, tag, attrs):
                return child
            found = child.query_selector(css_selector)
            if found:
                return found
        return None

    def query_selector_all(self, css_selector: str) -> List['ScrapedElement']:
        """Find all matching elements."""
        results: List[ScrapedElement] = []
        if not self.children:
            return results
        tag, attrs = self._parse_selector(css_selector)
        for child in self.children:
            if self._matches(child, tag, attrs):
                results.append(child)
            results.extend(child.query_selector_all(css_selector))
        return results

    def _parse_selector(self, selector: str) -> Tuple[Optional[str], Dict[str, str]]:
        """Parse CSS selector into tag and attributes."""
        attrs: Dict[str, str] = {}
        tag: Optional[str] = None

        # Handle #id selector
        id_match = re.search(r'#(\w+)', selector)
        if id_match:
            attrs['id'] = id_match.group(1)

        # Handle .class selector
        class_match = re.search(r'\.(\w+)', selector)
        if class_match:
            attrs['class'] = class_match.group(1)

        # Handle tag name
        tag_match = re.match(r'^([a-zA-Z][a-zA-Z0-9]*)', selector)
        if tag_match:
            tag = tag_match.group(1)

        # Handle [attr=value]
        attr_match = re.findall(r'\[([^=\]]+)(?:=["\']([^"\']*)["\'])?\]', selector)
        for name, value in attr_match:
            attrs[name.strip()] = value

        return tag, attrs

    def _matches(self, element: 'ScrapedElement', tag: Optional[str], attrs: Dict[str, str]) -> bool:
        """Check if element matches selector criteria."""
        if tag and element.tag.lower() != tag.lower():
            return False
        for name, value in attrs.items():
            if name == 'class':
                classes = element.attributes.get('class', '').split()
                if value not in classes:
                    return False
            elif element.attributes.get(name) != value:
                return False
        return True

    def css(self, selector: str) -> List['ScrapedElement']:
        """Alias for query_selector_all."""
        return self.query_selector_all(selector)

    def xpath(self, path: str) -> List['ScrapedElement']:
        """Simple XPath-like navigation."""
        parts = path.strip('/').split('/')
        results = [self]
        for part in parts:
            next_results: List[ScrapedElement] = []
            for r in results:
                if part == '..':
                    if r.parent:
                        next_results.append(r.parent)
                elif part == '*':
                    next_results.extend(r.children)
                else:
                    next_results.extend(r.query_selector_all(part))
            results = next_results
        return results


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Replace tabs and newlines with spaces
    cleaned = text.translate(str.maketrans('\t\r\n', '   '))
    # Collapse multiple spaces
    cleaned = re.sub(r' {2,}', ' ', cleaned)
    return cleaned.strip()


def decode_html_entities(text: str) -> str:
    """Decode HTML entities."""
    import html
    return html.unescape(text)


def extract_text_from_html(html_content: str) -> str:
    """Extract clean text from HTML."""
    # Remove script and style tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    # Decode entities
    text = decode_html_entities(text)
    # Clean whitespace
    return clean_text(text)


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/17.2',
]


class BrowserFingerprint:
    """Generate and rotate browser fingerprints."""

    def __init__(self) -> None:
        self._fingerprints: List[Dict[str, str]] = []
        self._current_index = 0

    def generate(self) -> Dict[str, str]:
        """Generate a random browser fingerprint."""
        fp = {
            'user_agent': random.choice(USER_AGENTS),
            'accept_language': self._random_language(),
            'platform': random.choice(['Win32', 'MacIntel', 'Linux x86_64']),
            'screen_resolution': random.choice([
                '1920x1080', '2560x1440', '1366x768', '1536x864',
            ]),
            'timezone': random.choice([
                'America/New_York', 'Europe/London', 'Asia/Tokyo',
            ]),
        }
        self._fingerprints.append(fp)
        return fp

    def rotate(self) -> Dict[str, str]:
        """Get next fingerprint in rotation."""
        if not self._fingerprints:
            self.generate()
        fp = self._fingerprints[self._current_index % len(self._fingerprints)]
        self._current_index += 1
        return fp

    def _random_language(self) -> str:
        langs = ['en-US,en;q=0.9', 'en-GB,en;q=0.8', 'en-US,en;q=0.9,fr;q=0.8']
        return random.choice(langs)


class StealthConfig:
    """Configuration for stealth scraping."""

    def __init__(
        self,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
        delay_range: Tuple[float, float] = (1.0, 3.0),
        max_retries: int = 3,
        respect_robots: bool = True,
    ) -> None:
        self.use_proxy = use_proxy
        self.proxy_url = proxy_url
        self.delay_range = delay_range
        self.max_retries = max_retries
        self.respect_robots = respect_robots
        self._robots_cache: Dict[str, Set[str]] = {}

    def random_delay(self) -> float:
        """Random delay between requests."""
        return random.uniform(*self.delay_range)

    def get_headers(self) -> Dict[str, str]:
        """Get randomized headers."""
        fp = BrowserFingerprint()
        fingerprint = fp.generate()
        return {
            'User-Agent': fingerprint['user_agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': fingerprint['accept_language'],
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        }
