"""Tests for status environment configuration and error handling."""

from __future__ import annotations

import pytest
from apple_silicon_ha.probes import ProbeResult
from code_qa.status import (
    resolve_auth_backend,
    gather_ha_checks,
    check_tailscale,
    check_git,
)
from ldap_sso.auth import LdapAuth


def test_resolve_auth_backend_ldap_vs_none(monkeypatch):
    # Unset LDAP_SERVER_URI
    monkeypatch.setenv("LDAP_SERVER_URI", "")
    assert resolve_auth_backend() is None

    # Set LDAP_SERVER_URI
    monkeypatch.setenv("LDAP_SERVER_URI", "ldap://localhost:389")
    backend = resolve_auth_backend()
    assert isinstance(backend, LdapAuth)
    assert backend.server_uri == "ldap://localhost:389"


def test_gather_ha_checks_list_vs_none(monkeypatch):
    # Unset PHANTOM_HA_PEERS
    monkeypatch.setenv("PHANTOM_HA_PEERS", "")
    assert gather_ha_checks() is None

    # Set PHANTOM_HA_PEERS and mock check_peer_reachable
    monkeypatch.setenv("PHANTOM_HA_PEERS", "host-a, host-b")
    called_hosts = []

    def mock_check_peer_reachable(host: str) -> ProbeResult:
        called_hosts.append(host)
        return ProbeResult(name=f"peer:{host}", ok=True, detail="mocked")

    monkeypatch.setattr("code_qa.status.check_peer_reachable", mock_check_peer_reachable)

    results = gather_ha_checks()
    assert results is not None
    assert len(results) == 2
    assert called_hosts == ["host-a", "host-b"]
    assert results[0].name == "peer:host-a"
    assert results[1].name == "peer:host-b"


def test_check_tailscale_exception_handling():
    def failing_router() -> list[object]:
        raise Exception("router connection failed")

    res = check_tailscale(router=failing_router)
    assert res == ProbeResult(
        name="tailscale",
        ok=False,
        detail="router connection failed",
    )


def test_check_git_exception_handling():
    def failing_lister(*args, **kwargs) -> list[object]:
        raise Exception("lister database error")

    res = check_git(lister=failing_lister)
    assert res == ProbeResult(
        name="git",
        ok=False,
        detail="lister database error",
    )
