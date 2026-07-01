"""Tests for the loose partial match functionality of the Tailscale router."""

from vpn_aware_routing import router
from vpn_aware_routing.router import tailscale_route


def test_dot_free_query_resolves_loose_match(monkeypatch):
    """Test that a dot-free query resolves via the loose branch to a matching peer IP.

    If a peer has empty TailscaleIPs, it should resolve to None.
    """
    status = {
        "Self": {
            "HostName": "mac-node",
            "TailscaleIPs": ["100.64.0.1"],
            "Online": True,
            "OS": "macOS",
        },
        "Peer": {
            "nodekey:aaa": {
                "HostName": "win-node-a",
                "TailscaleIPs": ["100.64.0.13"],
                "Online": True,
                "OS": "linux",
            },
            "nodekey:bbb": {
                "HostName": "win-node-b",
                "TailscaleIPs": [],
                "Online": False,
                "OS": "windows",
            },
        },
    }
    monkeypatch.setattr(router, "_tailscale_status_json", lambda: status)

    # 1. A dot-free query resolves via the loose branch to the matching peer's IP
    assert tailscale_route("win-node") == "100.64.0.13"
    assert tailscale_route("node-a") == "100.64.0.13"

    # 2. A peer with empty TailscaleIPs resolves to None
    assert tailscale_route("win-node-b") is None
    assert tailscale_route("node-b") is None
