"""Shape tests: confirm the auth backends instantiate and raise NotImplementedError.

These tests prove the *interface contract* is stable so consumers can
code against it now and the real implementation drops in later.
"""

import pytest

from ldap_sso.auth import AuthBackend, LdapAuth, SamlAuth, OidcAuth, AuthResult


def test_authresult_is_immutable_dataclass():
    r = AuthResult(subject="cn=mark,dc=corp", email="m@corp.tld", groups=("eng",))
    assert r.subject == "cn=mark,dc=corp"
    assert r.email == "m@corp.tld"
    assert r.groups == ("eng",)
    with pytest.raises(Exception):  # frozen dataclass
        r.subject = "other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "cls,kwargs",
    [
        (LdapAuth, {"server_uri": "ldaps://ad.corp.tld", "bind_dn_template": "uid={u},ou=people"}),
        (SamlAuth, {"idp_metadata_url": "https://idp/metadata.xml", "sp_entity_id": "phantom-mesh"}),
        (OidcAuth, {"issuer": "https://idp", "client_id": "phantom-mesh"}),
    ],
)
def test_backend_instantiates_and_is_authbackend(cls, kwargs):
    backend = cls(**kwargs)
    assert isinstance(backend, AuthBackend)


@pytest.mark.parametrize("cls", [LdapAuth, SamlAuth, OidcAuth])
def test_backend_raises_not_implemented(cls):
    backend = cls()
    with pytest.raises(NotImplementedError):
        backend.authenticate("user", "secret")
