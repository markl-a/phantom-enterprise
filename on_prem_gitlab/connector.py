"""Proof-of-concept enterprise connector against a real on-prem Git host.

Validated daily against the maintainer's self-hosted **Gitea on z13**
(``http://100.87.70.65:3000``) over Tailscale. The same URL-shape works
unmodified for self-hosted GitLab — only the ``/api/v1`` path differs
(``/api/v4`` for GitLab) and that swap is the first thing to add when a
real GitLab instance is in scope.

Public API:

    list_repos(token=None, base_url=DEFAULT_BASE_URL, timeout=5) -> list[dict]
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

import requests

DEFAULT_BASE_URL = "http://100.87.70.65:3000"
"""Maintainer's self-hosted Gitea on z13 (reachable over Tailscale)."""


class GiteaUnreachable(RuntimeError):
    """Raised when the on-prem Gitea/GitLab host is not reachable."""


def list_repos(
    token: Optional[str] = None,
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 5.0,
    limit: int = 50,
) -> list[dict]:
    """List repositories visible to the given token (or anon if None).

    Hits Gitea's ``/api/v1/repos/search`` endpoint which works without
    authentication for public repos — perfect for a smoke-test connector
    that proves Tailscale → on-prem-git reachability end-to-end.

    Args:
        token: Optional Gitea/GitLab personal access token. If None, only
            public repos are returned.
        base_url: Base URL of the on-prem instance.
        timeout: Per-request timeout in seconds.
        limit: Max repos to return (Gitea page size).

    Returns:
        List of dicts (Gitea repo objects). Empty list if the instance
        has no visible repos.

    Raises:
        GiteaUnreachable: Host unreachable, timed out, or non-2xx response.
    """
    url = urljoin(base_url.rstrip("/") + "/", "api/v1/repos/search")
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        resp = requests.get(
            url,
            params={"limit": limit},
            headers=headers,
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise GiteaUnreachable(f"{base_url}: {exc}") from exc

    if not resp.ok:
        raise GiteaUnreachable(
            f"{base_url}: HTTP {resp.status_code} {resp.reason}"
        )

    try:
        payload = resp.json()
    except ValueError as exc:
        raise GiteaUnreachable(f"{base_url}: non-JSON response") from exc

    # Gitea search response: {"ok": bool, "data": [...]}
    data = payload.get("data") if isinstance(payload, dict) else payload
    return list(data or [])
