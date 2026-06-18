"""Offline tests for the private-code Q&A feature.

These do NOT call the real ``phantom`` binary or a live Gitea — the LLM call
is stubbed so the tests are deterministic and CI-safe.
"""

import textwrap
from pathlib import Path
from urllib.parse import unquote

import pytest

import importlib
from on_prem_gitlab import gitlab as gitlab_mod

# NB: code_qa/__init__ re-exports the ``ask`` function, which shadows the
# ``code_qa.ask`` submodule attribute. Pull the real module from sys.modules.
ask_mod = importlib.import_module("code_qa.ask")
from code_qa.context import build_local_context
from code_qa.cli import build_parser


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "myrepo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "auth.py").write_text(
        textwrap.dedent(
            """
            def authenticate(token):
                '''Authenticate using a bearer token.'''
                return {"Authorization": f"token {token}"}
            """
        )
    )
    (repo / "src" / "unrelated.py").write_text("def add(a, b):\n    return a + b\n")
    (repo / ".gitignore").write_text("secrets.txt\n*.log\n")
    (repo / "secrets.txt").write_text("SUPER_SECRET")
    (repo / "debug.log").write_text("noise")
    # binary-ish file should be skipped
    (repo / "blob.bin").write_bytes(b"\x00\x01\x02\x03")
    return repo


def test_local_context_ranks_relevant_file_first(tmp_path):
    repo = _make_repo(tmp_path)
    ctx = build_local_context(str(repo), "How does authenticate use a token?")
    paths = [f.path for f in ctx.files]
    assert "src/auth.py" in paths
    # the auth file should outrank the unrelated arithmetic file
    assert paths.index("src/auth.py") < paths.index("src/unrelated.py")


def test_local_context_respects_gitignore_and_skips_binary(tmp_path):
    repo = _make_repo(tmp_path)
    ctx = build_local_context(str(repo), "token authenticate")
    paths = [f.path for f in ctx.files]
    assert "secrets.txt" not in paths  # gitignored
    assert "debug.log" not in paths    # gitignored glob
    assert "blob.bin" not in paths     # binary


def test_context_blob_contains_file_contents(tmp_path):
    repo = _make_repo(tmp_path)
    ctx = build_local_context(str(repo), "authenticate token")
    blob = ctx.as_prompt_blob()
    assert "=== FILE: src/auth.py ===" in blob
    assert "Authorization" in blob


def test_ask_local_calls_phantom_with_grounding_prompt(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    captured = {}

    def fake_answer(question, context, **kwargs):
        captured["question"] = question
        captured["blob"] = context.as_prompt_blob()
        return "stubbed answer citing src/auth.py"

    monkeypatch.setattr(ask_mod, "answer_with_phantom", fake_answer)
    result = ask_mod.ask(str(repo), "How does authenticate use a token?")
    assert result.answer == "stubbed answer citing src/auth.py"
    assert "src/auth.py" in captured["blob"]
    assert result.context.files


def test_answer_with_phantom_invokes_subprocess(monkeypatch, tmp_path):
    from code_qa.context import RepoContext, SelectedFile

    ctx = RepoContext(source="test", files=[SelectedFile("a.py", "x=1", 1.0)])
    calls = {}

    class FakeProc:
        returncode = 0
        stdout = "  the answer  "
        stderr = ""

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["input"] = kwargs.get("input")
        return FakeProc()

    monkeypatch.setattr(ask_mod.subprocess, "run", fake_run)
    out = ask_mod.answer_with_phantom("q?", ctx, phantom_bin="phantom")
    assert out == "the answer"
    assert calls["cmd"][:2] == ["phantom", "exec"]
    assert "q?" in calls["input"]
    assert "a.py" in calls["input"]


def test_gitea_unreachable_propagates(monkeypatch):
    from on_prem_gitlab import GiteaUnreachable

    def boom(*a, **k):
        raise GiteaUnreachable("host down")

    monkeypatch.setattr("on_prem_gitlab.list_repo_files", boom)
    with pytest.raises(GiteaUnreachable):
        ask_mod.ask("owner/repo", "q", is_gitea=True)


def test_cli_parser_ask_args():
    parser = build_parser()
    ns = parser.parse_args(["ask", "--repo", "/tmp/x", "what is this?"])
    assert ns.command == "ask"
    assert ns.repo == "/tmp/x"
    assert ns.question == "what is this?"

class GitLabResponse:
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
        return self._payload


_GITLAB_TREE = [
    {"type": "blob", "path": "src/auth.py"},
    {"type": "blob", "path": "README.md"},
]

_GITLAB_FILES = {
    "src/auth.py": textwrap.dedent(
        """
        def authenticate(token):
            return {"Authorization": f"Bearer {token}"}
        """
    ),
    "README.md": "# Canned project\n\nAuthentication details live in src/auth.py.\n",
}


def _fake_gitlab_get(url, *, params, headers, timeout):
    if "repository/tree" in url:
        return GitLabResponse(_GITLAB_TREE)
    if "repository/files" in url and "/raw" in url:
        encoded_path = url.split("/repository/files/", 1)[1].rsplit("/raw", 1)[0]
        return GitLabResponse(text=_GITLAB_FILES[unquote(encoded_path)])
    raise AssertionError(f"unexpected GitLab URL: {url}")


def test_ask_gitlab_pulls_files_through_connector(monkeypatch):
    captured = {}

    def fake_answer(question, context, **kwargs):
        captured["blob"] = context.as_prompt_blob()
        return "stubbed answer citing src/auth.py"

    monkeypatch.setattr(ask_mod, "answer_with_phantom", fake_answer)
    monkeypatch.setattr(gitlab_mod.requests, "get", _fake_gitlab_get)

    result = ask_mod.ask(
        "group/proj",
        "How does authenticate work?",
        is_gitlab=True,
        token="secret",
        base_url="http://gitlab.example",
    )

    paths = [f.path for f in result.context.files]
    assert result.context.source.startswith("on-prem GitLab")
    assert result.context.files
    assert "src/auth.py" in paths
    assert "Authorization" in captured["blob"]


def test_cli_ask_gitlab_pulls_files_through_connector(monkeypatch, capsys):
    from code_qa.cli import main

    def fake_answer(question, context, **kwargs):
        return "stubbed answer citing src/auth.py"

    monkeypatch.setattr(ask_mod, "answer_with_phantom", fake_answer)
    monkeypatch.setattr(gitlab_mod.requests, "get", _fake_gitlab_get)

    result = main(
        [
            "ask",
            "--repo",
            "group/proj",
            "--gitlab",
            "--base-url",
            "http://gitlab.example",
            "--token",
            "secret",
            "How does authenticate work?",
        ]
    )

    stdout = capsys.readouterr().out
    assert result == 0
    assert "on-prem GitLab" in stdout
    assert "src/auth.py" in stdout
