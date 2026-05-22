"""Live Tailscale tests (skip gracefully if CLI / tailnet not available)."""

import ipaddress
import shutil

import pytest

from vpn_aware_routing.router import RouteResult, list_peers, tailscale_route


pytestmark = pytest.mark.skipif(
    shutil.which("tailscale") is None,
    reason="tailscale CLI not installed — VPN routing tests require live tailnet",
)


def _is_tailnet_ip(s: str) -> bool:
    try:
        return ipaddress.ip_address(s) in ipaddress.ip_network("100.64.0.0/10")
    except ValueError:
        return False


def test_list_peers_returns_routeresults():
    peers = list_peers()
    if not peers:
        pytest.skip("tailscale not logged in or no peers — cannot validate")
    assert all(isinstance(p, RouteResult) for p in peers)
    # At least one peer should resolve to a tailnet IP
    routable = [p for p in peers if p.ip and _is_tailnet_ip(p.ip)]
    assert routable, "expected at least one tailnet-routable peer"


def test_tailscale_route_returns_ip_for_known_peer():
    peers = list_peers()
    if not peers:
        pytest.skip("tailscale not logged in or no peers")

    # Pick first peer with a non-empty hostname and IP
    candidates = [p for p in peers if p.hostname and p.ip]
    if not candidates:
        pytest.skip("no peer with hostname+ip — cannot validate lookup")

    target = candidates[0]
    ip = tailscale_route(target.hostname)
    assert ip == target.ip
    assert _is_tailnet_ip(ip)


def test_tailscale_route_unknown_host_returns_none():
    assert tailscale_route("this-host-definitely-not-on-tailnet-xyz") is None


def test_tailscale_route_empty_string_returns_none():
    assert tailscale_route("") is None
