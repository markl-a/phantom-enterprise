"""Hermetic tests for `phantom-enterprise ask` CLI exit codes and stderr hints.

Stubs ``code_qa.ask.ask`` to raise each documented error (or return an
empty-files result) and asserts ``main([...])`` returns the matching exit
code with a helpful stderr message — no network, no real ``ask()`` call.
"""

from __future__ import annotations

import importlib

from code_qa.cli import main
from code_qa.context import RepoContext
from on_prem_gitlab import GiteaUnreachable, GitLabUnreachable

# NB (see test_ask.py): code_qa/__init__ re-exports `ask`, shadowing the
# `code_qa.ask` submodule attribute. Pull the real module from sys.modules.
ask_mod = importlib.import_module("code_qa.ask")


def _run(monkeypatch, capsys, stub):
    monkeypatch.setattr(ask_mod, "ask", stub)
    rc = main(["ask", "--repo", "/tmp/repo", "what does this do?"])
    return rc, capsys.readouterr().err


def test_gitlab_unreachable_exits_2_with_local_checkout_hint(monkeypatch, capsys):
    def boom(*a, **k):
        raise GitLabUnreachable("host down")

    rc, err = _run(monkeypatch, capsys, boom)
    assert rc == 2
    assert "on-prem GitLab unreachable" in err
    assert "host down" in err
    assert "phantom-enterprise ask --repo /path/to/your/repo" in err


def test_gitea_unreachable_exits_2_with_local_checkout_hint(monkeypatch, capsys):
    def boom(*a, **k):
        raise GiteaUnreachable("host down")

    rc, err = _run(monkeypatch, capsys, boom)
    assert rc == 2
    assert "on-prem Gitea unreachable" in err
    assert "host down" in err
    assert "phantom-enterprise ask --repo /path/to/your/repo" in err


def test_not_a_directory_exits_2(monkeypatch, capsys):
    def boom(*a, **k):
        raise NotADirectoryError("/tmp/not-a-repo is not a directory")

    rc, err = _run(monkeypatch, capsys, boom)
    assert rc == 2
    assert "error:" in err
    assert "not a directory" in err


def test_runtime_error_exits_1(monkeypatch, capsys):
    def boom(*a, **k):
        raise RuntimeError("phantom exec failed")

    rc, err = _run(monkeypatch, capsys, boom)
    assert rc == 1
    assert "error: phantom exec failed" in err


def test_no_files_found_exits_3(monkeypatch, capsys):
    def empty(*a, **k):
        return ask_mod.AskResult(
            question="q",
            answer="",
            context=RepoContext(source="local:/tmp/repo"),
            prompt_chars=0,
        )

    rc, err = _run(monkeypatch, capsys, empty)
    assert rc == 3
    assert "no readable/relevant files found" in err
