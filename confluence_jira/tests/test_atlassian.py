"""Live Atlassian connector tests (skip gracefully if env or instance unavailable)."""

import os

import pytest
import requests

from confluence_jira.atlassian import DEFAULT_BASE_URL, AtlassianError, search_pages


def _configured() -> bool:
    return all(
        os.environ.get(name)
        for name in ("ATLASSIAN_BASE_URL", "ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN")
    )


def _atlassian_reachable() -> bool:
    if not _configured():
        return False
    try:
        r = requests.get(
            f"{DEFAULT_BASE_URL.rstrip('/')}/wiki/rest/api/space",
            auth=(os.environ["ATLASSIAN_EMAIL"], os.environ["ATLASSIAN_API_TOKEN"]),
            timeout=3,
        )
        return r.ok
    except requests.RequestException:
        return False


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("PHANTOM_ENTERPRISE_LIVE") != "1" or not _atlassian_reachable(),
        reason="set PHANTOM_ENTERPRISE_LIVE=1 with Atlassian env to run live Atlassian tests",
    ),
]


def test_search_pages_returns_list():
    pages = search_pages(
        "type = page",
        email=os.environ["ATLASSIAN_EMAIL"],
        token=os.environ["ATLASSIAN_API_TOKEN"],
        base_url=DEFAULT_BASE_URL,
        timeout=5,
        limit=1,
    )
    assert isinstance(pages, list)
    for page in pages:
        assert isinstance(page, dict)


def test_search_pages_unreachable_raises():
    with pytest.raises(AtlassianError):
        search_pages(
            "type = page",
            email=os.environ["ATLASSIAN_EMAIL"],
            token=os.environ["ATLASSIAN_API_TOKEN"],
            base_url="http://127.0.0.1:1",
            timeout=1,
        )
