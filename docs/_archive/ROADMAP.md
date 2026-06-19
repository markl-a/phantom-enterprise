> ARCHIVED 2026-06-19 — 內容已併入 docs/phantom-enterprise.md;此為歷史版本。

# ROADMAP

> **Single source of truth for project status.** Anything about what is
> shipped / in progress / planned lives here — not in `README.md`, not in
> module READMEs. Last updated **2026-06-19**.

phantom-enterprise is the **7th and intentionally lowest-priority** project in
the phantom-mesh sibling set (master-plan slot M4 W13-14, ~2026-08). It is a
connector scaffold whose modules graduate from stub to production **only when a
real target system exists to validate against** (a corporate AD, a fab MES, a
鼎新 ERP sandbox, a customer Atlassian). Building speculative connectors against
zero real instances is explicitly avoided.

The honest one-line status: **alpha scaffold — the architecture and the local
on-prem path are proven; the customer-specific connectors wait for a real
target.**

## Shipped

Verified against the working tree and merge history on `master` as of
2026-06-19. "Real" = working code with hermetic tests wired into CI
(`.github/workflows/ci.yml` runs `pytest` over the modules listed in
`pyproject.toml` `testpaths`).

- **VPN-aware routing** (`vpn_aware_routing/`) — real. Shells out to
  `tailscale status --json`, resolves a short hostname to its tailnet IP,
  and lists peers; returns no route (never crashes) when Tailscale is absent.
  Hardened: UTF-8 decode to avoid cp950 crash on Windows (`6927213`); MagicDNS
  first-label match anchored to the trusted `*.ts.net` suffix to close a
  wrong-host match (`9585455`); hermetic test suite (`b86bae4`).
- **On-prem Git connector** (`on_prem_gitlab/`) — real. Live Gitea (`/api/v1`)
  plus a provider-aware GitLab v4 (`/api/v4`) client with real HTTP + auth and
  hermetic tests (`1c96413`, `44d22bb`). Security: hardcoded tailnet IP scrubbed,
  base URL now env-driven (`99d6cd3`).
- **Confluence / Jira connector** (`confluence_jira/atlassian.py`) — real.
  `search_pages` / `get_page` / `list_issues` / `add_comment` over Atlassian
  REST with Basic-auth, mirroring the Gitea connector; 8 hermetic tests
  (`0d1306d`, merged `3c8d3d6`). Live-instance validation honestly deferred.
- **Private-code `ask` CLI** (`code_qa/`) — real. `phantom-enterprise ask`
  reads a repo locally (or over the on-prem Gitea/GitLab connector) and answers
  via a local phantom agent — code never leaves the machine (`d7dee9b`). GitLab
  source mode wired into the `ask` path mirroring Gitea (`677700f`, merged
  `476140a`). `phantom-enterprise status` runs real auth + HA probes instead of
  always reporting DEGRADED (`7b267e8`); productized entrypoint with `--version`
  and graceful interrupt/pipe handling (`7671896`).
- **Apple Silicon HA probes** (`apple_silicon_ha/probes.py`) — real, injectable
  health probes (launchd / port / peer-reachable / failover decision) with
  hermetic tests (`bd7a7a9`). The companion deploy runbook is
  [`docs/apple-silicon-ha-deploy.md`](docs/apple-silicon-ha-deploy.md).
- **LDAP/SSO interface seam** (`ldap_sso/`) — interface stubs by design.
  `AuthBackend` / `AuthResult` contract plus `LdapAuth` / `SamlAuth` / `OidcAuth`
  concrete classes that raise `NotImplementedError` until a real IdP is
  available. The injection-sensitive part is real: RFC 4515/4514 filter and DN
  escaping (`escape_filter_value`, `escape_dn_value`, `build_user_filter`) with
  contract tests (`7048911`), plus NUL/control-char escaping (`0431f7d`).
- **Project plumbing** — Apache-2.0 LICENSE (`ebcec96`); GitHub Actions pytest
  workflow + CI badge (`a3c8b89`); setuptools multi-package layout (`65100f2`);
  self-hosted asciinema demo cast, no third-party tracking
  ([`docs/demo.cast`](docs/demo.cast), `31eb80f`).

So of the seven named connectors, **four have real working code**
(vpn-aware-routing, on-prem-git, confluence/jira, apple-silicon-ha probes), one
is a deliberate interface seam (ldap/sso), and two are 0-LOC placeholders
(mes, erp). The `code_qa` private-`ask` CLI — not part of the original seven —
is also real and is the package entrypoint.

## In progress

- Nothing actively in flight on `master`. The last landed work (2026-06-18)
  wired the GitLab connector into the `ask` CLI path. The repo is at a clean
  stopping point pending the next activation trigger.

## Planned-next

Activation is **demand-gated**, not effort-gated. Each item unlocks when its
real target appears:

- **LDAP/AD activation** — implement `LdapAuth.authenticate` against a real
  corporate AD / LDAP, preserving the `AuthBackend` / `AuthResult` contract.
  Design is fully specced: [`docs/ldap-activation-spec.md`](docs/ldap-activation-spec.md).
  *Trigger: a real directory to validate against.*
- **SAML 2.0 / OIDC activation** — implement `SamlAuth` / `OidcAuth` against a
  real IdP. Design specced: [`docs/saml-oidc-spec.md`](docs/saml-oidc-spec.md).
  *Trigger: a specific IdP + metadata source + audience.*
- **Confluence/Jira live validation** — exercise the (already real) connector
  against a real corporate Atlassian instance.
  *Trigger: first hour at any employer running Atlassian.*
- **MES connector** (`mes_connector/`) — placeholder; `list_lots` /
  `get_lot_status` / `post_wafer_event` shape. Schemas are NDA-locked per fab.
  *Trigger: joining 鴻海 / 南亞科 / 台積, or an NDA-covered pilot.*
- **ERP connector** (`erp_connector/`) — placeholder; 鼎新 T100 / B2 / Workflow
  (read-only first). *Trigger: M4 W13-14 (~2026-08) or a first real ERP customer.*
- **Apple Silicon HA, graduated** — promote `apple_silicon_ha` from probes +
  runbook to a full failover trigger once a second M-series host (or a customer
  with two M-series Macs) exists. *Trigger: second M-series node.*
- **WireGuard / OpenVPN fallback routes** (P4.2) — deferred; Tailscale is the
  only demonstrated VPN-aware path. *Trigger: live WireGuard/OpenVPN infra.*

If no demand signal ever arrives, staying a scaffold is an **acceptable
outcome** — the repo already demonstrates that the phantom-mesh architecture
extends cleanly to enterprise on-prem needs.

## Authority

Status conflicts resolve to this file. Forward-looking design intent lives in
[`docs/05-phantom-enterprise.md`](docs/05-phantom-enterprise.md) and the
per-feature specs under `docs/`; where a spec's checkbox list disagrees with the
Shipped section above, **this ROADMAP wins** and the spec is treated as design
intent, not status.
