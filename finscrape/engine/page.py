"""
Unified Page and Element wrappers.

Provides a consistent API for navigating parsed HTML regardless
of how the page was fetched (HTTP, stealth browser, dynamic render).
CSS selector support via BeautifulSoup's `select()`.
"""

from __future__ import annotations

from typing import Optional
from bs4 import BeautifulSoup, Tag


class Element:
    """Wrapper around a BeautifulSoup Tag with a cleaner API."""

    __slots__ = ("_tag",)

    def __init__(self, tag: Tag):
        self._tag = tag

    @property
    def text(self) -> str:
        return self._tag.get_text(strip=True)

    @property
    def raw_text(self) -> str:
        return self._tag.get_text(strip=False)

    @property
    def attrib(self) -> dict[str, str]:
        return dict(self._tag.attrs) if self._tag.attrs else {}

    @property
    def tag_name(self) -> str:
        return self._tag.name or ""

    @property
    def inner_html(self) -> str:
        return self._tag.decode_contents()

    @property
    def outer_html(self) -> str:
        return str(self._tag)

    def css(self, selector: str) -> list[Element]:
        return [Element(t) for t in self._tag.select(selector) if isinstance(t, Tag)]

    def css_first(self, selector: str) -> Optional[Element]:
        result = self._tag.select_one(selector)
        return Element(result) if result and isinstance(result, Tag) else None

    def get_attribute(self, name: str, default: str = "") -> str:
        return self._tag.get(name, default)

    def find_all(self, *args, **kwargs) -> list[Element]:
        return [Element(t) for t in self._tag.find_all(*args, **kwargs) if isinstance(t, Tag)]

    def find(self, *args, **kwargs) -> Optional[Element]:
        result = self._tag.find(*args, **kwargs)
        return Element(result) if result and isinstance(result, Tag) else None

    def __repr__(self) -> str:
        tag = self._tag.name
        text_preview = self.text[:40]
        return f"<Element tag={tag!r} text={text_preview!r}>"


class Page:
    """
    Parsed HTML page with CSS selector access.

    Built from raw HTML string. Provides the same element API
    regardless of how the HTML was obtained.
    """

    def __init__(self, html: str, url: str = "", status_code: int = 200):
        self._soup = BeautifulSoup(html, "html.parser")
        self.url = url
        self.status_code = status_code

    @property
    def title(self) -> str:
        tag = self._soup.find("title")
        return tag.get_text(strip=True) if tag else ""

    @property
    def text(self) -> str:
        return self._soup.get_text(strip=True)

    @property
    def html(self) -> str:
        return str(self._soup)

    def css(self, selector: str) -> list[Element]:
        return [Element(t) for t in self._soup.select(selector) if isinstance(t, Tag)]

    def css_first(self, selector: str) -> Optional[Element]:
        result = self._soup.select_one(selector)
        return Element(result) if result and isinstance(result, Tag) else None

    def find_all(self, *args, **kwargs) -> list[Element]:
        return [Element(t) for t in self._soup.find_all(*args, **kwargs) if isinstance(t, Tag)]

    def find(self, *args, **kwargs) -> Optional[Element]:
        result = self._soup.find(*args, **kwargs)
        return Element(result) if result and isinstance(result, Tag) else None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 400

    def __repr__(self) -> str:
        return f"<Page url={self.url!r} status={self.status_code}>"

    def __bool__(self) -> bool:
        return self.ok
