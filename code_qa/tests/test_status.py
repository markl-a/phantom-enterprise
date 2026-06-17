"""Hermetic tests for the HA-readiness status command."""

from __future__ import annotations

import json

import pytest

from apple_silicon_ha.probes import ProbeResult
from code_qa.cli import _pkg_version, build_parser, main
from code_qa.status import (
    check_auth,
    check_git,
    check_ha,
    check_tailscale,
    gather_status,
)
from ldap_sso.auth import LdapAuth
from on_prem_gitlab import GiteaUnreachable


def test_check_tailscale_reports_tailnet_nodes():
    def fake_router() -> list[object]:
        return [object()]

    result = check_tailscale(router=fake_router)

    assert result == ProbeResult(
        name="tailscale",
        ok=True,
        detail="1 tailnet node(s)",
    )


def test_check_tailscale_reports_no_peers():
    def fake_router() -> list[object]:
        return []

    result = check_tailscale(router=fake_router)

    assert result == ProbeResult(
        name="tailscale",
        ok=False,
        detail="tailscale unavailable / no peers",
    )


def test_check_git_reports_repo_count():
    def fake_lister() -> list[str]:
        return ["a", "b"]

    result = check_git(lister=fake_lister)

    assert result == ProbeResult(name="git", ok=True, detail="2 repo(s)")


def test_check_git_reports_unreachable():
    def fake_lister() -> list[str]:
        raise GiteaUnreachable("host down")

    result = check_git(lister=fake_lister)

    assert result == ProbeResult(name="git", ok=False, detail="host down")


def test_check_auth_reports_missing_backend():
    result = check_auth()

    assert result == ProbeResult(
        name="auth",
        ok=False,
        detail="no SSO backend configured (LDAP/SAML/OIDC pending)",
    )


def test_check_auth_reports_configured_backend():
    result = check_auth(backend=LdapAuth())

    assert result == ProbeResult(
        name="auth",
        ok=True,
        detail="LdapAuth configured",
    )


def test_check_ha_reports_missing_checks():
    result = check_ha()

    assert result == ProbeResult(name="ha", ok=False, detail="HA probes not configured")


def test_check_ha_reports_all_healthy():
    result = check_ha(
        checks=[
            ProbeResult(name="primary", ok=True, detail="ok"),
            ProbeResult(name="replica", ok=True, detail="ok"),
        ]
    )

    assert result == ProbeResult(name="ha", ok=True, detail="2/2 HA checks healthy")


def test_check_ha_reports_degraded():
    result = check_ha(
        checks=[
            ProbeResult(name="primary", ok=True, detail="ok"),
            ProbeResult(name="replica", ok=False, detail="down"),
        ]
    )

    assert result == ProbeResult(name="ha", ok=False, detail="1/2 HA checks healthy")


def test_gather_status_preserves_order_and_health():
    def fake_router() -> list[object]:
        return [object()]

    def fake_lister(*, base_url: str) -> list[str]:
        assert base_url == "http://git.example"
        return ["a"]

    result = gather_status(
        base_url="http://git.example",
        backend=LdapAuth(),
        ha_checks=[ProbeResult(name="primary", ok=True, detail="ok")],
        router=fake_router,
        lister=fake_lister,
    )

    assert result["healthy"] is True
    assert [check["name"] for check in result["checks"]] == [
        "tailscale",
        "git",
        "auth",
        "ha",
    ]


def test_gather_status_reports_degraded_when_any_check_fails():
    def fake_router() -> list[object]:
        return []

    def fake_lister() -> list[str]:
        return ["a"]

    result = gather_status(router=fake_router, lister=fake_lister)

    assert result["healthy"] is False
    assert [check["name"] for check in result["checks"]] == [
        "tailscale",
        "git",
        "auth",
        "ha",
    ]


def test_cli_parser_status_json_args():
    parser = build_parser()
    ns = parser.parse_args(["status", "--json"])

    assert ns.command == "status"
    assert ns.json is True
    assert ns.base_url is None


def test_cli_status_json_output_is_hermetic(monkeypatch, capsys):
    expected = {
        "healthy": False,
        "checks": [
            {"name": "tailscale", "ok": True, "detail": "1 tailnet node(s)"},
            {"name": "git", "ok": True, "detail": "2 repo(s)"},
            {"name": "auth", "ok": False, "detail": "missing"},
            {"name": "ha", "ok": False, "detail": "not configured"},
        ],
    }

    def fake_gather_status(*, base_url=None, backend=None, ha_checks=None):
        assert base_url is None
        assert backend is None
        assert ha_checks is None
        return expected

    monkeypatch.setattr("code_qa.status.resolve_auth_backend", lambda: None)
    monkeypatch.setattr("code_qa.status.gather_ha_checks", lambda: None)
    monkeypatch.setattr("code_qa.status.gather_status", fake_gather_status)

    exit_code = main(["status", "--json"])

    assert exit_code == 1
    assert json.loads(capsys.readouterr().out) == expected


def test_cli_status_healthy_environment_is_not_degraded(monkeypatch, capsys):
    monkeypatch.setattr("code_qa.status.resolve_auth_backend", lambda: LdapAuth())
    monkeypatch.setattr(
        "code_qa.status.gather_ha_checks",
        lambda: [ProbeResult(name="primary", ok=True, detail="ok")],
    )
    monkeypatch.setattr(
        "code_qa.status.check_tailscale",
        lambda **_: ProbeResult(name="tailscale", ok=True, detail="1 tailnet node(s)"),
    )
    monkeypatch.setattr(
        "code_qa.status.check_git",
        lambda **_: ProbeResult(name="git", ok=True, detail="2 repo(s)"),
    )

    exit_code = main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "overall: healthy" in output
    assert "DEGRADED" not in output


def test_cli_parser_version_flag(capsys):
    parser = build_parser()

    with pytest.raises(SystemExit) as excinfo:
        parser.parse_args(["--version"])

    assert excinfo.value.code == 0
    assert capsys.readouterr().out.startswith("phantom-enterprise ")


def test_pkg_version_returns_non_empty_string():
    assert _pkg_version()


def test_cli_status_human_output_is_hermetic(monkeypatch, capsys):
    expected = {
        "healthy": False,
        "checks": [
            {"name": "tailscale", "ok": True, "detail": "1 tailnet node(s)"},
            {"name": "git", "ok": False, "detail": "host down"},
        ],
    }

    def fake_gather_status(*, base_url=None, backend=None, ha_checks=None):
        assert base_url is None
        assert backend is None
        assert ha_checks is None
        return expected

    monkeypatch.setattr("code_qa.status.resolve_auth_backend", lambda: None)
    monkeypatch.setattr("code_qa.status.gather_ha_checks", lambda: None)
    monkeypatch.setattr("code_qa.status.gather_status", fake_gather_status)

    exit_code = main(["status"])
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "overall: DEGRADED" in output
    assert "[OK] tailscale: 1 tailnet node(s)" in output
    assert "[--] git: host down" in output
