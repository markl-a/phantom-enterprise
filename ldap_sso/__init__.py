"""LDAP / SAML / OIDC authentication connectors (interface stubs).

Real implementations are deferred until a customer or employing company
provides a target IdP (corp AD, Okta, Azure AD, etc).
"""

from .auth import AuthBackend, LdapAuth, SamlAuth, OidcAuth

__all__ = ["AuthBackend", "LdapAuth", "SamlAuth", "OidcAuth"]
