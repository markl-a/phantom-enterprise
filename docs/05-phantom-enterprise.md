# ⑤ phantom-enterprise

> **phantom-mesh 接企業 on-prem 環境(LDAP/SSO/MES/ERP/VPN/Confluence)的 connector pack**
> 招聘精準命中鼎新 / 中信 / 國泰 / 鴻海 / 聯發科

## 一句話定位

「phantom-mesh 在企業內網無痛跑 — 接公司的 SSO / VPN / ERP / MES / 內部 GitLab,讓公司的 AI 也能用 phantom 的 mesh 跨裝置 + privacy-first 架構。」

## 對齊 BIG-GOAL

- **P1 跨裝置 mesh**:擴展到企業 VPN-aware routing(node 跨企業網段通訊)
- **P4 加密為先**:on-prem 部署,資料不離公司

## 競品分析

| 競品 | 強項 | phantom-enterprise 差異 |
|---|---|---|
| **Azure AI Foundry** | 企業 LLM 部署 | phantom 為 self-hosted、不綁雲 |
| **Databricks Mosaic AI** | Enterprise ML | 本專案 cluster scale 小 + cross-device |
| **HashiCorp Boundary** | 企業 access mgmt | 本專案 AI-native,不只 ACL |
| **Open WebUI** | self-hosted LLM UI | 本專案為 agent + workflow + mesh,不只 chat |
| **n8n self-hosted** | 工作流 | 本專案 connector 為 AI-aware + cluster-aware |

**niche**:**第一個 cross-device + agent + workflow + privacy-first 的 enterprise AI mesh connector pack**。

## 七個內建 connector

```
phantom-enterprise/
├── ldap-sso/                  # LDAP + SAML 2.0 + OIDC
├── vpn-aware-routing/         # Tailscale / Wireguard / OpenVPN node discovery
├── mes-connector/             # 鴻海 / 南亞科 廠端 MES API
├── erp-connector/             # 鼎新 T100 / B2 / Workflow ERP
├── confluence-jira/           # Atlassian 內網
├── on-prem-gitlab/            # 自架 GitLab / Gitea
└── apple-silicon-ha/          # M-series active/standby deploy(原 platform-stack)
```

## 招聘 / 副業 / 應用評分

| 維度 | 評分 | 對應 |
|---|---|---|
| **招聘** | ⭐⭐⭐⭐⭐ | **鼎新數智**(ERP+AI) / **中信銀**(企業 RAG) / **國泰世華** / **鴻海 C3** / **聯發科 MLOps Architect** |
| **副業** | ⭐⭐⭐ | 企業 AI 導入顧問接案(有 lead 才接) |
| **個人應用** | ⭐⭐ | 間接(進大廠後可派上用場) |

## 應用範圍

- 主要為 enterprise 場景,個人 daily 使用較少;間接支援進入大廠 narrative。

## MVP scope

### Must have(M4 W13-14)
- [ ] LDAP/SAML/OIDC 一個 unified `phantom auth` 介面
- [ ] VPN-aware routing(從現有 Tailscale 擴張)
- [ ] On-prem GitLab connector(自架 GitLab 為第一個用戶)
- [ ] Apple Silicon HA deploy runbook(原 platform-stack 已有)
- [ ] 1 個 demo:phantom node 在公司 VPN 內也能跟家裡 mesh 通訊

### Nice to have(看商機)
- [ ] 鼎新 T100 / B2 connector(若進鼎新)
- [ ] MES connector(若進鴻海 / 南亞科)
- [ ] Confluence / Jira(常見企業)
- [ ] SOC2 compliance pack(配合 ④ secure-connector)

### NOT doing
- 完整 Active Directory 取代(本專案為接,不是取代)
- ERP 全功能 module(只接資料 / 觸發,不重做)
- 企業 SaaS(仍為 self-hosted)

## 改裝來源

**現有**:
- phantom-mesh `scripts/setup-tailscale-mesh.sh`(已有 VPN-aware)
- Apple Silicon HA + Docker Compose 部署(已 24/7 跑著)
- `platform-core`(self-hosted GitLab CE + Prometheus + Loki + Grafana,7 個 business stack)

## 風險

- **進大廠才能驗證**:connector 寫了但未在實際 enterprise 環境驗證
- **legal**:企業 connector 可能踩 license issue(ERP API 通常閉源)
- **scope creep**:容易變成「另一個 n8n」,要守住「跑在 phantom-mesh 上」這個區隔
- **demand**:小公司沒 LDAP/SSO,大公司用 Microsoft 全套 — 中間客群有多大?

## 變現路徑

| 路徑 | 細節 |
|---|---|
| 企業 AI 導入顧問 | 有 lead 才接 |
| Pro tier:enterprise license | 加密 SSO 等企業功能需付費(per seat 訂閱) |
| 對應大廠面試 narrative | 不是直接變現,但進大廠後可推動 phantom 內部試用 |

## 為什麼放 M4 W13-14(最後做)

- 招聘信號雖然強,**但需要 ① 到 ④ 先做完才有 enterprise-ready 的本錢**
- 副業變現速度慢(要客戶,客戶要驗證)
- 個人應用較弱(可延後)
- **真正的價值是「投履歷時可以講」**,不是「現在就要跑」
- 若 M3 就拿到大廠 offer,這個項目可以在新公司延後做

---

*Sanitized public spec. Author: Mark Lai ([@markl-a](https://github.com/markl-a)).*
