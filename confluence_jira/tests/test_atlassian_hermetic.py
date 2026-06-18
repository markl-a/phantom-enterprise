import base64

import pytest

from confluence_jira import atlassian
from confluence_jira.atlassian import (
    AtlassianError,
    add_comment,
    get_page,
    list_issues,
    search_pages,
)

BASE = "https://acme.atlassian.net"
EMAIL = "dev@example.com"
TOKEN = "api-token"


class Response:
    def __init__(
        self,
        payload=None,
        *,
        ok=True,
        status_code=200,
        reason="OK",
    ):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.reason = reason

    def json(self):
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload


def _decoded_auth(headers):
    scheme, encoded = headers["Authorization"].split(" ", 1)
    assert scheme == "Basic"
    return base64.b64decode(encoded).decode("utf-8")


@pytest.fixture(autouse=True)
def _no_real_network(monkeypatch):
    """Fail loudly if any test forgets to stub ``requests.get`` or ``post``."""

    def boom(*a, **k):  # pragma: no cover - only hit on a test bug
        raise AssertionError("real network call escaped the stub")

    monkeypatch.setattr(atlassian.requests, "get", boom)
    monkeypatch.setattr(atlassian.requests, "post", boom)


def test_search_pages_builds_url_headers_params_and_unwraps_results(monkeypatch):
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        return Response({"results": [{"id": "1", "title": "Runbook"}]})

    monkeypatch.setattr(atlassian.requests, "get", fake_get)

    pages = search_pages(
        'type = page and text ~ "deploy"',
        email=EMAIL,
        token=TOKEN,
        base_url=BASE + "/",
        timeout=2.5,
        limit=10,
    )

    assert pages == [{"id": "1", "title": "Runbook"}]
    assert calls == [
        {
            "url": "https://acme.atlassian.net/wiki/rest/api/content/search",
            "params": {"cql": 'type = page and text ~ "deploy"', "limit": 10},
            "headers": {
                "Accept": "application/json",
                "Authorization": calls[0]["headers"]["Authorization"],
            },
            "timeout": 2.5,
        }
    ]
    assert _decoded_auth(calls[0]["headers"]) == f"{EMAIL}:{TOKEN}"


def test_get_page_builds_content_url_with_expand_and_returns_dict(monkeypatch):
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        return Response({"id": "123", "body": {"storage": {"value": "<p>x</p>"}}})

    monkeypatch.setattr(atlassian.requests, "get", fake_get)

    page = get_page(
        "123",
        email=EMAIL,
        token=TOKEN,
        base_url=BASE,
        timeout=3,
        expand="body.storage,version",
    )

    assert page == {"id": "123", "body": {"storage": {"value": "<p>x</p>"}}}
    assert calls == [
        {
            "url": "https://acme.atlassian.net/wiki/rest/api/content/123",
            "params": {"expand": "body.storage,version"},
            "headers": {
                "Accept": "application/json",
                "Authorization": calls[0]["headers"]["Authorization"],
            },
            "timeout": 3,
        }
    ]
    assert _decoded_auth(calls[0]["headers"]) == f"{EMAIL}:{TOKEN}"


def test_list_issues_builds_search_url_with_jql_and_unwraps_issues(monkeypatch):
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        return Response({"issues": [{"key": "ENG-1"}]})

    monkeypatch.setattr(atlassian.requests, "get", fake_get)

    issues = list_issues(
        "project = ENG",
        email=EMAIL,
        token=TOKEN,
        base_url=BASE,
        timeout=4,
        max_results=5,
    )

    assert issues == [{"key": "ENG-1"}]
    assert calls == [
        {
            "url": "https://acme.atlassian.net/rest/api/3/search",
            "params": {"jql": "project = ENG", "maxResults": 5},
            "headers": {
                "Accept": "application/json",
                "Authorization": calls[0]["headers"]["Authorization"],
            },
            "timeout": 4,
        }
    ]
    assert _decoded_auth(calls[0]["headers"]) == f"{EMAIL}:{TOKEN}"


def test_add_comment_posts_adf_body_and_accepts_201(monkeypatch):
    calls = []

    def fake_post(url, *, json, headers, timeout):
        calls.append(
            {
                "url": url,
                "json": json,
                "headers": headers,
                "timeout": timeout,
            }
        )
        return Response({"id": "10001", "body": json["body"]}, status_code=201)

    monkeypatch.setattr(atlassian.requests, "post", fake_post)

    comment = add_comment(
        "ENG-1",
        "Ship it",
        email=EMAIL,
        token=TOKEN,
        base_url=BASE + "/",
        timeout=5,
    )

    expected_json = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": "Ship it"}],
                }
            ],
        }
    }
    assert comment == {"id": "10001", "body": expected_json["body"]}
    assert calls == [
        {
            "url": "https://acme.atlassian.net/rest/api/3/issue/ENG-1/comment",
            "json": expected_json,
            "headers": {
                "Accept": "application/json",
                "Authorization": calls[0]["headers"]["Authorization"],
                "Content-Type": "application/json",
            },
            "timeout": 5,
        }
    ]
    assert _decoded_auth(calls[0]["headers"]) == f"{EMAIL}:{TOKEN}"


def test_request_exception_maps_to_atlassian_error(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        raise atlassian.requests.RequestException("connection failed")

    monkeypatch.setattr(atlassian.requests, "get", fake_get)

    with pytest.raises(AtlassianError, match="connection failed"):
        search_pages("type = page", email=EMAIL, token=TOKEN, base_url=BASE)


def test_http_error_maps_to_atlassian_error(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        return Response(ok=False, status_code=404, reason="Not Found")

    monkeypatch.setattr(atlassian.requests, "get", fake_get)

    with pytest.raises(AtlassianError, match="404"):
        get_page("missing", email=EMAIL, token=TOKEN, base_url=BASE)


def test_post_http_error_maps_to_atlassian_error(monkeypatch):
    def fake_post(url, *, json, headers, timeout):
        return Response(ok=False, status_code=500, reason="Internal Server Error")

    monkeypatch.setattr(atlassian.requests, "post", fake_post)

    with pytest.raises(AtlassianError, match="500"):
        add_comment("ENG-1", "x", email=EMAIL, token=TOKEN, base_url=BASE)


def test_non_json_maps_to_atlassian_error(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        return Response(ValueError("not json"))

    monkeypatch.setattr(atlassian.requests, "get", fake_get)

    with pytest.raises(AtlassianError, match="non-JSON response"):
        list_issues("project = ENG", email=EMAIL, token=TOKEN, base_url=BASE)
