from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_readme_points_to_public_demo_and_live_gate():
    text = _read("README.md")

    assert "Quickstart" in text
    assert "code_qa.cli --help" in text
    assert "demo-loop" in text
    assert "connector-matrix" in text
    assert "knowledge-scenario" in text
    assert "PHANTOM_ENTERPRISE_LIVE=1" in text
    assert "docs/PUBLIC_DEMO.md" in text
    assert "docs/KNOWLEDGE_LOOKUP_SCENARIO.md" in text


def test_pyproject_exposes_demo_loop_connector_matrix_and_scenario_entrypoints():
    text = _read("pyproject.toml")

    assert "phantom-enterprise-demo-loop" in text
    assert "code_qa.demo_loop:main" in text
    assert "phantom-enterprise-connector-matrix" in text
    assert "code_qa.connector_matrix:main" in text
    assert "phantom-enterprise-knowledge-scenario" in text
    assert "code_qa.knowledge_lookup_scenario:main" in text


def test_public_demo_documents_local_checkout_and_mock_only_policy():
    text = _read("docs/PUBLIC_DEMO.md")

    assert "local checkout" in text
    assert "respects `.gitignore`" in text
    assert "PHANTOM_ENTERPRISE_LIVE=1" in text
    assert "status is an environment probe" in text
    assert "Do not commit internal URLs" in text


def test_public_demo_documents_p2_artifact_contract():
    text = _read("docs/PUBLIC_DEMO.md")

    assert "deterministic synthetic local-code Q&A bundle" in text
    assert "answer.json" in text
    assert "evidence.json" in text
    assert "audit-log.jsonl" in text
    assert "live_connectors" in text


def test_public_demo_documents_connector_matrix_and_permission_boundary_contract():
    text = _read("docs/PUBLIC_DEMO.md")

    assert "mock connector matrix" in text
    assert "connector-matrix.json" in text
    assert "permission-boundary.json" in text
    assert "metadata-only" in text
    assert "deny live connectors" in text


def test_public_demo_documents_knowledge_lookup_scenario_contract():
    text = _read("docs/PUBLIC_DEMO.md")

    assert "knowledge-scenario" in text
    assert "knowledge-lookup.json" in text
    assert "citation-map.json" in text
    assert "permission-review.json" in text
    assert "audit-summary.json" in text
    assert "live_connectors=false" in text
    assert "credentials_required=false" in text
    assert "permission_boundary=mock_metadata_only" in text


def test_knowledge_lookup_scenario_doc_documents_safety_boundary():
    text = _read("docs/KNOWLEDGE_LOOKUP_SCENARIO.md")

    assert "synthetic_enterprise_knowledge_lookup_scenario" in text
    assert "knowledge-lookup.json" in text
    assert "citation-map.json" in text
    assert "permission-review.json" in text
    assert "audit-summary.json" in text
    assert "live_connectors" in text
    assert "external_network" in text
    assert "credentials_required" in text
    assert "local_llm_required" in text
    assert "mock_metadata_only" in text
    assert "Production connectors" in text
