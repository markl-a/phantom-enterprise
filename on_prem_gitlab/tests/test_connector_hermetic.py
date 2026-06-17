"""Hermetic (offline) tests for the on-prem Gitea/GitLab connector.

The companion ``test_connector.py`` only runs against a *live* Gitea and skips
entirely when the host is unreachable, so the connector's request-building,
auth-header, and error-handling logic shipped with no CI-safe coverage.

These tests stub ``requests.get`` (the single network call site) so the pure
HTTP-shaping logic is verified fully offline — no socket is ever opened. A
guard fixture makes any *real* network call a hard failure.
"""

import pytest
import requests

from on_prem_gitlab import connector
from on_prem_gitlab.connector import (
    GiteaUnreachable,
    get_repo_file,
    list_repo_files,
    list_repos,
)

BASE = "http://gitea.example:3000"


class FakeResponse:
    def __init__(self, *, status=200, reason="OK", json_data=None, text="", raises=None):
        self.status_code = status
        self.reason = reason
        self.ok = 200 <= status < 400
        self._json = json_data
        self._raises = raises
        self.text = text

    def json(self):
        if self._raises is not None:
            raise self._raises
        return self._json


def _capturing_get(captured, response):
    """Return a fake ``requests.get`` that records its call and returns ``response``."""

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        captured["headers"] = kwargs.get("headers") or {}
        captured["timeout"] = kwargs.get("timeout")
        return response

    return fake_get


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    """Fail loudly if any test forgets to stub ``requests.get``."""

    def boom(*a, **k):  # pragma: no cover - only hit on a test bug
        raise AssertionError("real network call escaped the stub")

    monkeypatch.setattr(connector.requests, "get", boom)


# --- list_repos ------------------------------------------------------------

def test_list_repos_builds_search_url_and_unwraps_data(monkeypatch):
    captured = {}
    resp = FakeResponse(json_data={"ok": True, "data": [{"name": "r1"}, {"name": "r2"}]})
    monkeypatch.setattr(connector.requests, "get", _capturing_get(captured, resp))

    repos = list_repos(base_url=BASE, limit=10)

    assert repos == [{"name": "r1"}, {"name": "r2"}]
    assert captured["url"] == "http://gitea.example:3000/api/v1/repos/search"
    assert captured["params"] == {"limit": 10}
    assert captured["headers"]["Accept"] == "application/json"
    # anonymous: no Authorization header
    assert "Authorization" not in captured["headers"]


def test_list_repos_sends_token_auth_header(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(json_data={"data": []})),
    )

    list_repos(token="SECRET", base_url=BASE)

    assert captured["headers"]["Authorization"] == "token SECRET"


def test_list_repos_trailing_slash_base_url_no_double_slash(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(json_data={"data": []})),
    )
    list_repos(base_url=BASE + "/")
    assert captured["url"] == "http://gitea.example:3000/api/v1/repos/search"


def test_list_repos_bare_list_payload(monkeypatch):
    # Some endpoints return a bare list rather than {"data": [...]}.
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get({}, FakeResponse(json_data=[{"name": "x"}])),
    )
    assert list_repos(base_url=BASE) == [{"name": "x"}]


def test_list_repos_connection_error_raises_unreachable(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("no route to host")

    monkeypatch.setattr(connector.requests, "get", boom)
    with pytest.raises(GiteaUnreachable):
        list_repos(base_url=BASE)


def test_list_repos_http_error_raises_unreachable(monkeypatch):
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get({}, FakeResponse(status=500, reason="Internal Server Error")),
    )
    with pytest.raises(GiteaUnreachable) as ei:
        list_repos(base_url=BASE)
    assert "500" in str(ei.value)


def test_list_repos_non_json_raises_unreachable(monkeypatch):
    resp = FakeResponse(raises=ValueError("not json"))
    monkeypatch.setattr(connector.requests, "get", _capturing_get({}, resp))
    with pytest.raises(GiteaUnreachable):
        list_repos(base_url=BASE)


# --- list_repo_files -------------------------------------------------------

def test_list_repo_files_builds_tree_url_and_filters_non_dicts(monkeypatch):
    captured = {}
    tree = [
        {"path": "a.py", "type": "blob", "size": 10},
        {"path": "sub", "type": "tree"},
        "garbage-non-dict",  # must be filtered out
    ]
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(json_data={"tree": tree})),
    )

    entries = list_repo_files("acme", "widgets", ref="main", base_url=BASE)

    assert entries == [
        {"path": "a.py", "type": "blob", "size": 10},
        {"path": "sub", "type": "tree"},
    ]
    assert captured["url"] == (
        "http://gitea.example:3000/api/v1/repos/acme/widgets/git/trees/main"
    )
    assert captured["params"] == {"recursive": "true", "per_page": 1000}


def test_list_repo_files_defaults_ref_to_head(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(json_data={"tree": []})),
    )
    list_repo_files("acme", "widgets", base_url=BASE)
    assert captured["url"].endswith("/git/trees/HEAD")


def test_list_repo_files_token_header_and_errors(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(json_data={"tree": []})),
    )
    list_repo_files("a", "b", token="T", base_url=BASE)
    assert captured["headers"]["Authorization"] == "token T"

    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get({}, FakeResponse(status=404, reason="Not Found")),
    )
    with pytest.raises(GiteaUnreachable):
        list_repo_files("a", "b", base_url=BASE)


# --- get_repo_file ---------------------------------------------------------

def test_get_repo_file_builds_raw_url_and_returns_text(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(text="print('hi')\n")),
    )

    out = get_repo_file("acme", "widgets", "src/app.py", ref="dev", base_url=BASE)

    assert out == "print('hi')\n"
    assert captured["url"] == (
        "http://gitea.example:3000/api/v1/repos/acme/widgets/raw/src/app.py"
    )
    assert captured["params"] == {"ref": "dev"}


def test_get_repo_file_strips_leading_slash_and_omits_ref(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get(captured, FakeResponse(text="x")),
    )
    get_repo_file("acme", "widgets", "/README.md", base_url=BASE)
    assert captured["url"].endswith("/raw/README.md")
    # no ref -> no ref param
    assert captured["params"] == {}


def test_get_repo_file_http_error_raises_unreachable(monkeypatch):
    monkeypatch.setattr(
        connector.requests,
        "get",
        _capturing_get({}, FakeResponse(status=403, reason="Forbidden")),
    )
    with pytest.raises(GiteaUnreachable) as ei:
        get_repo_file("a", "b", "c.py", base_url=BASE)
    assert "403" in str(ei.value)


def test_get_repo_file_connection_error_raises_unreachable(monkeypatch):
    def boom(*a, **k):
        raise requests.Timeout("slow")

    monkeypatch.setattr(connector.requests, "get", boom)
    with pytest.raises(GiteaUnreachable):
        get_repo_file("a", "b", "c.py", base_url=BASE)
