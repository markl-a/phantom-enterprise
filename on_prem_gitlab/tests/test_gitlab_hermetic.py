import pytest

from on_prem_gitlab import gitlab
from on_prem_gitlab.gitlab import (
    GitLabUnreachable,
    get_project_file,
    list_project_files,
    list_projects,
)


class Response:
    def __init__(
        self,
        payload=None,
        *,
        ok=True,
        status_code=200,
        reason="OK",
        text="",
    ):
        self._payload = payload
        self.ok = ok
        self.status_code = status_code
        self.reason = reason
        self.text = text

    def json(self):
        if isinstance(self._payload, BaseException):
            raise self._payload
        return self._payload


def test_list_projects_builds_url_headers_params(monkeypatch):
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        return Response([{"id": 1, "name": "alpha"}])

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    projects = list_projects(
        token="secret",
        base_url="http://gitlab.example/",
        timeout=2.5,
        per_page=25,
    )

    assert projects == [{"id": 1, "name": "alpha"}]
    assert calls == [
        {
            "url": "http://gitlab.example/api/v4/projects",
            "params": {"membership": "true", "per_page": 25, "simple": "true"},
            "headers": {"Accept": "application/json", "PRIVATE-TOKEN": "secret"},
            "timeout": 2.5,
        }
    ]


def test_list_project_files_url_encodes_namespaced_id_and_ref(monkeypatch):
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        return Response(
            [
                {"type": "blob", "path": "README.md"},
                "not-a-dict",
                {"type": "tree", "path": "src"},
            ]
        )

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    files = list_project_files(
        "group/name",
        ref="main",
        base_url="http://gitlab.example",
        timeout=3,
    )

    assert files == [
        {"type": "blob", "path": "README.md"},
        {"type": "tree", "path": "src"},
    ]
    assert calls == [
        {
            "url": "http://gitlab.example/api/v4/projects/group%2Fname/repository/tree",
            "params": {"recursive": "true", "per_page": 100, "ref": "main"},
            "headers": {"Accept": "application/json"},
            "timeout": 3,
        }
    ]


def test_get_project_file_url_encodes_nested_filepath_and_returns_text(monkeypatch):
    calls = []

    def fake_get(url, *, params, headers, timeout):
        calls.append(
            {"url": url, "params": params, "headers": headers, "timeout": timeout}
        )
        return Response(text="hello\n")

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    content = get_project_file(
        "group/name",
        "/src/app/config.yml",
        ref="main",
        token="secret",
        base_url="http://gitlab.example/",
        timeout=4,
    )

    assert content == "hello\n"
    assert calls == [
        {
            "url": "http://gitlab.example/api/v4/projects/group%2Fname/repository/files/src%2Fapp%2Fconfig.yml/raw",
            "params": {"ref": "main"},
            "headers": {"Accept": "application/json", "PRIVATE-TOKEN": "secret"},
            "timeout": 4,
        }
    ]


def test_request_exception_maps_to_gitlab_unreachable(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        raise gitlab.requests.RequestException("connection failed")

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    with pytest.raises(GitLabUnreachable, match="connection failed"):
        list_projects(base_url="http://gitlab.example")


def test_http_404_maps_to_gitlab_unreachable(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        return Response(ok=False, status_code=404, reason="Not Found")

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    with pytest.raises(GitLabUnreachable, match="HTTP 404 Not Found"):
        list_project_files("group/name", base_url="http://gitlab.example")
