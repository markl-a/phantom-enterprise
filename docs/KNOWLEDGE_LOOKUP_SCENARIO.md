# Synthetic Enterprise Knowledge Lookup Scenario

`phantom-enterprise` P3 adds a deterministic permission-aware knowledge lookup
scenario. It combines the P2 synthetic local-code Q&A bundle with the P2 mock
connector matrix, then writes a scenario bundle with citations, permission
review, and metadata-only audit evidence.

Run it locally:

```powershell
python -m code_qa.cli knowledge-scenario --out <bundle-dir>
```

Or, after installation:

```powershell
phantom-enterprise knowledge-scenario --out <bundle-dir>
phantom-enterprise-knowledge-scenario --out <bundle-dir>
```

## Artifact Contract

The bundle writes these top-level files:

- `manifest.json`: schema version, mode, safety flags, source bundle references,
  and artifact map.
- `knowledge-lookup.json`: question, answer, consulted mock sources,
  readiness flags, and explicit unsupported boundaries.
- `citation-map.json`: synthetic citation records for mock code, docs, issues,
  and runbooks.
- `permission-review.json`: mock-only connector decisions under the public
  permission boundary.
- `audit-summary.json`: metadata-only event summary.
- `summary.md`: short human-readable summary.

It also writes these source bundles:

- `source-code-qa/`: the deterministic synthetic local-code Q&A bundle.
- `connector-matrix/`: the deterministic mock connector and permission-boundary
  bundle.

`manifest.json` must include:

```json
{
  "schema_version": 1,
  "mode": "synthetic_enterprise_knowledge_lookup_scenario",
  "synthetic_only": true,
  "live_connectors": false,
  "external_network": false,
  "credentials_required": false,
  "local_llm_required": false,
  "permission_boundary": "mock_metadata_only"
}
```

## Boundary

The scenario is synthetic-only. It does not contact live GitLab, Gitea,
Confluence, Jira, VPN services, LDAP, MES, ERP, or any external network. It does
not require credentials and does not store prompt text, source bodies, internal
URLs, customer data, or credential values in the metadata audit.

The citations are synthetic fixtures. Production connectors, credentialed
sources, private corpus export, and permission-aware deployment are not enabled
by this public scenario.
