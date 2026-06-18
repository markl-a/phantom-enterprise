"""Atlassian Cloud connector using the Confluence and Jira REST APIs.

Public API:

    search_pages(cql, *, email, token, base_url=DEFAULT_BASE_URL, timeout=10.0, limit=25) -> list[dict]
    get_page(page_id, *, email, token, base_url=DEFAULT_BASE_URL, timeout=10.0, expand="body.storage,version") -> dict
    list_issues(jql, *, email, token, base_url=DEFAULT_BASE_URL, timeout=10.0, max_results=50) -> list[dict]
    add_comment(issue_key, body, *, email, token, base_url=DEFAULT_BASE_URL, timeout=10.0) -> dict
"""

from __future__ import annotations

import base64
import os

import requests

DEFAULT_BASE_URL = os.environ.get("ATLASSIAN_BASE_URL", "https://your-domain.atlassian.net")
"""Atlassian Cloud base URL. Set ``ATLASSIAN_BASE_URL`` to your cloud instance."""


class AtlassianError(RuntimeError):
    """Raised when the Atlassian Cloud host is not reachable."""


def _auth_header(email: str, token: str) -> dict[str, str]:
    raw = f"{email}:{token}".encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    return {"Authorization": f"Basic {encoded}"}


def _headers(email: str, token: str, json_body: bool = False) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    headers.update(_auth_header(email, token))
    if json_body:
        headers["Content-Type"] = "application/json"
    return headers


def _get_json(
    url: str,
    *,
    params: dict[str, object],
    headers: dict[str, str],
    timeout: float,
    base_url: str,
) -> object:
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise AtlassianError(f"{base_url}: {exc}") from exc

    return _parse_json_response(resp, base_url=base_url)


def _post_json(
    url: str,
    *,
    json: dict[str, object],
    headers: dict[str, str],
    timeout: float,
    base_url: str,
) -> object:
    try:
        resp = requests.post(url, json=json, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise AtlassianError(f"{base_url}: {exc}") from exc

    return _parse_json_response(resp, base_url=base_url)


def _parse_json_response(resp: requests.Response, *, base_url: str) -> object:
    if not resp.ok:
        raise AtlassianError(f"{base_url}: HTTP {resp.status_code} {resp.reason}")

    try:
        return resp.json()
    except ValueError as exc:
        raise AtlassianError(f"{base_url}: non-JSON response") from exc


def search_pages(
    cql: str,
    *,
    email: str = os.environ.get("ATLASSIAN_EMAIL", ""),
    token: str = os.environ.get("ATLASSIAN_API_TOKEN", ""),
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 10.0,
    limit: int = 25,
) -> list[dict]:
    """Search Confluence pages using CQL.

    Hits Confluence's ``/wiki/rest/api/content/search`` endpoint.

    Args:
        cql: Confluence Query Language expression.
        email: Atlassian account email.
        token: Atlassian API token.
        base_url: Base URL of the Atlassian Cloud instance.
        timeout: Per-request timeout in seconds.
        limit: Max pages to return.

    Returns:
        List of dicts (Confluence content objects).

    Raises:
        AtlassianError: Host unreachable, timed out, non-2xx response, or
            non-JSON response.
    """
    base = base_url.rstrip("/")
    url = base + "/wiki/rest/api/content/search"
    payload = _get_json(
        url,
        params={"cql": cql, "limit": limit},
        headers=_headers(email, token),
        timeout=timeout,
        base_url=base_url,
    )
    if isinstance(payload, dict):
        return list(payload.get("results") or [])
    return []


def get_page(
    page_id: int | str,
    *,
    email: str = os.environ.get("ATLASSIAN_EMAIL", ""),
    token: str = os.environ.get("ATLASSIAN_API_TOKEN", ""),
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 10.0,
    expand: str = "body.storage,version",
) -> dict:
    """Fetch a single Confluence page by ID.

    Uses ``/wiki/rest/api/content/{page_id}``.

    Returns:
        Dict containing the Confluence content object.

    Raises:
        AtlassianError: Host unreachable, timed out, non-2xx response, or
            non-JSON response.
    """
    base = base_url.rstrip("/")
    url = base + f"/wiki/rest/api/content/{page_id}"
    payload = _get_json(
        url,
        params={"expand": expand},
        headers=_headers(email, token),
        timeout=timeout,
        base_url=base_url,
    )
    return dict(payload)


def list_issues(
    jql: str,
    *,
    email: str = os.environ.get("ATLASSIAN_EMAIL", ""),
    token: str = os.environ.get("ATLASSIAN_API_TOKEN", ""),
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 10.0,
    max_results: int = 50,
) -> list[dict]:
    """List Jira issues matching a JQL query.

    Hits Jira's ``/rest/api/3/search`` endpoint.

    Returns:
        List of dicts (Jira issue objects).

    Raises:
        AtlassianError: Host unreachable, timed out, non-2xx response, or
            non-JSON response.
    """
    base = base_url.rstrip("/")
    url = base + "/rest/api/3/search"
    payload = _get_json(
        url,
        params={"jql": jql, "maxResults": max_results},
        headers=_headers(email, token),
        timeout=timeout,
        base_url=base_url,
    )
    if isinstance(payload, dict):
        return list(payload.get("issues") or [])
    return []


def add_comment(
    issue_key: str,
    body: str,
    *,
    email: str = os.environ.get("ATLASSIAN_EMAIL", ""),
    token: str = os.environ.get("ATLASSIAN_API_TOKEN", ""),
    base_url: str = DEFAULT_BASE_URL,
    timeout: float = 10.0,
) -> dict:
    """Add a plain-text Jira comment using Atlassian Document Format.

    Uses ``/rest/api/3/issue/{issue_key}/comment``.

    Returns:
        Dict containing the created Jira comment.

    Raises:
        AtlassianError: Host unreachable, timed out, non-2xx response, or
            non-JSON response.
    """
    base = base_url.rstrip("/")
    url = base + f"/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": body}],
                }
            ],
        }
    }
    response = _post_json(
        url,
        json=payload,
        headers=_headers(email, token, json_body=True),
        timeout=timeout,
        base_url=base_url,
    )
    return dict(response)
