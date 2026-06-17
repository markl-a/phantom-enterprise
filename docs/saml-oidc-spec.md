# SAML 2.0 & OIDC Spec

## Scope

This document specifies the activation design for the existing SAML and OIDC
authentication stubs in `ldap_sso/auth.py`.

The current code already provides:

- `AuthBackend.authenticate(username, credential) -> AuthResult`.
- `AuthResult(subject, email, groups, raw)`.
- `SamlAuth(idp_metadata_url="", sp_entity_id="")`.
- `OidcAuth(issuer="", client_id="")`.

Both concrete classes intentionally raise `NotImplementedError` until a real
identity provider target exists. The real implementation must preserve the
same interface so callers can swap backends by configuration.

## Shared Contract

All enterprise SSO backends return the same result shape:

```python
from ldap_sso.auth import AuthBackend, AuthResult


class SamlAuth(AuthBackend):
    def authenticate(self, username: str, credential: str) -> AuthResult:
        ...


class OidcAuth(AuthBackend):
    def authenticate(self, username: str, credential: str) -> AuthResult:
        ...
```

`username` is advisory for SAML and OIDC. It may be used for logging,
pre-selected login hints, or consistency checks, but the authenticated identity
must come from the validated assertion or token.

`credential` is protocol-specific secret material:

- SAML: base64-encoded SAML Response from the IdP.
- OIDC: ID token JWT issued by the configured OpenID Provider.

## SamlAuth Contract

`SamlAuth.authenticate(username, credential)` validates a base64 SAML Response
and maps the assertion into `AuthResult`.

Required configuration:

- `idp_metadata_url`: source for IdP entity ID, SSO endpoint, and signing certs.
- `sp_entity_id`: service provider audience expected in the assertion.
- Optional: accepted clock skew, replay cache adapter, group attribute names.

Validation sequence:

1. Base64-decode `credential` into XML.
2. Parse XML with external entity resolution disabled.
3. Load IdP metadata and signing certificates.
4. Validate the SAML Response or Assertion signature against the IdP cert.
5. Validate `Conditions`, including `NotBefore` and `NotOnOrAfter`.
6. Validate `AudienceRestriction` equals configured `sp_entity_id`.
7. Validate `Recipient` and `Destination` if ACS URL config is present.
8. Check assertion ID against a replay cache.
9. Extract `NameID` as `AuthResult.subject`.
10. Extract attribute statements into `email`, `groups`, and `raw`.

Mapping example:

```python
AuthResult(
    subject=name_id,
    email=attributes.get("email") or attributes.get("mail"),
    groups=tuple(attributes.get("groups", ())),
    raw={
        "backend": "saml",
        "issuer": issuer,
        "assertion_id": assertion_id,
    },
)
```

Group mapping should support configurable claim names such as `groups`,
`memberOf`, or an IdP-specific URI claim. Preserve group values as strings.

## OidcAuth Contract

`OidcAuth.authenticate(username, credential)` validates an OIDC ID token JWT and
maps the token claims into `AuthResult`.

Required configuration:

- `issuer`: expected `iss` claim and source for discovery metadata.
- `client_id`: expected `aud` claim.
- Optional: accepted clock skew, expected nonce, replay cache adapter.

Validation sequence:

1. Parse the JWT header and claims without trusting them yet.
2. Resolve OpenID Provider metadata from `issuer`.
3. Fetch and cache the issuer JWKS.
4. Select the signing key by `kid`.
5. Verify JWT signature and allowed algorithm.
6. Validate `iss` equals configured `issuer`.
7. Validate `aud` contains configured `client_id`.
8. Validate `exp`, `iat`, and optional `nbf` with bounded clock skew.
9. Validate `nonce` when the login flow supplied one.
10. Check `jti` or token hash against a replay cache when available.
11. Map `sub` to `AuthResult.subject`.
12. Map `email` and `groups` claims into the result.

Mapping example:

```python
AuthResult(
    subject=claims["sub"],
    email=claims.get("email"),
    groups=tuple(claims.get("groups", ())),
    raw={
        "backend": "oidc",
        "issuer": claims["iss"],
        "kid": jwt_header.get("kid"),
    },
)
```

If `groups` is a string, normalize it to a one-item tuple. If it is absent,
return an empty tuple.

## Failure Modes

SAML failures:

| Condition | Required exception | Notes |
| --- | --- | --- |
| Expired assertion | `PermissionError` | `NotOnOrAfter` is in the past. |
| Assertion not yet valid | `PermissionError` | `NotBefore` exceeds allowed skew. |
| Bad signature | `PermissionError` | Do not accept unsigned assertions. |
| Audience mismatch | `PermissionError` | Must equal `sp_entity_id`. |
| Replay detected | `PermissionError` | Assertion ID already consumed. |
| IdP metadata unavailable | `ConnectionError` | Network/config dependency failed. |
| Malformed XML/base64 | `PermissionError` | Treat as invalid credential. |
| Current stub behavior | `NotImplementedError` | Present behavior in `ldap_sso/auth.py`. |

OIDC failures:

| Condition | Required exception | Notes |
| --- | --- | --- |
| Expired token | `PermissionError` | `exp` is in the past. |
| Bad signature | `PermissionError` | Key or signature validation failed. |
| Audience mismatch | `PermissionError` | `aud` must contain `client_id`. |
| Issuer mismatch | `PermissionError` | `iss` must equal configured issuer. |
| Nonce mismatch | `PermissionError` | Required for browser login flows. |
| Replay detected | `PermissionError` | Reused `jti` or token hash. |
| JWKS unavailable | `ConnectionError` | Issuer dependency failed. |
| Malformed JWT | `PermissionError` | Treat as invalid credential. |
| Current stub behavior | `NotImplementedError` | Present behavior in `ldap_sso/auth.py`. |

## Security Notes

- Always validate audience. A valid token for another client is not valid here.
- Always validate issuer. Do not trust arbitrary JWKS URLs from token headers.
- Reject unsigned SAML assertions and unsigned JWTs.
- Restrict JWT algorithms to the issuer metadata policy; never accept `none`.
- Use a small clock skew window, for example 60 to 120 seconds.
- Use a replay cache for SAML assertion IDs and OIDC `jti` or token hashes.
- Disable XML external entity resolution for SAML parsing.
- Do not log raw assertions, raw ID tokens, passwords, or bearer tokens.
- Keep `AuthResult.raw` diagnostic but non-secret.
- Rotate and refresh IdP metadata/JWKS with bounded cache lifetimes.

## Implementation Status

`SamlAuth.authenticate` and `OidcAuth.authenticate` currently raise
`NotImplementedError` by design. That is the correct behavior until there is a
specific IdP, metadata source, audience, and replay-cache target to validate
against.

Activation should add protocol libraries, hermetic tests for validation and
failure mapping, and one manual IdP integration runbook. The caller contract in
`AuthBackend` and `AuthResult` should not change.
