# phantom-enterprise

[![CI](https://github.com/markl-a/phantom-enterprise/actions/workflows/ci.yml/badge.svg)](https://github.com/markl-a/phantom-enterprise/actions/workflows/ci.yml)
![license: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)
[![phantom-mesh ecosystem](https://img.shields.io/badge/ecosystem-phantom--mesh-purple)](https://github.com/markl-a/phantom-mesh)

> phantom-mesh 的企業 on-prem 連接器套件 — LDAP/SSO、VPN-aware routing、on-prem GitLab/Gitea、Confluence/Jira、MES/ERP、Apple Silicon HA;資料不離開機器。隱私優先、mesh 原生、台廠 on-prem 形狀。

## Quickstart

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m code_qa.cli --help
```

Deterministic synthetic local-code Q&A bundle:

```powershell
$bundle = Join-Path $env:TEMP ("phantom-enterprise-demo-" + [guid]::NewGuid().ToString("N"))
python -m code_qa.cli demo-loop --out $bundle
Get-Content (Join-Path $bundle "manifest.json")
Remove-Item -LiteralPath $bundle -Recurse -Force
```

Deterministic mock connector matrix and permission-boundary bundle:

```powershell
$bundle = Join-Path $env:TEMP ("phantom-enterprise-connectors-" + [guid]::NewGuid().ToString("N"))
python -m code_qa.cli connector-matrix --out $bundle
Get-Content (Join-Path $bundle "manifest.json")
Remove-Item -LiteralPath $bundle -Recurse -Force
```

Deterministic synthetic enterprise knowledge lookup scenario:

```powershell
$bundle = Join-Path $env:TEMP ("phantom-enterprise-knowledge-" + [guid]::NewGuid().ToString("N"))
python -m code_qa.cli knowledge-scenario --out $bundle
Get-Content (Join-Path $bundle "manifest.json")
Remove-Item -LiteralPath $bundle -Recurse -Force
```

Public demos should use a tiny local checkout or the test fixtures, not real
enterprise services:

```powershell
python -m code_qa.cli ask --repo <local-demo-repo> "How does authentication work?"
```

Live connector checks stay gated behind `PHANTOM_ENTERPRISE_LIVE=1` and explicit
service configuration. `status` is an environment probe, not the default public
smoke path. See [docs/PUBLIC_DEMO.md](docs/PUBLIC_DEMO.md) and
[docs/KNOWLEDGE_LOOKUP_SCENARIO.md](docs/KNOWLEDGE_LOOKUP_SCENARIO.md).

## Install

```powershell
# from a clone
python -m pip install -e .[dev]

# runtime only (no test tooling)
python -m pip install -e .
```

Requires Python >= 3.10. The only runtime dependency is `requests`.

## Usage

Console entry points (installed by `pip install`):

| Command | Purpose |
| --- | --- |
| `phantom-enterprise ask --repo <path> "<question>"` | Answer a question about a local checkout (the reliable public path). |
| `phantom-enterprise demo-loop --out <dir>` | Emit a deterministic synthetic local-code Q&A bundle. |
| `phantom-enterprise connector-matrix --out <dir>` | Emit a deterministic mock connector + permission-boundary bundle. |
| `phantom-enterprise knowledge-scenario --out <dir>` | Emit a deterministic enterprise knowledge-lookup scenario. |
| `phantom-enterprise status` | Probe the local environment (not a live-service smoke). |

Equivalent module form: `python -m code_qa.cli <subcommand>`. Each also has a
dedicated script alias (`phantom-enterprise-demo-loop`, etc.) — see
`[project.scripts]` in `pyproject.toml`.

## What's inside

The connectors keep data on-prem. See [FEATURE-AUDIT.md](FEATURE-AUDIT.md) for the
honest shipped-vs-roadmap status of each module.

- `code_qa` — the CLI + deterministic demo bundles (primary surface).
- `on_prem_gitlab` — self-hosted GitLab v4 + Gitea connector.
- `confluence_jira` — Atlassian Confluence/Jira REST connector.
- `vpn_aware_routing` — Tailscale peer → tailnet-IP resolver.
- `apple_silicon_ha` — health-probe helpers for Apple Silicon HA nodes.
- `ldap_sso` — LDAP/SAML/OIDC interfaces + tested LDAP escaping helpers (concrete auth pending a real IdP).
- `mes_connector` / `erp_connector` — roadmap stubs, activate on a real pilot.

📄 完整文件(定位/快速上手/狀態路線圖/開源生態與方向):見 [docs/phantom-enterprise.md](docs/phantom-enterprise.md)
