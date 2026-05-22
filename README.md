# phantom-enterprise

> **phantom-mesh × 企業 on-prem 環境連接器** — LDAP/SSO、VPN-aware routing、
> MES/ERP、Confluence/Jira、on-prem GitLab/Gitea、Apple Silicon HA;招聘對齊
> 鼎新 / 中信 / 鴻海 / 聯發科等台廠 enterprise 棧。

![status: alpha · scaffold (2/7 connectors live)](https://img.shields.io/badge/status-alpha%20%C2%B7%20scaffold%20(2%2F7%20live)-orange)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

## Status — honest disclosure

**SCAFFOLD — awaiting first enterprise customer.**

This is the **7th and intentionally lowest-priority** project in the
phantom-mesh sibling set (scheduled M4 W13-14, ~2026-08). Building 7
connectors against zero real ERP/MES/AD instances guarantees 7 untested
mocks. **Only 2 modules have working code today**; the other 5 are
placeholders that activate **once a real customer (or employing company)
defines the target system**.

This is by design — the architecture is proven to extend cleanly to
enterprise needs, while avoiding fake "demo against a Docker stub"
implementations that don't survive contact with a real corp AD.

## 一句話 niche

Azure AI Foundry / Databricks / HashiCorp 都是雲端優先 + 美式企業 stack。
**phantom-enterprise 的 niche 是台廠 + on-prem + Apple Silicon HA + 跨
VPN 的連接器套件** — 鼎新 T100、鴻海 MES、本地 Gitea、Tailscale subnet
router 直接是一等公民,不是 marketplace 上的第三方 plugin。

## The 7 connector modules

| Module | Status | First validation target |
|---|---|---|
| `ldap_sso/` | interface stubs (LDAP/SAML/OIDC ABC) | 真實 corp AD / SAML IdP |
| `vpn_aware_routing/` | **✅ working** (live Tailscale) | already deployed |
| `on_prem_gitlab/` | **✅ working** (live Gitea on z13) | self-hosted Gitea over Tailscale |
| `mes_connector/` | placeholder README | 鴻海 / 南亞科 MES API |
| `erp_connector/` | placeholder README | 鼎新 T100 / B2 / Workflow ERP |
| `confluence_jira/` | placeholder README | corp Atlassian instance |
| `apple_silicon_ha/` | runbook in `docs/` | this MBA + future M-series cluster |

## 30-second quickstart

```bash
git clone https://github.com/markl-a/phantom-enterprise
cd phantom-enterprise
pip install pytest requests
pytest -v
```

What actually runs today:

- `vpn_aware_routing.router.tailscale_route('z13')` → 真實 IP 從
  `tailscale status --json` 抓
- `on_prem_gitlab.connector.list_repos()` → 真實打 `http://100.87.70.65:3000`
  (作者 z13 Gitea over Tailscale)
- `ldap_sso.auth.*` → 3 ABC subclasses,全部 `NotImplementedError`(shape
  proven, impl deferred 到有真實 AD 可測時)

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
  懂台廠 MES/ERP 真實 schema、懂 on-prem first 思維」— 即使 5/7 還是 stub,
  接口形狀 + Apple Silicon HA runbook + 真實 Tailscale/Gitea integration 已
  足以 demonstrate 能力。
- **Co-builders**: 任何在台廠做 internal tool / AI infra,想接 phantom-mesh
  跑 cross-device agent 的工程師。

## Roadmap (per master plan)

| When | Trigger | Work |
|---|---|---|
| Now (2026-05) | — | scaffold + 2 working connectors |
| M4 W13-14 (~2026-08) | 第一個 enterprise lead OR 加入 target 公司 | 實作 `ldap_sso/` against 真實 AD/SAML |
| Post-employment | depends on employer stack | activate MES / ERP / Confluence based on actual stack |
| Indefinite | no demand signal | stays scaffold (acceptable outcome) |

Full design at [`docs/05-phantom-enterprise.md`](docs/).

## License

Apache-2.0. © 2026 Mark Lai ([markl-a](https://github.com/markl-a)). See
[LICENSE](LICENSE).
