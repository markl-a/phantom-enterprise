"""LDAP escaping helpers for search filters and DN components.

These functions cover the pure string-escaping rules needed before user
input is interpolated into LDAP search filters or distinguished names.
"""

from __future__ import annotations


def escape_filter_value(value: str) -> str:
    """Escape a value for safe interpolation into an LDAP search filter.

    RFC 4515 requires special filter assertion-value characters to be
    represented as backslash-prefixed hexadecimal octets. Backslash is
    escaped first so existing escape-looking input is treated as literal
    user data.
    """

    return (
        value.replace("\\", "\\5c")
        .replace("*", "\\2a")
        .replace("(", "\\28")
        .replace(")", "\\29")
        .replace("\x00", "\\00")
    )


def escape_dn_value(value: str) -> str:
    """Escape a value for use as a single LDAP DN component.

    RFC 4514 requires certain DN value characters to be escaped with a
    leading backslash. Leading ``#`` and leading or trailing spaces are
    also escaped.
    """

    special_chars = {",", "+", '"', "\\", "<", ">", ";", "="}
    escaped: list[str] = []
    last_index = len(value) - 1

    for index, char in enumerate(value):
        if char in special_chars:
            escaped.append(f"\\{char}")
        elif index == 0 and char == "#":
            escaped.append("\\#")
        elif char == " " and (index == 0 or index == last_index):
            escaped.append("\\ ")
        else:
            escaped.append(char)

    return "".join(escaped)


def build_user_filter(template: str, username: str) -> str:
    """Substitute an escaped username into an LDAP search filter template.

    Args:
        template: LDAP filter containing the literal ``"{user}"`` marker.
        username: User-controlled value to escape before substitution.

    Raises:
        ValueError: If the template does not contain ``"{user}"``.
    """

    if "{user}" not in template:
        raise ValueError('LDAP user filter template must contain "{user}"')

    return template.replace("{user}", escape_filter_value(username))
