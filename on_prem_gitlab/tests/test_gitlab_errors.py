import pytest

from on_prem_gitlab import gitlab
from on_prem_gitlab.gitlab import GitLabUnreachable, get_project_file, list_projects


class Response:
    def __init__(self, *, ok=True, status_code=200, reason="OK", text=""):
        self.ok = ok
        self.status_code = status_code
        self.reason = reason
        self.text = text

    def json(self):
        raise ValueError("invalid json")


def test_list_projects_non_json_response_maps_to_gitlab_unreachable(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        return Response()

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    with pytest.raises(GitLabUnreachable, match="non-JSON"):
        list_projects(base_url="http://gitlab.example")


def test_get_project_file_404_maps_to_gitlab_unreachable(monkeypatch):
    def fake_get(url, *, params, headers, timeout):
        return Response(ok=False, status_code=404, reason="Not Found")

    monkeypatch.setattr(gitlab.requests, "get", fake_get)

    with pytest.raises(GitLabUnreachable, match="HTTP 404"):
        get_project_file("group/name", "README.md", base_url="http://gitlab.example")
