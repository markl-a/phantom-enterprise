from __future__ import annotations

import json
from pathlib import Path

from code_qa.cli import build_parser
from code_qa.demo_loop import PUBLIC_ARTIFACTS, write_synthetic_code_qa_demo


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_demo_loop_writes_local_code_qa_bundle(tmp_path: Path):
    bundle = write_synthetic_code_qa_demo(tmp_path / "bundle")

    assert bundle.out_dir == tmp_path / "bundle"
    for name in ["synthetic-repo/src/auth.py", *PUBLIC_ARTIFACTS]:
        assert (bundle.out_dir / name).exists(), name

    manifest = _read_json(bundle.out_dir / "manifest.json")
    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_local_code_qa"
    assert manifest["synthetic_only"] is True
    assert manifest["live_connectors"] is False
    assert manifest["external_network"] is False
    assert manifest["local_llm_required"] is False
    assert manifest["artifacts"] == ["synthetic-repo/src/auth.py", *PUBLIC_ARTIFACTS]

    answer = _read_json(bundle.out_dir / "answer.json")
    assert answer["question"] == "How does authentication work?"
    assert answer["answer"]
    assert answer["citations"] == [
        {
            "path": "src/auth.py",
            "line_start": 1,
            "line_end": 4,
            "snippet": "def authenticate(token):",
        }
    ]

    evidence = _read_json(bundle.out_dir / "evidence.json")
    assert evidence["source"].startswith("local working tree:")
    assert evidence["files"][0]["path"] == "src/auth.py"
    assert evidence["files"][0]["sha256"]
    assert evidence["files"][0]["snippet_line_start"] == 1


def test_demo_loop_audit_log_does_not_store_source_body(tmp_path: Path):
    bundle = write_synthetic_code_qa_demo(tmp_path / "bundle")

    audit_text = (bundle.out_dir / "audit-log.jsonl").read_text(encoding="utf-8")
    assert "def authenticate" not in audit_text
    assert "Authorization" not in audit_text
    assert "synthetic-repo/src/auth.py" in audit_text

    events = [json.loads(line) for line in audit_text.splitlines()]
    assert [event["event"] for event in events] == [
        "demo_started",
        "context_built",
        "answer_generated",
        "artifact_written",
    ]
    assert all(event["schema_version"] == 1 for event in events)


def test_demo_loop_is_deterministic_for_public_artifacts(tmp_path: Path):
    first = write_synthetic_code_qa_demo(tmp_path / "first")
    second = write_synthetic_code_qa_demo(tmp_path / "second")

    for name in PUBLIC_ARTIFACTS:
        assert (first.out_dir / name).read_text(encoding="utf-8") == (
            second.out_dir / name
        ).read_text(encoding="utf-8"), name


def test_cli_exposes_demo_loop_subcommand():
    parser = build_parser()

    ns = parser.parse_args(["demo-loop", "--out", "bundle"])

    assert ns.command == "demo-loop"
    assert ns.out == "bundle"


def test_cli_exposes_connector_matrix_subcommand():
    parser = build_parser()

    ns = parser.parse_args(["connector-matrix", "--out", "bundle"])

    assert ns.command == "connector-matrix"
    assert ns.out == "bundle"
