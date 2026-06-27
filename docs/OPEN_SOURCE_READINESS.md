# Open Source Readiness

Project: `phantom-enterprise`
Current phase: P3 synthetic enterprise knowledge lookup scenario verified
Master plan: `../../PHANTOM-SATELLITES-OPEN-SOURCE-MASTER-PLAN.md`

## Shipped Features

- Enterprise connector package skeleton for private/on-prem contexts.
- CLI entrypoint: `phantom-enterprise = code_qa.cli:main`.
- CLI entrypoint: `phantom-enterprise-demo-loop = code_qa.demo_loop:main`.
- CLI entrypoint: `phantom-enterprise-connector-matrix = code_qa.connector_matrix:main`.
- CLI entrypoint: `phantom-enterprise-knowledge-scenario = code_qa.knowledge_lookup_scenario:main`.
- Help surface verified with `python -m code_qa.cli --help`.
- Subcommands include `ask`, `status`, `demo-loop`, `connector-matrix`, and `knowledge-scenario`.
- Root README points to `docs/phantom-enterprise.md`.
- Root README now includes safe public quickstart and states live connector checks are gated behind `PHANTOM_ENTERPRISE_LIVE=1`.
- Public demo/live-gate/data policy is documented in `docs/PUBLIC_DEMO.md`.
- P2 artifact demo writes a deterministic synthetic local-code Q&A bundle with `manifest.json`, `answer.json`, `evidence.json`, `audit-log.jsonl`, and `summary.md`.
- P2 connector matrix demo writes a deterministic mock connector/permission bundle with `manifest.json`, `connector-matrix.json`, `permission-boundary.json`, `audit-log.jsonl`, and `summary.md`.
- P3 knowledge lookup scenario writes a deterministic permission-aware bundle with `manifest.json`, `knowledge-lookup.json`, `citation-map.json`, `permission-review.json`, `audit-summary.json`, and `summary.md`.
- Test suite baseline after P2 local code-QA additions: `python -m pytest -q` passed with 103 tests and 8 live-gated skips.

## Planned Or Deferred Features

- Broader enterprise knowledge and ops assistant skeleton: connector contracts, citation/evidence, audit log, permission-aware boundaries.
- Production MES/ERP, LDAP/SSO, and real enterprise deployment automation remain deferred unless a private deployment supplies credentials and infrastructure.

## Install And Test Commands

```powershell
python -m pip install -e .[dev]
python -m pytest -q
python -m code_qa.cli --help
python -m code_qa.cli demo-loop --out <bundle-dir>
python -m code_qa.cli connector-matrix --out <bundle-dir>
python -m code_qa.cli knowledge-scenario --out <bundle-dir>
python -m code_qa.cli ask --repo <local-demo-repo> "How does authentication work?"
```

Observed P0 result on 2026-06-26:

```text
97 passed, 8 skipped in 0.13s
```

Skipped tests are live-gated VPN, Gitea, and Atlassian checks requiring `PHANTOM_ENTERPRISE_LIVE=1` and external services.

P2 local code-QA result:

```text
Targeted: 36 passed in 0.09s
Full: 103 passed, 8 skipped in 0.16s
CLI smoke: python -m code_qa.cli demo-loop --out <temp> wrote manifest.json
```

P2 connector matrix result:

```text
Targeted: 71 passed in 0.14s
Full: 109 passed, 8 skipped in 0.21s
Collect-only: 117 tests collected
Packaging: python -m pip install -e . --dry-run --no-deps would install phantom-enterprise-0.1.0
CLI smoke: python -m code_qa.cli connector-matrix --out <temp> wrote manifest.json
```

P3 enterprise knowledge lookup scenario result:

```text
Targeted: 47 passed in 0.27s
Full: 114 passed, 8 skipped in 0.29s
CLI smoke: python -m code_qa.cli knowledge-scenario --out <temp> wrote manifest.json
Agy review: NO BLOCKERS
```

## Fixture And Data Policy

- Public examples must use mock enterprise datasets only.
- No internal URLs, tokens, proprietary documents, enterprise code, issue contents, or customer data may be committed.
- Live connector tests must stay gated behind explicit environment variables.
- Demo-loop audit logs must store metadata, paths, counts, hashes, and artifact names only; they must not store source body text or prompt contents.
- Connector matrix audit logs must store metadata, connector IDs, counts, decisions, and artifact names only; they must not store internal URLs, tokens, secrets, source bodies, issue bodies, or document contents.
- Knowledge lookup scenario audit summaries must remain metadata-only and must not store prompt text, source bodies, internal URLs, customer data, credential values, or live connector payloads.

## Safety And Privacy Risks

- Enterprise connectors can leak private code and documents if misconfigured.
- Auth and LDAP/SSO seams must be described as prototype/planned unless production-ready.
- Query logs must avoid secrets and private content by default.

## Blockers To Next Phase

- None for P3 synthetic enterprise knowledge lookup scenario. Next slice should harden admin audit or permission-aware retrieval semantics without enabling real enterprise connectors by default.

## Evidence

- `pyproject.toml` declares project `phantom-enterprise` and scripts `phantom-enterprise`, `phantom-enterprise-demo-loop`, `phantom-enterprise-connector-matrix`, and `phantom-enterprise-knowledge-scenario`.
- `README.md` points to `docs/phantom-enterprise.md`.
- `README.md` documents deterministic synthetic `demo-loop`, deterministic `connector-matrix`, deterministic `knowledge-scenario`, local-checkout public demo, and `PHANTOM_ENTERPRISE_LIVE=1` live connector gate.
- `docs/PUBLIC_DEMO.md` documents local checkout, `.gitignore` respect, P2 artifact contracts, mock connector matrix, permission boundary, P3 knowledge lookup scenario, live-gated connector policy, and no internal-data public fixtures.
- `docs/KNOWLEDGE_LOOKUP_SCENARIO.md` documents the scenario artifact contract and synthetic-only permission boundary.
- `python -m pytest code_qa/tests -q`: 36 passed.
- `python -m pytest -q`: 103 passed, 8 skipped.
- P2 connector matrix targeted `python -m pytest code_qa/tests/test_connector_matrix_contract.py code_qa/tests/test_open_source_contract.py code_qa/tests/test_demo_loop_contract.py code_qa/tests/test_ask.py code_qa/tests/test_status.py on_prem_gitlab/tests/test_connector_hermetic.py confluence_jira/tests/test_atlassian_hermetic.py vpn_aware_routing/tests/test_router_hermetic.py -q`: 71 passed.
- P2 connector matrix final `python -m pytest -q`: 109 passed, 8 skipped.
- P2 connector matrix collect-only `python -m pytest --collect-only -q`: 117 tests collected.
- P2 connector matrix packaging `python -m pip install -e . --dry-run --no-deps`: would install `phantom-enterprise-0.1.0`.
- `python -m code_qa.cli --help`: help OK.
- `python -m code_qa.connector_matrix --help`: help OK.
- `python -m code_qa.cli demo-loop --out <temp>`: wrote schema version 1 manifest with `synthetic_only=true`, `live_connectors=false`, `external_network=false`, and `local_llm_required=false`.
- `python -m code_qa.cli connector-matrix --out <temp>`: wrote schema version 1 manifest with `synthetic_only=true`, `live_connectors=false`, `external_network=false`, `credentials_required=false`, and `permission_boundary=mock_metadata_only`.
- P3 knowledge lookup scenario targeted `python -m pytest code_qa/tests/test_knowledge_lookup_scenario_contract.py code_qa/tests/test_open_source_contract.py code_qa/tests/test_connector_matrix_contract.py code_qa/tests/test_demo_loop_contract.py code_qa/tests/test_ask.py code_qa/tests/test_status.py -q`: 47 passed.
- P3 knowledge lookup scenario final `python -m pytest -q`: 114 passed, 8 skipped.
- `python -m code_qa.cli knowledge-scenario --out <temp>`: wrote deterministic scenario manifest with `mode=synthetic_enterprise_knowledge_lookup_scenario`, `synthetic_only=true`, `live_connectors=false`, `external_network=false`, `credentials_required=false`, `permission_boundary=mock_metadata_only`, 4 citations, and mock sources `mock_code,mock_docs,mock_issues,mock_runbooks`.
- `agy` P3 knowledge lookup scenario reviewer result: `NO BLOCKERS` for live connector/network use, credential or internal URL leakage, source body or prompt retention in metadata audit, production connector overclaiming, permission boundary mismatch, nondeterminism, docs/CLI/script/test mismatch, demo-loop regression, or connector-matrix regression.
- `agy` reviewer result: no P2 blockers for live connector/network use, local LLM requirement, audit-log retention, citation/evidence contract, determinism, docs/tests mismatch, or live connector gates.
- `agy` P2 connector matrix reviewer result: `NO BLOCKERS` for live connector/network drift, credential/internal URL leakage, raw audit-log retention, docs/tests/CLI mismatch, nondeterminism, production connector overclaiming, demo-loop regression, or `PHANTOM_ENTERPRISE_LIVE=1` gate drift.
- Notes:
  - `status` is documented as an environment probe, not the default public smoke path.
  - Local `ask` requires a local `phantom` binary; CI tests stub the LLM call and verify local context/citation behavior without external services.

## P4 Release-Prep Slice 1

Status: governance baseline added; this does not mark the project release-ready.

Evidence:
- `CONTRIBUTING.md` defines the contribution workflow, required test command, readiness-doc update rule, and no-private-data/no-credentials boundary.
- `SECURITY.md` defines private vulnerability reporting, supported version scope, 7-day acknowledgement target, and safe report contents.
- `python -m pytest code_qa/tests/test_release_prep_contract.py -q`: 1 passed.
- `python -m pytest -q`: 115 passed, 8 skipped.

Remaining P4 work: full release gate, final docs audit, package metadata audit, release notes, tag plan, and maintainer sign-off.

## P4 Release-Prep Slice 2

Status: final release gate checklist added; this does not mark the project release-ready.

Evidence:
- `CHANGELOG.md` records the unreleased governance/release-checklist work and points back to readiness evidence.
- `docs/RELEASE_CHECKLIST.md` documents final tests, dependency/license review, secret/private-data scan, known limitations, and manual maintainer approval.
- `python -m pytest code_qa/tests/test_release_prep_contract.py -q`: 2 passed.
- `python -m pytest -q`: 116 passed, 8 skipped.

Remaining P4 work: execute final scans, complete dependency/license review, finalize release notes, and record manual maintainer approval.

## P4 Release-Prep Slice 3

Status: final scan and direct dependency/license audit recorded; not release-ready.

Evidence:
- `docs/FINAL_RELEASE_AUDIT.md` records scan scope, `high_conf_secret_hits=0`, direct dependency/license review, and remaining release blockers.
- Direct release-scope dependency metadata reviewed: `requests==2.34.2` Apache-2.0.
- `python -m pytest code_qa/tests/test_release_prep_contract.py -q`: 3 passed.
- `python -m pytest -q`: 117 passed, 8 skipped.

Remaining P4 work: release notes finalization, tag plan, final maintainer approval, and separate production connector/NDA/credential review.

## P4 Release-Prep Slice 4

Status: maintainer approval recorded, conductor sign-off complete, and release-candidate tag created.

Evidence:
- `docs/RELEASE_NOTES.md` records public release-candidate notes, known limitations, and verification pointers.
- `docs/TAG_PLAN.md` records proposed tag `v0.1.0-alpha.0`, required approval-before-tag sequence, and rollback steps.
- `docs/PUBLIC_RELEASE_APPROVAL.md` records `Status: approved` with approver, approval date, and approved tag.
- Conductor root approval packet `PHANTOM-SATELLITES-PUBLIC-RELEASE-APPROVAL.md` records all ten candidate tags as approved.
- `.github/workflows/ci.yml` runs an explicit `release-prep gate` against `code_qa/tests/test_release_prep_contract.py`.
- `python -m pytest code_qa/tests/test_release_prep_contract.py -q`: 5 passed.
- `python -m pytest -q`: 119 passed, 8 skipped.

Remaining P4 work: none for the approved release-candidate tag.

## P4 Release-Prep Slice 5

Status: public release gate hardened and verified for package metadata, PEP 440 alpha versioning, CI installability, wheel build, ruff, public synthetic enterprise smoke paths, and current release evidence.

Evidence:
- `pyproject.toml` now uses PEP 440 alpha version `0.1.0a0`, matching the approved `v0.1.0-alpha.0` release-candidate tag.
- `pyproject.toml` includes public package classifiers, GitHub project URLs, and a `dev` extra for release verification tooling.
- `.github/workflows/ci.yml` installs `.[dev]`, builds a wheel with `python -m pip wheel . --no-deps -w dist-smoke`, runs ruff, runs the full pytest suite, runs deterministic `demo-loop`, `connector-matrix`, and `knowledge-scenario` smoke paths, and runs the release-prep gate.
- `CHANGELOG.md` now records `0.1.0-alpha.0 - 2026-06-27` as the approved release candidate instead of the stale not-release-ready status.
- `docs/FINAL_RELEASE_AUDIT.md` records current install, wheel, CLI help, synthetic demo-loop, connector-matrix, knowledge-scenario, dependency/license, ruff, pytest, and high-confidence secret scan evidence.
- `python -m pytest code_qa\tests\test_packaging.py code_qa\tests\test_release_prep_contract.py -q`: 8 passed.
- `python -m pip install -e . --dry-run --no-deps`: editable metadata OK; would install `phantom-enterprise-0.1.0a0`.
- `python -m pip wheel . --no-deps -w <temp>`: built `phantom_enterprise-0.1.0a0-py3-none-any.whl`.
- `python -m code_qa.cli --help`: help OK.
- `python -m code_qa.cli demo-loop --out <bundle>`: wrote synthetic local-code Q&A manifest with `synthetic_only=true`, `live_connectors=false`, `external_network=false`, and `local_llm_required=false`.
- `python -m code_qa.cli connector-matrix --out <bundle>`: wrote mock connector matrix manifest with `synthetic_only=true`, `live_connectors=false`, `external_network=false`, `credentials_required=false`, and `permission_boundary=mock_metadata_only`.
- `python -m code_qa.cli knowledge-scenario --out <scenario>`: wrote synthetic enterprise lookup manifest with `synthetic_only=true`, `live_connectors=false`, `external_network=false`, `credentials_required=false`, `local_llm_required=false`, and `permission_boundary=mock_metadata_only`.
- Current dependency/license review: `requests==2.32.5`, Apache-2.0.
- `python -m ruff check .`: all checks passed.
- High-confidence secret scan: `high_conf_secret_hits=0`.
- `python -m pytest -q`: 122 passed, 8 skipped. The skipped tests are live-gated and require `PHANTOM_ENTERPRISE_LIVE=1` plus external VPN, Gitea, or Atlassian services.

Remaining P4 work: none for the current approved public source release candidate.
