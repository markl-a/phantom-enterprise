import pytest
pytest.importorskip("mcp")

import importlib
import textwrap
from pathlib import Path

from apple_silicon_ha.probes import ProbeResult
from code_qa.mcp_server import enterprise_code_ask, enterprise_status
from ldap_sso.auth import LdapAuth

ask_mod = importlib.import_module("code_qa.ask")


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
    (repo / "blob.bin").write_bytes(b"\x00\x01\x02\x03")
    return repo


def test_enterprise_code_ask_returns_plain_dict(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    stub = "stubbed answer citing src/auth.py"

    def fake_answer(question, context, **kwargs):
        return stub

    monkeypatch.setattr(ask_mod, "answer_with_phantom", fake_answer)

    result = enterprise_code_ask(str(repo), "How does authenticate use a token?")

    assert set(result) == {"answer", "files", "prompt_chars"}
    assert result["answer"] == stub
    assert "src/auth.py" in result["files"]
    assert result["prompt_chars"] > 0


def test_enterprise_status_accepts_injected_checks():
    def fake_router() -> list[object]:
        return [object()]

    def fake_lister() -> list[str]:
        return ["a"]

    result = enterprise_status(
        backend=LdapAuth(),
        ha_checks=[ProbeResult(name="primary", ok=True, detail="ok")],
        router=fake_router,
        lister=fake_lister,
    )

    assert result["healthy"] is True
    assert [check["name"] for check in result["checks"]] == [
        "tailscale",
        "git",
        "auth",
        "ha",
    ]
