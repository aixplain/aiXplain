"""Central URL trust policy for the SDK (BUG-939).

Three unrelated code paths used to trust a URL simply because it parsed:

* the configured endpoints (``BACKEND_URL``, ``MODELS_RUN_URL``,
  ``PIPELINES_RUN_URL``), which are read straight from the environment and can
  therefore be set by any ``.env`` on the machine;
* URLs handed to the SDK by a caller or read out of a backend response, which
  were gated only by ``validators.url()`` -- a *syntax* check that happily
  accepts ``http://169.254.169.254/latest/meta-data/``, ``http://127.0.0.1:8080/x``
  and ``http://10.0.0.1/``;
* the presigned ``uploadUrl``, which decides where every dataset, database file
  and attachment is PUT.

All three decisions live here so the call sites stay one-liners and the policy
cannot drift between v1, v2 and ``aixplain/utils``. This module deliberately
imports nothing from ``aixplain.v2`` -- it is consumed by ``aixplain.utils.config``
and by v1, neither of which may depend on v2.

Residual risk: :func:`safe_get` resolves the host to validate it and then lets
``requests`` resolve it again to connect, so a hostile resolver serving a
zero-TTL record can still swing the second lookup (classic DNS rebinding).
Closing that window requires connecting to the pinned address with an explicit
``Host`` header and an SNI override; it is tracked separately.
"""

import ipaddress
import logging
import os
import socket
from typing import Any, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse

import requests

logger = logging.getLogger(__name__)

#: Opt-in that allows plain ``http://`` config and upload URLs (local dev, on-prem).
INSECURE_OPT_IN_ENV_VAR = "AIXPLAIN_ALLOW_INSECURE_URLS"

#: Opt-in that allows :func:`safe_get` to reach private/loopback addresses.
ALLOW_PRIVATE_FETCH_ENV_VAR = "AIXPLAIN_ALLOW_PRIVATE_FETCH"

#: Comma-separated extra hosts/suffixes accepted by :func:`validate_upload_url`.
UPLOAD_ALLOWLIST_ENV_VAR = "AIXPLAIN_UPLOAD_HOST_ALLOWLIST"

#: Host suffix considered "an aiXplain endpoint" for the config-URL warning.
AIXPLAIN_HOST_SUFFIX = "aixplain.com"

#: Upload hosts accepted without configuration.
DEFAULT_UPLOAD_HOST_SUFFIXES = ("amazonaws.com", "aixplain.com")

# Deliberately tighter than the API client's 300s read timeout: this fetches an
# arbitrary caller-supplied URL, so it bounds an attacker-controlled peer rather
# than a model execution.
FETCH_TIMEOUT_CONNECT = 10.0
FETCH_TIMEOUT_READ = 30.0

#: How many redirects :func:`safe_get` will follow (each one re-validated).
MAX_FETCH_REDIRECTS = 3

_ALLOWED_SCHEMES = frozenset({"http", "https"})
_TRUTHY = frozenset({"1", "true", "yes", "on"})
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_METADATA_HOSTS = frozenset({"metadata.google.internal", "metadata.goog"})
_METADATA_IPS = frozenset({"169.254.169.254", "fd00:ec2::254"})
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})
# NAT64: ``64:ff9b::7f00:1`` is 127.0.0.1 reached over IPv6.
_NAT64_PREFIX = ipaddress.ip_network("64:ff9b::/96")

# ``(variable, host)`` pairs already warned about, so a module reload or a second
# ``Aixplain()`` does not repeat the line. A plain set (not ``lru_cache``) so a
# test fixture can clear it.
_WARNED_CONFIG_HOSTS: Set[Tuple[str, str]] = set()


class UnsafeURLError(ValueError):
    """Raised when a URL fails the SDK's trust policy.

    Subclasses :class:`ValueError` so existing ``except ValueError`` handlers at
    the call sites keep working.
    """


def _env_flag(name: str) -> bool:
    """Return True when environment variable *name* holds an affirmative value."""
    return os.getenv(name, "").strip().lower() in _TRUTHY


def _parse_http_url(url: str, label: str) -> Any:
    """Parse *url* and enforce the shared structural rules.

    Rejects anything that is not an ``http``/``https`` URL with a host, and
    anything carrying userinfo (``https://trusted.example@evil.tld/``), which no
    legitimate aiXplain endpoint ever does and which exists mainly to disguise
    the real target.

    Args:
        url: The URL to parse.
        label: Human-readable name of the URL, used in error messages.

    Returns:
        urllib.parse.ParseResult: The parsed URL.

    Raises:
        UnsafeURLError: If the URL is unparseable, not http(s), carries userinfo,
            or has no host.
    """
    if not isinstance(url, str) or not url.strip():
        raise UnsafeURLError(f"{label} must be a non-empty URL string")
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise UnsafeURLError(f"{label} is not a parseable URL: {exc}")
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise UnsafeURLError(f"{label} must use http or https, got {parsed.scheme or '(none)'!r}: {url}")
    try:
        has_userinfo = bool(parsed.username or parsed.password)
        parsed.port  # noqa: B018 -- the attribute access is what validates the port
    except ValueError as exc:  # malformed port, e.g. "https://host:notaport/x"
        raise UnsafeURLError(f"{label} has a malformed host or port: {exc}")
    if has_userinfo:
        raise UnsafeURLError(f"{label} must not contain credentials in the URL: {url}")
    if not parsed.hostname:
        raise UnsafeURLError(f"{label} has no host: {url}")
    return parsed


def _host_matches(host: str, suffix: str) -> bool:
    """True if *host* equals *suffix* or is a subdomain of it.

    Suffix matching is done label-wise, so ``evil-aixplain.com`` does not match
    ``aixplain.com``.
    """
    host = host.lower().rstrip(".")
    suffix = suffix.lower().lstrip("*").lstrip(".").rstrip(".")
    return bool(suffix) and (host == suffix or host.endswith("." + suffix))


def validate_config_url(url: str, name: str) -> str:
    """Validate a configured endpoint URL (``BACKEND_URL``, ``*_RUN_URL``).

    Requires ``https://`` unless ``AIXPLAIN_ALLOW_INSECURE_URLS=1``, which is
    also what permits ``http://localhost`` for local development. Emits one
    WARNING per ``(name, host)`` when the host is not an ``aixplain.com`` host,
    because a redirected endpoint is the difference between the team key
    reaching aiXplain and reaching whoever wrote the ``.env`` (BUG-939).

    Args:
        url: The configured URL.
        name: The environment variable name, used in messages.

    Returns:
        str: *url* unchanged, when it satisfies the policy.

    Raises:
        UnsafeURLError: If the URL is not http(s), has no host, carries
            userinfo, or is ``http://`` without the explicit opt-in.
    """
    parsed = _parse_http_url(url, name)
    if parsed.scheme != "https" and not _env_flag(INSECURE_OPT_IN_ENV_VAR):
        raise UnsafeURLError(
            f"{name} must use https (got {url!r}). The API key is sent on every request, so plain http would "
            f"put it on the wire in clear text. Set {INSECURE_OPT_IN_ENV_VAR}=1 to allow http for local "
            f"development or an on-prem deployment."
        )
    host = parsed.hostname.lower()
    if host in _LOOPBACK_HOSTS:
        # A loopback endpoint under the explicit insecure opt-in is local dev;
        # warning about it every process would be pure noise.
        return url
    if not _host_matches(host, AIXPLAIN_HOST_SUFFIX) and (name, host) not in _WARNED_CONFIG_HOSTS:
        _WARNED_CONFIG_HOSTS.add((name, host))
        logger.warning(
            f"{name} points at {host!r}, which is not an aiXplain host. The aiXplain API key will be sent "
            f"there. If you did not configure this deliberately, check for a .env file or an exported "
            f"{name} in your environment."
        )
    return url


def _classify_address(raw: str) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
    """Return *raw* as an address object, unwrapping IPv4-in-IPv6 forms.

    ``::ffff:127.0.0.1`` is loopback, but ``IPv6Address.is_loopback`` is False
    for it, so the mapped form has to be unwrapped before classification.
    """
    address = ipaddress.ip_address(raw)
    if isinstance(address, ipaddress.IPv6Address):
        mapped = address.ipv4_mapped or address.sixtofour
        if mapped is not None:
            return mapped
    return address


def _is_blocked_address(address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
    """True if *address* is one the SDK must never be pointed at."""
    if str(address) in _METADATA_IPS:
        return True
    if isinstance(address, ipaddress.IPv6Address) and address in _NAT64_PREFIX:
        return True
    return bool(
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_reserved
        or address.is_multicast
        or address.is_unspecified
    )


def _resolve(host: str, port: int) -> List[str]:
    """Resolve *host* to the list of addresses a connection could actually use.

    Raises:
        UnsafeURLError: If the host does not resolve. A name that cannot be
            resolved is rejected rather than passed through, so a resolver
            failure can never be mistaken for a successful check.
    """
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Cannot resolve host {host!r}: {exc}")
    return [info[4][0] for info in infos]


def validate_fetch_url(url: str) -> str:
    """Validate a URL the SDK is about to fetch for a caller or from a response.

    ``validators.url()`` -- the check these call sites used to rely on -- is a
    syntax check: against validators 0.35.0 it returns True for
    ``http://169.254.169.254/latest/meta-data/``, ``http://127.0.0.1:8080/x``
    and ``http://10.0.0.1/`` (BUG-939). This is the security check that has to
    sit next to it: scheme allowlist, no userinfo, and *every* resolved address
    rejected if it is loopback, private, link-local, reserved, multicast,
    unspecified or a known cloud-metadata endpoint.

    Set ``AIXPLAIN_ALLOW_PRIVATE_FETCH=1`` on an on-prem deployment whose
    artifact host lives on a private range. That opt-in relaxes the *private
    range* rule only -- the cloud metadata endpoints stay refused either way.
    Nobody's artifact host is ``169.254.169.254``, and the flag exists to reach
    an internal file server, not to let a caller-supplied (or model-generated)
    URL read the container's instance credentials and upload them.

    Args:
        url: The URL about to be fetched.

    Returns:
        str: *url* unchanged, when it satisfies the policy.

    Raises:
        UnsafeURLError: If the scheme, host or any resolved address is rejected,
            or if the host does not resolve.
    """
    parsed = _parse_http_url(url, "URL")
    host = parsed.hostname.lower().rstrip(".")
    if host in _METADATA_HOSTS:
        raise UnsafeURLError(f"Refusing to fetch cloud metadata host {host!r}: {url}")
    allow_private = _env_flag(ALLOW_PRIVATE_FETCH_ENV_VAR)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    for raw in _resolve(host, port):
        try:
            address = _classify_address(raw)
        except ValueError as exc:
            raise UnsafeURLError(f"Host {host!r} resolved to an unusable address {raw!r}: {exc}")
        if str(address) in _METADATA_IPS:
            raise UnsafeURLError(
                f"Refusing to fetch {url!r}: host {host!r} resolves to the cloud metadata address "
                f"{address}, which stays blocked even under {ALLOW_PRIVATE_FETCH_ENV_VAR}."
            )
        if allow_private:
            continue
        if _is_blocked_address(address):
            raise UnsafeURLError(
                f"Refusing to fetch {url!r}: host {host!r} resolves to the non-public address {address}. "
                f"Set {ALLOW_PRIVATE_FETCH_ENV_VAR}=1 if this deployment really does host artifacts on an "
                f"internal address."
            )
    return url


def _read_bounded(response: requests.Response, max_bytes: int, url: str) -> None:
    """Consume *response* into memory, refusing to buffer more than *max_bytes*.

    The body of a fetched URL is uploaded to the platform as a utility model's
    source, so a hostile endpoint must not be able to balloon the memory of the
    process (often an agent container) that fetched it.

    Raises:
        UnsafeURLError: If the body exceeds *max_bytes*.
    """
    if getattr(response, "raw", None) is None or getattr(response, "_content_consumed", False):
        # Already buffered by the adapter: there is nothing to stream, so the
        # cap is enforced against what is in hand.
        buffered = response._content if isinstance(response._content, (bytes, bytearray)) else b""
        if len(buffered) > max_bytes:
            raise UnsafeURLError(f"Refusing to read more than {max_bytes} bytes from {url!r}")
        response._content_consumed = True
        return

    body = bytearray()
    for chunk in response.iter_content(chunk_size=8192):
        if not chunk:
            continue
        body.extend(chunk)
        if len(body) > max_bytes:
            response.close()
            raise UnsafeURLError(f"Refusing to read more than {max_bytes} bytes from {url!r}")
    response._content = bytes(body)
    response._content_consumed = True


def _credential_scope(url: str) -> Tuple[str, str]:
    """Return the ``(scheme, netloc)`` pair that request headers are scoped to.

    Headers are dropped whenever this changes across a redirect: a different
    host obviously, but also the same host over a weaker scheme.
    """
    parsed = urlparse(url)
    return parsed.scheme.lower(), parsed.netloc.lower()


def safe_get(
    url: str,
    *,
    timeout: Optional[Any] = None,
    stream: bool = False,
    headers: Optional[dict] = None,
    max_redirects: int = MAX_FETCH_REDIRECTS,
    max_bytes: Optional[int] = None,
    session: Optional[requests.Session] = None,
    **kwargs: Any,
) -> requests.Response:
    """GET *url*, applying :func:`validate_fetch_url` to it and to every redirect.

    Redirects are followed manually (``allow_redirects=False``) so that each
    ``Location`` is re-validated: a perfectly public host that 302s to
    ``http://169.254.169.254/`` is otherwise indistinguishable from a safe fetch.

    Args:
        url: The URL to fetch.
        timeout: ``requests`` timeout; defaults to
            ``(FETCH_TIMEOUT_CONNECT, FETCH_TIMEOUT_READ)``.
        stream: Leave the body unconsumed (ignored when *max_bytes* is set).
        headers: Extra request headers.
        max_redirects: How many redirects to follow before giving up.
        max_bytes: Optional cap on the response body size.
        session: Optional ``requests.Session`` to issue the request on.
        **kwargs: Forwarded to ``requests.get``.

    Returns:
        requests.Response: The final response. The status is **not** raised on,
        so callers keep their existing error handling.

    Raises:
        UnsafeURLError: If the target, or any redirect target, fails the policy,
            or if the redirect budget is exhausted.
    """
    if timeout is None:
        timeout = (FETCH_TIMEOUT_CONNECT, FETCH_TIMEOUT_READ)
    requester = session or requests
    current = url
    current_headers = headers
    for _ in range(max_redirects + 1):
        validate_fetch_url(current)
        response = requester.get(
            current,
            timeout=timeout,
            headers=current_headers,
            stream=True if max_bytes is not None else stream,
            allow_redirects=False,
            **kwargs,
        )
        location = response.headers.get("Location") if response.status_code in _REDIRECT_STATUSES else None
        if location:
            response.close()
            following = urljoin(current, location)
            if current_headers and _credential_scope(following) != _credential_scope(current):
                # ``requests`` drops ``Authorization`` across a host change; following
                # redirects by hand means doing that here, for every header, or a
                # 302 becomes a way to harvest whatever the caller passed in.
                # The scheme is part of the comparison because ``validate_fetch_url``
                # permits http: an https -> http downgrade keeps the netloc
                # identical and would otherwise put the caller's headers on the
                # wire in clear text.
                current_headers = None
            current = following
            continue
        if max_bytes is not None:
            _read_bounded(response, max_bytes, current)
        return response
    raise UnsafeURLError(f"Refusing to follow more than {max_redirects} redirects from {url!r}")


def _upload_host_suffixes() -> Tuple[str, ...]:
    """Return the allowed upload host suffixes, including the env extension."""
    extra = os.getenv(UPLOAD_ALLOWLIST_ENV_VAR, "")
    entries = [entry.strip() for entry in extra.split(",") if entry.strip()]
    return DEFAULT_UPLOAD_HOST_SUFFIXES + tuple(entries)


def validate_upload_url(url: str) -> str:
    """Validate a presigned ``uploadUrl`` before the SDK PUTs a file to it.

    The URL comes straight out of a backend response, so a compromised backend
    -- or a ``BACKEND_URL`` redirected by an ambient ``.env`` -- would otherwise
    receive every dataset, database file, skill bundle and attachment while the
    SDK reported success (BUG-939).

    ``*.amazonaws.com`` and ``*.aixplain.com`` are allowed by default; extend
    with a comma-separated ``AIXPLAIN_UPLOAD_HOST_ALLOWLIST`` (each entry may be
    a bare host, ``.suffix`` or ``*.suffix``). https is required unless
    ``AIXPLAIN_ALLOW_INSECURE_URLS=1``.

    Args:
        url: The presigned upload URL returned by the backend.

    Returns:
        str: *url* unchanged, when it satisfies the policy.

    Raises:
        UnsafeURLError: If the scheme or host is not allowed.
    """
    parsed = _parse_http_url(url, "Upload URL")
    if parsed.scheme != "https" and not _env_flag(INSECURE_OPT_IN_ENV_VAR):
        raise UnsafeURLError(
            f"Refusing to upload over plain http to {parsed.hostname!r}. Set {INSECURE_OPT_IN_ENV_VAR}=1 to allow it."
        )
    host = parsed.hostname.lower()
    suffixes = _upload_host_suffixes()
    if not any(_host_matches(host, suffix) for suffix in suffixes):
        raise UnsafeURLError(
            f"Refusing to upload to unexpected host {host!r}. Allowed: {', '.join(suffixes)}. "
            f"Set {UPLOAD_ALLOWLIST_ENV_VAR} to add a host."
        )
    return url
