# LDAP/AD Activation Spec

## Scope

This document specifies how to activate the existing LDAP authentication stub in
`ldap_sso/auth.py` without changing the caller-facing authentication contract.

The current code already defines:

- `AuthBackend`, an abstract base class with `authenticate(username, credential)`.
- `AuthResult(subject, email, groups, raw)`, the stable success result shape.
- `LdapAuth`, currently a stub that raises `NotImplementedError`.
- `ldap_sso/filters.py`, with RFC 4515/4514 escaping helpers:
  `escape_filter_value`, `escape_dn_value`, and `build_user_filter`.

The activation work should implement `LdapAuth.authenticate` only after a real
LDAP or Active Directory target is available for validation.

## LdapConfig Shape

Use an explicit config object rather than growing positional constructor
arguments. The existing `LdapAuth(server_uri="", bind_dn_template="")`
constructor can remain backward-compatible and be expanded to accept this shape.

```python
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LdapConfig:
    server_uri: str                    # Required, prefer "ldaps://ldap.corp:636"
    bind_dn_template: str              # Example: "uid={user},ou=people,dc=corp"
    search_base: str                   # Example: "ou=people,dc=corp"
    user_filter_template: str = "(uid={user})"
    group_attr: str = "memberOf"
    use_start_tls: bool = False
    timeout: float = 5.0
    ca_cert_path: Optional[str] = None
```

Field requirements:

- `server_uri` must be an LDAP URI. Production should prefer `ldaps://`.
- `bind_dn_template` identifies the DN used for simple bind.
- `search_base` scopes the post-bind lookup for user attributes and groups.
- `user_filter_template` must include the literal `{user}` marker.
- `group_attr` defaults to `memberOf`, matching common AD deployments.
- `use_start_tls` applies only when using `ldap://`; do not combine with
  `ldaps://` unless the selected LDAP library explicitly supports that mode.
- `timeout` applies to connection and operation timeouts.
- `ca_cert_path` pins the corporate CA bundle when TLS uses a private PKI.

## Auth Contract

The backend must preserve the abstract interface already present in
`ldap_sso/auth.py`:

```python
from ldap_sso.auth import AuthBackend, AuthResult


class LdapAuth(AuthBackend):
    def authenticate(self, username: str, credential: str) -> AuthResult:
        ...
```

Inputs:

- `username`: user-supplied login name, UPN, email, or `sAMAccountName`.
- `credential`: the password for LDAP simple bind.

Success returns:

- `AuthResult.subject`: the canonical LDAP DN from the directory search result.
- `AuthResult.email`: primary mail attribute if available.
- `AuthResult.groups`: tuple of group names or DNs from `group_attr`.
- `AuthResult.raw`: minimal backend payload for diagnostics, excluding secrets.

Example result:

```python
AuthResult(
    subject="uid=alice,ou=people,dc=corp",
    email="alice@corp.example",
    groups=("cn=engineering,ou=groups,dc=corp",),
    raw={"backend": "ldap", "server_uri": "ldaps://ldap.corp:636"},
)
```

## Simple-Bind Flow

The implementation should follow this sequence:

1. Validate config at construction time.
2. Build the bind DN using `bind_dn_template` and an escaped DN component.
3. Connect to `server_uri` with TLS verification enabled.
4. If configured, perform StartTLS before binding.
5. Simple-bind with the derived bind DN and `credential`.
6. Build the user search filter with `build_user_filter`.
7. Search `search_base` for one matching user entry.
8. Read the entry DN, mail attribute, and configured group attribute.
9. Return `AuthResult(subject=dn, email=email, groups=groups, raw=raw)`.

Sketch:

```python
from ldap_sso.auth import AuthResult
from ldap_sso.filters import build_user_filter, escape_dn_value


def authenticate(self, username: str, credential: str) -> AuthResult:
    bind_dn = self.config.bind_dn_template.format(user=escape_dn_value(username))
    user_filter = build_user_filter(self.config.user_filter_template, username)

    # Pseudocode: exact calls depend on the selected LDAP client library.
    conn = ldap_connect(self.config.server_uri, timeout=self.config.timeout)
    if self.config.use_start_tls:
        conn.start_tls(ca_cert_path=self.config.ca_cert_path)
    conn.simple_bind(bind_dn, credential)
    entry = conn.search_one(
        base=self.config.search_base,
        filter=user_filter,
        attributes=("dn", "mail", self.config.group_attr),
    )
    if entry is None:
        raise PermissionError("LDAP user not found")

    return AuthResult(
        subject=entry.dn,
        email=entry.attributes.get("mail"),
        groups=tuple(entry.attributes.get(self.config.group_attr, ())),
        raw={"backend": "ldap", "dn": entry.dn},
    )
```

## Filter Escaping

LDAP filters are injection-sensitive. A username such as `*)(uid=*` can break out
of a naive filter template and turn `(uid={user})` into a broad match.

Always use `build_user_filter` from `ldap_sso/filters.py`, which delegates to
`escape_filter_value` and applies RFC 4515 escaping for `*`, `(`, `)`,
backslash, and NUL.

```python
from ldap_sso.filters import build_user_filter


malicious = "*)(uid=*"
safe_filter = build_user_filter("(uid={user})", malicious)

assert safe_filter == "(uid=\\2a\\29\\28uid=\\2a)"
```

The resulting filter treats every character as literal user data. It does not
create a wildcard search and does not add a second `uid` predicate.

DN interpolation is a separate context. Use `escape_dn_value` when placing a
username inside `bind_dn_template`; use `build_user_filter` only for search
filters.

## Failure Modes

| Condition | Required exception | Notes |
| --- | --- | --- |
| Bad credential | `PermissionError` | Do not reveal whether the user exists. |
| User not found | `PermissionError` | Keep the same class as bad credentials. |
| Server down or timeout | `ConnectionError` | Include target URI, not the password. |
| TLS validation failure | `ConnectionError` | Treat as connection failure. |
| Multiple user entries | `PermissionError` | Ambiguous identity must not authenticate. |
| Invalid config | `ValueError` | Prefer constructor-time failure. |
| Current stub behavior | `NotImplementedError` | Present behavior in `ldap_sso/auth.py`. |

## Activation Checklist

- Choose the LDAP library and pin it in project dependencies.
- Add `LdapConfig` and keep `LdapAuth` constructor backward-compatible.
- Validate `server_uri`, `bind_dn_template`, `search_base`, and filter template.
- Enforce TLS verification for `ldaps://` and StartTLS.
- Use `escape_dn_value` for bind DN interpolation.
- Use `build_user_filter` for user searches.
- Normalize group values into `tuple[str, ...]`.
- Exclude passwords, tokens, and full server responses from `AuthResult.raw`.
- Add hermetic tests for escaping, failure mapping, and result mapping.
- Add one manual activation runbook for a real corporate LDAP or AD target.

## Compatibility

No caller should need to know whether the backend is LDAP, SAML, or OIDC.
Activation must preserve `AuthBackend.authenticate` and return the existing
`AuthResult` dataclass from `ldap_sso/auth.py`.

Until a real directory is configured, `LdapAuth.authenticate` should continue to
raise `NotImplementedError`. Once activated, callers should only observe the
documented transition from `NotImplementedError` to `AuthResult`,
`PermissionError`, or `ConnectionError`.
