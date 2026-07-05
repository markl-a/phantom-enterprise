# phantom-enterprise — Feature Audit

Honest status of what is actually shipped and tested versus what is a
documented interface or roadmap stub. Grounded in the modules as they exist
in the tree, not in aspirational copy. Update this file when module status
changes.

Legend:
- **Shipped + tested** — working code with hermetic/unit tests in the module's `tests/`.
- **Interface only** — public API + contract is defined and (where noted) partially tested, but the concrete backend raises `NotImplementedError` until validated against a real system.
- **Roadmap stub** — package placeholder (`__init__.py` + README) only; activates on a real customer/NDA. No implementation yet.

## Module status

| Module | Status | Notes |
| --- | --- | --- |
| `code_qa` | Shipped + tested | The primary product surface: `phantom-enterprise` CLI (`ask`, `demo-loop`, `connector-matrix`, `knowledge-scenario`, `status`) plus deterministic synthetic bundles. 9 test files covering ask flow, status probe, packaging, and the deterministic-bundle contracts. |
| `on_prem_gitlab` | Shipped + tested | Self-hosted GitLab v4 REST connector (`list_projects`, `list_project_files`, `get_project_file`) and a Gitea path, with unreachable-host error types (`GitLabUnreachable`, `GiteaUnreachable`). 3 hermetic/unit test files. |
| `confluence_jira` | Shipped + tested | Atlassian Cloud connector over Confluence/Jira REST (`search_pages`, `get_page`, `list_issues`, `add_comment`). 2 test files (unit + hermetic). |
| `vpn_aware_routing` | Shipped + tested | Real Tailscale peer→tailnet-IP resolver; degrades gracefully when the Tailscale CLI is absent or the peer is off the tailnet. 2 test files (unit + hermetic). |
| `apple_silicon_ha` | Shipped + tested | Hermetic-friendly health-probe helpers (`ProbeResult`, socket/subprocess probes) for Apple Silicon HA nodes. 1 test file. |
| `ldap_sso` | Interface + partial | LDAP/SAML/OIDC auth backends are defined as abstract interfaces that raise `NotImplementedError` until validated against a real corporate IdP. The RFC 4515 LDAP escaping helpers (`filters.py`) are real and tested. 2 test files (filters + interface contract). |
| `mes_connector` | Roadmap stub | Package placeholder only. Targets in-house MES APIs (Foxconn / Nanya / TSMC-shape); schemas are NDA-locked. Planned surface: `list_lots()`, `get_lot_status()`, `post_wafer_event()`. Activates on a real MES pilot. |
| `erp_connector` | Roadmap stub | Package placeholder only. Activates on a real ERP customer/NDA. |

## What "tested" means here

Tests are hermetic: connector tests mock the HTTP layer / external CLI, so
`python -m pytest -q` runs offline with no enterprise services. Live paths are
gated behind `PHANTOM_ENTERPRISE_LIVE=1` and explicit service configuration and
are **not** exercised in CI (see the `live` pytest marker in `pyproject.toml`).

## Honest limitations

- No enterprise customer has deployed this yet; the connectors are validated
  against mocked API contracts, not against a production LDAP/GitLab/Atlassian/MES
  instance.
- `ldap_sso` cannot actually authenticate against an IdP today — only the escaping
  helpers and the interface shape are real.
- `mes_connector` / `erp_connector` are intentionally empty until there is a real
  target system to build against.
- This package ships **no MCP server**; it is a CLI + connector library. The
  console entry points are listed under `[project.scripts]` in `pyproject.toml`.

## Roadmap (not yet shipped)

- Activate `ldap_sso` concrete backends against a real corporate IdP.
- Implement `mes_connector` on a real MES pilot (~M4, or first MES customer).
- Implement `erp_connector` on a first ERP customer/NDA.
