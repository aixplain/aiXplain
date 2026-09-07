"""Client module for making HTTP requests to the aiXplain API."""

from typing import Any, Iterable, Optional, Tuple, Union, List, FrozenSet
import inspect
import json
import logging
import os
import re
import requests
from requests.adapters import HTTPAdapter, Retry
from urllib.parse import urljoin, urlparse

from .exceptions import APIError, UntrustedURLError

logger = logging.getLogger(__name__)


DEFAULT_RETRY_TOTAL = 5
DEFAULT_RETRY_BACKOFF_FACTOR = 0.1

# 429 belongs in the forcelist now that ``allowed_methods`` is GET-only: retrying
# a throttled *poll* is safe, and is what lets the client honour the server's own
# backoff signal instead of hammering through it. A throttled POST is still never
# re-sent (see RETRY_ALLOWED_METHODS below), so this cannot duplicate a billable
# submission.
DEFAULT_RETRY_STATUS_FORCELIST = [429, 500, 502, 503, 504]

# urllib3's ``backoff_jitter`` is *additive*: the sleep becomes
# ``backoff_factor * 2**(n-1) + uniform(0, backoff_jitter)``. With
# backoff_factor=0.1 the nominal sleeps are 0.1/0.2/0.4/0.8/1.6s, so 0.3s of
# spread decorrelates a fleet across that whole window without materially
# slowing any one client. Without it, a platform 5xx makes every installed copy
# of the SDK retry inside the same ~3s window, and the recovery wave
# re-degrades the platform it is recovering (BUG-942).
DEFAULT_RETRY_BACKOFF_JITTER = 0.3

# Bound both sleep sources. urllib3's own defaults are 120s of backoff and
# **6 hours** of Retry-After; honouring an unbounded header would hand a
# misconfigured (or hostile) edge the ability to pin a caller's thread.
DEFAULT_RETRY_BACKOFF_MAX = 60.0
DEFAULT_RETRY_AFTER_MAX = 60.0

# urllib3 defaults to 10/10 with block=False, so above 10 in-flight requests the
# adapter opens connections and then *discards* them instead of pooling them --
# a fresh TLS handshake per request plus a "Connection pool is full" warning
# each time. That peaks exactly when the poll burst does.
DEFAULT_POOL_CONNECTIONS = 32
DEFAULT_POOL_MAXSIZE = 64

# Methods urllib3 may retry once a request has actually been put on the wire.
# Dropping POST is what closes BUG-1090: with POST listed, a single ``/execute``
# could become up to ``total + 1`` billable submissions as soon as a default read
# timeout existed, because a model slower than DEFAULT_TIMEOUT_READ raises
# ReadTimeout inside urllib3, which then silently re-POSTs below the SDK.
#
# Scope of the guarantee, since urllib3 consults ``allowed_methods`` for only
# some retry classes: ``status_forcelist`` responses and *read* errors
# (ReadTimeoutError, ProtocolError) are now method-gated, so POST gets neither.
# *Connect* errors (ConnectTimeoutError, NewConnectionError) are still retried
# for every method — urllib3 skips the method check there by design, and safely
# so: the connection was never established, so no request bytes reached the
# backend and no run was submitted.
#
# Retrying a submission that may have landed belongs to the SDK layer, which
# knows what one costs — see ``RunnableResourceMixin._submit_with_retries`` and
# the ``run_retries`` param.
RETRY_ALLOWED_METHODS = frozenset({"GET"})

# Default (connect, read) timeout applied to every request that doesn't pass
# its own ``timeout=``.  Without one, ``requests`` waits forever: a backend
# that accepts the connection and then goes quiet blocks the calling thread
# indefinitely (observed in production: a LIST_INPUTS POST to
# /api/v2/execute hung for 938s after a RemoteDisconnected).  The read
# timeout is generous because this session also carries synchronous model
# executions; it bounds a hang, it does not schedule work.  For streaming
# requests the read timeout applies per chunk, not to the whole stream.
DEFAULT_TIMEOUT_CONNECT = 10.0
DEFAULT_TIMEOUT_READ = 300.0
TimeoutType = Union[float, Tuple[float, float]]


def _timeout_from_env(name: str, default: float) -> float:
    """Read a positive float timeout from ``name``, falling back to ``default``.

    A malformed value must not silently remove the bound the variable exists
    to configure, so it logs and keeps the default.
    """
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        logger.warning(f"Ignoring non-numeric {name}={raw!r}; using {default}s")
        return default
    if value <= 0:
        logger.warning(f"Ignoring non-positive {name}={raw!r}; using {default}s")
        return default
    return value


def default_timeout() -> Tuple[float, float]:
    """Resolve the default (connect, read) timeout, honouring env overrides.

    ``AIXPLAIN_HTTP_CONNECT_TIMEOUT`` / ``AIXPLAIN_HTTP_READ_TIMEOUT`` (seconds)
    override the built-in defaults per environment without a code change.
    """
    return (
        _timeout_from_env("AIXPLAIN_HTTP_CONNECT_TIMEOUT", DEFAULT_TIMEOUT_CONNECT),
        _timeout_from_env("AIXPLAIN_HTTP_READ_TIMEOUT", DEFAULT_TIMEOUT_READ),
    )


# Hosts the SDK is willing to send ``TEAM_API_KEY`` to, on top of whatever the
# running configuration points at.  Poll URLs are chosen by a response body, so
# without an allowlist any JSON field can name the host that receives the
# credential (BUG-937).
DEFAULT_TRUSTED_URLS = (
    "https://platform-api.aixplain.com",
    "https://models.aixplain.com",
)


# Opt-in that re-enables (redacted, truncated) body logging at DEBUG.
LOG_BODIES_ENV_VAR = "AIXPLAIN_LOG_BODIES"
LOG_BODY_MAX_BYTES = 2048

# Keys whose *value* is a credential, whatever the surrounding structure.
_REDACT_KEYS = frozenset(
    {
        "x-api-key",
        "x-aixplain-key",
        "authorization",
        "api_key",
        "apikey",
        "access_key",
        "accesskey",
        "secret",
        "client_secret",
        "password",
        "token",
        "access_token",
        "refresh_token",
        "credential",
        "credentials",
    }
)

# Values that look like a credential even under a key we don't recognise: the
# leak this closes was a *third-party* Slack token nested inside a tool payload.
_TOKEN_PATTERNS = (
    re.compile(r"xox[baprs]-[\w-]+"),  # Slack
    re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9]{16,}"),  # OpenAI-style
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),  # GitHub
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"\beyJ[A-Za-z0-9._\-]{20,}"),  # JWT
)

_REDACTED = "***REDACTED***"


def _log_path(url: str) -> str:
    """Return *url* reduced to scheme, host and path, dropping the query string.

    Query strings carry presigned signatures and one-time tokens, so only the
    path is safe to put in a log record.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return "<unparseable url>"
    if not parsed.netloc:
        return parsed.path or url
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def _redact(value: Any) -> Any:
    """Return *value* with credential-shaped keys and token-shaped strings masked.

    Recurses through dicts and lists so a token nested inside a tool payload is
    caught as well as a top-level one.
    """
    if isinstance(value, dict):
        return {key: (_REDACTED if str(key).lower() in _REDACT_KEYS else _redact(item)) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        redacted = value
        for pattern in _TOKEN_PATTERNS:
            redacted = pattern.sub(_REDACTED, redacted)
        return redacted
    return value


def _render_redacted_body(value: Any) -> str:
    """Render *value* as text with credential-shaped keys and values masked.

    A body arrives here either as a structure (``json=``) or already serialised
    (``data=`` and ``response.text``). The serialised form has to be parsed back
    before it can be redacted *by key*: ``{"accessKey": "..."}`` -- which is what
    ``APIKey.list()`` returns for every key on the account -- and an ``x-api-key``
    nested in a serialised payload match none of the token patterns, so treating
    the body as an opaque string would log them verbatim (BUG-939). Anything that
    is not JSON falls back to pattern redaction alone.
    """
    if isinstance(value, (bytes, bytearray)):
        try:
            value = value.decode("utf-8")
        except UnicodeDecodeError:
            return f"<{len(value)} bytes of non-text body>"
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except ValueError:
            return _redact(value)
        if isinstance(parsed, (dict, list)):
            return json.dumps(_redact(parsed), default=str)
        return _redact(value)
    return str(_redact(value))


def _redact_body(value: Any) -> str:
    """Total wrapper around :func:`_render_redacted_body`.

    Rendering a body walks an arbitrary structure that a *response* can shape,
    so it can fail in ways the request itself would not -- deeply nested JSON
    raises ``RecursionError`` out of ``json.loads``, and a ``__str__`` on a
    caller's object can raise anything. A diagnostic must never turn a working
    call into a traceback, and it must never fall back to emitting the raw body,
    so every failure collapses to a placeholder.
    """
    try:
        return _render_redacted_body(value)
    except Exception:  # noqa: BLE001 -- a log line must not break the request
        return "<body omitted: could not be redacted>"


def _truncate(text: str) -> str:
    """Cap *text* at :data:`LOG_BODY_MAX_BYTES` characters with a visible marker."""
    if len(text) <= LOG_BODY_MAX_BYTES:
        return text
    return f"{text[:LOG_BODY_MAX_BYTES]}…(truncated)"


def _log_request(method: str, url: str, kwargs: Optional[dict] = None) -> None:
    """Log the outline of an outgoing request: method and path, nothing more.

    Headers are never logged, opt-in or not: ``request_raw`` merges the API key
    into ``kwargs["headers"]`` before this point, which is exactly how the team
    key -- and the third-party tokens inside tool payloads -- used to reach DEBUG
    logs (BUG-939). The body is logged only under ``AIXPLAIN_LOG_BODIES=1``, and
    then redacted and truncated.
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return
    logger.debug(f"Requesting {method} {_log_path(url)}")
    if not _log_bodies_enabled() or not kwargs:
        return
    body = kwargs.get("json", kwargs.get("data"))
    if body is None:
        return
    logger.debug(f"Request body ({method} {_log_path(url)}): {_truncate(_redact_body(body))}")


def _log_bodies_enabled() -> bool:
    """True when the operator explicitly opted into body logging."""
    return os.getenv(LOG_BODIES_ENV_VAR, "").strip().lower() in ("1", "true", "yes", "on")


def _response_size(response: requests.Response, read_body: bool) -> Optional[int]:
    """Best-effort byte count for *response* without consuming a stream.

    ``read_body`` is False on the streaming path, where touching ``.content``
    would consume the very stream the caller is about to iterate.
    """
    length = response.headers.get("Content-Length")
    if length is not None:
        try:
            return int(length)
        except (TypeError, ValueError):
            pass
    if not read_body:
        return None
    try:
        return len(response.content)
    except Exception:
        return None


def _log_response(method: str, url: str, response: requests.Response, *, read_body: bool = True) -> None:
    """Log the outline of a response: method, path, status and byte count.

    The body itself is logged only under ``AIXPLAIN_LOG_BODIES=1`` (redacted and
    truncated) and never on the streaming path.
    """
    if not logger.isEnabledFor(logging.DEBUG):
        return
    size = _response_size(response, read_body)
    size_text = f"{size} bytes" if size is not None else "unknown size"
    logger.debug(f"Response {method} {_log_path(url)} -> {response.status_code} ({size_text})")
    if not (read_body and _log_bodies_enabled()):
        return
    try:
        body = response.text
    except Exception:
        return
    logger.debug(f"Response body ({method} {_log_path(url)}): {_truncate(_redact_body(body))}")


# Every header that carries an aiXplain credential.  These are custom headers,
# so ``requests`` does not strip them across a redirect the way it does
# ``Authorization`` -- ``_AixplainSession`` has to do it.
AUTH_HEADER_NAMES = ("x-api-key", "x-aixplain-key")

# Comma-separated ``host[:port]`` or full URLs, for on-prem/regional deployments
# whose poll hosts are not derivable from the configured endpoints.
TRUSTED_HOSTS_ENV_VAR = "AIXPLAIN_TRUSTED_HOSTS"

Origin = Tuple[str, str, int]


def normalize_origin(url: str) -> Optional[Origin]:
    """Return the normalized ``(scheme, host, port)`` triple for *url*, or None.

    Uses ``hostname``/``port`` rather than ``netloc`` so that userinfo
    (``https://platform-api.aixplain.com@evil.example.com/x``) cannot disguise the
    real target and so ``:443`` compares equal to the implicit default. Returns
    ``None`` for anything that is not a parseable http(s) URL with a host, and for
    URLs carrying userinfo, which a legitimate aiXplain endpoint never does.
    """
    try:
        parsed = urlparse(url)
    except ValueError:
        return None
    if parsed.scheme not in ("http", "https"):
        return None
    try:
        if parsed.username or parsed.password:
            return None
        host, port = parsed.hostname, parsed.port
    except ValueError:  # malformed port, e.g. "https://host:notaport/x"
        return None
    if not host:
        return None
    # ``port is None`` means "not specified", which is the scheme default. An
    # explicit ``:0`` is a distinct (unconnectable) origin, so it must not be
    # folded into the default and inherit its trust.
    if port is None:
        port = 443 if parsed.scheme == "https" else 80
    return (parsed.scheme, host.lower(), port)


def _origins_from_env() -> List[Origin]:
    """Parse ``AIXPLAIN_TRUSTED_HOSTS`` into origins, ignoring unparseable entries."""
    origins = []
    for entry in os.getenv(TRUSTED_HOSTS_ENV_VAR, "").split(","):
        entry = entry.strip()
        if not entry:
            continue
        origin = normalize_origin(entry if "://" in entry else f"https://{entry}")
        if origin is None:
            logger.warning(f"Ignoring unparseable {TRUSTED_HOSTS_ENV_VAR} entry {entry!r}")
            continue
        origins.append(origin)
    return origins


def build_trusted_origins(urls: Iterable[str]) -> FrozenSet[Origin]:
    """Build the trusted origin set from configured endpoints, defaults and env.

    Scheme is part of the origin, so plain ``http`` to an aiXplain host is not
    trusted; ``http`` is only ever trusted when an operator explicitly configured
    an ``http`` endpoint (e.g. ``BACKEND_URL=http://localhost:8000``), which is a
    deliberate opt-in on a host they control rather than something a response
    body can induce.
    """
    origins = set()
    for url in [*urls, *DEFAULT_TRUSTED_URLS]:
        if not url:
            continue
        origin = normalize_origin(url if "://" in url else f"https://{url}")
        if origin is not None:
            origins.add(origin)
    origins.update(_origins_from_env())
    return frozenset(origins)


class _AixplainSession(requests.Session):
    """Session that drops aiXplain credentials when a redirect leaves the trusted set.

    ``requests`` strips only ``Authorization`` on a host change; a custom
    ``x-api-key`` header is copied verbatim to the redirect target, so a single
    302 from a trusted host would hand the team key to an attacker-chosen one.
    Redirects stay enabled -- a legitimate ``302`` to a presigned S3 result URL
    still resolves, it just arrives unauthenticated (presigned URLs carry their
    own signature).
    """

    # Class-level default so a session restored without ``__init__`` (deepcopy,
    # pickle) fails closed -- trusting nothing means credentials are stripped on
    # every redirect, rather than ``rebuild_auth`` raising AttributeError.
    trusted_origins: FrozenSet[Origin] = frozenset()

    # ``requests.Session`` pickles only the names in ``__attrs__``; without this
    # a ``deepcopy`` of a client's session would silently drop the allowlist.
    __attrs__ = requests.Session.__attrs__ + ["trusted_origins"]

    def __init__(self, trusted_origins: FrozenSet[Origin] = frozenset()) -> None:
        """Initialize the session with the origins allowed to receive credentials."""
        super().__init__()
        self.trusted_origins = trusted_origins

    def rebuild_auth(self, prepared_request: requests.PreparedRequest, response: requests.Response) -> None:
        """Strip aiXplain credentials when the redirect target is not trusted."""
        super().rebuild_auth(prepared_request, response)
        if normalize_origin(prepared_request.url or "") not in self.trusted_origins:
            for name in AUTH_HEADER_NAMES:
                prepared_request.headers.pop(name, None)


_RETRY_INIT_PARAMS = frozenset(inspect.signature(Retry.__init__).parameters)

# The hardening kwargs this module adds that a pre-2.x urllib3 may not accept:
# ``backoff_jitter``/``backoff_max`` landed in 2.0 and ``retry_after_max`` in
# 2.1, while the only declared bound is ``requests``' own loose ``urllib3<3``.
# Deliberately a closed list -- anything *outside* it still reaches ``Retry``
# and raises, so a caller's typo is not silently discarded as "unsupported".
_OPTIONAL_RETRY_KWARGS = frozenset(
    {
        "backoff_jitter",
        "backoff_max",
        "respect_retry_after_header",
        "retry_after_max",
    }
)


def _build_retry(**kwargs: Any) -> Retry:
    """Construct a ``Retry``, dropping optional kwargs this urllib3 doesn't accept.

    Only the names in :data:`_OPTIONAL_RETRY_KWARGS` are droppable: an
    environment resolving to urllib3 1.26 must lose the jitter rather than raise
    ``TypeError``. Every other keyword is passed through untouched, so an
    unrecognised one still fails loudly instead of being quietly ignored.

    Args:
        **kwargs: Candidate ``Retry`` keyword arguments.

    Returns:
        urllib3.util.Retry: Configured with every supported kwarg.

    Raises:
        TypeError: If a keyword outside the optional set is not a ``Retry``
            parameter.
    """
    unsupported = sorted(key for key in kwargs if key in _OPTIONAL_RETRY_KWARGS and key not in _RETRY_INIT_PARAMS)
    for key in unsupported:
        kwargs.pop(key)
    if unsupported:
        logger.debug(
            "Installed urllib3 Retry does not support %s; continuing without it",
            ", ".join(unsupported),
        )
    return Retry(**kwargs)


def create_retry_session(
    total: Optional[int] = None,
    backoff_factor: Optional[float] = None,
    status_forcelist: Optional[List[int]] = None,
    trusted_origins: FrozenSet[Origin] = frozenset(),
    **kwargs: Any,
) -> requests.Session:
    """Creates a requests.Session with a specified retry strategy.

    Only ``GET`` is retried (see :data:`RETRY_ALLOWED_METHODS`): POST is not
    idempotent here, so a transport-level retry of ``/execute`` submits — and
    bills — the run again. Callers that want a run re-submitted on a transient
    failure use the SDK-level ``run_retries`` parameter instead.

    Args:
        total (int, optional): Total number of retries allowed. Defaults to 5.
        backoff_factor (float, optional): Backoff factor to apply between retry attempts. Defaults to 0.1.
        status_forcelist (list, optional): List of HTTP status codes to force a retry on.
            Defaults to [429, 500, 502, 503, 504]. Retries are jittered and honour ``Retry-After``
            (bounded by DEFAULT_RETRY_AFTER_MAX).
        trusted_origins (frozenset, optional): ``(scheme, host, port)`` triples allowed
            to receive aiXplain credentials across a redirect. Defaults to none, i.e.
            any redirect drops them.
        kwargs (dict, optional): Additional keyword arguments for internal Retry object.

    Returns:
        requests.Session: A requests.Session object with the specified retry strategy.
    """
    total = total or DEFAULT_RETRY_TOTAL
    backoff_factor = backoff_factor or DEFAULT_RETRY_BACKOFF_FACTOR
    status_forcelist = status_forcelist or DEFAULT_RETRY_STATUS_FORCELIST
    retry_kwargs: dict = {
        "total": total,
        "backoff_factor": backoff_factor,
        "status_forcelist": status_forcelist,
        "allowed_methods": RETRY_ALLOWED_METHODS,
        "backoff_jitter": DEFAULT_RETRY_BACKOFF_JITTER,
        "backoff_max": DEFAULT_RETRY_BACKOFF_MAX,
        "respect_retry_after_header": True,
        "retry_after_max": DEFAULT_RETRY_AFTER_MAX,
    }
    # Caller kwargs win over the defaults above rather than colliding with them.
    retry_kwargs.update(kwargs)
    retry_strategy = _build_retry(**retry_kwargs)
    session = _AixplainSession(trusted_origins=trusted_origins)
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=DEFAULT_POOL_CONNECTIONS,
        pool_maxsize=DEFAULT_POOL_MAXSIZE,
        pool_block=False,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class AixplainClient:
    """HTTP client for aiXplain API with retry support."""

    def __init__(
        self,
        base_url: str,
        aixplain_api_key: Optional[str] = None,
        team_api_key: Optional[str] = None,
        retry_total: int = DEFAULT_RETRY_TOTAL,
        retry_backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
        retry_status_forcelist: List[int] = DEFAULT_RETRY_STATUS_FORCELIST,
        timeout: Optional[TimeoutType] = None,
        trusted_urls: Optional[List[str]] = None,
    ) -> None:
        """Initialize AixplainClient with authentication and retry configuration.

        Args:
            base_url (str): The base URL for the API.
            aixplain_api_key (str, optional): The individual API key.
            team_api_key (str, optional): The team API key.
            retry_total (int): Total number of retries allowed. Defaults to 5.
            retry_backoff_factor (float): Backoff factor between retry attempts. Defaults to 0.1.
            retry_status_forcelist (list): HTTP status codes that trigger a retry.
                Defaults to [429, 500, 502, 503, 504].
            timeout (float or (float, float) tuple, optional): Default timeout for every
                request that doesn't pass its own ``timeout=``. Defaults to
                (AIXPLAIN_HTTP_CONNECT_TIMEOUT or 10, AIXPLAIN_HTTP_READ_TIMEOUT or 300)
                seconds. Individual calls can still override it per request.
            trusted_urls (list, optional): Extra endpoints allowed to receive the
                API key, on top of ``base_url``, the aiXplain defaults and
                ``AIXPLAIN_TRUSTED_HOSTS``. Any other URL raises
                :class:`UntrustedURLError` before a socket is opened.
        """
        self.base_url = base_url
        self.timeout: TimeoutType = timeout if timeout is not None else default_timeout()
        self.team_api_key = team_api_key
        self.aixplain_api_key = aixplain_api_key

        if not (self.aixplain_api_key or self.team_api_key):
            raise ValueError("Either `aixplain_api_key` or `team_api_key` should be set")

        if self.aixplain_api_key and self.team_api_key:
            raise ValueError("Either `aixplain_api_key` or `team_api_key` should be set")

        self.trusted_origins = build_trusted_origins([base_url, *(trusted_urls or [])])

        self.session = create_retry_session(
            total=retry_total,
            backoff_factor=retry_backoff_factor,
            status_forcelist=retry_status_forcelist,
            trusted_origins=self.trusted_origins,
        )
        # The credential deliberately does NOT live on the session: session
        # headers ride along with any absolute URL handed to ``request_raw``,
        # which is exactly how the key used to reach body-supplied hosts.
        self.session.headers.update({"Content-Type": "application/json"})

    def resolve_url(self, path: str) -> str:
        """Resolve *path* against ``base_url`` unless it is already absolute."""
        if path.startswith(("http://", "https://")):
            return path
        return urljoin(self.base_url, path)

    def is_trusted_url(self, url: str) -> bool:
        """Return True when *url* is an origin allowed to receive the API key."""
        return normalize_origin(url) in self.trusted_origins

    def ensure_trusted_url(self, path: str) -> str:
        """Resolve *path* and return it, raising unless it is a trusted origin.

        Validation happens on the *resolved* URL: a relative input such as
        ``//evil.example.com/x`` becomes an absolute foreign URL only after
        ``urljoin``, so checking the caller's string would be bypassable.

        Raises:
            UntrustedURLError: If the resolved URL is not a trusted aiXplain origin.
        """
        url = self.resolve_url(path)
        if not self.is_trusted_url(url):
            allowed = sorted(f"{scheme}://{host}:{port}" for scheme, host, port in self.trusted_origins)
            raise UntrustedURLError(
                f"Refusing to send credentials to untrusted URL {url!r}. "
                f"Allowed origins: {allowed}. "
                f"Set {TRUSTED_HOSTS_ENV_VAR} to extend this list."
            )
        return url

    def _auth_headers(self) -> dict:
        """Return the credential headers for a single request."""
        if self.team_api_key:
            return {"x-api-key": self.team_api_key}
        return {"x-aixplain-key": self.aixplain_api_key}

    def request_raw(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Sends an HTTP request.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path or full URL
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            requests.Response: The response from the request

        Raises:
            UntrustedURLError: If the resolved URL is not a trusted aiXplain origin.
        """
        url = self.ensure_trusted_url(path)
        kwargs["headers"] = {**self._auth_headers(), **(kwargs.pop("headers", None) or {})}
        kwargs.setdefault("timeout", self.timeout)
        # ``headers`` now carries the API key, and ``kwargs`` carries the request
        # body, so neither is ever formatted into a log record (BUG-939).
        _log_request(method, url, kwargs)
        response = self.session.request(method=method, url=url, **kwargs)
        _log_response(method, url, response)
        if not response.ok:
            error_obj = None
            try:
                error_obj = response.json()
            except Exception as e:
                logger.error(f"Error parsing error response: {e}")

            if isinstance(error_obj, list):
                raise APIError(error_obj, status_code=response.status_code, response_data={"errors": error_obj})
            if error_obj:
                # supplierError carries the actionable detail (e.g. "Name already
                # exists"); the "error" field is often just a code like
                # "err.supplier_error".
                message = (
                    error_obj.get("supplierError")
                    or error_obj.get("supplier_error")
                    or error_obj.get("message")
                    or error_obj.get("error")
                    or response.text
                )
                raise APIError(
                    message,
                    status_code=error_obj.get("statusCode", response.status_code),
                    response_data=error_obj,
                    error=error_obj.get("error", response.text),
                )
            else:
                raise APIError(response.text, status_code=response.status_code, error=response.text)

        return response

    def request(self, method: str, path: str, **kwargs: Any) -> dict:
        """Sends an HTTP request.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            dict: The response from the request
        """
        response = self.request_raw(method, path, **kwargs)
        return response.json()

    def get(self, path: str, **kwargs: Any) -> dict:
        """Sends an HTTP GET request.

        Args:
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            dict: The JSON response from the request
        """
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> dict:
        """Sends an HTTP POST request.

        Args:
            path (str): URL path
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            dict: The JSON response from the request
        """
        return self.request("POST", path, **kwargs)

    def request_stream(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Sends a streaming HTTP request.

        This method is similar to request_raw but enables streaming mode,
        which is necessary for Server-Sent Events (SSE) responses.

        Args:
            method (str): HTTP method (e.g. 'GET', 'POST')
            path (str): URL path or full URL
            kwargs (dict, optional): Additional keyword arguments for the request

        Returns:
            requests.Response: The streaming response (not consumed)

        Raises:
            APIError: If the request fails
            UntrustedURLError: If the resolved URL is not a trusted aiXplain origin.
        """
        url = self.ensure_trusted_url(path)

        kwargs["headers"] = {**self._auth_headers(), **(kwargs.pop("headers", None) or {})}
        # Enable streaming mode
        kwargs["stream"] = True
        # In streaming mode the read timeout applies per chunk read, not to the
        # stream's total lifetime, so long-lived SSE streams stay safe as long
        # as the server keeps sending (events or keep-alives).
        kwargs.setdefault("timeout", self.timeout)

        _log_request(method, url, kwargs)
        response = self.session.request(method=method, url=url, **kwargs)
        # ``read_body=False``: the caller iterates this stream, so the log line
        # must not consume it.
        _log_response(method, url, response, read_body=False)

        # For streaming, we check status but don't consume the response body
        if not response.ok:
            error_obj = None
            try:
                # Try to get error details from response
                error_obj = response.json()
            except Exception as e:
                logger.error(f"Error parsing error response: {e}")

            if error_obj:
                raise APIError(
                    error_obj.get("message", error_obj.get("error", "Stream request failed")),
                    status_code=error_obj.get("statusCode", response.status_code),
                    response_data=error_obj,
                    error=error_obj.get("error", ""),
                )
            else:
                raise APIError(
                    f"Stream request failed with status {response.status_code}",
                    status_code=response.status_code,
                    error="",
                )

        return response
