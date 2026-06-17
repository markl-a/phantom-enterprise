"""HA-readiness status checks for the ``phantom-enterprise`` CLI."""

from __future__ import annotations

import os
from typing import Callable, Optional

from apple_silicon_ha.probes import ProbeResult, check_peer_reachable, run_all
from ldap_sso.auth import AuthBackend, LdapAuth
from on_prem_gitlab import GiteaUnreachable


def resolve_auth_backend() -> Optional[AuthBackend]:
    """Build the configured SSO backend from the environment, or None.

    If the env var LDAP_SERVER_URI is set (non-empty), return
    LdapAuth(server_uri=that value); otherwise return None (no backend
    configured yet, so the existing default "pending" detail then applies).
    """

    server_uri = os.environ.get("LDAP_SERVER_URI", "")
    if server_uri:
        return LdapAuth(server_uri=server_uri)
    return None


def gather_ha_checks() -> Optional[list[ProbeResult]]:
    """Collect Apple Silicon HA probe results from configuration, or None.

    If the env var PHANTOM_HA_PEERS is set (comma-separated hostnames), run
    check_peer_reachable(host) for each non-empty hostname and return the list
    of ProbeResult; otherwise return None (HA not configured).
    """

    hosts = [
        host.strip()
        for host in os.environ.get("PHANTOM_HA_PEERS", "").split(",")
        if host.strip()
    ]
    if not hosts:
        return None

    return [check_peer_reachable(host) for host in hosts]


def check_tailscale(*, router: Optional[Callable[[], list[object]]] = None) -> ProbeResult:
    """Check whether Tailscale can report at least one tailnet node.

    The ``router`` callable is injectable so tests and callers can avoid
    touching the real Tailscale CLI.
    """

    if router is None:
        from vpn_aware_routing.router import list_peers

        router = list_peers

    try:
        peers = router()
    except Exception as exc:
        return ProbeResult(name="tailscale", ok=False, detail=str(exc))

    count = len(peers)
    if count:
        return ProbeResult(name="tailscale", ok=True, detail=f"{count} tailnet node(s)")
    return ProbeResult(
        name="tailscale",
        ok=False,
        detail="tailscale unavailable / no peers",
    )


def check_git(
    *,
    base_url: Optional[str] = None,
    lister: Optional[Callable[..., list[object]]] = None,
) -> ProbeResult:
    """Check whether the on-prem Git service can list repositories.

    The ``lister`` callable is injectable so tests and callers can avoid
    touching a real Gitea/GitLab host.
    """

    if lister is None:
        from on_prem_gitlab import list_repos

        lister = list_repos

    try:
        repos = lister(base_url=base_url) if base_url else lister()
    except GiteaUnreachable as exc:
        return ProbeResult(name="git", ok=False, detail=str(exc))
    except Exception as exc:
        return ProbeResult(name="git", ok=False, detail=str(exc))

    return ProbeResult(name="git", ok=True, detail=f"{len(repos)} repo(s)")


def check_auth(*, backend: Optional[AuthBackend] = None) -> ProbeResult:
    """Report whether an SSO backend is configured.

    This intentionally does not call ``authenticate`` because the current
    backend implementations raise ``NotImplementedError`` by design.
    """

    if backend is None:
        return ProbeResult(
            name="auth",
            ok=False,
            detail="no SSO backend configured (LDAP/SAML/OIDC pending)",
        )
    return ProbeResult(
        name="auth",
        ok=True,
        detail=f"{type(backend).__name__} configured",
    )


def check_ha(*, checks: Optional[list[ProbeResult]] = None) -> ProbeResult:
    """Summarize pre-collected Apple Silicon HA probe results."""

    if checks is None:
        return ProbeResult(name="ha", ok=False, detail="HA probes not configured")

    healthy = sum(check.ok for check in checks)
    total = len(checks)
    return ProbeResult(
        name="ha",
        ok=healthy == total,
        detail=f"{healthy}/{total} HA checks healthy",
    )


def gather_status(
    *,
    base_url: Optional[str] = None,
    backend: Optional[AuthBackend] = None,
    ha_checks: Optional[list[ProbeResult]] = None,
    router: Optional[Callable[[], list[object]]] = None,
    lister: Optional[Callable[..., list[object]]] = None,
) -> dict:
    """Run HA-readiness checks and return the shared probe summary shape."""

    checks = [
        check_tailscale(router=router),
        check_git(base_url=base_url, lister=lister),
        check_auth(backend=backend),
        check_ha(checks=ha_checks),
    ]
    return run_all(checks)
