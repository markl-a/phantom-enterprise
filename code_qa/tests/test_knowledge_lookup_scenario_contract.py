from __future__ import annotations

import json
from pathlib import Path

from code_qa.connector_matrix import PRIVATE_MARKERS
from code_qa import knowledge_lookup_scenario
from code_qa.cli import build_parser


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_knowledge_lookup_scenario_writes_permission_aware_bundle(
    tmp_path: Path,
    capsys,
):
    out = tmp_path / "scenario"

    assert knowledge_lookup_scenario.main(["--out", str(out)]) == 0
    manifest_path = Path(capsys.readouterr().out.strip())
    assert manifest_path == out / "manifest.json"

    manifest = _read_json(manifest_path)
    lookup = _read_json(out / "knowledge-lookup.json")
    citations = _read_json(out / "citation-map.json")
    permission = _read_json(out / "permission-review.json")
    audit = _read_json(out / "audit-summary.json")
    summary = (out / "summary.md").read_text(encoding="utf-8")

    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_enterprise_knowledge_lookup_scenario"
    assert manifest["synthetic_only"] is True
    assert manifest["live_connectors"] is False
    assert manifest["external_network"] is False
    assert manifest["credentials_required"] is False
    assert manifest["local_llm_required"] is False
    assert manifest["permission_boundary"] == "mock_metadata_only"
    assert manifest["source_bundles"] == {
        "connector_matrix": "connector-matrix/manifest.json",
        "local_code_qa": "source-code-qa/manifest.json",
    }
    assert manifest["artifacts"] == {
        "audit_summary": "audit-summary.json",
        "citation_map": "citation-map.json",
        "lookup": "knowledge-lookup.json",
        "permission_review": "permission-review.json",
        "summary": "summary.md",
    }

    assert (out / "source-code-qa" / "manifest.json").exists()
    assert (out / "connector-matrix" / "manifest.json").exists()

    assert lookup["mode"] == "synthetic_enterprise_knowledge_lookup"
    assert lookup["question"] == "How does authentication work?"
    assert lookup["sources_consulted"] == [
        "mock_code",
        "mock_docs",
        "mock_issues",
        "mock_runbooks",
    ]
    assert lookup["citation_count"] == 4
    assert lookup["readiness"] == {
        "citations_complete": True,
        "permission_boundary_enforced": True,
        "metadata_audit_ready": True,
        "live_connectors_disabled": True,
        "credentials_not_required": True,
    }
    assert lookup["boundaries"]["production_connectors"] == "not_enabled"
    assert lookup["boundaries"]["credentialed_sources"] == "not_supported"
    assert lookup["boundaries"]["private_corpus_export"] == "not_included"

    assert citations["mode"] == "synthetic_citation_map"
    assert [item["connector_id"] for item in citations["citations"]] == [
        "mock_code",
        "mock_docs",
        "mock_issues",
        "mock_runbooks",
    ]
    assert all(item["sha256"] for item in citations["citations"])
    assert all("secret" not in item for item in citations["citations"])

    assert permission["mode"] == "synthetic_permission_review"
    assert permission["default_policy"] == "deny_live_connectors"
    assert permission["raw_payload_retained"] is False
    assert permission["live_connector_gate"] == "PHANTOM_ENTERPRISE_LIVE=1"
    assert all(
        decision["decision"] == "allow_mock_only"
        for decision in permission["source_decisions"]
    )

    assert audit["mode"] == "metadata_only_enterprise_lookup_audit"
    assert audit["raw_payload_retained"] is False
    assert audit["prompt_text_retained"] is False
    assert audit["credential_values_retained"] is False
    assert audit["event_count"] == 4
    assert "Enterprise knowledge lookup scenario" in summary


def test_knowledge_lookup_scenario_is_deterministic_and_public_safe(
    tmp_path: Path,
    capsys,
):
    first = tmp_path / "first"
    second = tmp_path / "second"

    assert knowledge_lookup_scenario.main(["--out", str(first)]) == 0
    capsys.readouterr()
    assert knowledge_lookup_scenario.main(["--out", str(second)]) == 0
    capsys.readouterr()

    files = (
        "manifest.json",
        "knowledge-lookup.json",
        "citation-map.json",
        "permission-review.json",
        "audit-summary.json",
        "summary.md",
        "source-code-qa/answer.json",
        "connector-matrix/permission-boundary.json",
    )
    for rel in files:
        assert (first / rel).read_text(encoding="utf-8") == (second / rel).read_text(
            encoding="utf-8"
        )

    exported_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in first.rglob("*")
        if path.is_file()
    )
    forbidden = (
        *PRIVATE_MARKERS,
        "internal url",
        "customer data",
        "private key",
        "credential value",
    )
    assert all(term.lower() not in exported_text.lower() for term in forbidden)


def test_cli_exposes_knowledge_lookup_scenario_subcommand():
    parser = build_parser()

    ns = parser.parse_args(["knowledge-scenario", "--out", "bundle"])

    assert ns.command == "knowledge-scenario"
    assert ns.out == "bundle"
