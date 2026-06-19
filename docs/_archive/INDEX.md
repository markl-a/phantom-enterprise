> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-enterprise.md;此為歷史版本。

# Documentation index

> **Single navigation entry for phantom-enterprise docs.** Every Markdown doc in
> the repo is listed here with a one-line description and its authority level.
> For *what is shipped / planned* see [`/ROADMAP.md`](../ROADMAP.md) — the status
> source of truth. Last updated **2026-06-19**.

## Front matter

| Doc | What it is | Authority |
|---|---|---|
| [`/README.md`](../README.md) | Front door: positioning, niche, 30-second quickstart, links here and to ROADMAP. | Positioning |
| [`/ROADMAP.md`](../ROADMAP.md) | ⭐ Single status source of truth — Shipped / In progress / Planned-next, date-stamped. | **Status SSOT** |
| [`/LICENSE`](../LICENSE) | Apache-2.0 license text. | Legal |

## Design & positioning

| Doc | What it is | Authority |
|---|---|---|
| [`05-phantom-enterprise.md`](05-phantom-enterprise.md) | Canonical design + positioning spec: niche, competitor analysis, the seven connectors, MVP scope, risks, monetization path. | Design SSOT |

## Activation specs (forward-looking)

These specify how a stubbed module is *activated* once a real target system
exists. They are design intent, not status — see ROADMAP for what is built.

| Doc | What it is | Authority |
|---|---|---|
| [`ldap-activation-spec.md`](ldap-activation-spec.md) | How to activate `ldap_sso.LdapAuth` against a real AD/LDAP: `LdapConfig` shape, simple-bind flow, filter escaping, failure modes, checklist. | Activation spec |
| [`saml-oidc-spec.md`](saml-oidc-spec.md) | How to activate `SamlAuth` / `OidcAuth` against a real IdP: validation sequences, claim mapping, failure modes, security notes. | Activation spec |

## Runbooks (manual, not CI)

| Doc | What it is | Authority |
|---|---|---|
| [`apple-silicon-ha-deploy.md`](apple-silicon-ha-deploy.md) | Real two-node Apple Silicon HA deploy runbook (launchd + Docker Compose + Tailscale), failover table, honest single-laptop limits. | Runbook |
| [`vpn-mesh-demo.md`](vpn-mesh-demo.md) | Manual demo of the VPN-aware routing + on-prem Git + `ask` path. Explicitly not headless / not wired into CI. | Runbook |

## Media

| Doc | What it is | Authority |
|---|---|---|
| [`demo.cast`](demo.cast) | Self-hosted asciinema recording of the working VPN-aware routing connector (no real tailnet IPs leak). | Media |

## Archive

Superseded / frozen historical snapshots. Kept for provenance; never the current
truth — current status always lives in [`/ROADMAP.md`](../ROADMAP.md).

| Doc | What it is |
|---|---|
| [`_archive/2026-05-22-tier1-initial-dev.md`](_archive/2026-05-22-tier1-initial-dev.md) | Frozen 2026-05-22 Tier-1 initial-dev log (LOC tables now stale). |

## Module READMEs

Each connector package carries a short README describing its target and shape.
These are per-module pointers; the authoritative build status for all of them is
the ROADMAP **Shipped** section, not the individual READMEs.

| README | Module |
|---|---|
| [`../apple_silicon_ha/README.md`](../apple_silicon_ha/README.md) | Apple Silicon HA module; deploy runbook in `docs/`. |
| [`../confluence_jira/README.md`](../confluence_jira/README.md) | Atlassian Confluence + Jira connector. |
| [`../erp_connector/README.md`](../erp_connector/README.md) | 鼎新 / SAP ERP connector. |
| [`../mes_connector/README.md`](../mes_connector/README.md) | 鴻海 / 南亞科 MES connector. |
