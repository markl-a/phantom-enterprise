# VPN-Mesh Demo (manual / not headless)

## Scope

This is a manual runbook for demonstrating the existing VPN-aware routing and
on-prem Git connector path. It is not an automated test and must not be wired
into CI.

The demo uses existing code:

- `vpn_aware_routing.router.tailscale_route(hostname)`.
- `vpn_aware_routing.router.list_peers()`.
- `on_prem_gitlab` Gitea/GitLab connector package.
- `phantom-enterprise status`.
- `phantom-enterprise ask --repo ...`.

The current routing implementation shells out to `tailscale status --json`,
parses peers, and resolves a short host name to a tailnet IP. If Tailscale is
missing, unavailable, or the peer is absent, it returns no route instead of
crashing.

## Prerequisites

- Tailscale CLI installed on the demo machine.
- User logged in to the intended tailnet.
- A live on-prem Gitea or GitLab instance reachable on the tailnet.
- A repository visible to the demo user or token.
- `phantom-enterprise` installed from this checkout or available on `PATH`.
- Optional personal access token for private repository access.

Environment variables used by the existing connector and CLI:

```bash
export GITEA_BASE_URL="http://<tailnet-host-or-ip>:3000"
export GITEA_TOKEN="<optional-token>"
```

For self-hosted GitLab connector checks, the lower-level module uses:

```bash
export GITLAB_BASE_URL="http://<tailnet-host-or-ip>"
# The token is passed explicitly (e.g. via --token / token=); there is no GITLAB_TOKEN env var.
```

The `ask` CLI path is currently Gitea-oriented. Use `--base-url`,
`--token`, and `--gitea` when demonstrating a repo addressed as
`owner/repo`.

## Step 1: Confirm Tailscale State

Run:

```bash
tailscale status
tailscale status --json
```

Expected result:

- The local node appears in the status output.
- The on-prem Git host appears as an online peer.
- The peer has a `100.x.y.z` tailnet IP.

If this fails, stop the demo. The remaining commands require a live tailnet.

## Step 2: Resolve a Tailnet Peer in Python

Replace `z13` with the short host name of the on-prem Git machine:

```bash
python -c "from vpn_aware_routing.router import tailscale_route; print(tailscale_route('z13'))"
```

Expected result:

```text
100.x.y.z
```

To list all peers as route objects:

```bash
python -c "from vpn_aware_routing.router import list_peers; [print(p) for p in list_peers()]"
```

Expected result:

- At least one `RouteResult(hostname=..., ip='100.x.y.z', online=True, os=...)`.
- The Git host appears with the host name expected by `tailscale_route`.

If `tailscale_route` prints `None`, check the short host name and confirm the
peer is visible in `tailscale status --json`.

## Step 3: Point the Connector at On-Prem Git

For Gitea:

```bash
export GITEA_BASE_URL="http://z13:3000"
export GITEA_TOKEN="<optional-token>"
```

Or use the resolved tailnet IP:

```bash
export GITEA_BASE_URL="http://100.x.y.z:3000"
export GITEA_TOKEN="<optional-token>"
```

Smoke-check the connector:

```bash
python -c "from on_prem_gitlab import list_repos; print(list_repos(token=None, limit=5))"
```

For a private Gitea instance:

```bash
python -c "import os; from on_prem_gitlab import list_repos; print(list_repos(token=os.environ.get('GITEA_TOKEN'), limit=5))"
```

Expected result:

- A list of repository objects.
- An empty list is acceptable if the instance is reachable but no public repos
  are visible.
- A `GiteaUnreachable` error means the host, port, token, or route is wrong.

## Step 4: Run CLI Status

Run:

```bash
phantom-enterprise status
```

Optional JSON form:

```bash
phantom-enterprise status --json
```

Expected result:

- Tailscale check reports available when the CLI can inspect peers.
- Git readiness check succeeds when `GITEA_BASE_URL` reaches the instance.
- Failures should be explicit rather than stack traces.

This status command is useful before a live demo because it validates the same
host assumptions used by `ask`.

## Step 5: Ask Against an On-Prem Repo

Use a Gitea-style `owner/repo` reference:

```bash
phantom-enterprise ask \
  --repo owner/repo \
  "Summarize the project structure" \
  --base-url "$GITEA_BASE_URL" \
  --token "$GITEA_TOKEN" \
  --gitea
```

For public repos, omit the token:

```bash
phantom-enterprise ask \
  --repo owner/repo \
  "What are the main modules?" \
  --base-url "$GITEA_BASE_URL" \
  --gitea
```

Expected result:

- The CLI fetches repository file contents through the on-prem connector.
- The answer is based on private repo context, not a public network clone.
- If the host is unreachable, the CLI should report an on-prem Gitea
  reachability error with a local-repo fallback hint.

## Manual Demo Boundaries

This cannot run in CI or in a headless hermetic test job. It requires:

- A live tailnet session.
- A logged-in Tailscale identity.
- A reachable host that exists only in that tailnet or private network.
- A live Gitea/GitLab service and repository state.
- Optional private tokens that must not be stored in the repo.

Therefore this file is a documented runbook, not an automated test. Automated
tests should continue to stub subprocess, network, and connector calls.

## Troubleshooting

- `tailscale: command not found`: install the Tailscale CLI on the demo host.
- `tailscale_route(...)` returns `None`: use the peer short host name, not the
  full MagicDNS name, or confirm the peer is online.
- `GiteaUnreachable`: verify `GITEA_BASE_URL`, port, token, and tailnet route.
- Empty repo list: check whether the instance has public repos or provide a
  token with repository visibility.
- `phantom-enterprise` not found: install the package from this checkout or run
  the module through the active virtual environment.

## Remaining / not yet built

WireGuard and OpenVPN fallback stubs from P4.2 are deferred. They need live VPN
infrastructure to validate route discovery, peer identity, and failure behavior.
Until that infrastructure exists, Tailscale remains the only demonstrated
VPN-aware route path.
