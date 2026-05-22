"""VPN-aware routing — resolve internal hostnames over Tailscale."""

from .router import tailscale_route, list_peers, RouteResult

__all__ = ["tailscale_route", "list_peers", "RouteResult"]
