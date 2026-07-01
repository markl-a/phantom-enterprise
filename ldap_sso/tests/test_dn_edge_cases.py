"""RFC 4514 edge-case coverage for `escape_dn_value` (leading '#', spaces)."""

from __future__ import annotations

import pytest

from ldap_sso.filters import escape_dn_value


def test_escape_dn_value_escapes_leading_hash() -> None:
    assert escape_dn_value("#admin") == "\\#admin"


def test_escape_dn_value_escapes_leading_and_trailing_space() -> None:
    assert escape_dn_value(" bob ") == "\\ bob\\ "


@pytest.mark.parametrize(
    "value, expected",
    [
        ("ad#min", "ad#min"),
        ("bob middle name", "bob middle name"),
    ],
)
def test_escape_dn_value_leaves_middle_hash_and_space_unescaped(
    value: str, expected: str
) -> None:
    assert escape_dn_value(value) == expected
