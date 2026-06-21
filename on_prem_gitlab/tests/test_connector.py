"""Live Gitea connector tests (skip gracefully if the on-prem host is unreachable)."""

import os

import pytest
import requests

from on_prem_gitlab.connector import DEFAULT_BASE_URL, GiteaUnreachable, list_repos


def _live_enabled() -> bool:
    return os.environ.get("PHANTOM_ENTERPRISE_LIVE") == "1"


def _gitea_reachable() -> bool:
    try:
        r = requests.get(
            f"{DEFAULT_BASE_URL}/api/v1/version",
            timeout=3,
        )
        return r.ok
    except requests.RequestException:
        return False


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not _live_enabled() or not _gitea_reachable(),
        reason="set PHANTOM_ENTERPRISE_LIVE=1 with reachable GITEA_BASE_URL to run live Gitea tests",
    ),
]


def test_list_repos_returns_list():
    repos = list_repos(timeout=5)
    assert isinstance(repos, list)
    # Gitea always returns a list (may be empty if no public repos)
    for r in repos:
        assert isinstance(r, dict)


def test_list_repos_unreachable_raises():
    with pytest.raises(GiteaUnreachable):
        list_repos(base_url="http://127.0.0.1:1", timeout=1)
