"""Authentication backend interfaces for phantom-mesh enterprise SSO.

Three protocols are stubbed: LDAP, SAML 2.0, and OIDC. Each subclass
documents its expected inputs/outputs so the real implementation can
slot in without breaking callers.

All concrete classes raise ``NotImplementedError`` until validated
against a real corporate IdP. This is intentional — see project README
for the "no enterprise customer yet" rationale.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class AuthResult:
    """Result of a successful authentication.

    Attributes:
        subject: Stable unique identifier (e.g. LDAP DN, SAML NameID,
            OIDC ``sub`` claim).
        email: User's primary email if available.
        groups: Group / role memberships used for phantom-mesh RBAC.
        raw: Backend-specific raw payload for debugging.
    """

    subject: str
    email: Optional[str] = None
    groups: tuple[str, ...] = field(default_factory=tuple)
    raw: dict = field(default_factory=dict)


class AuthBackend(ABC):
    """Abstract authentication backend.

    All concrete backends in this package implement the same shape so
    the phantom-mesh ``serve`` process can swap them via config without
    code changes.
    """

    @abstractmethod
    def authenticate(self, username: str, credential: str) -> AuthResult:
        """Validate the given credential and return an :class:`AuthResult`.

        Args:
            username: User-supplied identifier (UPN, email, sAMAccountName,
                or SAML/OIDC equivalent).
            credential: Password, assertion XML, or ID-token depending on
                backend. Treat as opaque secret material.

        Returns:
            AuthResult: Subject + groups on success.

        Raises:
            NotImplementedError: Until a real IdP target is wired up.
            PermissionError: On authentication failure (in real impl).
        """
        raise NotImplementedError


class LdapAuth(AuthBackend):
    """LDAP simple-bind backend.

    Expected config (passed to ``__init__`` in real impl): server URI,
    bind DN template, search base, group attribute (``memberOf``).
    """

    def __init__(self, server_uri: str = "", bind_dn_template: str = "") -> None:
        self.server_uri = server_uri
        self.bind_dn_template = bind_dn_template

    def authenticate(self, username: str, credential: str) -> AuthResult:
        raise NotImplementedError(
            "LdapAuth not implemented — awaiting target AD/LDAP server. "
            "See phantom-enterprise/docs for activation runbook."
        )


class SamlAuth(AuthBackend):
    """SAML 2.0 SP-initiated assertion validator.

    ``credential`` is the base64-encoded SAML response from the IdP.
    """

    def __init__(self, idp_metadata_url: str = "", sp_entity_id: str = "") -> None:
        self.idp_metadata_url = idp_metadata_url
        self.sp_entity_id = sp_entity_id

    def authenticate(self, username: str, credential: str) -> AuthResult:
        raise NotImplementedError(
            "SamlAuth not implemented — awaiting target IdP metadata."
        )


class OidcAuth(AuthBackend):
    """OpenID Connect ID-token validator.

    ``credential`` is a JWT issued by the configured OP.
    """

    def __init__(self, issuer: str = "", client_id: str = "") -> None:
        self.issuer = issuer
        self.client_id = client_id

    def authenticate(self, username: str, credential: str) -> AuthResult:
        raise NotImplementedError(
            "OidcAuth not implemented — awaiting target OIDC issuer."
        )
