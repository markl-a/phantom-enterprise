"""Live Gitea connector tests (skip gracefully if z13 unreachable)."""

import pytest
import requests

from on_prem_gitlab.connector import DEFAULT_BASE_URL, GiteaUnreachable, list_repos


def _z13_reachable() -> bool:
    try:
        r = requests.get(
            f"{DEFAULT_BASE_URL}/api/v1/version",
            timeout=3,
        )
        return r.ok
    except requests.RequestException:
        return False


pytestmark = pytest.mark.skipif(
    not _z13_reachable(),
    reason="z13 Gitea (100.87.70.65:3000) not reachable — needs live Tailscale + z13 online",
)


def test_list_repos_returns_list():
    repos = list_repos(timeout=5)
    assert isinstance(repos, list)
    # Gitea always returns a list (may be empty if no public repos)
    for r in repos:
        assert isinstance(r, dict)


def test_list_repos_unreachable_raises():
    with pytest.raises(GiteaUnreachable):
        list_repos(base_url="http://127.0.0.1:1", timeout=1)
