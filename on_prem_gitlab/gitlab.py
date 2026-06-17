"""Self-hosted GitLab connector using the GitLab v4 REST API.

Public API:

    list_projects(token=None, base_url=GITLAB_DEFAULT_BASE_URL, timeout=5.0, per_page=50) -> list[dict]
    list_project_files(project_id, *, ref=None, token=None, base_url=GITLAB_DEFAULT_BASE_URL, timeout=5.0) -> list[dict]
    get_project_file(project_id, filepath, *, ref=None, token=None, base_url=GITLAB_DEFAULT_BASE_URL, timeout=5.0) -> str
"""

from __future__ import annotations

import os
from urllib.parse import quote

import requests

GITLAB_DEFAULT_BASE_URL = os.environ.get("GITLAB_BASE_URL", "http://gitlab.internal")
"""On-prem GitLab base URL. Set ``GITLAB_BASE_URL`` to your self-hosted instance."""


class GitLabUnreachable(RuntimeError):
    """Raised when the on-prem GitLab host is not reachable."""


def _headers(token: str | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["PRIVATE-TOKEN"] = token
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
        raise GitLabUnreachable(f"{base_url}: {exc}") from exc

    if not resp.ok:
        raise GitLabUnreachable(
            f"{base_url}: HTTP {resp.status_code} {resp.reason}"
        )

    try:
        return resp.json()
    except ValueError as exc:
        raise GitLabUnreachable(f"{base_url}: non-JSON response") from exc


def list_projects(
    token: str | None = None,
    base_url: str = GITLAB_DEFAULT_BASE_URL,
    timeout: float = 5.0,
    per_page: int = 50,
) -> list[dict]:
    """List GitLab projects visible to the given token (or anon if None).

    Hits GitLab's ``/api/v4/projects`` endpoint with membership scoping.

    Args:
        token: Optional GitLab personal access token. If None, only public
            projects are returned.
        base_url: Base URL of the on-prem instance.
        timeout: Per-request timeout in seconds.
        per_page: Max projects to return per GitLab page.

    Returns:
        List of dicts (GitLab project objects).

    Raises:
        GitLabUnreachable: Host unreachable, timed out, non-2xx response, or
            non-JSON response.
    """
    base = base_url.rstrip("/")
    url = base + "/api/v4/projects"
    payload = _get_json(
        url,
        params={"membership": "true", "per_page": per_page, "simple": "true"},
        headers=_headers(token),
        timeout=timeout,
        base_url=base_url,
    )
    return list(payload)


def list_project_files(
    project_id: int | str,
    *,
    ref: str | None = None,
    token: str | None = None,
    base_url: str = GITLAB_DEFAULT_BASE_URL,
    timeout: float = 5.0,
) -> list[dict]:
    """List the files in a GitLab project's repository tree recursively.

    Uses ``/api/v4/projects/{project_id}/repository/tree``. ``project_id`` may
    be a numeric ID or a namespaced path such as ``group/name``.

    Returns:
        List of tree entries. GitLab uses ``type`` values like ``blob`` and
        ``tree`` and a ``path`` key.

    Raises:
        GitLabUnreachable: Host unreachable, timed out, non-2xx response, or
            non-JSON response.
    """
    base = base_url.rstrip("/")
    enc_id = quote(str(project_id), safe="")
    url = base + f"/api/v4/projects/{enc_id}/repository/tree"
    params: dict[str, object] = {"recursive": "true", "per_page": 100}
    if ref:
        params["ref"] = ref
    payload = _get_json(
        url,
        params=params,
        headers=_headers(token),
        timeout=timeout,
        base_url=base_url,
    )
    return [e for e in payload if isinstance(e, dict)]


def get_project_file(
    project_id: int | str,
    filepath: str,
    *,
    ref: str | None = None,
    token: str | None = None,
    base_url: str = GITLAB_DEFAULT_BASE_URL,
    timeout: float = 5.0,
) -> str:
    """Fetch the raw text content of a single GitLab project file.

    Uses ``/api/v4/projects/{project_id}/repository/files/{filepath}/raw``.

    Raises:
        GitLabUnreachable: Host unreachable, timed out, or non-2xx response.
    """
    base = base_url.rstrip("/")
    enc_id = quote(str(project_id), safe="")
    enc_filepath = quote(filepath.lstrip("/"), safe="")
    url = base + f"/api/v4/projects/{enc_id}/repository/files/{enc_filepath}/raw"
    try:
        resp = requests.get(
            url,
            params={"ref": ref or "HEAD"},
            headers=_headers(token),
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise GitLabUnreachable(f"{base_url}: {exc}") from exc

    if not resp.ok:
        raise GitLabUnreachable(
            f"{base_url}: HTTP {resp.status_code} {resp.reason}"
        )

    return resp.text
