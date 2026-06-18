# phantom-enterprise

[![CI](https://github.com/markl-a/phantom-enterprise/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-enterprise/actions/workflows/ci.yml)

> **phantom-mesh × 企業 on-prem 環境連接器** — LDAP/SSO、VPN-aware routing、
> MES/ERP、Confluence/Jira、on-prem GitLab/Gitea、Apple Silicon HA;招聘對齊
> 鼎新 / 中信 / 鴻海 / 聯發科等台廠 enterprise 棧。

![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

> **Status:** see **[ROADMAP.md](ROADMAP.md)**. Docs map:
> **[docs/INDEX.md](docs/INDEX.md)**.

## 30-second demo

[`docs/demo.cast`](docs/demo.cast) — asciinema recording of `vpn_aware_routing.router.tailscale_route()` (the working connector); demo uses a non-existent host so no real tailnet IPs leak in the cast.

```sh
# play in a terminal (requires asciinema)
asciinema play docs/demo.cast

# or view the captured text without any tooling:
cat docs/demo.cast | jq -r '.[] | select(.[1]=="o") | .[2]'
```

Self-hosted on purpose — no upload to asciinema.org, no third-party tracking.

## Status

See **[ROADMAP.md](ROADMAP.md)** — the single source of truth for what is
shipped / in progress / planned, plus the demand-gated activation triggers that
govern when each connector graduates from scaffold to production.

## 一句話 niche

Azure AI Foundry / Databricks / HashiCorp 都是雲端優先 + 美式企業 stack。
**phantom-enterprise 的 niche 是台廠 + on-prem + Apple Silicon HA + 跨
VPN 的連接器套件** — 鼎新 T100、鴻海 MES、本地 Gitea、Tailscale subnet
router 直接是一等公民,不是 marketplace 上的第三方 plugin。

## The 7 connector modules

| Module | First validation target |
|---|---|
| `ldap_sso/` | 真實 corp AD / SAML IdP |
| `vpn_aware_routing/` | live Tailscale tailnet |
| `on_prem_gitlab/` | self-hosted Gitea / GitLab over Tailscale |
| `mes_connector/` | 鴻海 / 南亞科 MES API |
| `erp_connector/` | 鼎新 T100 / B2 / Workflow ERP |
| `confluence_jira/` | corp Atlassian instance |
| `apple_silicon_ha/` | this MBA + future M-series cluster |

Which modules have working code today vs. are still placeholders is tracked in
**[ROADMAP.md](ROADMAP.md)**, not here.

## 30-second quickstart

```bash
git clone https://github.com/markl-a/phantom-enterprise
cd phantom-enterprise
pip install pytest requests
pytest -v
```

The hermetic test suite runs offline; live connectors degrade gracefully when
Tailscale or an on-prem host is absent. The CLI entrypoint is
`phantom-enterprise` (`code_qa.cli`) — try `phantom-enterprise status` and
`phantom-enterprise ask`. For exactly which modules have working code today vs.
remain placeholders, see **[ROADMAP.md](ROADMAP.md)**.

## Architecture (within phantom-mesh ecosystem)

phantom-enterprise 是 **P1 跨平台連線** 的 enterprise 變體 — 把 phantom-mesh
的 cross-device dispatch 延伸到企業內部的 on-prem 系統(MES / ERP / AD /
Confluence),並提供 VPN-aware routing 讓 phantom agent 在 corp network
和個人 mesh 之間自然切換。

```
phantom-mesh agent (Mac / Win / Linux)
   ↓ phantom-enterprise.vpn_aware_routing
Tailscale / corp VPN subnet router
   ↓
┌────────┬──────────┬─────────┬──────────────┬─────────────┐
│ ldap_  │ on_prem_ │ mes_    │ erp_         │ confluence_ │
│ sso    │ gitlab   │ connect │ connector    │ jira        │
└────────┴──────────┴─────────┴──────────────┴─────────────┘
   ↑                                            ↑
real Gitea (z13, today)                  scaffold (waiting)
```

Pillars served: **P1** (跨平台 — enterprise on-prem extension)、**P4**(加密
為先 — VPN-aware routing 強制流量走 Tailscale / corp VPN)。

## Target users (recruiter / co-builder angle)

招聘標的: **鼎新 / 中信 / 國泰 / 鴻海 / 聯發科 / 仁寶 / 廣達 / 緯創**。
當作者加入這些公司之一,相關 connector 從 stub 升級到 production。在那之前,
這個 repo 證明 phantom-mesh 架構可乾淨延伸到企業需求。

- **Recruiters**: 看的是「會做 enterprise integration、懂 LDAP/SAML/OIDC、
  懂台廠 MES/ERP 真實 schema、懂 on-prem first 思維」— 即使部分 connector 仍是
  stub,接口形狀 + Apple Silicon HA runbook + 真實 Tailscale/Gitea integration
  已足以 demonstrate 能力。(實際進度見 [ROADMAP.md](ROADMAP.md)。)
- **Co-builders**: 任何在台廠做 internal tool / AI infra,想接 phantom-mesh
  跑 cross-device agent 的工程師。

## Roadmap

See **[ROADMAP.md](ROADMAP.md)** for the full shipped / planned breakdown and
the demand-gated activation triggers. Full design rationale at
[`docs/05-phantom-enterprise.md`](docs/05-phantom-enterprise.md); browse all docs
via [`docs/INDEX.md`](docs/INDEX.md).

## License

Apache-2.0. © 2026 Mark Lai ([markl-a](https://github.com/markl-a)). See
[LICENSE](LICENSE).
