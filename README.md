# phantom-enterprise

> Enterprise connector pack for [phantom-mesh](https://github.com/markl-a/phantom-mesh) — LDAP/SSO, VPN-aware routing, MES, ERP, Confluence/Jira, on-prem GitLab/Gitea, Apple Silicon HA.

## Status

**SCAFFOLD — awaiting first enterprise customer.**

This is the **last (7th) and lowest-priority** project in the phantom-mesh sibling set (originally scheduled for **M4 W13-14, ~2026-08**). It is intentionally minimal: building 7 connectors against zero real ERP/MES/AD instances guarantees 7 untested mocks. Only 2 modules have working code today; the other 5 are placeholders that activate once a real customer or employing company defines the target system.

A separate scaffold at `hailmary/phantom-enterprise/` provides a daily heartbeat (do not touch — launchd uses it). This top-level repo is the **library** that the connectors will live in once real work begins.

## Recruiting signal

招聘標的: **鼎新 / 中信 / 國泰 / 鴻海 / 聯發科** — when joining one of these, the relevant connector graduates from stub to production. Until then this repo proves the architecture extends cleanly to enterprise needs.

## The 7 connector modules

| Module | Status | First validation target |
|---|---|---|
| `ldap_sso/` | interface stubs (LDAP/SAML/OIDC ABC) | a real corp AD/SAML IdP |
| `vpn_aware_routing/` | **working** (live Tailscale) | already deployed |
| `on_prem_gitlab/` | **working** (live Gitea on z13) | self-hosted Gitea over Tailscale |
| `mes_connector/` | placeholder README | 鴻海 / 南亞科 MES API |
| `erp_connector/` | placeholder README | 鼎新 T100 / B2 / Workflow ERP |
| `confluence_jira/` | placeholder README | corp Atlassian instance |
| `apple_silicon_ha/` | runbook in `docs/` | this MBA + future M-series cluster |

## What runs today

```bash
pip install pytest requests
pytest -v
```

- `vpn_aware_routing.router.tailscale_route('z13')` → real IP from `tailscale status --json`
- `on_prem_gitlab.connector.list_repos()` → real call to `http://100.87.70.65:3000` over Tailscale
- `ldap_sso.auth.*` → 3 ABC subclasses, all raise `NotImplementedError` (shape proven, impl deferred)

## Roadmap

| When | Trigger | Work |
|---|---|---|
| Now (2026-05) | — | scaffold + 2 working connectors |
| M4 W13-14 (~2026-08) | first enterprise lead OR joining target company | implement `ldap_sso/` against real AD/SAML |
| Post-employment | depends on employer stack | activate MES / ERP / Confluence based on actual stack |
| Indefinite | no demand signal | stays scaffold (acceptable outcome) |

## License

Apache-2.0 — see [LICENSE](LICENSE).
