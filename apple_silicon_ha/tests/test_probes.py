"""Hermetic tests for Apple Silicon HA probe helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from apple_silicon_ha.probes import (
    ProbeResult,
    check_launchd_service,
    check_peer_reachable,
    check_port_listening,
    decide_failover,
    run_all,
)


@dataclass(frozen=True)
class StubCompletedProcess:
    """Minimal subprocess result stub for launchd tests."""

    returncode: int


class FakeSocket:
    """Minimal socket-like object for connector tests."""

    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_check_launchd_service_ok_when_runner_returns_zero():
    result = check_launchd_service(
        "com.example.primary",
        runner=lambda _args: StubCompletedProcess(returncode=0),
    )

    assert result == ProbeResult(
        name="launchd:com.example.primary",
        ok=True,
        detail="loaded",
    )


def test_check_launchd_service_false_when_runner_returns_nonzero():
    result = check_launchd_service(
        "com.example.primary",
        runner=lambda _args: StubCompletedProcess(returncode=1),
    )

    assert result.name == "launchd:com.example.primary"
    assert result.ok is False
    assert result.detail == "launchctl exited 1"


def test_check_launchd_service_handles_missing_launchctl():
    def missing_runner(_args: list[str]) -> StubCompletedProcess:
        raise FileNotFoundError("launchctl")

    result = check_launchd_service("com.example.primary", runner=missing_runner)

    assert result.name == "launchd:com.example.primary"
    assert result.ok is False
    assert result.detail == "launchctl unavailable"


def test_check_port_listening_ok_when_connector_succeeds():
    fake_socket = FakeSocket()

    result = check_port_listening(
        "127.0.0.1",
        8080,
        connector=lambda _host, _port, _timeout: fake_socket,
    )

    assert result == ProbeResult(name="port:127.0.0.1:8080", ok=True, detail="listening")
    assert fake_socket.closed is True


def test_check_port_listening_false_when_connector_raises_oserror():
    def broken_connector(_host: str, _port: int, _timeout: float) -> object:
        raise OSError("connection refused")

    result = check_port_listening("127.0.0.1", 8080, connector=broken_connector)

    assert result.name == "port:127.0.0.1:8080"
    assert result.ok is False
    assert result.detail == "connection refused"


def test_check_peer_reachable_ok_when_resolver_returns_ip():
    result = check_peer_reachable(
        "replica",
        resolver=lambda _hostname: "100.1.2.3",
    )

    assert result.name == "peer:replica"
    assert result.ok is True
    assert "100.1.2.3" in result.detail


def test_check_peer_reachable_false_when_resolver_returns_none():
    result = check_peer_reachable("replica", resolver=lambda _hostname: None)

    assert result == ProbeResult(name="peer:replica", ok=False, detail="not on tailnet")


@pytest.mark.parametrize(
    ("primary", "replica", "expected"),
    [
        (
            ProbeResult("primary", True),
            ProbeResult("replica", True),
            {"action": "none", "reason": "primary healthy"},
        ),
        (
            ProbeResult("primary", False),
            ProbeResult("replica", True),
            {"action": "promote_replica", "reason": "primary down, replica healthy"},
        ),
        (
            ProbeResult("primary", False),
            ProbeResult("replica", False),
            {"action": "alert", "reason": "primary and replica both down"},
        ),
    ],
)
def test_decide_failover_branches(primary: ProbeResult, replica: ProbeResult, expected: dict):
    assert decide_failover(primary, replica) == expected


def test_run_all_healthy_true_when_all_checks_ok():
    checks = [
        ProbeResult("launchd:primary", True, "loaded"),
        ProbeResult("port:primary:8080", True, "listening"),
    ]

    assert run_all(checks) == {
        "healthy": True,
        "checks": [
            {"name": "launchd:primary", "ok": True, "detail": "loaded"},
            {"name": "port:primary:8080", "ok": True, "detail": "listening"},
        ],
    }


def test_run_all_healthy_false_when_any_check_fails():
    result = run_all(
        [
            ProbeResult("launchd:primary", True, "loaded"),
            ProbeResult("port:primary:8080", False, "connection refused"),
        ]
    )

    assert result["healthy"] is False
    assert result["checks"][1] == {
        "name": "port:primary:8080",
        "ok": False,
        "detail": "connection refused",
    }
