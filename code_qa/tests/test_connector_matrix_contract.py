from __future__ import annotations

import json
from pathlib import Path

from code_qa.connector_matrix import (
    PRIVATE_MARKERS,
    PUBLIC_ARTIFACTS,
    write_connector_matrix_bundle,
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_connector_matrix_bundle_documents_mock_connectors_and_permission_boundary(
    tmp_path: Path,
):
    bundle = write_connector_matrix_bundle(tmp_path / "bundle")

    assert bundle.out_dir == tmp_path / "bundle"
    for name in PUBLIC_ARTIFACTS:
        assert (bundle.out_dir / name).exists(), name

    manifest = _read_json(bundle.out_dir / "manifest.json")
    assert manifest["schema_version"] == 1
    assert manifest["mode"] == "synthetic_connector_matrix"
    assert manifest["synthetic_only"] is True
    assert manifest["live_connectors"] is False
    assert manifest["external_network"] is False
    assert manifest["credentials_required"] is False
    assert manifest["permission_boundary"] == "mock_metadata_only"
    assert manifest["artifacts"] == PUBLIC_ARTIFACTS

    matrix = _read_json(bundle.out_dir / "connector-matrix.json")
    assert [item["connector_id"] for item in matrix["connectors"]] == [
        "mock_code",
        "mock_docs",
        "mock_issues",
        "mock_runbooks",
    ]
    assert all(item["status"] == "mock" for item in matrix["connectors"])
    assert all(item["live_enabled"] is False for item in matrix["connectors"])
    assert all(item["requires_credentials"] is False for item in matrix["connectors"])
    assert all("contract" in item for item in matrix["connectors"])

    boundary = _read_json(bundle.out_dir / "permission-boundary.json")
    assert boundary["default_policy"] == "deny_live_connectors"
    assert boundary["allowed_public_modes"] == ["mock", "local_fixture"]
    assert boundary["denied_public_modes"] == ["live_service", "vpn_service", "credentialed_api"]
    assert boundary["audit_retention"] == "metadata_only"


def test_connector_matrix_audit_log_is_metadata_only(tmp_path: Path):
    bundle = write_connector_matrix_bundle(tmp_path / "bundle")

    events = [
        json.loads(line)
        for line in (bundle.out_dir / "audit-log.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert [event["event"] for event in events] == [
        "connector_matrix_started",
        "connector_contracts_loaded",
        "permission_boundary_evaluated",
        "artifact_written",
    ]
    assert all(event["schema_version"] == 1 for event in events)
    assert all(event["raw_payload_retained"] is False for event in events)
    assert all("token" not in event for event in events)
    assert all("secret" not in event for event in events)
    assert events[2]["blocked_live_connector_count"] == 4


def test_connector_matrix_public_artifacts_do_not_contain_private_markers(
    tmp_path: Path,
):
    bundle = write_connector_matrix_bundle(tmp_path / "bundle")

    for name in PUBLIC_ARTIFACTS:
        text = (bundle.out_dir / name).read_text(encoding="utf-8")
        for marker in PRIVATE_MARKERS:
            assert marker not in text, f"{marker!r} leaked in {name}"


def test_connector_matrix_bundle_is_deterministic(tmp_path: Path):
    first = write_connector_matrix_bundle(tmp_path / "first")
    second = write_connector_matrix_bundle(tmp_path / "second")

    for name in PUBLIC_ARTIFACTS:
        assert (first.out_dir / name).read_text(encoding="utf-8") == (
            second.out_dir / name
        ).read_text(encoding="utf-8"), name
