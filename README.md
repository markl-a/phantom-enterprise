# phantom-enterprise

[![CI](https://github.com/markl-a/phantom-enterprise/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-enterprise/actions/workflows/ci.yml)

> **AI Q&A for your PRIVATE code, that runs on-prem** — ask a natural-language
> question about a private repo and get an answer grounded in the actual file
> contents. The source bytes are read locally and handed to a local phantom
> agent; this tool never uploads them. Ships with a real on-prem **Gitea**
> connector and **Tailscale** host routing so the same flow works across a
> tailnet without exposing the code to any cloud.

![status: alpha · 3 working modules](https://img.shields.io/badge/status-alpha%20%C2%B7%203%20working%20modules-orange)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

## What works today

Three modules have real, tested code (the others are roadmap stubs — see
[Roadmap connectors](#roadmap-connectors-not-implemented-yet)):

| Module | What it does | State |
|---|---|---|
| `code_qa/` | Private-code Q&A: rank the repo files most relevant to a question, build a grounding prompt, and answer via a **local** `phantom exec` call. Source is read on the machine and never uploaded by this tool. | **working** (unit-tested; needs the `phantom` binary on PATH for live answers) |
| `vpn_aware_routing/` | Resolve a Tailscale peer hostname to its tailnet IP via `tailscale status --json`; falls back cleanly when the CLI is missing or the peer is offline. | **working** (live Tailscale) |
| `on_prem_gitlab/` | Real connector against a self-hosted **Gitea** (`list_repos` / `list_repo_files` / `get_repo_file`). The same URL shape works for self-hosted GitLab with an `/api/v1`→`/api/v4` swap. | **working** (live Gitea; the 2 network tests skip when no host is set) |

## 30-second quickstart

```bash
git clone https://github.com/markl-a/phantom-enterprise
cd phantom-enterprise
pip install pytest requests
pytest -v
```

Ask a question about a private repo — the code stays on the machine:

```bash
# local checkout (the reliable default)
phantom-enterprise ask --repo /path/to/your/repo "where is auth handled?"

# on-prem Gitea over Tailscale (bonus path)
export GITEA_BASE_URL=http://<your-tailnet-host>:3000
phantom-enterprise ask --repo owner/repo --token "$GITEA_TOKEN" "what does the worker do?"
```

`ask` selects the files most relevant to the question (relevance-ranked, with
per-file and total context caps), builds a single grounding prompt, and runs
`phantom exec --quiet` **locally** to produce the answer. The LLM call goes
through the `phantom` binary on this machine — install it separately and put it
on `PATH` for live answers. If the on-prem Gitea host is unreachable, the CLI
prints a clear error and points you back at the reliable local-checkout path.

### How the no-upload claim holds

- **Local mode** walks the working tree, skips `.gitignore` entries, common
  build/cache dirs, and binary files, and only ever pipes the selected text to
  the local `phantom exec` subprocess on the same machine.
- **Gitea mode** pulls file contents from your own on-prem Gitea/GitLab host
  (typically reached over Tailscale), not a public service.

This tool does not POST your code to any third-party endpoint. Where the bytes
end up beyond the local `phantom` process depends on how *that* binary is
configured — choose a local/self-hosted model backend if you need a strict
air-gap.

## Routing + on-prem Git, directly

```bash
# resolve a tailnet peer to its IP
python -c "from vpn_aware_routing.router import tailscale_route; print(tailscale_route('z13'))"

# list repos on your on-prem Gitea
export GITEA_BASE_URL=http://<your-tailnet-host>:3000
python -c "from on_prem_gitlab import list_repos; print([r.get('full_name') for r in list_repos()])"
```

## 30-second demo

[`docs/demo.cast`](docs/demo.cast) — asciinema recording of
`vpn_aware_routing.router.tailscale_route()`; the demo uses a non-existent host
so no real tailnet IPs leak in the cast.

```sh
# play in a terminal (requires asciinema)
asciinema play docs/demo.cast

# or view the captured text without any tooling:
cat docs/demo.cast | jq -r '.[] | select(.[1]=="o") | .[2]'
```

Self-hosted on purpose — no upload to asciinema.org, no third-party tracking.

## 一句話 niche

Azure AI Foundry / Databricks / HashiCorp 都是雲端優先 + 美式企業 stack。
**phantom-enterprise 的 niche 是台廠 + on-prem + Apple Silicon HA + 跨
VPN 的連接器套件** — 本地 code Q&A、本地 Gitea、Tailscale subnet router
直接是一等公民,不是 marketplace 上的第三方 plugin,而且 source 不離開機器。

## Status — honest disclosure

**ALPHA — 3 working modules, the rest are roadmap stubs.**

This is the **lowest-priority** project in the phantom-mesh sibling set
(scheduled M4 W13-14, ~2026-08). The three modules above run today and are
unit-tested. The connectors in the next section are **placeholders or interface
stubs only** — they are written to be filled in once a real target system (a
corporate AD, an actual MES/ERP instance, a customer Atlassian) is in scope,
rather than shipping fake "demo against a Docker stub" implementations that
don't survive contact with a real corp environment.

## Roadmap connectors (not implemented yet)

None of the following have working logic today. The table is explicit about
exactly what exists so there is no overclaim.

| Module | What exists now | First validation target |
|---|---|---|
| `ldap_sso/` | LDAP / SAML / OIDC **interface stubs** — ABC + dataclass shape; every `authenticate()` raises `NotImplementedError` (interface tests only). | 真實 corp AD / SAML IdP |
| `mes_connector/` | placeholder README, no code | 鴻海 / 南亞科 / 台積 MES API |
| `erp_connector/` | placeholder README, no code | 鼎新 T100 / B2 / Workflow ERP |
| `confluence_jira/` | placeholder README, no code | corp Atlassian instance |
| `apple_silicon_ha/` | placeholder module; runbook in [`docs/apple-silicon-ha-deploy.md`](docs/apple-silicon-ha-deploy.md) | second M-series host or customer HA request |

## Architecture (within phantom-mesh ecosystem)

phantom-enterprise extends phantom-mesh into enterprise on-prem systems. The
working path today is **local/on-prem code Q&A** routed over Tailscale; the
enterprise connectors (MES / ERP / AD / Confluence) are the planned extension.

```
phantom-mesh agent (Mac / Win / Linux)
   ↓ vpn_aware_routing  (Tailscale host routing — working)
on-prem host over tailnet
   ↓
┌───────────┬───────────────┬──────────────────────────────┐
│ code_qa   │ on_prem_gitlab│ ldap_sso / mes / erp / conf.  │
│ (working) │ (working)     │ (roadmap stubs)               │
└───────────┴───────────────┴──────────────────────────────┘
```

Pillars served: **P1** (跨平台 — enterprise on-prem extension)、**P4**(加密
為先 — VPN-aware routing 讓流量走 Tailscale / corp VPN,code 留在本機)。

## Target users (recruiter / co-builder angle)

招聘標的: **鼎新 / 中信 / 國泰 / 鴻海 / 聯發科 / 仁寶 / 廣達 / 緯創**。
當作者加入這些公司之一,roadmap connector 從 stub 升級到 production。在那之前,
這個 repo 用三個會跑的模組(本地 code Q&A、真實 Tailscale 路由、真實 Gitea
connector)證明 phantom-mesh 架構可乾淨延伸到企業需求。

- **Recruiters**: 看的是「會做 enterprise integration、懂 on-prem first、
  懂 LDAP/SAML/OIDC 接口形狀、懂台廠 MES/ERP schema」— 已落地的三個模組 +
  其餘 connector 的 interface 形狀已足以 demonstrate 能力。
- **Co-builders**: 任何在台廠做 internal tool / AI infra,想接 phantom-mesh
  跑 cross-device agent 的工程師。

## Roadmap (per master plan)

| When | Trigger | Work |
|---|---|---|
| Now (2026-05) | — | code_qa + Tailscale routing + Gitea connector working |
| M4 W13-14 (~2026-08) | 第一個 enterprise lead OR 加入 target 公司 | 實作 `ldap_sso/` against 真實 AD/SAML |
| Post-employment | depends on employer stack | activate MES / ERP / Confluence based on actual stack |
| Indefinite | no demand signal | roadmap connectors stay stubs (acceptable outcome) |

Full design at [`docs/05-phantom-enterprise.md`](docs/).

## License

Apache-2.0. © 2026 Mark Lai ([markl-a](https://github.com/markl-a)). See
[LICENSE](LICENSE).
