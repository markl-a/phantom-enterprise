"""Hermetic tests for Atlassian payload-shape defensiveness.

``search_pages``/``list_issues`` unwrap a dict's ``results``/``issues`` key,
but a misbehaving server could return a bare list, a non-dict scalar, or a
dict missing that key. All three shapes must degrade to ``[]`` rather than
raising.
"""

import pytest

from confluence_jira import atlassian
from confluence_jira.atlassian import list_issues, search_pages

BASE = "https://acme.atlassian.net"
EMAIL = "dev@example.com"
TOKEN = "api-token"


class Response:
    def __init__(self, payload=None, *, ok=True, status_code=200, reason="OK"):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.reason = reason

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    def boom(*a, **k):  # pragma: no cover - only hit on a test bug
        raise AssertionError("real network call escaped the stub")

    monkeypatch.setattr(atlassian.requests, "get", boom)
    monkeypatch.setattr(atlassian.requests, "post", boom)


@pytest.mark.parametrize(
    "payload",
    [
        [{"id": "1", "title": "Runbook"}],
        "not-a-dict",
        42,
        None,
        {"unrelated": "shape"},
    ],
)
def test_search_pages_returns_empty_list_for_unexpected_payload_shapes(
    monkeypatch, payload
):
    monkeypatch.setattr(
        atlassian.requests, "get", lambda *a, **k: Response(payload)
    )

    assert search_pages("type = page", email=EMAIL, token=TOKEN, base_url=BASE) == []


@pytest.mark.parametrize(
    "payload",
    [
        [{"key": "ENG-1"}],
        "not-a-dict",
        42,
        None,
        {"unrelated": "shape"},
    ],
)
def test_list_issues_returns_empty_list_for_unexpected_payload_shapes(
    monkeypatch, payload
):
    monkeypatch.setattr(
        atlassian.requests, "get", lambda *a, **k: Response(payload)
    )

    assert (
        list_issues("project = ENG", email=EMAIL, token=TOKEN, base_url=BASE) == []
    )
