> ARCHIVED 2026-06-19 — frozen historical snapshot; current status lives in [/ROADMAP.md](../../ROADMAP.md)

# 2026-05-22 — Tier 1 initial dev

## What's in

| Module | LOC | Real or placeholder | Validation |
|---|---|---|---|
| `ldap_sso/` | ~110 | interface stubs (ABC + 3 concrete) | shape tests pass; impl raises `NotImplementedError` |
| `vpn_aware_routing/` | ~90 | **real, working** | live `tailscale status --json` |
| `on_prem_gitlab/` | ~75 | **real, working** | live Gitea on z13 over Tailscale |
| `mes_connector/` | 0 | placeholder README | — |
| `erp_connector/` | 0 | placeholder README | — |
| `confluence_jira/` | 0 | placeholder README | — |
| `apple_silicon_ha/` | 0 | placeholder README + runbook in `docs/` | runbook reflects maintainer's live setup |

Total: ~280 LOC of Python + ~120 LOC of tests + docs. Well under the 600 LOC budget — intentional.

## Why most modules are placeholder

This is the **last and lowest-priority** of the 7 phantom-mesh sibling
projects (originally scheduled for M4 W13-14, ~2026-08). The blocker is
not engineering effort — it's the absence of a real target system to
validate against:

- **No corporate AD/LDAP** to point `ldap_sso` at — would build a mock
  and never catch the real-world quirks (paged search, group-nesting,
  referrals, certificate validation edge cases).
- **No MES API access** — these are NDA-locked per fab; building a
  speculative connector wastes effort and risks IP boundary issues.
- **No 鼎新 ERP sandbox** — T100 / B2 connector specs require a customer
  license.
- **No corporate Atlassian** — could mock easily, but the 80/20 win is
  to wait one hour after joining a target employer and write it against
  their real instance.

## What's real today

Two connectors prove the architecture extends cleanly:

1. **`vpn_aware_routing.tailscale_route(host)`** — resolves any tailnet
   hostname to its IP. Used by phantom-mesh to route enterprise traffic
   over Tailscale without exposing internal DNS.
2. **`on_prem_gitlab.list_repos()`** — proves Tailscale → on-prem-git
   reachability end-to-end via the maintainer's live Gitea on z13. The
   same code shape works against self-hosted GitLab (swap `/api/v1` →
   `/api/v4`).

## When real work happens

| Trigger | Module activated |
|---|---|
| First enterprise pilot signing | the connector matching their stack |
| Joining 鼎新 / 中信 / 國泰 / 鴻海 / 聯發科 | the connector for that company's stack |
| Second M-series host arrives | `apple_silicon_ha` graduates from runbook to code |
| Indefinite (no demand) | this stays a scaffold — acceptable outcome |

## Test command

```bash
cd /Users/marklight/Documents/GitHub/phantom-enterprise
pytest -v
```

Live tests skip gracefully when Tailscale CLI is missing or z13 is offline.

## What is explicitly out of scope right now

- SOC2 / ISO 27001 controls (no customers to require it).
- SSO **provisioning** (SCIM) — read-only first.
- Multi-tenant data isolation (single-tenant per deploy is fine until customer #2).
- Audit log forwarding to enterprise SIEM (wait for real Splunk/Elastic target).
