import datetime
import hashlib
import ipaddress
import re
import secrets
import string
import uuid

from werkzeug.datastructures import Headers

from .errors import InvalidIdentifierError


def parse_token(headers: Headers) -> str:
    """Retrieve the authentication token from the "Authorization" header.

    If the header is missing or the token is invalid, returns an empty string.

    Args:
        headers (Headers): The headers to parse.

    Returns:
        The authentication token.
    """
    value: str = next(
        (value for key, value in headers.items(lower=True) if key == "authorization"), ""
    )

    auth_header_parts_count = 2
    parts = value.strip().split(" ", auth_header_parts_count)
    if len(parts) == auth_header_parts_count:
        prefix = parts[0].lower()
        token: str = parts[1]

        allowed_chars = string.ascii_letters + string.digits + "-_.="
        if prefix == "bearer" and all(c in allowed_chars for c in token):
            return token

    return ""


def generate_token() -> str:
    """Returns a sha256 hash of a random string of hex numbers."""
    token = secrets.token_hex(16)
    return sha256(token)


def sha256(data: str) -> str:
    """Returns a sha256 hash of the input string."""
    return hashlib.sha256(data.encode()).hexdigest()


def timestamp() -> datetime.datetime:
    """Returns the current date using the default timezone."""
    return datetime.datetime.now()


def as_uuid(id: str | uuid.UUID) -> uuid.UUID:
    """Return an UUID object from the the input value.

    Args:
        id (str | uuid.UUID): The input to convert.

    Returns:
        The UUID object.

    Raises:
        InvalidIdentifierError: Raised when the id has an invalid format.
    """
    if isinstance(id, uuid.UUID):
        return id
    else:
        try:
            return uuid.UUID(id)
        except ValueError as e:
            raise InvalidIdentifierError() from e


def is_host_valid(host: str) -> bool:
    """Returns true if the host is a valid IPv4, IPv6 or a FQDN."""
    try:
        ipaddress.ip_address(host)
    except Exception:
        return _is_valid_hostname(host)
    else:
        return True


def _is_valid_hostname(hostname: str) -> bool:
    if hostname[-1] == ".":
        # strip exactly one dot from the right, if present
        hostname = hostname[:-1]

    max_hostname_len = 253
    if len(hostname) > max_hostname_len:
        return False

    labels = hostname.split(".")

    if re.match(r"[0-9]+$", labels[-1]):
        return False

    allowed = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(label) for label in labels)
