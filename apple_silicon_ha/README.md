# apple_silicon_ha

**Status:** placeholder module — actual runbook lives in
[`../docs/apple-silicon-ha-deploy.md`](../docs/apple-silicon-ha-deploy.md).

The maintainer already runs phantom-mesh in HA on a personal Apple
Silicon Mac (MacBook Air M-series) — that working pattern is documented
in the runbook. Future Python helpers (cluster health probe, failover
trigger, etc) will land in this package.

Activates: when a second M-series host joins the maintainer's mesh, or a
customer asks for documented HA deploy steps.
