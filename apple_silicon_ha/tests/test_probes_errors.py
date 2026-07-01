"""Tests focusing on error handling and boundary conditions in health probes."""

from __future__ import annotations

import subprocess

from apple_silicon_ha.probes import (
    ProbeResult,
    check_launchd_service,
    check_port_listening,
)


def test_check_launchd_service_handles_timeout_expired():
    def timeout_runner(_args: list[str]):
        raise subprocess.TimeoutExpired(cmd=["launchctl", "list", "com.example.service"], timeout=5)

    result = check_launchd_service("com.example.service", runner=timeout_runner)

    assert result.name == "launchd:com.example.service"
    assert result.ok is False
    assert "timed out after 5 seconds" in result.detail


def test_check_port_listening_handles_connector_without_close():
    class ConnectorNoClose:
        pass

    result = check_port_listening(
        "127.0.0.1",
        8080,
        connector=lambda _host, _port, _timeout: ConnectorNoClose(),
    )

    assert result == ProbeResult(name="port:127.0.0.1:8080", ok=True, detail="listening")
