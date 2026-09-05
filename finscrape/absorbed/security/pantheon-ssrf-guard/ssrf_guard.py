# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Isaac Teague Frayling
"""A two-layer SSRF egress guard for Python's stdlib HTTP client — that survives DNS rebinding.

Blocking outbound requests to internal addresses with a hostname pre-check ALONE is not enough: an attacker
can pass a hostname that resolves public at check time, then rebinds to 127.0.0.1 / 169.254.169.254 / an
internal service by the time the socket actually connects. This guard closes that gap with two layers:

  * host_is_public(host)  — resolve the name and reject if ANY resulting address is private / loopback /
    link-local / reserved / multicast / CGN-shared / otherwise non-global (the fast pre-check).
  * GuardedHTTP(S)Connection / Handler — at CONNECT time, re-check the IP the socket ACTUALLY reached and
    raise SsrfBlocked if it isn't public. This is the layer a pre-check can't provide: it sees the real peer,
    so a rebind between the pre-check and the connection's own resolution can't land on an internal address.

The catch-all is `not ip.is_global`, which rejects everything the explicit flags miss — notably RFC 6598
shared/CGN space (100.64.0.0/10, used by k8s/internal LBs and the Alibaba/Tencent/Oracle metadata endpoint
at 100.100.100.200), plus benchmark / documentation / NAT64 ranges.

Extracted from PANTHEON (a multi-tenant AI substrate), where it is the single canonical guard on every
outbound path (link imports, uploaded-URL fetches, external MCP-server transports).

Usage — a urllib opener that refuses internal targets, even under rebind:

    from ssrf_guard import guarded_opener, SsrfBlocked
    opener = guarded_opener()                       # https-capable, redirects still re-checked at connect
    try:
        with opener.open("https://example.com/data.json", timeout=10) as r:
            body = r.read()
    except SsrfBlocked:
        ...                                         # target resolved (or rebound) to a non-public address
"""
from __future__ import annotations

import http.client
import ipaddress
import socket
import urllib.request
from urllib.request import HTTPHandler, HTTPSHandler


class SsrfBlocked(Exception):
    """The requested address resolved (or rebound) to a non-public IP and was refused."""


_NAT64_WK = ipaddress.ip_network("64:ff9b::/96")         # RFC 6052 well-known prefix: low 32 bits embed a v4


def ip_is_public(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True only for a public, routable address. `not ip.is_global` is the catch-all — it rejects everything
    the explicit flags miss (CGN 100.64.0.0/10, benchmark, documentation); the explicit flags stay for clarity.

    ENCAPSULATION: an IPv4-mapped (`::ffff:169.254.169.254`) or NAT64 well-known (`64:ff9b::a9fe:a9fe`) address
    smuggles a v4 target inside a v6 address, and the stdlib flags for these have SHIFTED across CPython releases
    — the exact edge this guard exists for. We normalise to the embedded v4 and classify THAT, so the verdict is
    version-independent instead of trusting whichever `is_*` flags a given interpreter happens to set."""
    if getattr(ip, "ipv4_mapped", None) is not None:
        ip = ip.ipv4_mapped                              # ::ffff:127.0.0.1 → 127.0.0.1
    elif ip.version == 6 and ip in _NAT64_WK:
        ip = ipaddress.ip_address(int(ip) & 0xFFFFFFFF)  # 64:ff9b::7f00:1 → 127.0.0.1
    return not (not ip.is_global or ip.is_private or ip.is_loopback or ip.is_link_local
                or ip.is_reserved or ip.is_multicast or ip.is_unspecified)


def host_is_public(host: str) -> bool:
    """True only if EVERY address `host` resolves to is a public, routable IP (the fast pre-check). A host that
    resolves to a mix of public and private addresses is rejected."""
    try:
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    if not infos:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except ValueError:
            return False
        if not ip_is_public(ip):
            return False
    return True


def peer_is_public(sock: socket.socket) -> bool:
    """The IP the socket ACTUALLY connected to is public. Checked at connect time so a DNS rebind between the
    pre-check and the connection's own resolution can't reach an internal address."""
    try:
        return ip_is_public(ipaddress.ip_address(sock.getpeername()[0]))
    except (OSError, ValueError):
        return False


class GuardedHTTPConnection(http.client.HTTPConnection):
    def connect(self) -> None:
        if not host_is_public(self.host):                # LAYER 1: fast pre-check by name — reject before any socket
            raise SsrfBlocked(f"refusing to connect to a non-public host: {self.host!r}")
        super().connect()
        if not peer_is_public(self.sock):                # LAYER 2: re-check the ACTUAL peer (survives DNS rebinding)
            self.close()
            raise SsrfBlocked("refusing to connect to a non-public address")


class GuardedHTTPSConnection(http.client.HTTPSConnection):
    def connect(self) -> None:
        if not host_is_public(self.host):                # LAYER 1: pre-check before the TCP+TLS handshake
            raise SsrfBlocked(f"refusing to connect to a non-public host: {self.host!r}")
        super().connect()                                # TCP + TLS (cert validated against the hostname). NB: on a
        if not peer_is_public(self.sock):                # rebind the handshake COMPLETES before this peer re-check —
            self.close()                                 # no request bytes are sent (that's after connect()), but the
            raise SsrfBlocked("refusing to connect to a non-public address")   # TLS handshake did reach the peer.


class GuardedHTTPHandler(HTTPHandler):
    def http_open(self, req):
        return self.do_open(GuardedHTTPConnection, req)


class GuardedHTTPSHandler(HTTPSHandler):
    def https_open(self, req):
        return self.do_open(GuardedHTTPSConnection, req)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects — a 3xx to an internal address would otherwise be followed. (The Guarded* connections
    would still catch the internal hop, but refusing is tighter and simpler.) Pass no_redirect=False to allow
    redirects; each hop is still re-checked at connect time by the Guarded* connections."""
    def redirect_request(self, *a, **k):
        return None


def guarded_opener(*, no_redirect: bool = True) -> urllib.request.OpenerDirector:
    """A urllib opener whose http/https connections refuse any non-public peer at connect time (rebind-safe).
    By default it also refuses redirects; set no_redirect=False to follow them (still re-checked per hop)."""
    handlers = [GuardedHTTPHandler, GuardedHTTPSHandler]
    if no_redirect:
        handlers.insert(0, _NoRedirect)
    return urllib.request.build_opener(*handlers)
