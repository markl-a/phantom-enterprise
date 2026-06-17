"""Hermetic-friendly health probe helpers for Apple Silicon HA nodes."""

from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class ProbeResult:
    """Result from a single health probe."""

    name: str
    ok: bool
    detail: str = ""


def check_launchd_service(label: str, *, runner: Optional[Callable[[list[str]], subprocess.CompletedProcess]] = None) -> ProbeResult:
    """Check whether a launchd service label is loaded.

    The ``runner`` argument is injectable so tests and callers can avoid
    touching the real ``launchctl`` binary.
    """

    name = f"launchd:{label}"
    command = ["launchctl", "list", label]

    if runner is None:

        def runner(args: list[str]) -> subprocess.CompletedProcess:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

    try:
        completed = runner(command)
    except FileNotFoundError:
        return ProbeResult(name=name, ok=False, detail="launchctl unavailable")
    except (OSError, subprocess.TimeoutExpired) as exc:
        return ProbeResult(name=name, ok=False, detail=str(exc))

    ok = completed.returncode == 0
    detail = "loaded" if ok else f"launchctl exited {completed.returncode}"
    return ProbeResult(name=name, ok=ok, detail=detail)


def check_port_listening(
    host: str,
    port: int,
    *,
    timeout: float = 1.0,
    connector: Optional[Callable[[str, int, float], object]] = None,
) -> ProbeResult:
    """Check whether a TCP port accepts a connection.

    The ``connector`` argument is injectable so tests can avoid opening real
    sockets. The default connector closes the socket it creates.
    """

    name = f"port:{host}:{port}"

    if connector is None:

        def connector(host: str, port: int, timeout: float) -> object:
            connection = socket.create_connection((host, port), timeout)
            connection.close()
            return connection

    try:
        connection = connector(host, port, timeout)
    except OSError as exc:
        return ProbeResult(name=name, ok=False, detail=str(exc))

    close = getattr(connection, "close", None)
    if callable(close):
        close()
    return ProbeResult(name=name, ok=True, detail="listening")


def check_peer_reachable(hostname: str, *, resolver: Optional[Callable[[str], Optional[str]]] = None) -> ProbeResult:
    """Check whether a peer hostname resolves to a tailnet IP."""

    name = f"peer:{hostname}"

    if resolver is None:
        from vpn_aware_routing.router import tailscale_route

        resolver = tailscale_route

    ip = resolver(hostname)
    if ip:
        return ProbeResult(name=name, ok=True, detail=ip)
    return ProbeResult(name=name, ok=False, detail="not on tailnet")


def decide_failover(primary: ProbeResult, replica: ProbeResult) -> dict:
    """Decide the HA action from already-collected primary and replica probes."""

    if primary.ok:
        return {"action": "none", "reason": "primary healthy"}
    if replica.ok:
        return {"action": "promote_replica", "reason": "primary down, replica healthy"}
    return {"action": "alert", "reason": "primary and replica both down"}


def run_all(checks: list[ProbeResult]) -> dict:
    """Summarize a list of probe results without performing any IO."""

    return {
        "healthy": all(check.ok for check in checks),
        "checks": [
            {"name": check.name, "ok": check.ok, "detail": check.detail}
            for check in checks
        ],
    }
