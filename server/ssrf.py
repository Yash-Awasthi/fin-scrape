"""SSRF guard: refuse URLs that resolve to non-public IP space.

The rss-proxy already gates by feed key (only registry URLs), but that registry is
data and could one day include a redirecting host. This is the defense-in-depth layer:
before *and* after following redirects we assert every host resolves to a public,
routable IP — blocking loopback, private, link-local, and reserved ranges.

Pure + testable: `is_public_ip` takes a literal address (no network), and
`assert_public_host` resolves a hostname via DNS (the only network touch).
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlsplit


class SSRFError(ValueError):
    """Raised when a URL targets a non-public / disallowed address."""


def is_public_ip(addr: str) -> bool:
    """True only for globally-routable unicast addresses."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    # is_global is the inverse of private/loopback/link-local/reserved/multicast.
    return ip.is_global and not ip.is_multicast


def assert_public_host(host: str) -> None:
    """Resolve `host` and raise SSRFError if any resolved IP is non-public.

    A hostname can map to several A/AAAA records; we reject if *any* is private,
    so a split-horizon DNS trick can't sneak one private record through.
    """
    if not host:
        raise SSRFError("empty host")
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise SSRFError(f"cannot resolve host: {host}") from exc
    for info in infos:
        addr = str(info[4][0])  # sockaddr[0] is the IP string for AF_INET/AF_INET6
        if not is_public_ip(addr):
            raise SSRFError(f"host {host} resolves to non-public address {addr}")


def assert_public_url(url: str) -> None:
    """Validate scheme + resolve the host. Raises SSRFError on anything unsafe."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise SSRFError(f"disallowed scheme: {parts.scheme!r}")
    if not parts.hostname:
        raise SSRFError("url has no host")
    assert_public_host(parts.hostname)
