"""Hermetic (offline) tests for the Tailscale router.

The live tests in ``test_router.py`` skip whenever the ``tailscale`` CLI or a
logged-in tailnet is absent, so the JSON-parsing and host-matching logic ships
with no CI-safe coverage. These tests stub ``_tailscale_status_json`` (the only
function that shells out) so the pure logic is exercised fully offline — no
subprocess, no network.
"""

from vpn_aware_routing import router
from vpn_aware_routing.router import RouteResult, list_peers, tailscale_route


# A representative ``tailscale status --json`` payload (trimmed to the fields
# the router actually reads).
SAMPLE_STATUS = {
    "Self": {
        "HostName": "MarkMacBook-Air",
        "TailscaleIPs": ["100.64.0.1", "fd7a::1"],
        "Online": True,
        "OS": "macOS",
    },
    "Peer": {
        "nodekey:aaa": {
            "HostName": "z13",
            "TailscaleIPs": ["100.64.0.13"],
            "Online": True,
            "OS": "linux",
        },
        "nodekey:bbb": {
            "HostName": "yoyogood",
            "TailscaleIPs": ["100.64.0.20"],
            "Online": False,
            "OS": "windows",
        },
    },
}


def _patch_status(monkeypatch, payload, counter=None):
    def fake():
        if counter is not None:
            counter["calls"] += 1
        return payload

    monkeypatch.setattr(router, "_tailscale_status_json", fake)


def test_list_peers_parses_self_and_peers(monkeypatch):
    _patch_status(monkeypatch, SAMPLE_STATUS)
    peers = list_peers()
    assert all(isinstance(p, RouteResult) for p in peers)
    by_host = {p.hostname: p for p in peers}
    # hostnames are lower-cased
    assert "markmacbook-air" in by_host
    assert "z13" in by_host
    assert "yoyogood" in by_host
    # first TailscaleIP is taken; offline flag preserved
    assert by_host["z13"].ip == "100.64.0.13"
    assert by_host["z13"].online is True
    assert by_host["yoyogood"].online is False
    assert by_host["markmacbook-air"].os == "macOS"


def test_list_peers_empty_when_status_unavailable(monkeypatch):
    _patch_status(monkeypatch, None)
    assert list_peers() == []


def test_route_exact_match_case_insensitive(monkeypatch):
    _patch_status(monkeypatch, SAMPLE_STATUS)
    assert tailscale_route("Z13") == "100.64.0.13"
    assert tailscale_route("yoyogood") == "100.64.0.20"


def test_route_loose_suffix_match(monkeypatch):
    _patch_status(monkeypatch, SAMPLE_STATUS)
    # MagicDNS-style FQDN query resolves via substring/prefix match
    assert tailscale_route("z13.tailnet.ts.net") == "100.64.0.13"


def test_route_fqdn_first_label_only_matches_trusted_tailnet_domain(monkeypatch):
    """A FQDN whose suffix is NOT the trusted tailnet domain must NOT resolve.

    Regression guard: the MagicDNS first-label match used to compare the first
    label of *any* FQDN against a peer's short hostname, so an attacker-controlled
    domain like ``z13.evil.com`` would resolve to the trusted peer ``z13``'s
    tailnet IP — routing traffic meant for the attacker's host straight at the
    real peer. The first-label shortcut must be anchored to ``*.ts.net``.
    """
    _patch_status(monkeypatch, SAMPLE_STATUS)
    # Attacker-controlled suffix borrowing a real peer's short name -> no route.
    assert tailscale_route("z13.evil.com") is None
    assert tailscale_route("yoyogood.attacker.net") is None
    # Sanity: the legitimate MagicDNS FQDN for the same peer still resolves.
    assert tailscale_route("z13.tailnet.ts.net") == "100.64.0.13"


def test_route_unknown_and_empty_return_none(monkeypatch):
    _patch_status(monkeypatch, SAMPLE_STATUS)
    assert tailscale_route("no-such-host") is None
    assert tailscale_route("") is None
    assert tailscale_route("   ") is None


def test_route_queries_tailnet_at_most_once(monkeypatch):
    """An unknown-host lookup must not shell out to the CLI twice.

    ``tailscale_route`` previously called ``list_peers()`` once for the exact
    pass and again for the loose pass, doubling the ``tailscale status --json``
    subprocess cost on the (common) miss path.
    """
    counter = {"calls": 0}
    _patch_status(monkeypatch, SAMPLE_STATUS, counter=counter)
    tailscale_route("definitely-not-a-peer")
    assert counter["calls"] == 1, (
        f"expected the tailnet to be queried once, got {counter['calls']}"
    )
