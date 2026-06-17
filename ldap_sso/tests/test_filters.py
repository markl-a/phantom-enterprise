"""Contract tests for LDAP filter and DN escaping helpers."""

from __future__ import annotations

import pytest

from ldap_sso.filters import build_user_filter, escape_dn_value, escape_filter_value


@pytest.mark.parametrize(
    "value, expected",
    [
        ("*", "\\2a"),
        ("(", "\\28"),
        (")", "\\29"),
        ("\\", "\\5c"),
        ("\x00", "\\00"),
        ("alice", "alice"),
    ],
)
def test_escape_filter_value_handles_special_chars(value: str, expected: str) -> None:
    assert escape_filter_value(value) == expected


def test_escape_filter_value_neutralises_classic_injection() -> None:
    escaped = escape_filter_value("*)(uid=*")

    assert escaped == "\\2a\\29\\28uid=\\2a"
    assert "*" not in escaped
    assert "(" not in escaped
    assert ")" not in escaped


def test_build_user_filter_substitutes_escaped_username() -> None:
    assert build_user_filter("(uid={user})", "a)(b") == "(uid=a\\29\\28b)"


def test_build_user_filter_requires_user_placeholder() -> None:
    with pytest.raises(ValueError):
        build_user_filter("(uid=alice)", "alice")


def test_escape_dn_value_escapes_special_chars() -> None:
    assert escape_dn_value("Smith, Alice+Ops\\QA") == "Smith\\, Alice\\+Ops\\\\QA"


@pytest.mark.parametrize(
    "value, expected",
    [
        ("\x00", "\\00"),
        ("\x1f", "\\1f"),
        ("\x7f", "\\7f"),
    ],
)
def test_escape_dn_value_escapes_control_chars_as_hex(
    value: str, expected: str
) -> None:
    assert escape_dn_value(value) == expected


def test_escape_dn_value_escapes_embedded_null_byte() -> None:
    escaped = escape_dn_value("admin\x00,dc=evil")

    assert escaped == "admin\\00\\,dc\\=evil"
    assert "\x00" not in escaped
