"""Resolve a Tailscale peer hostname to its tailnet IP.

This is a real, working connector — phantom-mesh uses Tailscale as its
zero-trust VPN substrate so any enterprise deployment that runs Tailscale
gets host routing for free.

Falls back gracefully when the Tailscale CLI is missing or the peer is
not on the tailnet.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RouteResult:
    """Resolved route to a tailnet peer."""

    hostname: str
    ip: Optional[str]
    online: bool
    os: Optional[str] = None


def _tailscale_status_json() -> Optional[dict]:
    """Return ``tailscale status --json`` output, or None if unavailable."""
    if shutil.which("tailscale") is None:
        return None
    try:
        out = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return None


def list_peers() -> list[RouteResult]:
    """List all known tailnet peers (and self) as :class:`RouteResult` entries."""
    status = _tailscale_status_json()
    if not status:
        return []

    results: list[RouteResult] = []

    # Include self
    self_node = status.get("Self") or {}
    if self_node:
        ips = self_node.get("TailscaleIPs") or []
        results.append(
            RouteResult(
                hostname=(self_node.get("HostName") or "").lower(),
                ip=ips[0] if ips else None,
                online=bool(self_node.get("Online", True)),
                os=self_node.get("OS"),
            )
        )

    for _peer_id, peer in (status.get("Peer") or {}).items():
        ips = peer.get("TailscaleIPs") or []
        results.append(
            RouteResult(
                hostname=(peer.get("HostName") or "").lower(),
                ip=ips[0] if ips else None,
                online=bool(peer.get("Online", False)),
                os=peer.get("OS"),
            )
        )
    return results


def tailscale_route(node_hostname: str) -> Optional[str]:
    """Return the tailnet IP for ``node_hostname``, or None if not found.

    Matching is case-insensitive and uses the peer's ``HostName``
    (not the full MagicDNS FQDN).

    Args:
        node_hostname: Short hostname, e.g. ``"yoyogood"``, ``"z13"``,
            ``"markmacbook-air"``.

    Returns:
        IPv4 string (e.g. ``"100.x.y.z"``) or None.
    """
    target = (node_hostname or "").lower().strip()
    if not target:
        return None

    for peer in list_peers():
        if peer.hostname == target:
            return peer.ip

    # Loose suffix match for MagicDNS-style queries
    for peer in list_peers():
        if peer.hostname.startswith(target) or target in peer.hostname:
            return peer.ip

    return None
