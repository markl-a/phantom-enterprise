"""Deterministic mock connector matrix bundle for public OSS readiness."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PUBLIC_ARTIFACTS = [
    "manifest.json",
    "connector-matrix.json",
    "permission-boundary.json",
    "audit-log.jsonl",
    "summary.md",
]

PRIVATE_MARKERS = (
    "corp.internal",
    "vpn.example",
    "ldap://",
    "jira.internal",
    "confluence.internal",
    "glpat-",
    "AKIA",
    "SECRET=",
    "BEGIN PRIVATE KEY",
)


@dataclass(frozen=True)
class ConnectorMatrixBundle:
    out_dir: Path
    artifacts: list[str]


def _dump_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _connectors() -> list[dict[str, Any]]:
    return [
        {
            "connector_id": "mock_code",
            "label": "Mock source-code connector",
            "status": "mock",
            "live_enabled": False,
            "requires_credentials": False,
            "allowed_public_modes": ["local_fixture"],
            "denied_public_modes": ["credentialed_gitlab", "credentialed_gitea"],
            "contract": {
                "source_type": "code",
                "query_fields": ["path", "symbol", "text"],
                "evidence_fields": ["path", "line_start", "line_end", "sha256"],
                "secret_fields": ["token", "password", "private_key"],
            },
        },
        {
            "connector_id": "mock_docs",
            "label": "Mock documentation connector",
            "status": "mock",
            "live_enabled": False,
            "requires_credentials": False,
            "allowed_public_modes": ["local_fixture"],
            "denied_public_modes": ["confluence_api", "sharepoint_api"],
            "contract": {
                "source_type": "document",
                "query_fields": ["title", "body", "tags"],
                "evidence_fields": ["doc_id", "section", "sha256"],
                "secret_fields": ["api_token", "cookie", "session"],
            },
        },
        {
            "connector_id": "mock_issues",
            "label": "Mock issue connector",
            "status": "mock",
            "live_enabled": False,
            "requires_credentials": False,
            "allowed_public_modes": ["local_fixture"],
            "denied_public_modes": ["jira_api", "gitlab_issues_api"],
            "contract": {
                "source_type": "issue",
                "query_fields": ["key", "summary", "status"],
                "evidence_fields": ["issue_id", "field", "sha256"],
                "secret_fields": ["api_token", "webhook_secret"],
            },
        },
        {
            "connector_id": "mock_runbooks",
            "label": "Mock runbook connector",
            "status": "mock",
            "live_enabled": False,
            "requires_credentials": False,
            "allowed_public_modes": ["local_fixture"],
            "denied_public_modes": ["vpn_runbook_store", "internal_wiki_api"],
            "contract": {
                "source_type": "runbook",
                "query_fields": ["service", "symptom", "step"],
                "evidence_fields": ["runbook_id", "step_id", "sha256"],
                "secret_fields": ["break_glass_token", "ssh_key"],
            },
        },
    ]


def _permission_boundary(connectors: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "default_policy": "deny_live_connectors",
        "allowed_public_modes": ["mock", "local_fixture"],
        "denied_public_modes": ["live_service", "vpn_service", "credentialed_api"],
        "live_connector_gate": "PHANTOM_ENTERPRISE_LIVE=1",
        "credential_policy": "never in public fixtures or committed config",
        "audit_retention": "metadata_only",
        "connector_decisions": [
            {
                "connector_id": connector["connector_id"],
                "decision": "allow_mock_only",
                "live_enabled": False,
                "requires_credentials": False,
            }
            for connector in connectors
        ],
    }


def _audit_events(connectors: list[dict[str, Any]], artifacts: list[str]) -> list[dict[str, Any]]:
    connector_ids = [connector["connector_id"] for connector in connectors]
    return [
        {
            "schema_version": 1,
            "event": "connector_matrix_started",
            "mode": "synthetic_connector_matrix",
            "raw_payload_retained": False,
        },
        {
            "schema_version": 1,
            "event": "connector_contracts_loaded",
            "connector_ids": connector_ids,
            "connector_count": len(connector_ids),
            "raw_payload_retained": False,
        },
        {
            "schema_version": 1,
            "event": "permission_boundary_evaluated",
            "default_policy": "deny_live_connectors",
            "blocked_live_connector_count": len(connector_ids),
            "raw_payload_retained": False,
        },
        {
            "schema_version": 1,
            "event": "artifact_written",
            "artifacts": artifacts,
            "raw_payload_retained": False,
        },
    ]


def _write_audit_log(path: Path, events: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def _summary_md(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Synthetic Connector Matrix",
            "",
            "This bundle documents mock enterprise connector contracts and the public permission boundary.",
            "It does not contact live enterprise services and does not require credentials.",
            "",
            f"- Connector count: {manifest['connector_count']}",
            "- Default policy: deny live connectors",
            "- Audit log retention: metadata only",
            "",
        ]
    )


def write_connector_matrix_bundle(out_dir: str | Path) -> ConnectorMatrixBundle:
    """Write a deterministic mock connector matrix and permission bundle."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    connectors = _connectors()
    matrix = {
        "schema_version": 1,
        "mode": "synthetic_connector_matrix",
        "description": "Mock connector contracts for public OSS demos.",
        "connectors": connectors,
    }
    boundary = _permission_boundary(connectors)
    manifest = {
        "schema_version": 1,
        "mode": "synthetic_connector_matrix",
        "synthetic_only": True,
        "live_connectors": False,
        "external_network": False,
        "credentials_required": False,
        "permission_boundary": "mock_metadata_only",
        "connector_count": len(connectors),
        "artifacts": PUBLIC_ARTIFACTS,
    }

    _dump_json(out_path / "manifest.json", manifest)
    _dump_json(out_path / "connector-matrix.json", matrix)
    _dump_json(out_path / "permission-boundary.json", boundary)
    _write_audit_log(out_path / "audit-log.jsonl", _audit_events(connectors, PUBLIC_ARTIFACTS))
    (out_path / "summary.md").write_text(_summary_md(manifest), encoding="utf-8")

    return ConnectorMatrixBundle(out_dir=out_path, artifacts=list(PUBLIC_ARTIFACTS))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="code_qa.connector_matrix")
    parser.add_argument("--out", required=True, help="directory to write the bundle")
    args = parser.parse_args(argv)

    try:
        bundle = write_connector_matrix_bundle(args.out)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    sys.stdout.write(
        json.dumps(
            {"out_dir": str(bundle.out_dir), "artifacts": bundle.artifacts},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
