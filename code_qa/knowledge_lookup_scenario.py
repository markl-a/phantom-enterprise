"""Deterministic enterprise knowledge lookup scenario bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .connector_matrix import write_connector_matrix_bundle
from .demo_loop import QUESTION, write_synthetic_code_qa_demo


SCHEMA_VERSION = 1

PUBLIC_ARTIFACTS = {
    "audit_summary": "audit-summary.json",
    "citation_map": "citation-map.json",
    "lookup": "knowledge-lookup.json",
    "permission_review": "permission-review.json",
    "summary": "summary.md",
}


@dataclass(frozen=True)
class KnowledgeLookupScenarioBundle:
    out_dir: Path
    artifacts: dict[str, str]


def write_knowledge_lookup_scenario(out_dir: str | Path) -> KnowledgeLookupScenarioBundle:
    """Write a synthetic permission-aware enterprise knowledge lookup bundle."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    code_bundle = write_synthetic_code_qa_demo(out_path / "source-code-qa")
    connector_bundle = write_connector_matrix_bundle(out_path / "connector-matrix")
    code_answer = _load_json(code_bundle.out_dir / "answer.json")
    connector_matrix = _load_json(connector_bundle.out_dir / "connector-matrix.json")
    permission_boundary = _load_json(connector_bundle.out_dir / "permission-boundary.json")

    citations = _citation_map(code_answer)
    permission_review = _permission_review(connector_matrix, permission_boundary)
    lookup = _lookup_scenario(citations, permission_review)
    audit_summary = _audit_summary(lookup, permission_review)

    _dump_json(out_path / "knowledge-lookup.json", lookup)
    _dump_json(out_path / "citation-map.json", citations)
    _dump_json(out_path / "permission-review.json", permission_review)
    _dump_json(out_path / "audit-summary.json", audit_summary)
    (out_path / "summary.md").write_text(_summary_md(lookup, audit_summary), encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_enterprise_knowledge_lookup_scenario",
        "synthetic_only": True,
        "live_connectors": False,
        "external_network": False,
        "credentials_required": False,
        "local_llm_required": False,
        "permission_boundary": "mock_metadata_only",
        "source_bundles": {
            "connector_matrix": "connector-matrix/manifest.json",
            "local_code_qa": "source-code-qa/manifest.json",
        },
        "artifacts": PUBLIC_ARTIFACTS,
    }
    _dump_json(out_path / "manifest.json", manifest)
    return KnowledgeLookupScenarioBundle(out_dir=out_path, artifacts=dict(PUBLIC_ARTIFACTS))


def _citation_map(code_answer: dict[str, Any]) -> dict[str, Any]:
    code_citation = (code_answer.get("citations") or [{}])[0]
    citations = [
        {
            "connector_id": "mock_code",
            "source_type": "code",
            "reference": "source-code-qa/answer.json#citations[0]",
            "path": code_citation.get("path", "src/auth.py"),
            "line_start": int(code_citation.get("line_start") or 1),
            "line_end": int(code_citation.get("line_end") or 1),
            "snippet": code_citation.get("snippet", "def authenticate(token):"),
        },
        {
            "connector_id": "mock_docs",
            "source_type": "document",
            "reference": "mock-docs/access-control.md#authentication",
            "path": "access-control.md",
            "section": "authentication",
            "snippet": "Synthetic access policy requires a bearer token for service calls.",
        },
        {
            "connector_id": "mock_issues",
            "source_type": "issue",
            "reference": "mock-issues/ENT-101#summary",
            "issue_id": "ENT-101",
            "field": "summary",
            "snippet": "Synthetic issue notes that missing tokens should fail before dispatch.",
        },
        {
            "connector_id": "mock_runbooks",
            "source_type": "runbook",
            "reference": "mock-runbooks/auth-service#step-1",
            "runbook_id": "auth-service",
            "step_id": "step-1",
            "snippet": "Synthetic runbook says to verify local token presence before retry.",
        },
    ]
    for citation in citations:
        citation["sha256"] = _sha256(str(citation["snippet"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_citation_map",
        "citation_policy": "synthetic_snippets_only",
        "citations": citations,
    }


def _permission_review(
    connector_matrix: dict[str, Any],
    permission_boundary: dict[str, Any],
) -> dict[str, Any]:
    connectors = connector_matrix.get("connectors") or []
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_permission_review",
        "default_policy": permission_boundary.get("default_policy", "deny_live_connectors"),
        "live_connector_gate": permission_boundary.get(
            "live_connector_gate",
            "PHANTOM_ENTERPRISE_LIVE=1",
        ),
        "allowed_public_modes": permission_boundary.get("allowed_public_modes", []),
        "denied_public_modes": permission_boundary.get("denied_public_modes", []),
        "raw_payload_retained": False,
        "source_decisions": [
            {
                "connector_id": connector.get("connector_id", ""),
                "decision": "allow_mock_only",
                "live_enabled": False,
                "requires_credentials": False,
                "evidence_mode": "synthetic_metadata_and_snippet",
            }
            for connector in connectors
        ],
    }


def _lookup_scenario(
    citation_map: dict[str, Any],
    permission_review: dict[str, Any],
) -> dict[str, Any]:
    citations = citation_map["citations"]
    source_ids = [citation["connector_id"] for citation in citations]
    allowed = all(
        decision.get("decision") == "allow_mock_only"
        and decision.get("live_enabled") is False
        and decision.get("requires_credentials") is False
        for decision in permission_review["source_decisions"]
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "synthetic_enterprise_knowledge_lookup",
        "question": QUESTION,
        "answer": (
            "Authentication is represented by a bearer-token check in the "
            "synthetic code fixture, supported by matching mock documentation, "
            "issue, and runbook evidence."
        ),
        "sources_consulted": source_ids,
        "citation_count": len(citations),
        "readiness": {
            "citations_complete": len(citations) == 4,
            "permission_boundary_enforced": allowed,
            "metadata_audit_ready": True,
            "live_connectors_disabled": True,
            "credentials_not_required": True,
        },
        "boundaries": {
            "production_connectors": "not_enabled",
            "credentialed_sources": "not_supported",
            "private_corpus_export": "not_included",
            "external_network": "not_required",
        },
    }


def _audit_summary(
    lookup: dict[str, Any],
    permission_review: dict[str, Any],
) -> dict[str, Any]:
    events = [
        "scenario_started",
        "source_bundles_verified",
        "knowledge_lookup_built",
        "artifacts_written",
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "metadata_only_enterprise_lookup_audit",
        "event_count": len(events),
        "events": events,
        "sources_consulted": lookup["sources_consulted"],
        "permission_decisions": len(permission_review["source_decisions"]),
        "raw_payload_retained": False,
        "prompt_text_retained": False,
        "credential_values_retained": False,
        "source_bodies_retained": False,
        "external_network": False,
        "live_connectors": False,
    }


def _summary_md(lookup: dict[str, Any], audit: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Enterprise knowledge lookup scenario",
            "",
            "This bundle combines the synthetic code-QA demo and mock connector matrix.",
            "It proves a permission-aware lookup with synthetic citations only.",
            "",
            f"- Question: {lookup['question']}",
            f"- Sources consulted: {', '.join(lookup['sources_consulted'])}",
            f"- Citations: {lookup['citation_count']}",
            f"- Audit events: {audit['event_count']}",
            "- Boundary: no live connectors, no external network, no committed secrets.",
            "",
        ]
    )


def _load_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RuntimeError(f"{path.name} must contain a JSON object")
    return raw


def _dump_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="code_qa.knowledge_lookup_scenario")
    parser.add_argument("--out", required=True, help="directory to write the scenario bundle")
    args = parser.parse_args(argv)

    try:
        bundle = write_knowledge_lookup_scenario(args.out)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(str(bundle.out_dir / "manifest.json") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
