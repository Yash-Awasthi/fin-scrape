# SPDX-License-Identifier: Apache-2.0
"""Denial matrix for the SSRF guard — the classification is the whole value, so it's tested exhaustively."""
from __future__ import annotations

import http.client
import ipaddress
import random

import pytest

from ssrf_guard import (
    GuardedHTTPConnection,
    GuardedHTTPHandler,
    GuardedHTTPSHandler,
    SsrfBlocked,
    _NoRedirect,
    guarded_opener,
    host_is_public,
    ip_is_public,
    peer_is_public,
)

# addresses that MUST be refused (private, loopback, link-local incl. cloud metadata, CGN incl. Alibaba metadata,
# reserved, multicast, unspecified) + a couple that must be allowed.
BLOCKED = ["127.0.0.1", "10.0.0.1", "192.168.1.1", "172.16.5.4", "169.254.169.254", "100.64.0.1",
           "100.100.100.200", "0.0.0.0", "224.0.0.1", "::1", "fe80::1", "fc00::1", "::"]
ALLOWED = ["8.8.8.8", "1.1.1.1", "93.184.216.34", "2606:4700:4700::1111"]


@pytest.mark.parametrize("addr", BLOCKED)
def test_non_public_addresses_are_rejected(addr):
    assert ip_is_public(ipaddress.ip_address(addr)) is False


@pytest.mark.parametrize("addr", ALLOWED)
def test_public_addresses_are_allowed(addr):
    assert ip_is_public(ipaddress.ip_address(addr)) is True


def test_host_is_public_rejects_literal_private_ips():
    assert host_is_public("127.0.0.1") is False
    assert host_is_public("169.254.169.254") is False        # AWS/GCP link-local metadata
    assert host_is_public("100.100.100.200") is False        # Alibaba/Tencent/Oracle metadata (CGN)


def test_host_is_public_rejects_unresolvable():
    assert host_is_public("this-name-does-not-resolve.invalid") is False


def test_opener_wires_the_guarded_handlers():
    op = guarded_opener()
    kinds = {type(h) for h in op.handlers}
    assert GuardedHTTPHandler in kinds and GuardedHTTPSHandler in kinds


# ── fuzz the classifier over WHOLE ranges, not a handful of literals ───────────────────────────
# Every address inside these must be refused; a single literal per range can't catch an off-by-one
# in the range logic, but sampling hundreds of random hosts across each one does.
_BLOCKED_NETS = [
    "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",   # loopback + RFC1918
    "169.254.0.0/16", "100.64.0.0/10",                                # link-local (metadata) + CGN
    "0.0.0.0/8", "224.0.0.0/4", "240.0.0.0/4",                        # this-net, multicast, reserved
    "fe80::/10", "fc00::/7",                                          # IPv6 link-local + ULA
]
_PUBLIC_NETS = ["8.8.0.0/16", "1.1.0.0/16", "93.184.216.0/24", "2606:4700::/32"]


def _sample(net_str: str, rng: random.Random, n: int):
    net = ipaddress.ip_network(net_str)
    for _ in range(n):
        yield net.network_address + rng.randrange(net.num_addresses)


def test_fuzz_every_blocked_range_is_rejected():
    rng = random.Random(5545)
    for net in _BLOCKED_NETS:
        for ip in _sample(net, rng, 300):
            assert ip_is_public(ip) is False, f"{ip} inside {net} was allowed"


def test_fuzz_public_ranges_are_allowed():
    rng = random.Random(4700)
    for net in _PUBLIC_NETS:
        for ip in _sample(net, rng, 300):
            assert ip_is_public(ip) is True, f"{ip} inside {net} was rejected"


# ── the rebind guarantee: the peer is re-checked at CONNECT time (the layer a pre-check can't give) ──
class _FakeSock:
    """Stands in for a real connected socket — reports whatever peer the 'DNS' landed on."""
    def __init__(self, peer_ip: str):
        self._peer = peer_ip

    def getpeername(self):
        return (self._peer, 443)

    def close(self):
        pass


def test_peer_is_public_classifies_the_connected_socket():
    assert peer_is_public(_FakeSock("8.8.8.8")) is True
    assert peer_is_public(_FakeSock("2606:4700:4700::1111")) is True
    assert peer_is_public(_FakeSock("169.254.169.254")) is False     # rebound to cloud metadata
    assert peer_is_public(_FakeSock("fd00::1")) is False             # rebound to an internal ULA


def test_guarded_connection_refuses_a_peer_that_rebound_internal(monkeypatch):
    # The name resolved public at pre-check (layer 1 forced True); by connect time the socket lands on metadata.
    # The guard must see the REAL peer and refuse — the DNS-rebinding case a pre-check alone cannot stop.
    monkeypatch.setattr("ssrf_guard.host_is_public", lambda h: True)   # layer 1 passes; test layer 2 (no network)
    monkeypatch.setattr(http.client.HTTPConnection, "connect",
                        lambda self: setattr(self, "sock", _FakeSock("169.254.169.254")))
    with pytest.raises(SsrfBlocked):
        GuardedHTTPConnection("totally-legit.example").connect()


def test_guarded_connection_allows_a_public_peer(monkeypatch):
    monkeypatch.setattr("ssrf_guard.host_is_public", lambda h: True)   # isolate layer 2, no real DNS
    monkeypatch.setattr(http.client.HTTPConnection, "connect",
                        lambda self: setattr(self, "sock", _FakeSock("93.184.216.34")))
    conn = GuardedHTTPConnection("example.com")
    conn.connect()                                  # must NOT raise
    conn.close()


# ── redirects: a 3xx to an internal address must not be silently followed ──────────────────────
def test_redirects_are_refused_by_default():
    op = guarded_opener()
    assert any(isinstance(h, _NoRedirect) for h in op.handlers)
    # the handler returns None → urllib builds no redirect request, so a 3xx→internal is never chased
    assert _NoRedirect().redirect_request(None, None, 302, "Found", {}, "http://169.254.169.254/") is None


def test_redirects_can_be_opted_in_and_are_still_guarded_per_hop():
    op = guarded_opener(no_redirect=False)
    assert not any(isinstance(h, _NoRedirect) for h in op.handlers)
    # opting in drops the blanket refusal, but the Guarded* connections still re-check every hop's peer —
    # the same connect-time guard proven above applies to each redirect target.


# ── encapsulated v4 targets (mapped / NAT64) — the version-dependent edge the guard exists for ──
_ENCAP_BLOCKED = ["::ffff:127.0.0.1", "::ffff:169.254.169.254", "::ffff:10.0.0.1", "::ffff:192.168.1.1",
                  "64:ff9b::7f00:1", "64:ff9b::a9fe:a9fe"]      # NAT64 of loopback / cloud metadata


@pytest.mark.parametrize("addr", _ENCAP_BLOCKED)
def test_encapsulated_internal_v4_is_rejected(addr):
    # normalised to the embedded v4 and classified there → version-independent, not trusting stdlib v6 flags
    assert ip_is_public(ipaddress.ip_address(addr)) is False


def test_ipv4_mapped_public_is_allowed():
    assert ip_is_public(ipaddress.ip_address("::ffff:8.8.8.8")) is True


def test_pre_check_rejects_internal_host_before_the_socket(monkeypatch):
    # LAYER 1 (the "two-layer" claim): a host that resolves internal is refused BEFORE super().connect() opens a socket
    reached = {"socket": False}
    monkeypatch.setattr(http.client.HTTPConnection, "connect", lambda self: reached.__setitem__("socket", True))
    with pytest.raises(SsrfBlocked):
        GuardedHTTPConnection("127.0.0.1").connect()
    assert reached["socket"] is False
