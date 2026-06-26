# Public Demo Contract

`phantom-enterprise` is for private/on-prem environments, so public demos must
not depend on a real VPN, LDAP/SSO service, Gitea/GitLab server, Jira,
Confluence, MES, ERP, or customer document store.

## Safe Public Surface

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m code_qa.cli --help
```

The reliable public path is a local checkout. `ask --repo <path>` reads files
from that local working tree, respects `.gitignore`, skips binary files, caps
context size, and sends the grounding prompt only to the configured local
`phantom exec` process.

```powershell
python -m code_qa.cli ask --repo <local-demo-repo> "How does authentication work?"
```

This command requires a local `phantom` binary. CI tests stub that call; public
docs must not require live enterprise infrastructure.

## P2 Artifact Demo

The deterministic synthetic local-code Q&A bundle is the default P2 public
artifact path. It creates a tiny synthetic repo, builds local context, writes a
deterministic answer with citations, records evidence metadata, and writes an
audit log. It does not call `phantom exec`, live GitLab/Gitea, Jira,
Confluence, LDAP, MES, ERP, VPN, or any network service.

```powershell
$bundle = Join-Path $env:TEMP ("phantom-enterprise-demo-" + [guid]::NewGuid().ToString("N"))
python -m code_qa.cli demo-loop --out $bundle
Get-Content (Join-Path $bundle "manifest.json")
```

After installation, the same path is available as:

```powershell
phantom-enterprise-demo-loop --out <bundle-dir>
```

The bundle writes:

- `synthetic-repo/src/auth.py`: tiny synthetic source fixture.
- `manifest.json`: schema version, mode, safety flags, and artifact list.
- `answer.json`: deterministic answer plus file/line citations.
- `evidence.json`: selected file paths, snippet line ranges, scores, hashes,
  and context counts.
- `audit-log.jsonl`: metadata-only audit events; it must not store source body
  text or answer prompt contents.
- `summary.md`: human-readable summary.

`manifest.json` must include `live_connectors=false`,
`external_network=false`, `local_llm_required=false`, and
`synthetic_only=true`.

## P2 Connector Matrix Demo

The deterministic mock connector matrix documents how contributors can add
enterprise sources without enabling real services in the public demo path. It
writes connector contracts, a permission boundary, and a metadata-only audit
log. It does not contact GitLab/Gitea, Jira, Confluence, LDAP, MES, ERP, VPN,
or any network service.

```powershell
$bundle = Join-Path $env:TEMP ("phantom-enterprise-connectors-" + [guid]::NewGuid().ToString("N"))
python -m code_qa.cli connector-matrix --out $bundle
Get-Content (Join-Path $bundle "manifest.json")
```

After installation, the same path is available as:

```powershell
phantom-enterprise-connector-matrix --out <bundle-dir>
```

The bundle writes:

- `manifest.json`: schema version, mode, safety flags, and artifact list.
- `connector-matrix.json`: mock `code`, `document`, `issue`, and `runbook`
  connector contracts.
- `permission-boundary.json`: public default policy to deny live connectors and
  allow only mock/local fixture modes.
- `audit-log.jsonl`: metadata-only audit events; it must not store source body
  text, issue bodies, internal URLs, tokens, or secrets.
- `summary.md`: human-readable summary.

`manifest.json` must include `synthetic_only=true`, `live_connectors=false`,
`external_network=false`, `credentials_required=false`, and
`permission_boundary=mock_metadata_only`.

The permission boundary must default to deny live connectors. Public modes are
limited to `mock` and `local_fixture`.

## P3 Enterprise Knowledge Lookup Scenario

The deterministic knowledge lookup scenario combines the synthetic local-code
Q&A bundle with the mock connector matrix and writes a permission-aware lookup
scenario:

```powershell
python -m code_qa.cli knowledge-scenario --out <bundle-dir>
```

After installation, the same path is available as:

```powershell
phantom-enterprise knowledge-scenario --out <bundle-dir>
phantom-enterprise-knowledge-scenario --out <bundle-dir>
```

The bundle writes `knowledge-lookup.json`, `citation-map.json`,
`permission-review.json`, `audit-summary.json`, and `summary.md`, plus nested
`source-code-qa/` and `connector-matrix/` source bundles. Its manifest must keep
`synthetic_only=true`, `live_connectors=false`, `external_network=false`,
`credentials_required=false`, `local_llm_required=false`, and
`permission_boundary=mock_metadata_only`.

The scenario does not contact live enterprise services and does not store prompt
text, source bodies, internal URLs, customer data, or credential values in the
metadata audit. See `docs/KNOWLEDGE_LOOKUP_SCENARIO.md` for the full contract.

## Live Connector Gate

- Live Gitea/GitLab, VPN, and Atlassian tests must remain gated behind
  `PHANTOM_ENTERPRISE_LIVE=1` and explicit service configuration.
- `status is an environment probe` and may contact configured local/on-prem
  services. It is not the default public smoke demo.
- LDAP/SAML/OIDC, MES/ERP, and HA deployment pieces are prototype/planned unless
  a private deployment explicitly configures and verifies them.

## Data Policy

- Do not commit internal URLs, tokens, proprietary code, customer documents,
  issue bodies, wiki pages, logs, or screenshots.
- Public examples should use tiny synthetic repos or mock connector payloads.
- Answer output must cite the local files used and should not claim knowledge
  outside the selected context.
